import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock


SKILL_DIR = Path(__file__).resolve().parents[1]
SCRIPT_PATH = SKILL_DIR / "scripts" / "session_snapshot.py"
sys.path.insert(0, str(SCRIPT_PATH.parent))
SPEC = importlib.util.spec_from_file_location("session_snapshot", SCRIPT_PATH)
session_snapshot = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(session_snapshot)
import t3_exec_wrapper

FIXTURES = Path(__file__).resolve().parent / "fixtures"


class SessionSnapshotTests(unittest.TestCase):
    def test_claude_uses_final_usage_per_message_and_redacts_evidence(self):
        result = session_snapshot.collect("claude", "claude-root", FIXTURES / "claude")

        primary = result["primary"]
        self.assertEqual(primary["usage"]["input_tokens"], 150)
        self.assertEqual(primary["usage"]["output_tokens"], 25)
        self.assertEqual(primary["billing_tokens"]["uncached_input_tokens"], 150)
        self.assertEqual(primary["billing_tokens"]["cache_read_tokens"], 20)
        self.assertEqual(primary["context"]["observed_input_tokens_peak"], 120)
        self.assertEqual(primary["tool_activity"][0]["tool"], "Bash")
        self.assertEqual(primary["tool_activity"][0]["total_seconds"], 2.0)
        self.assertEqual(primary["largest_tool_outputs"][0]["tool"], "Bash")
        self.assertEqual(primary["largest_tool_outputs"][0]["commands"], ["printf 'fixture-claude-command'"])
        self.assertEqual(primary["unreadable_shell_wrappers"], 0)
        self.assertEqual(primary["unparsed_wrappers"], 0)
        self.assertEqual(len(result["direct_subagents"]), 1)
        self.assertEqual(result["direct_subagents"][0]["usage"]["output_tokens"], 7)
        self.assertEqual(result["nested_agents"]["count"], 1)
        evidence = json.dumps(primary["evidence"])
        serialized = json.dumps(result)
        self.assertNotIn("super-secret", evidence)
        self.assertNotIn("tool-secret", evidence)
        self.assertNotIn("not emitted", evidence)
        self.assertIn("[REDACTED]", evidence)
        self.assertIn("fixture-claude-command", serialized)
        self.assertNotIn("fixture-claude-result", serialized)

    def test_codex_uses_latest_cumulative_snapshot_and_direct_children_only(self):
        result = session_snapshot.collect("codex", "root-thread", FIXTURES / "codex")

        primary = result["primary"]
        self.assertEqual(primary["usage"]["input_tokens"], 120)
        self.assertEqual(primary["usage"]["output_tokens"], 25)
        self.assertEqual(primary["billing_tokens"]["uncached_input_tokens"], 40)
        self.assertEqual(primary["billing_tokens"]["cache_read_tokens"], 80)
        self.assertEqual(primary["last_turn_usage"]["output_tokens"], 4)
        self.assertEqual(primary["context"]["model_context_window"], 200000)
        self.assertEqual(primary["tool_activity"][0]["tool"], "exec_command")
        self.assertEqual(primary["tool_activity"][0]["max_seconds"], 4.0)
        self.assertEqual(primary["largest_tool_outputs"][0]["tool"], "exec_command")
        self.assertEqual(primary["largest_tool_outputs"][0]["commands"], ["printf 'fixture-codex-command'"])
        self.assertEqual(primary["unreadable_shell_wrappers"], 0)
        self.assertEqual(primary["unparsed_wrappers"], 0)
        self.assertEqual(len(result["direct_subagents"]), 1)
        self.assertEqual(result["direct_subagents"][0]["id"], "child-thread")
        self.assertEqual(result["nested_agents"]["ids"], ["nested-thread"])
        self.assertEqual(result["other_associated_agents"]["ids"], ["guardian-thread"])
        evidence = json.dumps(primary["evidence"])
        serialized = json.dumps(result)
        self.assertIn("Root message", evidence)
        self.assertNotIn("other-secret", evidence)
        self.assertIn("[REDACTED]", evidence)
        self.assertIn("fixture-codex-command", serialized)
        self.assertNotIn("fixture-codex-result", serialized)

    def test_largest_tool_outputs_are_bounded_ordered_and_omit_unmatched_results(self):
        for runtime in ("claude", "codex"):
            with self.subTest(runtime=runtime):
                records = []
                for index in range(12):
                    call_id = f"call-{index}"
                    timestamp = f"2026-08-16T10:00:{index:02d}Z"
                    result_timestamp = f"2026-08-16T10:01:{index:02d}Z"
                    if runtime == "claude":
                        records.extend([
                            {"timestamp": timestamp, "_snapshot_bytes": 1, "message": {"content": [{"type": "tool_use", "id": call_id, "name": "Bash", "input": {"command": f"fixture-command-{index}"}}]}},
                            {"timestamp": result_timestamp, "_snapshot_bytes": index + 1, "message": {"content": [{"type": "tool_result", "tool_use_id": call_id, "content": "fixture-result-secret"}]}},
                        ])
                    else:
                        records.extend([
                            {"type": "response_item", "timestamp": timestamp, "_snapshot_bytes": 1, "payload": {"type": "function_call", "call_id": call_id, "name": "exec_command", "arguments": json.dumps({"cmd": f"fixture-command-{index}"})}},
                            {"type": "response_item", "timestamp": result_timestamp, "_snapshot_bytes": index + 1, "payload": {"type": "function_call_output", "call_id": call_id, "output": "fixture-result-secret"}},
                        ])
                if runtime == "claude":
                    records.append({"timestamp": "2026-08-16T10:02:00Z", "_snapshot_bytes": 99, "message": {"content": [{"type": "tool_result", "tool_use_id": "missing", "content": "fixture-result-secret"}]}})
                else:
                    records.append({"type": "response_item", "timestamp": "2026-08-16T10:02:00Z", "_snapshot_bytes": 99, "payload": {"type": "function_call_output", "call_id": "missing", "output": "fixture-result-secret"}})

                _, largest_outputs, _ = session_snapshot.tool_activity(records, runtime)

                self.assertEqual(len(largest_outputs), 10)
                self.assertEqual(
                    [entry["output_record_bytes_estimate"] for entry in largest_outputs],
                    list(range(12, 2, -1)),
                )
                self.assertEqual(
                    [entry["commands"] for entry in largest_outputs],
                    [[f"fixture-command-{index}"] for index in range(11, 1, -1)],
                )
                serialized = json.dumps(largest_outputs)
                self.assertNotIn("fixture-result-secret", serialized)

    def test_command_extraction_requires_explicit_supported_input(self):
        exact_command = "  printf 'command stays exact'  "
        self.assertEqual(
            session_snapshot.command_from_arguments("exec_command", {"cmd": exact_command}),
            exact_command,
        )
        self.assertEqual(
            session_snapshot.command_from_arguments("exec_command", json.dumps({"cmd": exact_command})),
            exact_command,
        )
        self.assertEqual(
            session_snapshot.command_from_arguments("Bash", {"command": exact_command}),
            exact_command,
        )
        self.assertIsNone(session_snapshot.command_from_arguments("Read", {"command": "hidden"}))
        self.assertIsNone(session_snapshot.command_from_arguments("Bash", "malformed-json"))
        self.assertIsNone(session_snapshot.command_from_arguments("Bash", {"command": 42}))

    def test_codex_custom_tool_input_retains_command_without_result_text(self):
        records = [
            {
                "type": "response_item",
                "timestamp": "2026-08-16T10:00:00Z",
                "_snapshot_bytes": 1,
                "payload": {
                    "type": "custom_tool_call",
                    "call_id": "custom-call",
                    "name": "exec_command",
                    "input": {"cmd": "printf 'custom command'", "workdir": "/tmp"},
                },
            },
            {
                "type": "response_item",
                "timestamp": "2026-08-16T10:00:01Z",
                "_snapshot_bytes": 2,
                "payload": {
                    "type": "custom_tool_call_output",
                    "call_id": "custom-call",
                    "output": "custom result secret",
                },
            },
        ]

        _, largest_outputs, _ = session_snapshot.tool_activity(records, "codex")

        self.assertEqual(largest_outputs[0]["commands"], ["printf 'custom command'"])
        serialized = json.dumps(largest_outputs)
        self.assertNotIn("/tmp", serialized)
        self.assertNotIn("custom result secret", serialized)

    def test_ambiguous_root_is_unavailable_instead_of_guessing(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            data_root = Path(temporary_directory)
            for project in ("one", "two"):
                transcript = data_root / "projects" / project / "same.jsonl"
                transcript.parent.mkdir(parents=True)
                transcript.write_text('{"type":"user","sessionId":"same"}\n')

            result = session_snapshot.safe_collect("claude", "same", data_root)

        self.assertEqual(result["status"], "unavailable")
        self.assertIn("exactly one", result["reason"])

    def test_partially_written_transcript_is_reported_without_discarding_prior_records(self):
        result = session_snapshot.collect("claude", "partial", FIXTURES / "partial")

        self.assertEqual(result["status"], "incomplete")
        self.assertIsNone(result["primary"]["usage"])
        self.assertIsNone(result["primary"]["billing_tokens"])
        self.assertIsNone(result["primary"]["unreadable_shell_wrappers"])
        self.assertIsNone(result["primary"]["unparsed_wrappers"])
        self.assertEqual(result["direct_subagents"], [])
        self.assertTrue(any("partially written" in warning for warning in result["warnings"]))

    def test_valid_session_without_subagents_reports_an_empty_direct_set(self):
        result = session_snapshot.collect("claude", "solo", FIXTURES / "no_subagents")

        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["direct_subagents"], [])
        self.assertEqual(result["nested_agents"], {"count": 0, "ids": []})

    def test_runtime_detection_refuses_dual_runtime_identity(self):
        with mock.patch.dict("os.environ", {"CODEX_THREAD_ID": "codex", "CLAUDE_SESSION_ID": "claude"}, clear=True):
            with self.assertRaises(session_snapshot.CollectionError):
                session_snapshot.detect_current_session(None, None)

    def test_configured_data_roots_honor_runtime_conventions(self):
        with mock.patch.dict("os.environ", {"CODEX_HOME": "/tmp/codex-home", "CLAUDE_CONFIG_DIR": "/tmp/claude-home"}, clear=True):
            self.assertEqual(session_snapshot.default_data_root("codex"), Path("/tmp/codex-home"))
            self.assertEqual(session_snapshot.default_data_root("claude"), Path("/tmp/claude-home"))


