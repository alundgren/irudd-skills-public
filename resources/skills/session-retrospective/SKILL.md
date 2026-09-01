---
name: session-retrospective
description: Review the current Claude Code or Codex session without requiring a PR. Produce evidence-based Efficiency, Correctness, and Speed findings for the primary agent and directly spawned subagents, with a read-only token/context snapshot and issue-ready improvement proposals when warranted.
---

# Run a session retrospective

Use this skill after work in the **current** session is complete enough to
reflect on, whether or not it produced a PR or used a particular workflow.
Its purpose is to learn from this session without changing the worktree,
transcripts, GitHub, a PR, or instructions.

## Collect a safe snapshot

Run the bundled helper first from the installed skill directory, not from the
project being reviewed:

```bash
session_retro_project_root="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
for session_retro_candidate in \
  "$session_retro_project_root/.agents/skills/session-retrospective" \
  "$session_retro_project_root/.claude/skills/session-retrospective" \
  "${CODEX_HOME:-$HOME/.codex}/skills/session-retrospective" \
  "$HOME/.claude/skills/session-retrospective"; do
  if [ -d "$session_retro_candidate" ]; then
    session_retro_skill_dir="$session_retro_candidate"
    break
  fi
done
test -n "${session_retro_skill_dir:-}" || { echo "session-retrospective is not installed" >&2; exit 2; }
python3 "$session_retro_skill_dir/scripts/session_snapshot.py"
```

It uses only the current runtime's session identity: `CODEX_THREAD_ID` for
Codex, or `CLAUDE_SESSION_ID` / `CLAUDE_CODE_SESSION_ID` for Claude Code. It
does not select the newest transcript. If an identity is absent, the root is
ambiguous, or an active transcript is incomplete, keep the affected metric
unavailable and explain the safe next step. An `incomplete` result has no
exact totals, context, source, timing, or excerpt claims for the affected
agent. Do not substitute a recent file.

For a controlled diagnostic or the sanitized fixture checks, pass both values
explicitly:

```bash
python3 scripts/session_snapshot.py --runtime codex --session-id SESSION_ID
```

The helper scans bounded Codex metadata headers to identify relationships, but
fully parses only the selected primary transcript and direct children. It
reports nested agents as excluded identifiers/counts, never folds them into
direct subagent totals. It emits final-snapshot accounting: final streamed
usage per distinct Claude message, and the latest cumulative Codex snapshot
per agent. It does not sum Codex cumulative snapshots. Codex `last_turn_usage`
is a per-turn value, not a session total.

The helper emits aggregate record sizes/types, safe per-tool output-record-byte
estimates and
repeat/read-scope indicators, measured completed-tool latency when matching
call/result timestamps exist, timeline-wide, deduplicated short redacted
excerpts, and exact commands for ranked completed outputs from command-running
tools. It never emits other tool arguments or tool results. Do not print raw
transcript content, additional credentials outside a retained command,
encrypted arguments, or long tool output. Ranked commands are session-only
evidence and are emitted verbatim, so they may contain credentials or other
sensitive text.
Treat its excerpts as bounded evidence, not a complete transcript; combine
them with the current session's in-context record and label inferences.

## Write the report

Start with one sentence naming the snapshot boundary and limitations. Then use
exactly these top-level sections, in order.

## Efficiency

Lead with a compact table separating the primary agent, directly spawned
subagents, and aggregate totals. Lead the cost view with the helper's
`billing_tokens`: uncached input, cache reads, cache writes, and output. Those
are billing categories, not a dollar estimate. Calculate an **API-equivalent**
cost only when the active model, its current rates, and applicable tool charges
are available; never present it as a subscription invoice or quota reading.

Report raw cumulative token fields and available current/peak context
separately as **context pressure**, not as a cost total. Name the largest
sources of context/token use for each group and overall, clearly marking exact
accounting versus inference from record size or timing.

Identify meaningful waste only: broad/repeated reads, oversized outputs,
duplicate work, or unproductive communication. Necessary evidence is not a
problem merely because it consumed context. State concrete improvements where
the evidence supports them.

`tool_activity` groups by the tool a call actually reached. Where a runtime
records every call under one wrapper name, shell runs, file patches and web
searches still appear as separate per-tool rows. A row named after the wrapper
itself means calls whose tool could not be read, counted by
`unparsed_wrappers`.

