---
name: code-guidance
description: House guidance for technical review and planning. Use for module boundaries, dependencies, data models, schemas, architecture, implementation structure, compatibility, or reviewing whether a plan or implementation is correct and fits the codebase. Use alongside `ux-design` when user-facing behavior is also in scope. Not for visual or interaction decisions on their own.
license: MIT
---

# Code guidance

Shared engineering preferences for these repositories. The guidance is
advisory. Deviate when the code needs something different and explain why.

## Decision ownership

`code-guidance` decides code structure, architecture, data models, schemas, and
compatibility. `ux-design` decides visual and interaction behavior. When a
technical decision creates an interface cost, both apply. `ux-design` names
the cost, and `code-guidance` decides the technical correction.

## Principles

1. **The data model comes first.** Data structures and models guide every other
   choice. This is where we do not compromise, and it is strongest for
   persisted data: a database schema is a decision you live with long after the
   code around it has been rewritten.

2. **Modules with real boundaries.** Well defined modules, explicit interaction
   contracts, internals hidden from everyone else. A boundary you can describe
   in a sentence is a boundary. One you have to trace through call sites is not.

3. **Simple and self explanatory beats layered.** The clean code habit of
   explicit layers everywhere, an interface per class, indirection for its own
   sake, is the failure to avoid. Fewer moving parts that say what they do.

4. **Do not generalize early.** Generalize only when it is very likely to be
   needed on current plans **and** it would be hard to change later. Both
   halves, not either.

5. **Data flow should be obvious.** Keep branching minimal. Prefer several
   clear interfaces over one that branches internally. A boolean parameter that
   switches behaviour is the smell; two functions are the fix.

6. **Be defensive. Design for reality.** Assume things break. Do not design the
   happy path and bolt on error handling. Prefer things that recover on their
   own after a failure rather than things that need a human to notice.

7. **Say when a change can break what is already running.** Deployed instances,
   in-flight data, old clients, existing rows. Call it out even when the change
   is correct.

8. **Document architecture, not implementation.** Arriving at a repo should give
   a human or an agent a quick, consistent overview: high level boxes and
   arrows, one sentence per module or component. Not a detailed spec. We have
   the code for detail.

9. **Comments say why, never how.** The code says how. If a comment has to
   explain how, the code is the thing to fix.

10. **Not style police.** Non-semantic style choices are a linter's job, not a
    person's and not an agent's. Do not spend review attention there.

11. **Changes should read as if they had been there from day one.** No issue
    numbers or issue names in comments, no narration of what changed. Judge the
    ceremony against what the code does on its own, not against how big the
    issue felt.

12. **A hack is a signal.** When a change looks like a workaround for poor
    architecture, say so and propose the architecture change instead of
    polishing the workaround.

## Review a complete change

For a task-scoped review, judge the complete plan or implementation against its
intended outcome before commenting on individual lines.

- Is the change technically correct for the intended outcome?
- What required behavior is missing?
- What is present but unnecessary?
- Does it respect the existing architecture, or would it look out of place if
  it had existed from the start?
- Does it preserve compatibility with deployed instances, in-flight work,
  existing data, and old clients where those apply?
- Give a concrete alternative for every objection. Flag work that belongs in a
  later change instead of expanding the current one without need.

Rank findings by consequence. A hard-to-reverse data decision outranks a naming
preference. Cite checkable evidence such as a source location, test, observed
behavior, or omitted case. Separate blocking findings from suggestions and
report only points that can change the outcome. Do not comment on formatting or
other choices enforced by tooling.

## Solutions outliving their issue

A change written from an issue tends to inherit the issue's shape. Watch for a
solution that is overly specific to how the issue was described rather than to
the problem underneath. The code stays. The issue does not.