def _exec_call(call_id: str, timestamp: str, source: str) -> dict:
    return {
        "type": "response_item",
        "timestamp": timestamp,
        "_snapshot_bytes": 1,
        "payload": {"type": "custom_tool_call", "call_id": call_id, "name": "exec", "input": source},
    }


def _exec_result(call_id: str, timestamp: str, output: str, size: int = 1) -> dict:
    return {
        "type": "response_item",
        "timestamp": timestamp,
        "_snapshot_bytes": size,
        "payload": {"type": "custom_tool_call_output", "call_id": call_id, "output": output},
    }


class ExecWrapperCoverageTests(unittest.TestCase):
    def test_write_stdin_update_plan_and_apply_patch_wrappers_get_no_commands(self):
        write_stdin = 'const r = await tools.write_stdin({"input":"y\\n"});\ntext(r.output);'
        update_plan = 'const r = await tools.update_plan({"plan":[]});\ntext(r.output);'
        apply_patch = 'const patch = "*** Begin Patch";\nconst r = await tools.apply_patch({"patch": patch});\ntext(r.output);'

        for source in (write_stdin, update_plan, apply_patch):
            with self.subTest(source=source):
                self.assertIsNone(session_snapshot.attribute_call("exec", source).commands)

    def test_variable_assigned_before_the_call_is_attributed_to_exec_command_not_unparsed(self):
        source = 'const workdir = "/tmp";\nconst r = await tools.exec_command({"cmd":"echo hi","workdir":"/tmp"});\ntext(r.output);'

        self.assertNotEqual(t3_exec_wrapper.recognize_exec_wrapper(source).status, "recognized")
        _, largest_outputs, coverage = session_snapshot.tool_activity(
            [_exec_call("call-1", "2026-08-16T10:00:00Z", source), _exec_result("call-1", "2026-08-16T10:00:01Z", "result text")],
            "codex",
        )
        self.assertEqual(coverage["unreadable_shell_wrappers"], 1)
        self.assertEqual(coverage["unparsed_wrappers"], 0)
        self.assertIsNone(largest_outputs[0].get("commands"))

    def test_unreadable_and_unparsed_counts_are_mutually_exclusive_and_apply_patch_counts_in_neither(self):
        recognized = 'const r = await tools.exec_command({"cmd":"echo ok"});\ntext(r.output);'
        refused_with_exec_site = 'const workdir = "/tmp";\nconst r = await tools.exec_command({"cmd":"echo hi"});\ntext(r.output);'
        apply_patch = 'const patch = "*** Begin Patch";\nconst r = await tools.apply_patch({"patch": patch});\ntext(r.output);'
        unparsed = 'const x = 1;\ntext(x);'

        records = []
        for index, source in enumerate((recognized, refused_with_exec_site, apply_patch, unparsed)):
            call_id = f"exec-{index}"
            records.append(_exec_call(call_id, f"2026-08-16T10:00:{index:02d}Z", source))
            records.append(_exec_result(call_id, f"2026-08-16T10:00:{index:02d}.5Z", "secret result text"))

        _, largest_outputs, coverage = session_snapshot.tool_activity(records, "codex")

        self.assertEqual(coverage["unreadable_shell_wrappers"], 1)
        self.assertEqual(coverage["unparsed_wrappers"], 1)
        recognized_entry = next(entry for entry in largest_outputs if entry.get("commands"))
        self.assertEqual(recognized_entry["commands"], ["echo ok"])
        self.assertEqual(sum(1 for entry in largest_outputs if entry.get("commands")), 1)

    def test_end_to_end_custom_tool_call_named_exec_retains_command_without_result_text(self):
        records = [
            _exec_call("call-1", "2026-08-16T10:00:00Z", 'const r = await tools.exec_command({"cmd":"printf \'wrapped command\'","workdir":"/tmp"});\ntext(r.output);'),
            _exec_result("call-1", "2026-08-16T10:00:01Z", "wrapped result secret", size=2),
        ]

        _, largest_outputs, coverage = session_snapshot.tool_activity(records, "codex")

        self.assertEqual(largest_outputs[0]["commands"], ["printf 'wrapped command'"])
        self.assertEqual(coverage["unreadable_shell_wrappers"], 0)
        self.assertEqual(coverage["unparsed_wrappers"], 0)
        serialized = json.dumps(largest_outputs)
        self.assertNotIn("wrapped result secret", serialized)
        self.assertNotIn("/tmp", serialized)

    def test_batch_ranks_as_one_entry_with_commands_in_source_order(self):
        source = (
            "const results = await Promise.all(["
            'tools.exec_command({cmd:"echo first"}),'
            'tools.apply_patch({patch:"*** Begin Patch\\n*** End Patch"}),'
            'tools.exec_command({cmd:"echo second"})'
            "]);\nfor (const r of results) text(r.output);"
        )
        records = [
            _exec_call("call-1", "2026-08-16T10:00:00Z", source),
            _exec_result("call-1", "2026-08-16T10:00:01Z", "batch result secret", size=42),
        ]

        _, largest_outputs, coverage = session_snapshot.tool_activity(records, "codex")

        self.assertEqual(largest_outputs, [{
            "tool": "exec_command",
            "commands": ["echo first", "echo second"],
            "output_record_bytes_estimate": 42,
        }])
        self.assertEqual(coverage["unreadable_shell_wrappers"], 0)
        self.assertNotIn("batch result secret", json.dumps(largest_outputs))

    def test_refused_batch_has_no_commands_and_counts_as_unreadable_shell(self):
        source = (
            "const results = await Promise.all(["
            'tools.exec_command({cmd:"echo first"}),'
            "makeCall()"
            "]);\ntext(results);"
        )
        records = [
            _exec_call("call-1", "2026-08-16T10:00:00Z", source),
            _exec_result("call-1", "2026-08-16T10:00:01Z", "secret", size=2),
        ]

        _, largest_outputs, coverage = session_snapshot.tool_activity(records, "codex")

        self.assertIsNone(largest_outputs[0].get("commands"))
        self.assertEqual(coverage["unreadable_shell_wrappers"], 1)

    def test_map_batch_has_no_commands_and_counts_as_unreadable_shell(self):
        source = (
            'const repos = ["one", "two"]; '
            "const results = await Promise.all(repos.map(repo => "
            "tools.exec_command({cmd: `gh api repos/${repo}/releases`})));"
        )
        records = [
            _exec_call("call-1", "2026-08-16T10:00:00Z", source),
            _exec_result("call-1", "2026-08-16T10:00:01Z", "secret", size=2),
        ]

        _, largest_outputs, coverage = session_snapshot.tool_activity(records, "codex")

        self.assertIsNone(largest_outputs[0].get("commands"))
        self.assertEqual(coverage["unreadable_shell_wrappers"], 1)

    def test_single_call_wrapper_still_emits_one_command(self):
        source = 'const r = await tools.exec_command({cmd:"echo one"});\ntext(r.output);'

        self.assertEqual(session_snapshot.attribute_call("exec", source).commands, ["echo one"])


