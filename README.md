# irudd-skills-public

Portable [Agent Skills](https://agentskills.io) for Claude Code, Codex, and
other agents that read the same format.

## The skills

| Skill | What it is for |
| --- | --- |
| `plan-issues` | Turn an idea or a rough issue into reviewed, right-sized GitHub issues |
| `implement-issue` | Implement an eligible GitHub issue through review, validation, and a PR |
| `next-issue` | Pick and launch the next eligible issue in the current checkout |
| `axis-review-plan` | The Plan review axis: is added machinery justified by a small coherent plan |
| `code-guidance` | Technical review and planning: boundaries, data models, architecture, compatibility |
| `ux-design` | Design and review anything a person sees or clicks, with worked before/after examples |
| `initial-architecture` | Turn an early product idea into a compact C4 record with Mermaid diagrams |
| `session-retrospective` | Review a finished session for efficiency, correctness, and speed |
| `grilling` | Stress-test your own thinking |
| `unslop` | Cut AI tells from writing |
| `example-skill` | Template showing the `SKILL.md` format — copy it to start a new skill |

## Layout

```text
resources/skills/<name>/SKILL.md   the canonical source
resources/codex/AGENTS.md          shared writing and GitHub-operations guidance
resources/claude/output-styles/    output styles
.claude/skills/  .agents/skills/   relative symlinks into resources/skills/
```

## Using them

Point your agent's skill directory at `resources/skills/`, or copy the folders
you want into `~/.claude/skills/` (Claude Code) or `~/.agents/skills/` (Codex,
OpenCode). Each skill is a self-contained directory.

## CI

`.github/workflows/validate.yml` checks every `SKILL.md` against the Agent
Skills spec, checks the shared review guidance, checks the two issue
workflows, and checks that the committed symlinks are relative and resolve.

## License

MIT, per the `license` field in each `SKILL.md`.
