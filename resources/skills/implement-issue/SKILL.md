---
name: implement-issue
description: Use when implementing an eligible GitHub issue through completion-time technical and optional UX review, validation, and a ready or draft pull request in Claude Code, Codex, or a compatible runtime.
license: MIT
---

# Implement a GitHub issue

This is the complete cross-runtime workflow. The main session implements the
issue, assesses review findings, and owns every GitHub write.

Do not load a runtime-prefixed implementation skill alongside this skill.

## 1. Check and claim the issue

Every run requires a GitHub issue. Before broad repository reading,
delegation, review, or implementation, read only enough issue metadata to
identify its repository and number. Inspect its state, labels, and complete
native `blockedBy` relationship.

Proceed only when all of these are true:

- the issue is open;
- it has `ready-for-agent`;
- it does not have `claimed`;
- it is not labelled `ready-for-human`, `epic`, or `needs-refinement`;
- every native blocking dependency is closed.

Stop if any check fails. Never remove or override an existing `claimed` label.
For an eligible issue, add `claimed` immediately. Stop on any claim write
failure. Do not begin broad implementation work unless the label write is
confirmed.

After claiming, read the complete issue and comments. Inspect linked work and
the repository guidance that applies to the files likely to change.

If the requirements are materially ambiguous, ask the person you are working
with before implementation and wait. Once implementation is underway, record
new ambiguity, make the safest in-scope decision that preserves stated
requirements, continue, and include the decision in the final report.

## 2. Implement and prove the result

The main session chooses the implementation method. Follow repository
guidance and existing project conventions. Do not impose a generic test order,
reading order, commit sequence, or command-output policy.

The main session owns every edit, implementation decision, review disposition,
and GitHub write. It may delegate only these bounded tasks:

- repository investigation;
- external research;
- failure reproduction;
- comparison of independent approaches.

Each delegated task needs a concrete output. Tell the delegate not to spawn or
delegate further work. Do not delegate implementation ownership, finding
disposition, or GitHub writes. Do not let two agents edit the same files at the
same time. Verify delegated evidence before relying on it.

Before review, collect validation evidence that proves the issue acceptance
criteria and affected behavior. Name each check, the behavior it exercises,
and the result. If a check fails, retain the diagnostic needed to understand
the failure. Do not declare implementation complete while a known failure
relevant to the issue remains.

## 3. Freeze the review target

Begin review only after the main session considers implementation complete.
Do not use completion review as implementation consultation.

Use one fixed base revision for every review. Prepare a complete review packet
containing:

- the complete issue and comments;
- the base revision;
- the committed branch diff from that base;
- all staged and unstaged changes;
- every untracked file and its contents;
- all applicable repository guidance;
- the validation evidence;
- implementation decisions needed to understand the result.

Refresh the full change set and validation evidence after every review-driven
edit. Do not edit the supplied target while a reviewer is reading it. Every
reviewer is read-only and must not delegate, spawn another agent, edit files,
or make GitHub writes. Remove delegation tools when the runtime supports
per-agent tool restrictions, and state the same limits in every reviewer
prompt.

Use this reviewer configuration throughout:

- In Codex, request `gpt-5.6-sol` with high reasoning.
- In Claude Code, request `claude-opus-5` and inherit the session effort. Do
  not set an effort override.
- In an unknown compatible runtime, inherit both model and effort. Do not
  guess provider-specific settings.

A reported model substitution or failed required reviewer launch is an
unavailable review. Record it. Never treat it as approval or silently fall
back to another model.

## 4. Run the Plan axis once

Launch one fresh Plan reviewer exactly once. Instruct it to load
`axis-review-plan` in embedded mode. Give it the complete review packet. Ask it
to return an explicit Pass or Fail, the smallest viable plan, and individually
identifiable findings with checkable evidence. Do not ask it to run another
review axis.

The launch is the one Plan-axis attempt even if it fails or reports model
substitution. Never retry the launch, resume the Plan reviewer, or rerun the
axis after edits.

Assess every Plan-axis finding. For each one, record one disposition:

- fix it and cite the resulting change and validation;
- reject it and cite checkable evidence;
- leave it unresolved and state why.

Keep the complete Plan output and every disposition for the combined reviewer.
A finding is supported when the main session accepts it or cannot reject it
with checkable evidence.

## 5. Run the combined review

After the Plan axis and its dispositions, launch one task-scoped combined
reviewer. Give it the refreshed complete review packet, the complete Plan-axis
output, and every Plan disposition.

The combined reviewer always loads `code-guidance`. It also loads `ux-design`
when the change affects a screen, view, form, layout, navigation path, control,
visible state, error, confirmation, notification, accessibility, interaction
order, destructive-action recovery, or end-user wording. It must not load or
run `axis-review-plan`.

Ask the reviewer to assess the complete implementation against the issue,
repository guidance, acceptance criteria, validation evidence, and Plan
dispositions. When `ux-design` applies, it also reviews the complete affected
experience. It ranks findings by consequence, cites checkable evidence,
separates blocking findings from suggestions, and gives a concrete correction
for every objection.

Use one combined-review thread. Permit at most four total rounds, including
the first. A failed launch or model substitution consumes a round. Do not
launch a replacement reviewer when the required reviewer is unavailable.

After each response, assess every finding. Fix each supported finding or
reject it with checkable evidence. Record a disposition for every blocking and
non-blocking finding. Refresh the complete review packet after edits.

Rerun the same combined reviewer after fixes or when disputing a supported
blocking finding. Supply every prior finding and disposition with the refreshed
packet. Stop when no supported blocking finding remains or after round four.
If a blocking fix made in round four cannot receive another round, treat the
finding as unresolved.

## 6. Choose ready or draft

Use this decision table after review:

| Review state | Pull request state |
| --- | --- |
| A required reviewer was unavailable or substituted | Draft |
| A supported Plan-axis finding remains unresolved after combined review | Draft |
| A supported blocking combined-review finding remains after round four | Draft |
| None of the conditions above applies | Ready |

Non-blocking suggestions require a recorded disposition but do not force a
draft.

For a draft, the pull request body must begin with this exact heading:

```markdown
## Unresolved review findings
```

Under it, record each unavailable review, unresolved supported Plan finding,
and unresolved supported blocking combined-review finding. Every item states:

- its review source;
- the finding or launch failure;
- the main-session disposition and evidence;
- the remaining decision or fix.

Do not create a follow-up issue automatically.

## 7. Open and verify the pull request

Open a non-draft pull request only for the Ready state. Open a draft for every
Draft state above.

Use an outcome-focused title. The body gives a concise high-level account of
the result and validation. It does not need to enumerate the diff. Both ready
and draft bodies must contain a literal `Closes #N` line for the implemented
issue. For a draft, place that line after the required first section.

After creation, verify the closing link:

```bash
gh pr view <pr> --json closingIssuesReferences
```

An empty array means the link is missing. Fix the body with `gh pr edit` and
check again. Do not report completion until the expected issue appears in
`closingIssuesReferences`.

Do not require an exact reviewer approval phrase. Do not post a separate
successful-review comment. Include review dispositions in the pull request
body only when they explain unresolved draft findings or a material decision.

On any GitHub write failure, stop making GitHub changes. Report completed
writes, the failed operation, and what remains. Finish with the pull request
URL and state, validation evidence, review outcome, and any ambiguity recorded
after implementation began.