class ExecWrapperAttributionTests(unittest.TestCase):
    SOURCES = {
        "exec_command": 'const r = await tools.exec_command({"cmd":"echo hi"});\ntext(r.output);',
        "apply_patch": 'const patch = "*** Begin Patch";\nconst r = await tools.apply_patch({"patch": patch});\ntext(r.output);',
        "web__run": 'const r = await tools.web__run({"q":"release notes"});\ntext(r.output);',
    }

    def _session(self, sources_with_sizes):
        records = []
        for index, (source, size) in enumerate(sources_with_sizes):
            call_id = f"exec-{index}"
            records.append(_exec_call(call_id, f"2026-08-16T10:00:{index:02d}Z", source))
            records.append(_exec_result(call_id, f"2026-08-16T10:00:{index:02d}.5Z", "result text", size=size))
        return session_snapshot.tool_activity(records, "codex")

    def test_mixed_wrappers_produce_one_row_per_called_tool_with_its_own_byte_total(self):
        activity, _, _ = self._session([
            (self.SOURCES["exec_command"], 10),
            (self.SOURCES["apply_patch"], 20),
            (self.SOURCES["web__run"], 30),
        ])

        self.assertEqual(
            {row["tool"]: row["output_record_bytes_estimate"] for row in activity},
            {"exec_command": 10, "apply_patch": 20, "web__run": 30},
        )
        self.assertEqual([row["calls"] for row in activity], [1, 1, 1])

    def test_wrapper_with_no_readable_call_site_keeps_the_exec_row(self):
        activity, _, coverage = self._session([("const x = 1;\ntext(x);", 5)])

        self.assertEqual([row["tool"] for row in activity], ["exec"])
        self.assertEqual(coverage["unparsed_wrappers"], 1)

    def test_ranked_entries_name_the_called_tool_alongside_commands(self):
        _, largest_outputs, _ = self._session([
            (self.SOURCES["exec_command"], 10),
            (self.SOURCES["apply_patch"], 20),
        ])

        self.assertEqual(
            [(entry["tool"], entry.get("commands")) for entry in largest_outputs],
            [("apply_patch", None), ("exec_command", ["echo hi"])],
        )

    def test_refused_shell_wrapper_still_groups_under_the_tool_it_called(self):
        source = 'const workdir = "/tmp";\nconst r = await tools.exec_command({"cmd":"echo hi"});\ntext(r.output);'

        activity, largest_outputs, coverage = self._session([(source, 7)])

        self.assertEqual([row["tool"] for row in activity], ["exec_command"])
        self.assertEqual(coverage["unreadable_shell_wrappers"], 1)
        self.assertIsNone(largest_outputs[0].get("commands"))

    def test_batch_attributes_to_the_tool_its_first_element_calls(self):
        source = (
            "const results = await Promise.all(["
            'tools.apply_patch({patch:"*** Begin Patch\\n*** End Patch"}),'
            'tools.exec_command({cmd:"echo hi"})'
            "]);\nfor (const r of results) text(r.output);"
        )

        activity, largest_outputs, _ = self._session([(source, 9)])

        self.assertEqual([row["tool"] for row in activity], ["apply_patch"])
        self.assertEqual(largest_outputs[0]["commands"], ["echo hi"])

    def test_patch_body_mentioning_a_tool_call_does_not_name_the_row(self):
        source = (
            'const patch = "*** Begin Patch\\n+const hit = tools.find(x);\\n*** End Patch";\n'
            "const r = await tools.apply_patch({patch: patch});\ntext(r.output);"
        )

        activity, _, coverage = self._session([(source, 4)])

        self.assertEqual([row["tool"] for row in activity], ["apply_patch"])
        self.assertEqual(coverage["unreadable_shell_wrappers"], 0)

    def test_multiline_patch_text_before_the_call_does_not_name_the_row(self):
        source = (
            "const patch = `*** Begin Patch\n"
            "*** Update File: example.py\n"
            ' tools.web__run({q: "mentioned in unchanged code"})\n'
            "*** End Patch`;\n"
            "const r = await tools.apply_patch(patch);\ntext(r);"
        )

        activity, largest_outputs, coverage = self._session([(source, 37)])

        self.assertEqual([row["tool"] for row in activity], ["apply_patch"])
        self.assertEqual([entry["tool"] for entry in largest_outputs], ["apply_patch"])
        self.assertEqual(coverage, {"unreadable_shell_wrappers": 0, "unparsed_wrappers": 0})

    def test_repeated_signatures_count_within_the_called_tool_bucket(self):
        activity, _, _ = self._session([
            (self.SOURCES["apply_patch"], 1),
            (self.SOURCES["apply_patch"], 1),
            (self.SOURCES["exec_command"], 1),
        ])

        self.assertEqual(
            {row["tool"]: row["repeated_argument_signatures"] for row in activity},
            {"apply_patch": 1, "exec_command": 0},
        )


