---
name: plan-issues
description: Use when asked to turn an early idea or a `needs-refinement` GitHub issue into reviewed, right-sized issues, including planning, refinement, decomposition, native hierarchy and dependencies, or safe publication in Claude Code, Codex, or a compatible runtime.
license: MIT
---

# Plan work into GitHub issues

The result is a small set of independently useful, verifiable issues, 
not a polished transcription of the initial request.

This is the complete workflow. Do not load a runtime-prefixed planning skill
alongside it.

## Non-negotiable safety rules

- Read the whole source issue and its comments when an issue is supplied.
  Verify it has `needs-refinement` before treating it as a refinement node.
- Discover repository, production, GitHub-label, issue-relationship, and prior
  art facts yourself. Ask the person you are working with for decisions, not
  facts that repository or GitHub evidence can establish.
- Confirm that native sub-issues and dependencies are available before
  offering publication. They are required and body text is not a substitute.
- Do not create, edit, label, close, link, or comment on any GitHub issue until
  the required review has finished, any review exceptions have separate
  approval, and the publish overview has been explicitly confirmed in this
  run.
- Do not silently reuse an issue by title or add hidden provenance markers.
  Never resume a partial publication unless recovery is explicitly chosen.
- Planning never applies `claimed`. That label is reserved for implementation.
- Do not load or run `axis-review-plan` during planning.
- The main planning session owns the plan and every GitHub write.

## Optional delegation

The main session may delegate a bounded repository investigation, external
research, failure reproduction, or comparison of independent approaches. Each
delegated task needs a concrete output. Do not delegate planning decisions,
issue drafting, review disposition, or GitHub writes. Do not delegate routine
work merely because another agent is available. Tell an investigation agent
not to delegate further, and verify its evidence before relying on it.

## 1. Establish scope and evidence

Turn the input into a provisional one-sentence outcome. Collect the facts
needed to plan it.

For a repository-backed idea, inspect its contribution and agent guidance,
relevant modules and tests, local conventions, existing related issues and
pull requests, labels, and completion convention. For a GitHub source issue,
inspect its body, comments, linked work, parent and sub-issue status,
dependencies, and labels.

Determine from repository and GitHub evidence whether the project is already
in production. If it is, ask how the work must be made safe before drafting
product delivery. Discuss applicable rollout, guardrail, rollback, and
observability requirements. Do not infer an irreversible product decision. For
a non-production project, plan direct delivery unless another fact requires a
guard.

## 2. Resolve decisions before drafting

This stage is mandatory, including when the input sounds complete. Do not
draft issues, propose a final split, or offer publication until it finishes.

1. Build a provisional design tree for the planner's own use. Include the
   desired outcome, candidate independently useful outcomes, primary
   integration points, unknowns, and likely deferred branches.
2. Find the currently unblocked decision frontier. This means every decision
   whose prerequisites are known and whose answer changes scope, safety,
   acceptance, ownership, ordering, integration, or a deliverable. Ask that
   whole frontier in one round of compact, grouped questions.
3. Challenge assumptions about speculative scope, unnecessary coupling,
   duplicate work, missing acceptance criteria, irreversible choices,
   ownership, external systems or credentials, and whether each outcome can
   ship and be verified independently.
4. Incorporate the answers and newly discovered facts, update the tree, then
   ask the next complete frontier. Repeat until no material planning decision
   remains unresolved.

Keep the internal terms out of questions to the person you are working with.
Say, "I need these decisions before drafting," and explain why a question
matters when the consequence is not obvious. When challenging assumptions,
name the concrete assumptions and ask whether they are intended. If the person
declines to decide, represent the bounded unknown as a `needs-refinement` node.
That node must state the evidence and exit condition needed to resolve it.
Never fabricate certainty.

## 3. Right-size the tree

Apply all four planner-checkable rules:

1. An executable issue delivers one independently useful behavior with named
   proof. Split behaviors that can ship and be verified independently.
2. Before an issue becomes ready, identify the likely implementation area,
   existing behavior to inspect, and a credible validation route.
3. Keep changes together when they are all required for one behavior and share
   an end-to-end check. Split unrelated components, execution environments, or
   independent validation paths.
