---
name: example-skill
description: Template skill demonstrating the SKILL.md format. Use as a starting point when creating new skills in this repo — copy the folder, rename it, and edit this file.
license: MIT
---

# Example Skill

Replace this with a clear explanation of what the skill does and when an
agent should use it. The `description` field above is what agents use to
decide whether to load this skill, so keep it specific and keyword-rich.

## Instructions

1. Describe the first step the agent should take.
2. Describe the second step.
3. Point to any reference material in `references/` if the task needs
   detail that would otherwise bloat this file.

## Notes

- Keep SKILL.md itself short — move long reference material into
  `references/` and long-running helper code into `scripts/`.
- Only use fields from the open spec (name, description, license,
  compatibility, metadata, allowed-tools) if you want this skill to work
  unmodified across agents. Agent-specific extensions (e.g. Claude Code's
  `context: fork`) are fine, but break portability.