class SessionSummaryIncludesExecCoverageTests(unittest.TestCase):
    def test_codex_summary_reports_coverage_counts_for_exec_wrappers(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            data_root = Path(temporary_directory)
            session_directory = data_root / "sessions" / "2026" / "08" / "16"
            session_directory.mkdir(parents=True)
            transcript = session_directory / "rollout-2026-08-16T10-00-00-root-thread.jsonl"
            lines = [
                json.dumps({"type": "session_meta", "timestamp": "2026-08-16T10:00:00Z", "payload": {"id": "root-thread"}}),
                json.dumps(_exec_call("call-1", "2026-08-16T10:00:01Z", 'const x = 1;\ntext(x);')),
                json.dumps(_exec_result("call-1", "2026-08-16T10:00:02Z", "no command here")),
            ]
            transcript.write_text("\n".join(lines) + "\n")

            result = session_snapshot.collect("codex", "root-thread", data_root)

        self.assertEqual(result["primary"]["unreadable_shell_wrappers"], 0)
        self.assertEqual(result["primary"]["unparsed_wrappers"], 1)
        self.assertEqual(result["primary"]["largest_tool_outputs"][0].get("commands"), None)


def _token_count(timestamp: str, rate_limits=None, info=None) -> dict:
    payload = {"type": "token_count", "info": info if info is not None else {"total_token_usage": {"input_tokens": 1}}}
    if rate_limits is not None:
        payload["rate_limits"] = rate_limits
    return {"type": "event_msg", "timestamp": timestamp, "payload": payload}


def _weekly(used_percent, resets_at=1788660000, window_minutes=10080) -> dict:
    return {"used_percent": used_percent, "window_minutes": window_minutes, "resets_at": resets_at}


class WeeklyRateLimitTests(unittest.TestCase):
    """The weekly indicator is account-wide server-reported state, so these cases use
    synthetic records only and assert the schema stays stable for every input shape."""

    def _weekly_result(self, records, session_id="root-thread", lines=None):
        with tempfile.TemporaryDirectory() as temporary_directory:
            data_root = Path(temporary_directory)
            session_directory = data_root / "sessions" / "2026" / "08" / "16"
            session_directory.mkdir(parents=True)
            transcript = session_directory / f"rollout-2026-08-16T10-00-00-{session_id}.jsonl"
            written = [json.dumps({"type": "session_meta", "timestamp": "2026-08-16T10:00:00Z", "payload": {"id": session_id}})]
            written.extend(json.dumps(record) for record in records)
            written.extend(lines or [])
            transcript.write_text("\n".join(written) + "\n")
            return session_snapshot.collect("codex", session_id, data_root)

    def test_weekly_rate_limit_reads_a_valid_candidate_in_primary(self):
        result = self._weekly_result([_token_count("2026-08-16T10:01:00Z", {"primary": _weekly(12.5)})])

        self.assertEqual(result["rate_limits"]["weekly"], {
            "scope": "account-wide-observation",
            "comparison_status": "single_snapshot",
            "first_used_percent": None,
            "last_used_percent": 12.5,
            "observed_change_percentage_points": None,
            "first_resets_at": None,
            "last_resets_at": 1788660000,
            "window_minutes": 10080,
        })

    def test_weekly_rate_limit_reads_secondary_when_the_five_hour_window_is_primary(self):
        records = [
            _token_count("2026-08-16T10:01:00Z", {
                "primary": {"used_percent": 44.0, "window_minutes": 300, "resets_at": 1788600000},
                "secondary": _weekly(17.0),
            }),
        ]

        weekly = self._weekly_result(records)["rate_limits"]["weekly"]

        self.assertEqual(weekly["comparison_status"], "single_snapshot")
        self.assertEqual(weekly["last_used_percent"], 17.0)
        self.assertEqual(weekly["window_minutes"], 10080)

    def test_weekly_rate_limit_reports_a_percentage_point_delta_across_snapshots(self):
        records = [
            _token_count("2026-08-16T10:01:00Z", {"primary": _weekly(17.0, resets_at=1788660000)}),
            _token_count("2026-08-16T10:02:00Z", {"primary": _weekly(17.5, resets_at=1788660000)}),
            _token_count("2026-08-16T10:03:00Z", {"primary": _weekly(18.0, resets_at=1788663261)}),
        ]

        self.assertEqual(self._weekly_result(records)["rate_limits"]["weekly"], {
            "scope": "account-wide-observation",
            "comparison_status": "comparable",
            "first_used_percent": 17.0,
            "last_used_percent": 18.0,
            "observed_change_percentage_points": 1.0,
            "first_resets_at": 1788660000,
            "last_resets_at": 1788663261,
            "window_minutes": 10080,
        })

    def test_weekly_rate_limit_delta_is_rounded_so_float_noise_is_not_reported_as_movement(self):
        records = [
            _token_count("2026-08-16T10:01:00Z", {"primary": _weekly(17.1)}),
            _token_count("2026-08-16T10:02:00Z", {"primary": _weekly(18.3)}),
        ]

        self.assertNotEqual(18.3 - 17.1, 1.2)
        self.assertEqual(self._weekly_result(records)["rate_limits"]["weekly"]["observed_change_percentage_points"], 1.2)

    def test_weekly_rate_limit_stays_comparable_when_resets_at_changes_or_is_unusable(self):
        moved = [
            _token_count("2026-08-16T10:01:00Z", {"primary": _weekly(20.0, resets_at=1788660000)}),
            _token_count("2026-08-16T10:02:00Z", {"primary": _weekly(19.0, resets_at=1789264800)}),
        ]
        unusable = [
            _token_count("2026-08-16T10:01:00Z", {"primary": _weekly(20.0, resets_at="soon")}),
            _token_count("2026-08-16T10:02:00Z", {"primary": _weekly(19.0, resets_at=True)}),
        ]

        moved_weekly = self._weekly_result(moved)["rate_limits"]["weekly"]
        unusable_weekly = self._weekly_result(unusable)["rate_limits"]["weekly"]

        self.assertEqual(moved_weekly["comparison_status"], "comparable")
        self.assertEqual(moved_weekly["first_resets_at"], 1788660000)
        self.assertEqual(moved_weekly["last_resets_at"], 1789264800)
        self.assertEqual(moved_weekly["observed_change_percentage_points"], -1.0)
        self.assertEqual(unusable_weekly["comparison_status"], "comparable")
        self.assertIsNone(unusable_weekly["first_resets_at"])
        self.assertIsNone(unusable_weekly["last_resets_at"])
        self.assertEqual(unusable_weekly["observed_change_percentage_points"], -1.0)

    def test_weekly_rate_limit_reports_missing_for_absent_or_malformed_input(self):
        malformed = (
            None,
            "not-an-object",
            {},
            {"primary": {"used_percent": 10.0}},
            {"primary": {"used_percent": 10.0, "window_minutes": 300}},
            {"primary": {"used_percent": 10.0, "window_minutes": 10080.0}},
            {"primary": {"used_percent": 10.0, "window_minutes": "10080"}},
            {"primary": {"used_percent": 10.0, "window_minutes": True}},
            {"primary": _weekly(True)},
            {"primary": _weekly(float("nan"))},
            {"primary": _weekly(float("inf"))},
            {"primary": _weekly(-0.5)},
            {"primary": _weekly(100.5)},
            {"primary": _weekly("17")},
            {"primary": _weekly(None)},
        )

        for rate_limits in malformed:
            with self.subTest(rate_limits=rate_limits):
                records = [_token_count("2026-08-16T10:01:00Z", rate_limits)]

                self.assertEqual(self._weekly_result(records)["rate_limits"]["weekly"], {
                    "scope": "account-wide-observation",
                    "comparison_status": "missing",
                    "first_used_percent": None,
                    "last_used_percent": None,
                    "observed_change_percentage_points": None,
                    "first_resets_at": None,
                    "last_resets_at": None,
                    "window_minutes": None,
                })

    def test_weekly_rate_limit_accepts_the_inclusive_percentage_bounds(self):
        records = [
            _token_count("2026-08-16T10:01:00Z", {"primary": _weekly(0)}),
            _token_count("2026-08-16T10:02:00Z", {"primary": _weekly(100)}),
        ]

        weekly = self._weekly_result(records)["rate_limits"]["weekly"]

        self.assertEqual(weekly["comparison_status"], "comparable")
        self.assertEqual(weekly["first_used_percent"], 0)
        self.assertEqual(weekly["last_used_percent"], 100)
        self.assertEqual(weekly["observed_change_percentage_points"], 100)

    def test_weekly_rate_limit_reports_an_unchanged_indicator_as_a_zero_delta(self):
        records = [
            _token_count("2026-08-16T10:01:00Z", {"primary": _weekly(18.0)}),
            _token_count("2026-08-16T10:02:00Z", {"primary": _weekly(18.0)}),
        ]

        weekly = self._weekly_result(records)["rate_limits"]["weekly"]

        self.assertEqual(weekly["comparison_status"], "comparable")
        self.assertEqual(weekly["observed_change_percentage_points"], 0.0)

    def test_weekly_rate_limit_is_ambiguous_when_one_record_holds_two_weekly_candidates(self):
        records = [
            _token_count("2026-08-16T10:01:00Z", {"primary": _weekly(17.0)}),
            _token_count("2026-08-16T10:02:00Z", {"primary": _weekly(18.0), "secondary": _weekly(19.0)}),
        ]

        self.assertEqual(self._weekly_result(records)["rate_limits"]["weekly"], {
            "scope": "account-wide-observation",
            "comparison_status": "ambiguous",
            "first_used_percent": None,
            "last_used_percent": None,
            "observed_change_percentage_points": None,
            "first_resets_at": None,
            "last_resets_at": None,
            "window_minutes": None,
        })

    def test_weekly_rate_limit_is_incomplete_when_the_primary_transcript_is_incomplete(self):
        records = [
            _token_count("2026-08-16T10:01:00Z", {"primary": _weekly(17.0)}),
            _token_count("2026-08-16T10:02:00Z", {"primary": _weekly(18.0)}),
        ]

        result = self._weekly_result(records, lines=['{"type":"event_msg","payload":'])

        self.assertEqual(result["status"], "incomplete")
        self.assertEqual(result["rate_limits"]["weekly"], {
            "scope": "account-wide-observation",
            "comparison_status": "incomplete",
            "first_used_percent": None,
            "last_used_percent": None,
            "observed_change_percentage_points": None,
            "first_resets_at": None,
            "last_resets_at": None,
            "window_minutes": None,
        })

    def test_weekly_rate_limit_reports_incomplete_ahead_of_ambiguous(self):
        records = [_token_count("2026-08-16T10:01:00Z", {"primary": _weekly(18.0), "secondary": _weekly(19.0)})]

        result = self._weekly_result(records, lines=['{"type":"event_msg","payload":'])

        self.assertEqual(result["rate_limits"]["weekly"]["comparison_status"], "incomplete")

    def test_weekly_rate_limit_is_missing_when_only_a_direct_child_reports_one(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            data_root = Path(temporary_directory)
            session_directory = data_root / "sessions" / "2026" / "08" / "16"
            session_directory.mkdir(parents=True)
            (session_directory / "rollout-2026-08-16T10-00-00-root-thread.jsonl").write_text(
                "\n".join([
                    json.dumps({"type": "session_meta", "timestamp": "2026-08-16T10:00:00Z", "payload": {"id": "root-thread"}}),
                    json.dumps(_token_count("2026-08-16T10:01:00Z")),
                ]) + "\n"
            )
            (session_directory / "rollout-2026-08-16T10-00-01-child-thread.jsonl").write_text(
                "\n".join([
                    json.dumps({
                        "type": "session_meta",
                        "timestamp": "2026-08-16T10:00:01Z",
                        "payload": {"id": "child-thread", "parent_thread_id": "root-thread", "source": {"subagent": {"thread_spawn": True}}},
                    }),
                    json.dumps(_token_count("2026-08-16T10:01:00Z", {"primary": _weekly(63.0)})),
                ]) + "\n"
            )

            result = session_snapshot.collect("codex", "root-thread", data_root)

        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["direct_subagents"][0]["id"], "child-thread")
        self.assertEqual(result["rate_limits"]["weekly"]["comparison_status"], "missing")
        self.assertIsNone(result["rate_limits"]["weekly"]["last_used_percent"])
        self.assertNotIn("63.0", json.dumps(result))

    def test_weekly_rate_limit_uses_only_the_primary_transcript_and_keeps_token_totals(self):
        result = session_snapshot.collect("codex", "root-thread", FIXTURES / "codex")

        self.assertEqual(result["rate_limits"]["weekly"], {
            "scope": "account-wide-observation",
            "comparison_status": "comparable",
            "first_used_percent": 17.0,
            "last_used_percent": 18.0,
            "observed_change_percentage_points": 1.0,
            "first_resets_at": 1788660000,
            "last_resets_at": 1788663261,
            "window_minutes": 10080,
        })
        child = result["direct_subagents"][0]
        self.assertEqual(child["id"], "child-thread")
        self.assertEqual(child["usage"]["output_tokens"], 9)
        self.assertNotIn("rate_limits", child)
        self.assertNotIn("rate_limits", result["primary"])
        self.assertEqual(result["primary"]["usage"]["input_tokens"], 120)
        self.assertEqual(result["primary"]["billing_tokens"]["cache_read_tokens"], 80)
        self.assertNotIn("91.0", json.dumps(result["rate_limits"]))

    def test_weekly_rate_limit_survives_an_incomplete_direct_child(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            data_root = Path(temporary_directory)
            session_directory = data_root / "sessions" / "2026" / "08" / "16"
            session_directory.mkdir(parents=True)
            (session_directory / "rollout-2026-08-16T10-00-00-root-thread.jsonl").write_text(
                "\n".join([
                    json.dumps({"type": "session_meta", "timestamp": "2026-08-16T10:00:00Z", "payload": {"id": "root-thread"}}),
                    json.dumps(_token_count("2026-08-16T10:01:00Z", {"primary": _weekly(17.0)})),
                    json.dumps(_token_count("2026-08-16T10:02:00Z", {"primary": _weekly(18.0)})),
                ]) + "\n"
            )
            (session_directory / "rollout-2026-08-16T10-00-01-child-thread.jsonl").write_text(
                "\n".join([
                    json.dumps({
                        "type": "session_meta",
                        "timestamp": "2026-08-16T10:00:01Z",
                        "payload": {"id": "child-thread", "parent_thread_id": "root-thread", "source": {"subagent": {"thread_spawn": True}}},
                    }),
                    '{"type":"event_msg","payload":',
                ]) + "\n"
            )

            result = session_snapshot.collect("codex", "root-thread", data_root)

        self.assertEqual(result["status"], "incomplete")
        self.assertTrue(result["direct_subagents"][0]["incomplete"])
        self.assertEqual(result["rate_limits"]["weekly"]["comparison_status"], "comparable")
        self.assertEqual(result["rate_limits"]["weekly"]["observed_change_percentage_points"], 1.0)

    def test_weekly_rate_limit_is_absent_from_claude_output_and_unavailable_results(self):
        claude = session_snapshot.collect("claude", "claude-root", FIXTURES / "claude")

        self.assertNotIn("rate_limits", claude)
        self.assertNotIn("rate_limits", json.dumps(claude))

        with tempfile.TemporaryDirectory() as temporary_directory:
            unavailable = session_snapshot.safe_collect("codex", "absent", Path(temporary_directory))

        self.assertEqual(unavailable["status"], "unavailable")
        self.assertNotIn("rate_limits", unavailable)
        self.assertEqual(sorted(unavailable), ["reason", "runtime", "session_id", "status"])


if __name__ == "__main__":
    unittest.main()