4. Settle product choices, irreversible data decisions, access requirements,
   and external contracts that could redirect implementation.

Each executable issue has one owner and bounded unknowns. Missing discovery
warrants `needs-refinement` when it could materially change behavior, affected
components, or validation. Ordinary code uncertainty does not require a
separate investigation issue. Add no context-risk score or new issue-body
section.

For insufficiently known product work, plan a mergeable incomplete product
slice, never a throwaway prototype. If this needs an epic, its description
must explain how to use the partial delivery, what evidence to collect, which
decision that evidence unlocks, and the next refinement step. An actually
small idea may produce one or a few standalone issues. Create an `epic` only
when a related tree benefits from a root organizer.

### Taxonomy and graph rules

Use exactly these labels and roles:

| Label | Role |
| --- | --- |
| `ready-for-agent` | Executable leaf that an agent can start without a human in the loop. |
| `ready-for-human` | Executable leaf requiring a focused human action. |
| `epic` | Non-executable root organizer. |
| `needs-refinement` | Temporary non-executable node whose unknowns need another planning run. |
| `claimed` | Reserved for implementation skills and never set while planning. |

Each created issue receives exactly one planner classification. Use one
readiness label for an executable leaf, `epic` for a root, or
`needs-refinement` for a refinement node. `ready-for-agent` and
`ready-for-human` are mutually exclusive.

An epic is a root only. Epics never nest and never block one another. Under an
epic, executable leaves are direct children of that root. Use native GitHub
blocking dependencies to order leaves under the same root, or related
standalone leaves when no epic is warranted. Never create a blocker across
root-epic boundaries or between epics. Use ordinary references for related
work in separate epics. Do not represent dependencies with markdown prose or
task lists.

A standalone executable issue has no epic parent. A refinement node may remain
in a tree only while its stated unknown is unresolved. It is not executable.
Do not create an epic merely to hold one ordinary issue.

## 4. Write complete issue drafts

Use the repository's domain terms and completion convention. Make every title
outcome-focused and every body self-contained.

Every created issue contains these sections:

```md
## Goal

## Why it matters

## Requirements

## Technical prior art

## Definition of done
```

Keep technical prior art short and relevant. Cite the files, patterns, issues,
or APIs that prevent repetitive rediscovery. Do not fill it with generic
advice.

Every executable leaf also contains:

```md
## Deliberately deferred

## Completion
```

`Deliberately deferred` names excluded work and its destination. The
destination is another issue or later refinement. If nothing is deferred, say
so explicitly. Every actual deferral has a destination. `Completion` states
whether the issue closes through a PR body containing `Closes #<issue>` or by
hand after named verification.

Agent and product leaves must be independently mergeable and end-user
verifiable. When feasible for code work, their definition of done names
behavior that a unit or integration test can prove. Human leaves state the
exact human action, required access and context, evidence comment to post, and
the agent work that evidence unblocks. Refinement nodes state the unknown,
required evidence, and exit condition. Epic definitions of done aggregate
their child and outcome completion criteria rather than treating the epic as
executable.

## 5. Review the completed drafts

Start review only after every issue draft is complete and the planner considers
the full tree ready. Run one task-scoped combined reviewer. Do not run separate
technical and UX reviewers, and do not consult the reviewer while drafting.

The reviewer must load `code-guidance` and `ux-design`. Give it the source
issue or idea, complete proposed tree, labels, native-link plan, every issue
draft, discovered facts, and acceptance criteria. Ask it to review the whole
plan for technical correctness, end-user value, decomposition, overlap,
labels, dependencies, discovery safety, issue clarity, and definitions of
done. It must rank findings by consequence, cite checkable evidence, separate
blocking findings from suggestions, and give a concrete correction for every
objection.

Use one reviewer thread for the entire review. The reviewer must not delegate
or spawn another agent, edit files, or make GitHub writes. Remove its
delegation tool when the runtime supports per-agent tool restrictions. State
the same limits in its task prompt on every runtime.

Select the reviewer configuration from the current runtime:

- In Codex, request `gpt-5.6-sol` with high reasoning for the reviewer.
- In Claude Code, request `claude-opus-5` and inherit the session effort. Do
  not set an effort override.
- In an unknown compatible runtime, inherit both model and effort. Do not
  guess provider-specific settings.

