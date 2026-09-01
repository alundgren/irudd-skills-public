#!/usr/bin/env python3
"""Check the shared skills that task-scoped plan and implementation reviews use."""

import re
import sys
from pathlib import Path

import yaml


RESOURCES_DIR = Path(__file__).resolve().parent.parent

CONTRACTS = {
    "code-guidance": {
        "review_heading": "Review a complete change",
        "description_fragments": (
            "technical review",
            "module boundaries",
            "data model",
            "schema",
            "architecture",
            "implementation",
            "compatibility",
            "use alongside `ux-design`",
            "user-facing behavior",
            "not for visual or interaction decisions",
        ),
        "review_fragments": (
            "technically correct",
            "intended outcome",
            "required behavior",
            "unnecessary",
            "existing architecture",
            "deployed instances",
            "in-flight",
            "existing data",
            "old clients",
            "rank findings by consequence",
            "checkable evidence",
            "blocking findings",
            "suggestions",
            "concrete alternative",
            "formatting",
        ),
    },
    "ux-design": {
        "review_heading": "Review a complete experience",
        "description_fragments": (
            "designing and reviewing",
            "screens",
            "states",
            "complete flows",
            "load `code-guidance` too",
            "both user-facing and technical behavior",
            "do not use for api design",
            "database schemas",
            "module boundaries",
            "cli flags",
        ),
        "review_fragments": (
            "end user's task",
            "entry points",
            "states",
            "errors",
            "recovery actions",
            "cancel, leave, or undo",
            "realistic content and conditions",
            "empty results",
            "long text",
            "large result sets",
            "delayed responses",
            "invalid or partial data",
            "remove controls",
            "do not help with this task",
            "combining tasks",
            "`ux.md`",
            "settled",
            "house defaults",
            "technical decision",
            "interface cost",
            "rank findings by their consequence",
            "checkable evidence",
            "blocking findings",
            "suggestions",
            "concrete correction",
            "source formatting",
        ),
    },
}

FORBIDDEN_REVIEW_FRAGMENTS = (
    "consult",
    "quick check",
    "tech round",
    "ux round",
    "person you are working with",
    "right change",
    "wrong change",
    "approved",
    "workspace",
)


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip().lower()


def section(text: str, heading: str, path: Path) -> tuple[str | None, list[str]]:
    pattern = re.compile(
        rf"^## {re.escape(heading)}\s*$\n(.*?)(?=^##\s|\Z)",
        re.MULTILINE | re.DOTALL,
    )
    matches = pattern.findall(text)
    if len(matches) != 1:
        return None, [
            f"{path}: expected exactly one level-two '{heading}' section; "
            f"found {len(matches)}"
        ]
    return normalize(matches[0]), []


def missing_fragments(text: str, fragments: tuple[str, ...]) -> list[str]:
    return [fragment for fragment in fragments if normalize(fragment) not in text]


def frontmatter_description(text: str, path: Path) -> tuple[str | None, list[str]]:
    match = re.match(r"\A---\s*\n(.*?)\n---\s*\n", text, re.DOTALL)
    if not match:
        return None, [f"{path}: missing or malformed frontmatter"]

    try:
        data = yaml.safe_load(match.group(1)) or {}
    except yaml.YAMLError as error:
        return None, [f"{path}: invalid YAML frontmatter ({error})"]

    description = data.get("description")
    if not description:
        return None, [f"{path}: frontmatter has no description"]
    return normalize(str(description)), []


def validate_skill(name: str, contract: dict[str, object]) -> list[str]:
    path = RESOURCES_DIR / "skills" / name / "SKILL.md"
    text = path.read_text(encoding="utf-8")
    errors = []

    description, description_errors = frontmatter_description(text, path)
    errors.extend(description_errors)
    if description is not None:
        for fragment in missing_fragments(
            description, contract["description_fragments"]
        ):
            errors.append(f"{path}: description is missing {fragment!r}")

    review_text, section_errors = section(text, contract["review_heading"], path)
    errors.extend(section_errors)
    if review_text is None:
        return errors

    for fragment in missing_fragments(review_text, contract["review_fragments"]):
        errors.append(
            f"{path}: '{contract['review_heading']}' is missing {fragment!r}"
        )

    for fragment in FORBIDDEN_REVIEW_FRAGMENTS:
        if normalize(fragment) in review_text:
            errors.append(
                f"{path}: '{contract['review_heading']}' contains role protocol "
                f"{fragment!r}"
            )

    return errors


def main() -> None:
    errors = []
    for name, contract in CONTRACTS.items():
        errors.extend(validate_skill(name, contract))

    if errors:
        print("Review guidance contract failed:")
        for error in errors:
            print(f"  - {error}")
        sys.exit(1)

    print("Shared technical and UX review guidance satisfies the contract.")


if __name__ == "__main__":
    main()
