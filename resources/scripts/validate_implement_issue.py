#!/usr/bin/env python3
"""Check the canonical cross-runtime issue implementation workflow contract."""

import re
import sys
from pathlib import Path

import yaml


REPO_ROOT = Path(__file__).resolve().parents[2]
SKILL_DIR = REPO_ROOT / "resources" / "skills" / "implement-issue"
SKILL_PATH = SKILL_DIR / "SKILL.md"
SIDECAR_PATH = SKILL_DIR / "agents" / "openai.yaml"
PLAN_PATH = REPO_ROOT / "resources" / "skills" / "axis-review-plan" / "SKILL.md"
NEXT_PATH = REPO_ROOT / "resources" / "skills" / "next-issue" / "SKILL.md"

REQUIRED_SECTIONS = (
    "1. Check and claim the issue",
    "2. Implement and prove the result",
    "3. Freeze the review target",
    "4. Run the Plan axis once",
    "5. Run the combined review",
    "6. Choose ready or draft",
    "7. Open and verify the pull request",
)

REQUIRED_FRAGMENTS = (
    # One complete workflow and the claim gate.
    "this is the complete cross-runtime workflow",
    "do not load a runtime-prefixed implementation skill",
    "before broad repository reading",
    "inspect its state, labels, and complete native `blockedby` relationship",
    "the issue is open",
    "it has `ready-for-agent`",
    "it does not have `claimed`",
    "`ready-for-human`, `epic`, or `needs-refinement`",
    "every native blocking dependency is closed",
    "never remove or override an existing `claimed` label",
    "add `claimed` immediately",
    # Ambiguity, implementation ownership, delegation, and validation.
    "materially ambiguous",
    "before implementation and wait",
    "once implementation is underway",
    "the main session chooses the implementation method",
    "repository investigation",
    "external research",
    "failure reproduction",
    "comparison of independent approaches",
    "concrete output",
    "not to spawn or delegate further work",
    "do not let two agents edit the same files at the same time",
    "validation evidence that proves the issue acceptance criteria and affected behavior",
    # Completion-time review target and reviewer policy.
    "begin review only after the main session considers implementation complete",
    "the complete issue and comments",
    "the base revision",
    "the committed branch diff from that base",
    "all staged and unstaged changes",
    "every untracked file and its contents",
    "all applicable repository guidance",
    "gpt-5.6-sol",
    "high reasoning",
    "claude-opus-5",
    "inherit the session effort",
    "unknown compatible runtime",
    "inherit both model and effort",
    "model substitution or failed required reviewer launch",
    "must not delegate",
    # Plan once, dispositions, and combined review.
    "launch one fresh plan reviewer exactly once",
    "`axis-review-plan` in embedded mode",
    "never retry the launch, resume the plan reviewer, or rerun the axis",
    "assess every plan-axis finding",
    "the complete plan output and every disposition for the combined reviewer",
    "launch one task-scoped combined reviewer",
    "always loads `code-guidance`",
    "also loads `ux-design`",
    "must not load or run `axis-review-plan`",
    "at most four total rounds, including the first",
    "failed launch or model substitution consumes a round",
    "rerun the same combined reviewer after fixes",
    "record a disposition for every blocking and non-blocking finding",
    # Ready and draft decisions and PR safeguards.
    "a required reviewer was unavailable or substituted | draft",
    "a supported plan-axis finding remains unresolved after combined review | draft",
    "a supported blocking combined-review finding remains after round four | draft",
    "none of the conditions above applies | ready",
    "non-blocking suggestions require a recorded disposition but do not force a draft",
    "## unresolved review findings",
    "its review source",
    "the main-session disposition and evidence",
    "the remaining decision or fix",
    "do not create a follow-up issue automatically",
    "outcome-focused title",
    "literal `closes #n` line",
    "closingissuesreferences",
)

FORBIDDEN_FRAGMENTS = (
    "follow a red/green/refactor",
    "read narrowly",
    "small, reviewable changes",
    "run the full suite",
    "gh pr comment",
    "search before reading",
    "output filtering",
)


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip().lower()


def read_yaml(path: Path, errors: list[str]) -> dict:
    if not path.is_file():
        errors.append(f"{path}: missing")
        return {}
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as error:
        errors.append(f"{path}: invalid YAML ({error})")
        return {}


