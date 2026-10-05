"""Dependency-free Agent Skill structure and local reference validation."""

from __future__ import annotations

import argparse
import re
from pathlib import Path


def validate_bundle(root):
    root = Path(root).resolve()
    errors, warnings = [], []
    path = root / "SKILL.md"
    if not path.is_file():
        return {"status": "FAIL", "errors": ["SKILL.md missing"], "warnings": []}
    text = path.read_text(encoding="utf-8")
    split = text.split("---\n", 2)
    if not text.startswith("---\n") or len(split) != 3:
        errors.append("Missing YAML frontmatter delimiters")
        front = ""
    else:
        front = split[1]
    name_match = re.search(r"^name:\s*(.+)$", front, re.M)
    desc_match = re.search(r"^description:\s*(.+)$", front, re.M)
    version_match = re.search(r"^  version:\s*[\"']?([^\"'\n]+)", front, re.M)
    name = name_match.group(1).strip().strip("\"'") if name_match else ""
    desc = desc_match.group(1).strip().strip("\"'") if desc_match else ""
    if not 1 <= len(name) <= 64 or not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", name):
        errors.append("Invalid Agent Skill name")
    if name != root.name:
        errors.append("Skill name must match its directory name")
    if not 1 <= len(desc) <= 1024:
        errors.append("Description must contain 1-1024 characters")
    canonical = root / "VERSION"
    if (
        not canonical.is_file()
        or not version_match
        or canonical.read_text().strip() != version_match.group(1).strip()
    ):
        errors.append("VERSION and Skill metadata must match")
    for reference in re.findall(
        r"(?:\]\(|`)((?:references|scripts|examples)/[^\s)`]+)(?:\)|`)", text
    ):
        resolved = (root / reference.split("#")[0]).resolve()
        if not resolved.is_relative_to(root) or not resolved.is_file():
            errors.append("Missing or unsafe local reference: " + reference)
    if len(text.splitlines()) > 500:
        warnings.append("Main Skill exceeds 500 lines; use progressive disclosure")
    return {"status": "FAIL" if errors else "PASS", "errors": errors, "warnings": warnings}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("skill_dir", nargs="?", default=str(Path(__file__).resolve().parents[2]))
    args = parser.parse_args()
    result = validate_bundle(args.skill_dir)
    for problem in result["errors"]:
        print("ERROR: " + problem)
    for warning in result["warnings"]:
        print("WARN: " + warning)
    print(result["status"] + ": Skill structural validation")
    return 0 if result["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