If the runtime reports model substitution, cannot launch the requested
reviewer, or the reviewer becomes unavailable, record review as
unavailable/substituted. Never treat that state as approval.

Assess every finding. Fix each supported finding or reject it with checkable
evidence. Summarize what changed, what was rejected and why, and what remains.
Send every material change back to the same reviewer thread with the complete
updated review context. There is no fixed review-round cap. The person you are
working with may stop and keep the drafts at any point, with no GitHub changes.

Review ends in one of three states: passed, blocked by supported findings, or
unavailable/substituted. Publication requires a passed review or separately
approved exceptions for every unresolved supported finding or review failure.

## 6. Approve review exceptions

Use this gate only when review did not pass. List each unresolved supported
finding, reviewer launch failure, or model substitution as a named exception.
For each one, state its practical consequence and the evidence already tried.

Offer retrying review, revising the drafts, stopping and keeping the drafts, or
approving named exceptions. Ask the person you are working with to approve
each named exception separately. A general approval is not enough. Exception
approval is the explicit override for that exception. It does not authorize
publication. Record approved exceptions for the publish overview. If an
exception is declined, do not proceed to publication.

## 7. Show the publish gate

After review and any separate exception approval, show the exact publish
overview in this order:

1. Review outcome and every approved exception.
2. Missing canonical labels that publication would create.
3. The proposed issue tree. Give one sentence per issue and show its title,
   planner label, and parent or standalone status.
4. Native blockers for each affected issue.
5. Ordinary references between related work that cannot use a native blocker.

The overview must account for all titles, labels, parent/root relation, native
blockers, and ordinary references, plus the missing canonical labels and
review outcome.

Then say: "Nothing has been written to GitHub. The review outcome and any
approved exceptions are listed above. Choose `Publish this exact plan`,
`Revise`, or `Stop and keep the drafts`. Only the first choice authorizes
GitHub changes."

Require unambiguous confirmation to publish this exact plan. A response that
continues discussion, approves one draft, approves a review exception, or asks
a question is not publication consent. Any material plan change requires
another review cycle, a revised overview, and fresh confirmation.

## 8. Publish safely after confirmation

First create only missing canonical labels: `ready-for-agent`,
`ready-for-human`, `epic`, and `needs-refinement`. Never create or apply
`claimed`. Then create issues in the reviewed order, recording each number,
URL, database ID, labels, and intended relationship immediately.

Create native sub-issue links and dependencies with GitHub's current
documented API, not body text. Recheck the API contract at publication time if
it has not been verified for this repository. Dependencies use the blocker
issue's internal database ID rather than its issue number or GraphQL node ID.
For example:

```bash
gh api repos/OWNER/REPO/issues/BLOCKER --jq .id
gh api --method POST repos/OWNER/REPO/issues/BLOCKED/dependencies/blocked_by \
  -F issue_id=BLOCKER_DATABASE_ID
gh api repos/OWNER/REPO/issues/BLOCKED/dependencies/blocked_by
```

Use the documented native sub-issue endpoint with the child's internal ID and
verify the resulting hierarchy. Verify each dependency by matching the
intended blocker's database ID. Matching the issue number in the returned
object is also sufficient. Never rely only on a dependency count because an
unrelated blocker could make the count look correct. Do not create an
epic-to-leaf dependency merely to mark the epic unavailable.

When expanding a `needs-refinement` issue, create and verify its replacements
and native links first. Then post and verify a comment that links to the
replacement issues or independent epic. Remove its native parent relationship
if it has one, and close it as `not planned` last. A partial failure must leave
the refinement issue active.

On any GitHub write failure, stop immediately. Do not roll back, retry, make a
different write, or guess whether GitHub completed the request. Preserve every
created issue and link. Report every completed write, including created labels,
issues, comments, relationship changes, and status changes. Include exact IDs
and URLs, verified links, the failed operation, and incomplete operations.
Offer read-only verification or stopping as the immediate choices. After
GitHub state is known, ask the person you are working with to choose an
explicit recovery path before any further write.

Finish with the created tree, native-link verification, any closed refinement
issue, and the next startable leaves. If publication is declined, return the
reviewed drafts and make no GitHub changes.
