---
name: axis-review-plan
description: "Load when the Plan axis is requested for a pull request or current branch, or when a review must decide whether added machinery is justified by a small coherent plan."
---

# Axis review: plan

Review one change only. This is a gate, not a code summary. It answers whether
the change has a small, coherent solution that explains the machinery it adds.

## Select the output mode

Direct mode is the default. Use embedded mode only when the caller explicitly
requests it as part of another review workflow. Both modes use every evidence
and decision rule below. Embedded mode relaxes only the exact output format.

## Gather the right evidence

For a GitHub PR URL:

1. Read the PR description, base revision, changed-file list, and full diff.
2. Read the repository instructions and architecture records at the PR base
   revision. Do not use later PRs or outcomes to reach the verdict.

For the current branch:

1. Use the caller's base ref. If none is supplied, resolve the merge base with
   the repository's default branch and say which base was used.
2. Read the committed branch diff and staged or unstaged worktree diff.
3. Read the repository instructions and architecture records at that base.

Find an existing focused command that an agent can run to verify the central
behavior. A compile, lint, mock-call assertion, test count, or process exit is
not enough on its own.

## Decide before writing

1. Identify the enduring problem without repeating the issue wording or naming
   implementation details. Use it to judge the change; include it in the
   review only when it helps explain the result.
2. Write the smallest viable plan in at most three numbered steps. It must
   explain what happens, which component owns it, and how to prove it worked.
3. Read the change. For every substantial addition, ask which plan step needs
   it. Treat a new runtime dependency, persistent state machine, process or
   transport boundary, large module, generated file, or recovery protocol
   as substantial.
4. A substantial addition without a specific, unavoidable reason is a
   structural concern. Do not excuse it because tests cover it, documentation
   names it, or nearby code looks similar.
5. Confirm one objective verification route. Name the command, the behavior it
   exercises, and what distinguishes success from failure. If an agent cannot
   run or inspect such a route from a clean checkout, that is a concern.

Pass only when the smallest plan explains the lasting code and an objective
verification route exists. Fail for a missing plan, unearned machinery, a
competing source of truth, an unfinished lifecycle contract, or missing proof.

## Direct mode output contract

Use exactly this shape. Put the result in the heading, then begin with the first
fact that explains it. Minimize words, not line breaks. Keep one claim per
paragraph. Start a new paragraph when moving from what changed to why it
matters, or from a finding to its proof. When one point names three or more
distinct additions, introduce a bulleted list and give each addition one short
bullet.

Write as one engineer explaining the change to another. Use the exact nouns
and verbs available in the diff. Name the file, service, database, process, or
dependency instead of replacing it with a category. Keep a qualifier only when
removing it would change the claim. In the smallest plan, state validation,
persistence, ordering, and limits as behavior rather than packing them into
adjectives.

```markdown
# Review: Plan - Pass

<Begin with the first useful reason for the result. Use short paragraphs and a
short bulleted list when it makes several additions easier to scan. Include the
verification route only when it changes the result. Cite paths or symbols only
when they make the claim checkable.>

## Smallest plan

1. <step>
2. <step>
3. <step, if needed>
```

Replace `Pass` with `Fail` when the gate fails. The heading is the only result
marker. Do not add a status line, score, or conclusion after the smallest
plan.

Do not use grades, scorecards, diff statistics, architecture maps, sequences,
or praise for test volume. Do not call a change "mostly aligned" or soften a
structural concern into a suggestion.

## Embedded mode output contract

Return a clear `Pass` or `Fail`, the smallest viable plan in at most three
numbered steps, and every finding as an individually identifiable item. Give
each finding the evidence and consequence needed for the caller to record a
disposition. Natural wording and headings are allowed. Do not require the
direct mode heading or section format.

Embedded mode changes presentation only. Apply the same pass and fail rule,
including the objective verification requirement. Do not invoke another
review axis or delegate any part of the review.

## Chaining

Run this axis alone or alongside other `axis-review-*` skills. Do not invoke
other axes by default. In direct mode, preserve the exact
`# Review: Plan - Pass` or `# Review: Plan - Fail` heading so a person or CI
job can consume it deterministically. In embedded mode, follow the embedded
output contract for the calling workflow.
