#!/usr/bin/env python3
"""Check the canonical cross-runtime issue planning workflow contract."""

import re
import sys
from pathlib import Path

import yaml


REPO_ROOT = Path(__file__).resolve().parents[2]
SKILL_DIR = REPO_ROOT / "resources" / "skills" / "plan-issues"
SKILL_PATH = SKILL_DIR / "SKILL.md"
SIDECAR_PATH = SKILL_DIR / "agents" / "openai.yaml"

REQUIRED_SECTIONS = (
    "Non-negotiable safety rules",
    "Optional delegation",
    "1. Establish scope and evidence",
    "2. Resolve decisions before drafting",
    "3. Right-size the tree",
    "4. Write complete issue drafts",
    "5. Review the completed drafts",
    "6. Approve review exceptions",
    "7. Show the publish gate",
    "8. Publish safely after confirmation",
)

REQUIRED_FRAGMENTS = (
    # Intake, evidence, and the complete decision process.
    "read the whole source issue and its comments",
    "verify it has `needs-refinement`",
    "native sub-issues and dependencies",
    "provisional design tree",
    "currently unblocked decision frontier",
    "ask that whole frontier in one round",
    "challenge assumptions",
    "if the person declines to decide, represent the bounded unknown as a `needs-refinement` node",
    # Planner-checkable sizing rules from issue #176.
    "one independently useful behavior with named proof",
    "likely implementation area",
    "existing behavior to inspect",
    "credible validation route",
    "share an end-to-end check",
    "product choices, irreversible data decisions, access requirements, and external contracts",
    # Labels, graph rules, and issue bodies.
    "exactly one planner classification",
    "epics never nest",
    "never create a blocker across root-epic boundaries",
    "## deliberately deferred",
    "## completion",
    "`closes #<issue>`",
    # Reviewer timing, inputs, policy, and resolution.
    "only after every issue draft is complete",
    "one task-scoped combined reviewer",
    "load `code-guidance` and `ux-design`",
    "complete proposed tree",
    "native-link plan",
    "discovered facts",
    "acceptance criteria",
    "same reviewer thread",
    "no fixed review-round cap",
    "gpt-5.6-sol",
    "high reasoning",
    "claude-opus-5",
    "inherit the session effort",
    "unknown compatible runtime",
    "inherit both",
    "must not delegate",
    "model substitution",
    "explicit override",
    # Optional delegation boundaries.
    "bounded repository investigation",
    "external research",
    "failure reproduction",
    "comparison of independent approaches",
    "concrete output",
    "main planning session owns the plan and every github write",
    # Separate exception approval and publication authorization.
    "approve each named exception separately",
    "does not authorize publication",
    "nothing has been written to github",
    "the review outcome and any approved exceptions are listed above",
    "publish this exact plan",
    "stop and keep the drafts",
    # Publication contents and safe writes.
    "titles, labels, parent/root relation, native blockers, and ordinary references",
    "missing canonical labels",
    "review outcome",
    "unambiguous confirmation",
    "never create or apply `claimed`",
    "recording each number, url, database id, labels, and intended relationship",
    "verify each dependency by matching",
    "report every completed write",
    "stop immediately",
    "explicit recovery path",
)

FORBIDDEN_FRAGMENTS = (
    "150k",
    "focused human work block",
    "search before reading",
    "keep reads narrow",
    "do not re-read",
    "command output",
    "at most three cycles",
    "workspace integrity",
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
            if frontmatter.get("name") != "plan-issues":
                errors.append(f"{SKILL_PATH}: name must be 'plan-issues'")
            description = normalize(str(frontmatter.get("description", "")))
            if not description.startswith("use when "):
                errors.append(
                    f"{SKILL_PATH}: description must contain trigger guidance "
                    "and start with 'Use when'"
                )
            for fragment in ("github", "issues", "planning", "claude code", "codex"):
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

    if "do not load or run `axis-review-plan`" not in normalized:
        errors.append(f"{SKILL_PATH}: must prohibit axis-review-plan during planning")


def validate_sidecar(errors: list[str]) -> None:
    sidecar = read_yaml(SIDECAR_PATH, errors)
    interface = sidecar.get("interface", {})
    expected = {
        "display_name": "Plan Issues",
        "short_description": "Plan and publish reviewed GitHub issue trees",
        "default_prompt": "Use $plan-issues to turn this idea or issue into a reviewed GitHub issue plan.",
    }
    if interface != expected:
        errors.append(f"{SIDECAR_PATH}: interface must equal {expected!r}")


def validate_installation(errors: list[str]) -> None:
    for runtime in (".claude", ".agents"):
        link = REPO_ROOT / runtime / "skills" / "plan-issues"
        if not link.is_symlink():
            errors.append(f"{link}: missing tracked symlink")
            continue
        if not link.exists() or link.resolve() != SKILL_DIR.resolve():
            errors.append(f"{link}: does not resolve to {SKILL_DIR}")

def main() -> None:
    errors: list[str] = []
    validate_skill(errors)
    validate_sidecar(errors)
    validate_installation(errors)

    if errors:
        print("Canonical plan-issues contract failed:")
        for error in errors:
            print(f"  - {error}")
        sys.exit(1)

    print("Canonical plan-issues workflow satisfies the cross-runtime contract.")


if __name__ == "__main__":
    main()
