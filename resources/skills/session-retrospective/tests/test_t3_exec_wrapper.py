import json
from pathlib import Path
import sys
import unittest


SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))
import t3_exec_wrapper as session_snapshot


FIXTURES = Path(__file__).resolve().parent / "fixtures"


class ExecWrapperRecognizerTests(unittest.TestCase):
    def test_recognizes_quoted_bare_and_mixed_key_forms(self):
        quoted = 'const r = await tools.exec_command({"cmd": "echo hi", "workdir": "/tmp"});\ntext(r.output);'
        bare = 'const result = await tools.exec_command({cmd: "echo hi", workdir: "/tmp"});\ntext(result.output);'
        mixed = (
            "const r = await tools.exec_command({cmd:\"sed -n '1,240p' file\",\"workdir\":\"/x\","
            '"yield_time_ms":10000});\ntext(r.output);'
        )
        for source in (quoted, bare, mixed):
            with self.subTest(source=source):
                self.assertEqual(session_snapshot.recognize_exec_wrapper(source).status, "recognized")

        self.assertEqual(session_snapshot.recognize_exec_wrapper(quoted).command, "echo hi")
        self.assertEqual(session_snapshot.recognize_exec_wrapper(bare).command, "echo hi")
        self.assertEqual(session_snapshot.recognize_exec_wrapper(mixed).command, "sed -n '1,240p' file")

    def test_accepts_cmd_with_quotes_newlines_and_shell_metacharacters(self):
        command = "printf 'a\nb' | grep \"x\" && echo $HOME; rm -rf /tmp/x*"
        source = f'const r = await tools.exec_command({{"cmd": {json.dumps(command)}}});\ntext(r.output);'

        result = session_snapshot.recognize_exec_wrapper(source)

        self.assertEqual(result.status, "recognized")
        self.assertEqual(result.command, command)

    def test_accepts_stringify_trailer_and_rejects_mismatched_identifier_reference(self):
        stringify = 'const r = await tools.exec_command({"cmd":"echo hi"});\ntext(JSON.stringify(r));'
        mismatched = 'const r = await tools.exec_command({"cmd":"echo hi"});\ntext(r2.output);'

        self.assertEqual(session_snapshot.recognize_exec_wrapper(stringify).status, "recognized")
        self.assertEqual(session_snapshot.recognize_exec_wrapper(mismatched).status, "unsupported")

    def test_identifier_spelled_out_inside_a_string_literal_is_not_a_reference(self):
        source = 'const r = await tools.exec_command({"cmd":"echo hi"});\ntext("r done");'

        self.assertEqual(session_snapshot.recognize_exec_wrapper(source).status, "unsupported")

    def test_rejects_mismatched_delimiters_and_missing_statement_separator(self):
        mismatched = 'const r = await tools.exec_command({"cmd":"echo hi"});\ntext(r.output]'
        adjacent = 'const r = await tools.exec_command({"cmd":"echo hi"});\ntext(r.output)text(r.output);'
        assignment_adjacent = 'const r = await tools.exec_command({"cmd":"echo hi"})text(r.output);'
        assignment_space_only = 'const r = await tools.exec_command({"cmd":"echo hi"}) text(r.output);'

        self.assertEqual(session_snapshot.recognize_exec_wrapper(mismatched).status, "unsupported")
        self.assertEqual(session_snapshot.recognize_exec_wrapper(adjacent).status, "unsupported")
        self.assertEqual(session_snapshot.recognize_exec_wrapper(assignment_adjacent).status, "unsupported")
        self.assertEqual(session_snapshot.recognize_exec_wrapper(assignment_space_only).status, "unsupported")

    def test_rejects_side_effecting_arguments_and_object_keys_that_only_spell_the_identifier(self):
        side_effect = 'const r = await tools.exec_command({"cmd":"echo hi"});\ntext(store("x", r.output));'
        object_key = 'const r = await tools.exec_command({"cmd":"echo hi"});\ntext({r: "not a reference"});'

        self.assertEqual(session_snapshot.recognize_exec_wrapper(side_effect).status, "unsupported")
        self.assertEqual(session_snapshot.recognize_exec_wrapper(object_key).status, "unsupported")

    def test_accepts_side_effect_free_expressions_observed_in_t3_wrappers(self):
        sources = (
            'const r = await tools.exec_command({"cmd":"echo hi"});\ntext(r.output || "");',
            'const r = await tools.exec_command({"cmd":"echo hi"});\ntext(r.output === "" ? "empty" : r.output);',
            'const r = await tools.exec_command({"cmd":"echo hi"});\ntext(JSON.stringify({exit_code:r.exit_code,output:r.output}));',
            'const r = await tools.exec_command({"cmd":"echo hi"});\ntext(r.output);\ntext("done");',
        )

        for source in sources:
            with self.subTest(source=source):
                self.assertEqual(session_snapshot.recognize_exec_wrapper(source).status, "recognized")

    def test_rejects_a_second_tool_call_hidden_inside_a_text_argument(self):
        source = (
            'const r = await tools.exec_command({"cmd":"echo hi"});\n'
            'text(r.output);\n'
            'text(await tools.exec_command({"cmd":"echo other"}));'
        )

        self.assertEqual(session_snapshot.recognize_exec_wrapper(source).status, "unsupported")

    def test_rejects_store_trailer_comment_and_for_loop_body(self):
        store_trailer = 'const r = await tools.exec_command({"cmd":"echo hi"});\nstore("reviewer_pre_consult", r.output);'
        comment_trailer = 'const r = await tools.exec_command({"cmd":"echo hi"});\n// note\ntext(r.output);'
        for_loop = 'for (const c of cmds) {\n  const r = await tools.exec_command(c);\n  text(r.output);\n}'

        for source in (store_trailer, comment_trailer, for_loop):
            with self.subTest(source=source):
                self.assertEqual(session_snapshot.recognize_exec_wrapper(source).status, "unsupported")

    def test_rejects_malformed_json_missing_cmd_non_string_cmd_duplicate_key_and_trailing_comma(self):
        malformed_json = 'const r = await tools.exec_command({cmd: echo hi});\ntext(r.output);'
        missing_cmd = 'const r = await tools.exec_command({"workdir":"/tmp"});\ntext(r.output);'
        non_string_cmd = 'const r = await tools.exec_command({"cmd": 123});\ntext(r.output);'
        duplicate_key = 'const r = await tools.exec_command({"cmd":"a","cmd":"b"});\ntext(r.output);'
        trailing_comma = 'const r = await tools.exec_command({"cmd":"a",});\ntext(r.output);'

        for source in (malformed_json, missing_cmd, non_string_cmd, duplicate_key, trailing_comma):
            with self.subTest(source=source):
                result = session_snapshot.recognize_exec_wrapper(source)
                self.assertEqual(result.status, "malformed")
                self.assertIsNone(result.command)

    def test_rejects_oversized_wrapper_and_oversized_command_before_decoding(self):
        oversized_wrapper = (
            'const r = await tools.exec_command({"cmd":"' + ("a" * session_snapshot.MAX_EXEC_WRAPPER_SOURCE_LENGTH) + '"});\ntext(r.output);'
        )
        oversized_command = (
            'const r = await tools.exec_command({"cmd":"' + ("a" * (session_snapshot.MAX_EXEC_COMMAND_LENGTH + 1)) + '"});\ntext(r.output);'
        )

        oversized_wrapper_result = session_snapshot.recognize_exec_wrapper(oversized_wrapper)
        self.assertEqual(oversized_wrapper_result.status, "unsupported")
        self.assertIsNone(oversized_wrapper_result.command)
        oversized_command_result = session_snapshot.recognize_exec_wrapper(oversized_command)
        self.assertEqual(oversized_command_result.status, "unsupported")
        self.assertIsNone(oversized_command_result.command)

    def test_enforces_the_object_literal_length_exactly(self):
        object_prefix = '{"cmd":"echo hi","pad":"'
        object_suffix = '"}'
        exact_padding = "a" * (
            session_snapshot.MAX_EXEC_OBJECT_LITERAL_LENGTH - len(object_prefix) - len(object_suffix)
        )
        exact_object = object_prefix + exact_padding + object_suffix
        oversized_object = object_prefix + exact_padding + "a" + object_suffix

        exact = f"const r = await tools.exec_command({exact_object});\ntext(r.output);"
        oversized = f"const r = await tools.exec_command({oversized_object});\ntext(r.output);"

        self.assertEqual(len(exact_object), session_snapshot.MAX_EXEC_OBJECT_LITERAL_LENGTH)
        self.assertEqual(session_snapshot.recognize_exec_wrapper(exact).status, "recognized")
        self.assertEqual(session_snapshot.recognize_exec_wrapper(oversized).status, "unsupported")

    def test_resource_heavy_inputs_fail_closed_without_raising(self):
        huge_number = "1" * 5_000
        numeric_source = (
            f'const r = await tools.exec_command({{"cmd":"echo hi","yield_time_ms":{huge_number}}});\n'
            "text(r.output);"
        )
        many_unary = (
            'const r = await tools.exec_command({"cmd":"echo hi"});\ntext('
            + ("!" * 1_500)
            + "r.output);"
        )
        many_conditionals = (
            'const r = await tools.exec_command({"cmd":"echo hi"});\ntext('
            + "r.output"
            + (" ? r.output : r.output" * 300)
            + ");"
        )
        bounded_unary = (
            'const r = await tools.exec_command({"cmd":"echo hi"});\ntext('
            + ("!" * 200)
            + "r.output);"
        )

        for source in (numeric_source, many_unary, many_conditionals):
            with self.subTest(source_length=len(source)):
                self.assertEqual(session_snapshot.recognize_exec_wrapper(source).status, "unsupported")
        self.assertEqual(session_snapshot.recognize_exec_wrapper(bounded_unary).status, "recognized")


class ExecBatchRecognizerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixtures = json.loads((FIXTURES / "t3_exec_batches.json").read_text())

    def test_recognizes_plain_and_destructured_fixture_heads_in_source_order(self):
        expected = {
            "two_call_plain_for": [
                "python3 -m unittest",
                "rg -n TODO resources",
            ],
            "four_call_destructured_for_each": [
                "python3 -m unittest",
                "python3 resources/scripts/validate_skills.py",
                "git status --short",
                "rg --files resources/skills",
            ],
        }

        for name, commands in expected.items():
            with self.subTest(name=name):
                result = session_snapshot.recognize_exec_batch(self.fixtures[name])
                self.assertEqual(result.status, "recognized")
                self.assertEqual(result.commands, commands)

    def test_mixed_tools_contribute_only_exec_commands(self):
        source = (
            "const results = await Promise.all(["
            'tools.exec_command({cmd:"echo first"}),'
            'tools.apply_patch({patch:"*** Begin Patch\\n*** End Patch"}),'
            'tools.exec_command({"cmd":"echo second"})'
            "]);\nresults.forEach(r => text(r.output));"
        )

        result = session_snapshot.recognize_exec_batch(source)

        self.assertEqual(result.status, "recognized")
        self.assertEqual(result.commands, ["echo first", "echo second"])

    def test_unreadable_element_rejects_the_whole_batch(self):
        source = (
            "const results = await Promise.all(["
            'tools.exec_command({cmd:"echo first"}),'
            "makeCall(),"
            'tools.exec_command({cmd:"echo last"})'
            "]);\ntext(results);"
        )

        result = session_snapshot.recognize_exec_batch(source)

        self.assertEqual(result.status, "unsupported")
        self.assertIsNone(result.commands)

    def test_unreadable_arguments_reject_the_whole_batch(self):
        source = (
            "const results = await Promise.all(["
            'tools.exec_command({cmd:"echo first"}),'
            "tools.apply_patch({patch}),"
            'tools.exec_command({cmd:"echo last"})'
            "]);\ntext(results);"
        )

        result = session_snapshot.recognize_exec_batch(source)

        self.assertEqual(result.status, "malformed")
        self.assertIsNone(result.commands)

    def test_map_head_and_unclosed_array_are_rejected(self):
        map_head = (
            'const repos = ["one", "two"]; '
            "const results = await Promise.all(repos.map(repo => "
            "tools.exec_command({cmd: `gh api repos/${repo}/releases`})));"
        )
        unclosed = (
            "const results = await Promise.all(["
            'tools.exec_command({cmd:"echo first"})'
        )

        for source in (map_head, unclosed):
            with self.subTest(source=source):
                self.assertEqual(session_snapshot.recognize_exec_batch(source).status, "unsupported")

    def test_cmd_bracket_does_not_move_the_trailer_start(self):
        source = (
            "const results = await Promise.all(["
            'tools.exec_command({cmd:"printf ]"}),'
            'tools.exec_command({cmd:"echo done",options:{"nested":[1,2]}})'
            "]);\nfor (const r of results) text(r.output);"
        )

        result = session_snapshot.recognize_exec_batch(source)

        self.assertEqual(result.status, "recognized")
        self.assertEqual(result.commands, ["printf ]", "echo done"])

    def test_trailer_containing_tools_text_is_rejected(self):
        source = (
            "const results = await Promise.all(["
            'tools.exec_command({cmd:"echo first"})'
            ']);\ntext("tools.exec_command was called");'
        )

        self.assertEqual(session_snapshot.recognize_exec_batch(source).status, "unsupported")


if __name__ == "__main__":
    unittest.main()