def validate_skill(errors: list[str]) -> None:
    if not SKILL_PATH.is_file():
        errors.append(f"{SKILL_PATH}: missing")
        return

    text = SKILL_PATH.read_text(encoding="utf-8")
    normalized = normalize(text)
    frontmatter_match = re.match(r"\A---\s*\n(.*?)\n---\s*\n", text, re.DOTALL)
    if not frontmatter_match:
        errors.append(f"{SKILL_PATH}: missing or malformed frontmatter")
    else:
        try:
            frontmatter = yaml.safe_load(frontmatter_match.group(1)) or {}
        except yaml.YAMLError as error:
            errors.append(f"{SKILL_PATH}: invalid frontmatter ({error})")
        else:
            if frontmatter.get("name") != "implement-issue":
                errors.append(f"{SKILL_PATH}: name must be 'implement-issue'")
            description = normalize(str(frontmatter.get("description", "")))
            if not description.startswith("use when "):
                errors.append(
                    f"{SKILL_PATH}: description must start with trigger guidance"
                )
            for fragment in ("github issue", "review", "pull request", "claude code", "codex"):
                if fragment not in description:
                    errors.append(
                        f"{SKILL_PATH}: description is missing {fragment!r}"
                    )

    for heading in REQUIRED_SECTIONS:
        count = len(re.findall(rf"^## {re.escape(heading)}\s*$", text, re.MULTILINE))
        if count != 1:
            errors.append(
                f"{SKILL_PATH}: expected one level-two {heading!r} section; found {count}"
            )

    for fragment in REQUIRED_FRAGMENTS:
        if normalize(fragment) not in normalized:
            errors.append(f"{SKILL_PATH}: missing contract text {fragment!r}")

    for fragment in FORBIDDEN_FRAGMENTS:
        if normalize(fragment) in normalized:
            errors.append(f"{SKILL_PATH}: retains removed behavior {fragment!r}")


def validate_sidecar(errors: list[str]) -> None:
    sidecar = read_yaml(SIDECAR_PATH, errors)
    expected = {
        "display_name": "Implement Issue",
        "short_description": "Implement and review an eligible GitHub issue",
        "default_prompt": (
            "Use $implement-issue to implement this GitHub issue and open the "
            "required pull request."
        ),
    }
    if sidecar.get("interface", {}) != expected:
        errors.append(f"{SIDECAR_PATH}: interface must equal {expected!r}")


def validate_plan_modes(errors: list[str]) -> None:
    if not PLAN_PATH.is_file():
        errors.append(f"{PLAN_PATH}: missing")
        return
    text = PLAN_PATH.read_text(encoding="utf-8")
    normalized = normalize(text)
    required = (
        "direct mode is the default",
        "embedded mode only when the caller explicitly requests it",
        "embedded mode relaxes only the exact output format",
        "## direct mode output contract",
        "# review: plan - pass",
        "replace `pass` with `fail`",
        "## embedded mode output contract",
        "return a clear `pass` or `fail`",
        "every finding as an individually identifiable item",
        "embedded mode changes presentation only",
        "apply the same pass and fail rule",
    )
    for fragment in required:
        if normalize(fragment) not in normalized:
            errors.append(f"{PLAN_PATH}: missing mode contract {fragment!r}")


def validate_dispatch(errors: list[str]) -> None:
    if not NEXT_PATH.is_file():
        errors.append(f"{NEXT_PATH}: missing")
        return
    normalized = normalize(NEXT_PATH.read_text(encoding="utf-8"))
    if "invoke `implement-issue`" not in normalized:
        errors.append(f"{NEXT_PATH}: must dispatch implement-issue")


def validate_installation(errors: list[str]) -> None:
    for runtime in (".claude", ".agents"):
        link = REPO_ROOT / runtime / "skills" / "implement-issue"
        if not link.is_symlink():
            errors.append(f"{link}: missing tracked symlink")
            continue
        if not link.exists() or link.resolve() != SKILL_DIR.resolve():
            errors.append(f"{link}: does not resolve to {SKILL_DIR}")

def main() -> None:
    errors: list[str] = []
    validate_skill(errors)
    validate_sidecar(errors)
    validate_plan_modes(errors)
    validate_dispatch(errors)
    validate_installation(errors)

    if errors:
        print("Canonical implement-issue contract failed:")
        for error in errors:
            print(f"  - {error}")
        sys.exit(1)

    print("Canonical implement-issue workflow satisfies the cross-runtime contract.")


if __name__ == "__main__":
    main()
