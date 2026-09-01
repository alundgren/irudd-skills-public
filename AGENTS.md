# Project guidance

`resources/skills/` is the canonical skill source. Every skill here is
portable: it names no host, no user, no private service, and no absolute path
that is true on only one machine. Keep it that way.

`.claude/skills/` and `.agents/skills/` hold committed relative symlinks into
`resources/skills/`, so an edit is live without reinstalling. Nothing installs
them, and CI checks they stay in step. Add and commit them by hand when adding
a skill.

## Who "the user" is

In `resources/`, never write a bare "the user":

- **"the end user"** is whoever uses the app being built. Every UX principle
  is about them.
- **"the person you are working with"** is whoever is running the session.
  They settle open questions and review disputes.

Do not name the person running the session.

## Issue workflows and UX guidance

`plan-issues` is the only planning workflow for GitHub issues.
`implement-issue` is the only implementation workflow. Both are cross-runtime
entry points and include task-scoped completion review.

Invoke `ux-design` directly for UI or UX design and review. It covers screens,
views, forms, layouts, navigation, visible states, interactions, and end-user
wording. Load `code-guidance` alongside it when technical structure also
affects the experience.

## Staying portable

Stick to the Agent Skills spec's fields — `name`, `description`, and optionally
`license`, `compatibility`, `metadata`, `allowed-tools` — and a skill runs
unmodified in both Claude Code and Codex. Agent-specific extensions work fine
but are not understood by other agents, so isolate them if one skill has to
serve multiple runtimes.