Use both `tool_activity`'s aggregate per-tool `output_record_bytes_estimate`
and `largest_tool_outputs` when the snapshot provides them. The latter ranks
at most ten completed output records per agent by bounded record-byte
estimate. It is an inspection signal, not an exact tool-result size or a
defect. Use current-session evidence to distinguish necessary diagnostic
output, including failure diagnosis, from avoidable verbosity in successful
output.

Use those aggregate and ranked estimates to name the largest output-volume
opportunities. For a command-running entry, cite its exact `commands`, a list,
and `output_record_bytes_estimate` together. Do not infer a command from a
generic tool name. A ranked entry with no `commands` still ranks; name it by
tool and size only, and do not guess its shell command. When an agent's
`commands` contains more than one item, the byte total belongs to the batch,
not to any one command in the list. Do not split or otherwise attribute those
bytes among the commands. When an agent's
`unreadable_shell_wrappers` and `unparsed_wrappers` counts are available,
report them as the bound on shell-command coverage rather than silently
listing fewer commands: `unreadable_shell_wrappers` counts wrapped shell calls
whose command text could not be safely read, and `unparsed_wrappers` counts
wrapper calls with no recognizable tool call at all. For other tools, describe
the tool or output category, not an individual tool argument or result, and
never reproduce, summarize, or infer transcript content from an
output-size signal. Recommend concise success summaries only when the
evidence supports it; full diagnostic output remains appropriate for
correctness, safety, or review.

### Weekly account indicator

A Codex snapshot carries a top-level `rate_limits.weekly` object read from the
primary transcript only. It is an observation of account-wide state the server
reported while this session ran. It is not a session cost, so keep it out of
`billing_tokens`, every token total, and any API-equivalent estimate, and never
convert it to tokens, credits, or money.

Report it as exactly one line and nothing else:

```
Weekly usage: <x>
```

Take `<x>` from `comparison_status`:

- `comparable`: `observed_change_percentage_points` as a percentage, such as
  `1%`, `0%`, or `-1%`. It is the last observation minus the first, already
  rounded to three decimals.
- `single_snapshot`, `missing`, `ambiguous`, or `incomplete`: `unknown`.

Omit the line entirely for a Claude snapshot, which has no such field. A Codex
snapshot with status `unavailable` has no `rate_limits` key at all; its line is
`Weekly usage: unknown`.

## Correctness

Identify rework, mistakes, or substantive feedback from direct subagents,
including a reviewer only if this session used one. Explain the most likely
cause from evidence: an unclear specification, weak workflow/instructions,
unclear repository conventions, an insufficient validation seam, or another
specific cause. Do not assume a reviewer or implementation workflow exists.

If a concrete prevention deserves follow-up, provide a self-contained issue
draft with a title, evidence/problem, proposed scope, and acceptance criteria.
Otherwise say explicitly that no follow-up issue is warranted. Never create
the issue or alter a PR in this retrospective.

## Speed

Assess tool-call execution time and workflow latency: slow tools,
unnecessarily broad reads or outputs, inappropriate tool choice, redundant
expensive commands, repeated full test suites, or intrinsically slow tests.
For each observation, distinguish work needed for confidence from avoidable
delay. Do not infer timings that are not exposed; mark them unavailable or
estimated with the method and uncertainty.

When the current session record or bounded snapshot evidence establishes both
an intent to run a focused test and execution of unrelated tests, report the
mismatch and recommend verifying the package's focused-test contract. Treat a
deliberate final full-suite run as required confidence work, not waste. Do not
flag a focused command when the available evidence cannot establish its scope.

A broad read or oversized output may appear here for latency and in Efficiency
for context cost, but cite the same evidence rather than repeating it.

## Guardrails

- The report is an as-of-now snapshot. It is not a PR postmortem and cannot
  attribute future work to an earlier change.
- Use neutral terms: **primary agent** and **subagent**. Do not assume agent
  roles, models, or a language-specific workflow.
- Preserve unavailable values. Never reconstruct exact context or token counts
  from unrelated records without labeling the method and uncertainty.
- Do not recursively analyze nested agents. Mention them only as excluded
  associated activity when the helper detects them.
