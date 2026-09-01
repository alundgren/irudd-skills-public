#!/usr/bin/env python3
"""Validate every resources/skills/*/SKILL.md against the Agent Skills open spec.

Checks:
- SKILL.md exists in each skill folder
- Frontmatter is present and parses as YAML
- Required fields: name, description
- `name` is lowercase/hyphens and matches the parent directory name
- `description` is non-empty

Exits non-zero if any skill fails, so this can run directly in CI.
"""
import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    sys.exit("Missing dependency: pip install pyyaml --break-system-packages")

RESOURCES_DIR = Path(__file__).resolve().parent.parent
SKILLS_DIR = RESOURCES_DIR / "skills"
NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")


def parse_frontmatter(text: str, path: Path):
    if not text.startswith("---"):
        return None, f"{path}: missing frontmatter (must start with '---')"
    parts = text.split("---", 2)
    if len(parts) < 3:
        return None, f"{path}: malformed frontmatter block"
    try:
        data = yaml.safe_load(parts[1]) or {}
    except yaml.YAMLError as e:
        return None, f"{path}: invalid YAML frontmatter ({e})"
    return data, None


def validate_skill(skill_dir: Path):
    errors = []
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        return [f"{skill_dir.name}: missing SKILL.md"]

    text = skill_md.read_text(encoding="utf-8")
    data, err = parse_frontmatter(text, skill_md)
    if err:
        return [err]

    name = data.get("name")
    description = data.get("description")

    if not name:
        errors.append(f"{skill_md}: missing required field 'name'")
    elif not NAME_RE.match(str(name)):
        errors.append(
            f"{skill_md}: name '{name}' must be lowercase letters/numbers "
            "with hyphens only"
        )
    elif name != skill_dir.name:
        errors.append(
            f"{skill_md}: name '{name}' must match folder name '{skill_dir.name}'"
        )

    if not description or not str(description).strip():
        errors.append(f"{skill_md}: missing or empty required field 'description'")

    return errors


def main():
    if not SKILLS_DIR.exists():
        sys.exit(f"No skills directory found at {SKILLS_DIR}")

    skill_dirs = sorted(p for p in SKILLS_DIR.iterdir() if p.is_dir())
    if not skill_dirs:
        print("No skills found under resources/skills/ — nothing to validate.")
        return

    all_errors = []
    for skill_dir in skill_dirs:
        errs = validate_skill(skill_dir)
        if errs:
            all_errors.extend(errs)
        else:
            print(f"OK   {skill_dir.name}")

    if all_errors:
        print("\nFAILED:")
        for e in all_errors:
            print(f"  - {e}")
        sys.exit(1)

    print(f"\nAll {len(skill_dirs)} skill(s) valid.")


if __name__ == "__main__":
    main()
