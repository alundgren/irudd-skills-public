#!/usr/bin/env python3
"""Collect a bounded, redacted snapshot of the active agent session.

The script intentionally never writes to a transcript or worktree.  It emits
metadata, short redacted message excerpts, and exact commands for ranked
command-runner outputs; other tool arguments and tool results are never
emitted.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable, NamedTuple

from t3_exec_wrapper import attribute_exec_wrapper


MAX_EVIDENCE_ITEMS = 12
MAX_EVIDENCE_CHARS = 400
MAX_LARGEST_TOOL_OUTPUTS = 10
WEEKLY_WINDOW_MINUTES = 10080
SECRET_PATTERNS = (
    re.compile(r"(?i)\b(authorization|api[_-]?key|token|password|secret)\s*[:=]\s*[^\s,;]+"),
    re.compile(r"(?i)\bbearer\s+[a-z0-9._~+/-]+"),
    re.compile(r"\bsk-[a-zA-Z0-9_-]+\b"),
    re.compile(r"https?://[^\s/@:]+:[^\s/@]+@"),
)


class CollectionError(RuntimeError):
    """The requested session cannot be collected without guessing."""


def redact(text: str) -> str:
    """Remove common secret shapes and bound the amount of message text."""
    result = text
    for pattern in SECRET_PATTERNS:
        result = pattern.sub("[REDACTED]", result)
    result = " ".join(result.split())
    if len(result) > MAX_EVIDENCE_CHARS:
        result = result[: MAX_EVIDENCE_CHARS - 1] + "…"
    return result


def read_jsonl(path: Path) -> tuple[list[dict[str, Any]], list[str]]:
    records: list[dict[str, Any]] = []
    warnings: list[str] = []
    with path.open(encoding="utf-8") as source:
        for line_number, line in enumerate(source, start=1):
            if not line.strip():
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                warnings.append(f"{path.name}: partially written or invalid JSONL at line {line_number}")
                continue
            if isinstance(record, dict):
                record["_snapshot_bytes"] = len(line.encode("utf-8"))
                records.append(record)
    return records, warnings


def numeric_fields(value: Any) -> dict[str, int | float]:
    if not isinstance(value, dict):
        return {}
    return {
        key: number
        for key, number in value.items()
        if isinstance(number, (int, float)) and not isinstance(number, bool)
    }


def add_usage(target: Counter[str], usage: dict[str, int | float]) -> None:
    for key, value in usage.items():
        target[key] += value


def billing_tokens(runtime: str, usage: dict[str, int | float]) -> dict[str, int | float | str]:
    """Normalize usage into billing categories without inventing a price."""
    if runtime == "claude":
        return {
            "uncached_input_tokens": usage.get("input_tokens", 0),
            "cache_read_tokens": usage.get("cache_read_input_tokens", 0),
            "cache_write_tokens": usage.get("cache_creation_input_tokens", 0),
            "output_tokens": usage.get("output_tokens", 0),
            "normalization": "Claude reports uncached input separately from cache reads and writes.",
        }
    cache_read = usage.get("cached_input_tokens", 0)
    cache_write = usage.get("cache_write_input_tokens", 0)
    return {
        "uncached_input_tokens": max(usage.get("input_tokens", 0) - cache_read - cache_write, 0),
        "cache_read_tokens": cache_read,
        "cache_write_tokens": cache_write,
        "output_tokens": usage.get("output_tokens", 0),
        "normalization": "Codex cached input and cache writes are reported as subsets of input_tokens.",
    }


def record_type(record: dict[str, Any]) -> str:
    value = record.get("type")
    return value if isinstance(value, str) else "unknown"


def permitted_text(value: Any) -> str | None:
    """Return only text blocks, never tool result/input content."""
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        parts = [permitted_text(item) for item in value]
        text = " ".join(part for part in parts if part)
        return text or None
    if not isinstance(value, dict):
        return None
    if value.get("type") in {"text", "input_text", "output_text"} and isinstance(value.get("text"), str):
        return value["text"]
    return None


def message_evidence(records: Iterable[dict[str, Any]]) -> list[dict[str, str]]:
    latest_by_message: dict[str, dict[str, str]] = {}
    for index, record in enumerate(records):
        kind = record_type(record)
        message = record.get("message")
        role: Any = None
        if kind == "response_item":
            payload = record.get("payload")
            if not isinstance(payload, dict) or payload.get("type") not in {"message", "agent_message"}:
                continue
            message = payload
            role = payload.get("role") or ("subagent" if payload.get("type") == "agent_message" else None)
        elif kind not in {"user", "assistant", "message"}:
            continue
        if not isinstance(message, dict):
            continue
        role = role or message.get("role")
        if role not in {"user", "assistant", "subagent"}:
            continue
        text = permitted_text(message.get("content"))
        if not text:
            continue
        message_id = message.get("id")
        key = message_id if isinstance(message_id, str) else f"record-{index}"
        latest_by_message[key] = {
            "timestamp": str(record.get("timestamp", "unknown")),
            "role": str(role),
            "text": redact(text),
        }
    evidence = sorted(latest_by_message.values(), key=lambda item: item["timestamp"])
    if len(evidence) <= MAX_EVIDENCE_ITEMS:
        return evidence
    indices = {round(index * (len(evidence) - 1) / (MAX_EVIDENCE_ITEMS - 1)) for index in range(MAX_EVIDENCE_ITEMS)}
    return [item for index, item in enumerate(evidence) if index in indices]


def source_breakdown(records: Iterable[dict[str, Any]]) -> list[dict[str, int | str]]:
    grouped: dict[str, Counter[str]] = defaultdict(Counter)
    for record in records:
        kind = record_type(record)
        grouped[kind]["records"] += 1
        grouped[kind]["bytes"] += int(record.get("_snapshot_bytes", 0))
    return [
        {"type": kind, "records": values["records"], "bytes": values["bytes"]}
        for kind, values in sorted(grouped.items(), key=lambda item: item[1]["bytes"], reverse=True)
    ]


def unavailable_summary(summary: dict[str, Any]) -> dict[str, Any]:
    """Keep an agent visible while withholding metrics affected by a bad tail."""
    return {
        "id": summary["id"],
        "incomplete": True,
        "usage": None,
        "billing_tokens": None,
        "last_turn_usage": None,
        "context": None,
        "sources": [],
        "tool_activity": [],
        "largest_tool_outputs": [],
        "unreadable_shell_wrappers": None,
        "unparsed_wrappers": None,
        "evidence": [],
    }


def parse_timestamp(value: Any) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def command_from_arguments(tool: str, arguments: Any) -> str | None:
    """Return the verbatim command for a supported argument-dict command-running tool."""
    command_key = {
        "Bash": "command",
        "exec_command": "cmd",
    }.get(tool)
    if command_key is None:
        return None

    parsed = arguments
    if isinstance(parsed, str):
        try:
            parsed = json.loads(parsed)
        except json.JSONDecodeError:
            return None
    if not isinstance(parsed, dict):
        return None
    command = parsed.get(command_key)
    return command if isinstance(command, str) else None


class RegisteredCall(NamedTuple):
    tool: str
    timestamp: datetime
    signature: str
    unbounded_read: bool
    commands: list[str] | None


class CallAttribution(NamedTuple):
    """The tool a record is grouped and ranked under, its verbatim commands, and the
    coverage bucket it falls in when a T3 wrapper produced none."""

    tool: str
    commands: list[str] | None
    coverage_bucket: str | None


def attribute_call(name: str, arguments: Any) -> CallAttribution:
    """Read one recorded call once, dispatching to one pure helper for argument-dict tools
    and another for T3 `exec` wrapper source.

    A T3 wrapper is grouped under the tool it actually called, so a session's per-tool table
    separates shell, patches and web search instead of pooling them. A wrapper with no
    readable `tools.<name>(` call site keeps `exec`, so the row stays honest about what is
    unknown. Commands are omitted (None) rather than a scalar when nothing is recognized,
    since an entry never carries both shapes."""
    if name == "exec" and isinstance(arguments, str):
        attribution = attribute_exec_wrapper(arguments)
        return CallAttribution(attribution.callee or name, attribution.commands, attribution.coverage_bucket)
    command = command_from_arguments(name, arguments)
    return CallAttribution(name, [command] if command is not None else None, None)


def tool_activity(
    records: Iterable[dict[str, Any]], runtime: str
) -> tuple[list[dict[str, int | float | str]], list[dict[str, Any]], dict[str, int]]:
    calls: dict[str, RegisteredCall] = {}
    activity: dict[str, Counter[str | float]] = defaultdict(Counter)
    completed_outputs: list[dict[str, Any]] = []
    coverage: Counter[str] = Counter()

    def register_call(call_id: str, name: str, timestamp: datetime, arguments: Any) -> None:
        try:
            serialized = json.dumps(arguments, sort_keys=True, separators=(",", ":"), default=str)
        except (TypeError, ValueError):
            serialized = "unavailable"
        signature = hashlib.sha256(serialized.encode("utf-8")).hexdigest()
        parsed = arguments
        if isinstance(arguments, str):
            try:
                parsed = json.loads(arguments)
            except json.JSONDecodeError:
                parsed = None
        unbounded_read = (
            name.lower() in {"read", "read_file", "readfile"}
            and isinstance(parsed, dict)
            and not any(key in parsed for key in {"limit", "length", "end_line"})
        )
        attribution = attribute_call(name, arguments)
        if attribution.coverage_bucket is not None:
            coverage[attribution.coverage_bucket] += 1
        tool = attribution.tool
        calls[call_id] = RegisteredCall(tool, timestamp, signature, unbounded_read, attribution.commands)
        activity[tool]["calls"] += 1
        activity[tool][f"signature:{signature}"] += 1
        if unbounded_read:
            activity[tool]["unbounded_read_calls"] += 1

    def register_result(call_id: str, timestamp: datetime, record: dict[str, Any]) -> None:
        call = calls.get(call_id)
        if not call:
            return
        output_bytes = int(record.get("_snapshot_bytes", 0))
        activity[call.tool]["completed_calls"] += 1
        activity[call.tool]["total_seconds"] += (timestamp - call.timestamp).total_seconds()
        activity[call.tool]["max_seconds"] = max(activity[call.tool]["max_seconds"], (timestamp - call.timestamp).total_seconds())
        activity[call.tool]["output_record_bytes_estimate"] += output_bytes
        output: dict[str, Any] = {"tool": call.tool}
        if call.commands:
            output["commands"] = call.commands
        output["output_record_bytes_estimate"] = output_bytes
        completed_outputs.append(output)

    for record in records:
        timestamp = parse_timestamp(record.get("timestamp"))
        if timestamp is None:
            continue
        if runtime == "codex" and record_type(record) == "response_item":
            payload = record.get("payload")
            if not isinstance(payload, dict):
                continue
            payload_type = payload.get("type")
            call_id = payload.get("call_id")
            if payload_type in {"function_call", "custom_tool_call"} and isinstance(call_id, str):
                name = payload.get("name")
                register_call(call_id, name if isinstance(name, str) else "unknown", timestamp, payload.get("arguments", payload.get("input")))
            elif payload_type in {"function_call_output", "custom_tool_call_output"} and isinstance(call_id, str):
                register_result(call_id, timestamp, record)
        if runtime == "claude":
            message = record.get("message")
            if not isinstance(message, dict):
                continue
            content = message.get("content")
            if not isinstance(content, list):
                continue
            for block in content:
                if not isinstance(block, dict):
                    continue
                block_type = block.get("type")
                if block_type == "tool_use" and isinstance(block.get("id"), str):
                    name = block.get("name")
                    register_call(block["id"], name if isinstance(name, str) else "unknown", timestamp, block.get("input"))
                elif block_type == "tool_result" and isinstance(block.get("tool_use_id"), str):
                    register_result(block["tool_use_id"], timestamp, record)
    return [
        {
            "tool": name,
            "calls": int(values["calls"]),
            "completed_calls": int(values["completed_calls"]),
            "total_seconds": round(float(values["total_seconds"]), 3),
            "max_seconds": round(float(values["max_seconds"]), 3),
            "output_record_bytes_estimate": int(values["output_record_bytes_estimate"]),
            "repeated_argument_signatures": sum(1 for key, count in values.items() if str(key).startswith("signature:") and count > 1),
            "unbounded_read_calls": int(values["unbounded_read_calls"]),
        }
        for name, values in sorted(activity.items(), key=lambda item: float(item[1]["total_seconds"]), reverse=True)
    ], sorted(
        completed_outputs,
        key=lambda entry: (
            -int(entry["output_record_bytes_estimate"]),
            str(entry["tool"]),
        ),
    )[:MAX_LARGEST_TOOL_OUTPUTS], {
        "unreadable_shell_wrappers": int(coverage["unreadable_shell_wrappers"]),
        "unparsed_wrappers": int(coverage["unparsed_wrappers"]),
    }


def claude_summary(agent_id: str, path: Path) -> tuple[dict[str, Any], list[str]]:
    records, warnings = read_jsonl(path)
    activity, largest_outputs, coverage = tool_activity(records, "claude")
    latest_by_message: dict[str, dict[str, int | float]] = {}
    for index, record in enumerate(records):
        message = record.get("message")
        if not isinstance(message, dict):
            continue
        usage = numeric_fields(message.get("usage"))
        message_id = message.get("id")
        if not usage or not isinstance(message_id, str):
            continue
        latest_by_message[message_id] = usage

    totals: Counter[str] = Counter()
    for usage in latest_by_message.values():
        add_usage(totals, usage)
    observed_input_tokens = [
        usage.get("input_tokens", 0) + usage.get("cache_read_input_tokens", 0) + usage.get("cache_creation_input_tokens", 0)
        for usage in latest_by_message.values()
    ]
    return (
        {
            "id": agent_id,
            "usage": dict(totals),
            "billing_tokens": billing_tokens("claude", dict(totals)),
            "last_turn_usage": None,
            "context": {
                "observed_input_tokens_peak": max(observed_input_tokens, default=None),
                "model_context_window": None,
            },
            "sources": source_breakdown(records),
            "tool_activity": activity,
            "largest_tool_outputs": largest_outputs,
            "unreadable_shell_wrappers": coverage["unreadable_shell_wrappers"],
            "unparsed_wrappers": coverage["unparsed_wrappers"],
            "evidence": message_evidence(records),
        },
        warnings,
    )


class WeeklyObservations(NamedTuple):
    """Accepted weekly rate-limit snapshots from one transcript, in record order, and
    whether any single record offered two valid weekly candidates at once."""

    snapshots: list[dict[str, Any]]
    ambiguous: bool


def weekly_candidate(entry: Any) -> dict[str, Any] | None:
    """Validate one rate-limit entry as a weekly observation, or reject it.

    These field names are server-reported state observed in local Codex logs, not a
    documented contract, so every value is checked before it is used and anything
    unexpected is simply not a candidate."""
    if not isinstance(entry, dict):
        return None
    window = entry.get("window_minutes")
    if isinstance(window, bool) or not isinstance(window, int) or window != WEEKLY_WINDOW_MINUTES:
        return None
    used = entry.get("used_percent")
    if isinstance(used, bool) or not isinstance(used, (int, float)):
        return None
    if not math.isfinite(used) or not 0 <= used <= 100:
        return None
    resets = entry.get("resets_at")
    return {
        "used_percent": used,
        "resets_at": None if isinstance(resets, bool) or not isinstance(resets, int) else resets,
    }


def accepted_weekly_snapshot(rate_limits: Any) -> tuple[dict[str, Any] | None, bool]:
    """Accept a record's weekly snapshot only when exactly one window is the weekly one.

    Local logs put the weekly entry in either `primary` or `secondary`, so both are read
    and neither position is assumed. Two weekly candidates in one record means the
    reading cannot be trusted, which the caller reports rather than resolves."""
    if not isinstance(rate_limits, dict):
        return None, False
    candidates = [
        candidate
        for candidate in (weekly_candidate(rate_limits.get(key)) for key in ("primary", "secondary"))
        if candidate is not None
    ]
    if len(candidates) > 1:
        return None, True
    return (candidates[0] if candidates else None), False


def weekly_observation(observations: WeeklyObservations, incomplete: bool) -> dict[str, Any]:
    """Describe the account-wide weekly indicator with one stable schema.

    This is an observation of server-reported account state, never a per-session token,
    credit, or currency amount. An incomplete primary transcript outranks ambiguity
    because nothing read from that transcript is trustworthy. `resets_at` is
    undocumented and observed to move within one session, so it is stored at both
    endpoints but never decides whether two snapshots are comparable."""
    weekly: dict[str, Any] = {
        "scope": "account-wide-observation",
        "comparison_status": "missing",
        "first_used_percent": None,
        "last_used_percent": None,
        "observed_change_percentage_points": None,
        "first_resets_at": None,
        "last_resets_at": None,
        "window_minutes": None,
    }
    if incomplete:
        weekly["comparison_status"] = "incomplete"
        return weekly
    if observations.ambiguous:
        weekly["comparison_status"] = "ambiguous"
        return weekly
    if not observations.snapshots:
        return weekly
    last = observations.snapshots[-1]
    weekly["last_used_percent"] = last["used_percent"]
    weekly["last_resets_at"] = last["resets_at"]
    weekly["window_minutes"] = WEEKLY_WINDOW_MINUTES
    if len(observations.snapshots) == 1:
        weekly["comparison_status"] = "single_snapshot"
        return weekly
    first = observations.snapshots[0]
    weekly["comparison_status"] = "comparable"
    weekly["first_used_percent"] = first["used_percent"]
    weekly["first_resets_at"] = first["resets_at"]
    # Rounded so binary floating point noise is not reported as observed movement.
    weekly["observed_change_percentage_points"] = round(last["used_percent"] - first["used_percent"], 3)
    return weekly


def codex_summary(agent_id: str, path: Path) -> tuple[dict[str, Any], list[str], WeeklyObservations]:
    records, warnings = read_jsonl(path)
    activity, largest_outputs, coverage = tool_activity(records, "codex")
    latest_total: dict[str, int | float] = {}
    latest_turn: dict[str, int | float] = {}
    context_window: int | float | None = None
    observed_input_tokens: list[int | float] = []
    weekly_snapshots: list[dict[str, Any]] = []
    ambiguous_weekly = False
    for record in records:
        if record_type(record) != "event_msg":
            continue
        payload = record.get("payload")
        if not isinstance(payload, dict) or payload.get("type") != "token_count":
            continue
        snapshot, ambiguous = accepted_weekly_snapshot(payload.get("rate_limits"))
        ambiguous_weekly = ambiguous_weekly or ambiguous
        if snapshot is not None:
            weekly_snapshots.append(snapshot)
        info = payload.get("info")
        if not isinstance(info, dict):
            continue
        total = numeric_fields(info.get("total_token_usage"))
        turn = numeric_fields(info.get("last_token_usage"))
        if total:
            latest_total = total
        if turn:
            latest_turn = turn
            if isinstance(turn.get("input_tokens"), (int, float)):
                observed_input_tokens.append(turn["input_tokens"])
        if isinstance(info.get("model_context_window"), (int, float)):
            context_window = info["model_context_window"]
    return (
        {
            "id": agent_id,
            "usage": latest_total,
            "billing_tokens": billing_tokens("codex", latest_total),
            "last_turn_usage": latest_turn or None,
            "context": {
                "observed_input_tokens_peak": max(observed_input_tokens, default=None),
                "model_context_window": context_window,
            },
            "sources": source_breakdown(records),
            "tool_activity": activity,
            "largest_tool_outputs": largest_outputs,
            "unreadable_shell_wrappers": coverage["unreadable_shell_wrappers"],
            "unparsed_wrappers": coverage["unparsed_wrappers"],
            "evidence": message_evidence(records),
        },
        warnings,
        WeeklyObservations(weekly_snapshots, ambiguous_weekly),
    )


def locate_claude_root(session_id: str, data_root: Path) -> Path:
    candidates = [
        path
        for path in (data_root / "projects").glob(f"**/{session_id}.jsonl")
        if "subagents" not in path.parts
    ]
    if len(candidates) != 1:
        raise CollectionError(f"expected exactly one Claude root transcript for the current session; found {len(candidates)}")
    return candidates[0]


def codex_metadata_header(path: Path) -> tuple[str | None, str | None, bool]:
    """Read only a bounded header from an unrelated transcript."""
    try:
        with path.open(encoding="utf-8") as source:
            for _ in range(64):
                line = source.readline()
                if not line:
                    break
                try:
                    record = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if not isinstance(record, dict) or record_type(record) != "session_meta":
                    continue
                payload = record.get("payload")
                if not isinstance(payload, dict):
                    continue
                identity = payload.get("id") or payload.get("thread_id")
                parent = payload.get("parent_thread_id")
                source_metadata = payload.get("source")
                subagent_metadata = source_metadata.get("subagent") if isinstance(source_metadata, dict) else None
                spawned = isinstance(subagent_metadata, dict) and bool(subagent_metadata.get("thread_spawn"))
                return (
                    identity if isinstance(identity, str) else None,
                    parent if isinstance(parent, str) else None,
                    spawned,
                )
    except OSError:
        return None, None, False
    return None, None, False


def locate_codex_root(session_id: str, data_root: Path) -> Path:
    candidates = list((data_root / "sessions").glob(f"**/rollout-*{session_id}.jsonl"))
    if len(candidates) != 1:
        raise CollectionError(f"expected exactly one Codex root transcript for the current session; found {len(candidates)}")
    return candidates[0]


def collect_claude(session_id: str, data_root: Path) -> dict[str, Any]:
    root = locate_claude_root(session_id, data_root)
    primary, primary_warnings = claude_summary(session_id, root)
    warnings = list(primary_warnings)
    subagent_root = root.parent / session_id / "subagents"
    direct_paths = sorted(subagent_root.glob("*.jsonl")) if subagent_root.exists() else []
    direct_subagents: list[dict[str, Any]] = []
    for path in direct_paths:
        summary, child_warnings = claude_summary(path.stem, path)
        if child_warnings:
            summary = unavailable_summary(summary)
        direct_subagents.append(summary)
        warnings.extend(child_warnings)
    nested_paths = sorted(subagent_root.glob("**/*.jsonl")) if subagent_root.exists() else []
    nested_ids = [path.stem for path in nested_paths if path.parent != subagent_root]
    if primary_warnings:
        primary = unavailable_summary(primary)
    return {
        "status": "incomplete" if warnings else "ok",
        "runtime": "claude",
        "session_id": session_id,
        "primary": primary,
        "direct_subagents": direct_subagents,
        "nested_agents": {"count": len(nested_ids), "ids": nested_ids},
        "warnings": warnings,
    }


def collect_codex(session_id: str, data_root: Path) -> dict[str, Any]:
    root = locate_codex_root(session_id, data_root)
    primary, primary_warnings, primary_weekly = codex_summary(session_id, root)
    warnings = list(primary_warnings)
    metadata: dict[str, tuple[Path, str | None, bool]] = {}
    for path in (data_root / "sessions").glob("**/rollout-*.jsonl"):
        identity, parent, spawned = codex_metadata_header(path)
        if identity:
            metadata[identity] = (path, parent, spawned)
    direct_ids = sorted(identity for identity, (_, parent, spawned) in metadata.items() if parent == session_id and spawned)
    other_root_child_ids = sorted(identity for identity, (_, parent, spawned) in metadata.items() if parent == session_id and not spawned)
    direct_subagents: list[dict[str, Any]] = []
    for identity in direct_ids:
        # A child's own rate-limit records are deliberately dropped: the collection-level
        # observation describes the account while the primary transcript ran.
        summary, child_warnings, _ = codex_summary(identity, metadata[identity][0])
        if child_warnings:
            summary = unavailable_summary(summary)
        direct_subagents.append(summary)
        warnings.extend(child_warnings)
    nested_ids: set[str] = set()
    frontier = set(direct_ids)
    while frontier:
        child_ids = {identity for identity, (_, parent, _) in metadata.items() if parent in frontier and identity not in nested_ids and identity not in direct_ids}
        nested_ids.update(child_ids)
        frontier = child_ids
    if primary_warnings:
        primary = unavailable_summary(primary)
    return {
        "status": "incomplete" if warnings else "ok",
        "runtime": "codex",
        "session_id": session_id,
        "rate_limits": {"weekly": weekly_observation(primary_weekly, bool(primary_warnings))},
        "primary": primary,
        "direct_subagents": direct_subagents,
        "nested_agents": {"count": len(nested_ids), "ids": sorted(nested_ids)},
        "other_associated_agents": {"count": len(other_root_child_ids), "ids": other_root_child_ids},
        "warnings": warnings,
    }


def collect(runtime: str, session_id: str, data_root: Path) -> dict[str, Any]:
    if runtime == "claude":
        return collect_claude(session_id, data_root)
    if runtime == "codex":
        return collect_codex(session_id, data_root)
    raise CollectionError(f"unsupported runtime: {runtime}")


def safe_collect(runtime: str, session_id: str, data_root: Path) -> dict[str, Any]:
    try:
        return collect(runtime, session_id, data_root)
    except (CollectionError, OSError, UnicodeError) as error:
        return {"status": "unavailable", "runtime": runtime, "session_id": session_id, "reason": str(error)}


def detect_current_session(runtime: str | None, session_id: str | None) -> tuple[str, str]:
    detected_runtime = runtime
    detected_id = session_id
    if not detected_runtime:
        candidates = []
        if os.environ.get("CODEX_THREAD_ID"):
            candidates.append("codex")
        if os.environ.get("CLAUDE_SESSION_ID") or os.environ.get("CLAUDE_CODE_SESSION_ID"):
            candidates.append("claude")
        if len(candidates) != 1:
            raise CollectionError("current runtime identity is unavailable or ambiguous; provide both --runtime and --session-id rather than guessing")
        detected_runtime = candidates[0]
    if not detected_id:
        if detected_runtime == "codex":
            detected_id = os.environ.get("CODEX_THREAD_ID")
        elif detected_runtime == "claude":
            detected_id = os.environ.get("CLAUDE_SESSION_ID") or os.environ.get("CLAUDE_CODE_SESSION_ID")
    if detected_runtime not in {"claude", "codex"} or not detected_id:
        raise CollectionError("current runtime/session identity is unavailable; provide both --runtime and --session-id rather than guessing")
    return detected_runtime, detected_id


def default_data_root(runtime: str) -> Path:
    if runtime == "codex":
        return Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex")))
    return Path(os.environ.get("CLAUDE_CONFIG_DIR", str(Path.home() / ".claude")))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runtime", choices=("claude", "codex"))
    parser.add_argument("--session-id")
    parser.add_argument("--data-root", type=Path)
    arguments = parser.parse_args()
    try:
        runtime, session_id = detect_current_session(arguments.runtime, arguments.session_id)
        data_root = arguments.data_root or default_data_root(runtime)
        result = safe_collect(runtime, session_id, data_root)
    except CollectionError as error:
        result = {"status": "unavailable", "reason": str(error)}
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result.get("status") == "ok" else 2


if __name__ == "__main__":
    sys.exit(main())
