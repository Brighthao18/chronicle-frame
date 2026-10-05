#!/usr/bin/env python3
"""Non-destructive v1.2-or-earlier project upgrade helper.

Default is dry-run. Use --apply to create only missing v1.3 files and update
project.json's skill_pipeline_version. Existing creative files are never overwritten.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from historical_shortfilm_director import __version__

import historical_shortfilm_director.project as MOD

NEW_FILES = [
    "03_asset_style_bible.md",
    "05_animatic_plan.md",
    "06_ai_prompts.md",
]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("project_dir")
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    root = Path(args.project_dir).resolve()
    if not root.exists():
        print(f"ERROR: missing project directory: {root}")
        return 2

    actions: list[tuple[str, Path]] = []
    for name in NEW_FILES:
        path = root / name
        if not path.exists():
            actions.append(("create", path))

    manifest = root / "06_generation_manifest.json"
    if not manifest.exists():
        actions.append(("create_manifest", manifest))
    log = root / "06_generation_log.csv"
    if not log.exists():
        actions.append(("create_log", log))

    board = root / "05_storyboard.md"
    board_needs_v13 = False
    if board.exists():
        text = board.read_text(encoding="utf-8", errors="replace")
        board_needs_v13 = "ONE primary action" not in text or "Safer fallback" not in text

    note = root / "V13_UPGRADE_NOTES.md"
    if board_needs_v13 and not note.exists():
        actions.append(("create_note", note))

    print("v1.3 project upgrade plan" + (" (APPLY)" if args.apply else " (DRY RUN)"))
    for action, path in actions:
        print(f"- {action}: {path.name}")
    if not actions:
        print("- no missing v1.3 support files detected")

    if not args.apply:
        print(
            "Run again with --apply to create missing support files. Existing files will not be overwritten."
        )
        return 0

    for action, path in actions:
        if action == "create":
            path.write_text(MOD.FILES[path.name], encoding="utf-8")
        elif action == "create_manifest":
            meta = {}
            meta_path = root / "project.json"
            if meta_path.exists():
                try:
                    meta = json.loads(meta_path.read_text(encoding="utf-8"))
                except Exception:
                    meta = {}
            data = dict(MOD.GENERATION_MANIFEST)
            data["project_title"] = meta.get("title", root.name)
            path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        elif action == "create_log":
            path.write_text(MOD.GENERATION_LOG_HEADER, encoding="utf-8")
        elif action == "create_note":
            path.write_text(
                "# v1.3 upgrade notes\n\n"
                "The existing `05_storyboard.md` was preserved. Before new AI generation, migrate its shot schema to include:\n\n"
                "- story purpose / director intent\n"
                "- lens feel and camera position/height\n"
                "- ONE primary action per generated shot\n"
                "- stable Reference IDs\n"
                "- generation risk + safer fallback\n"
                "- why-this-cut + continuity anchors\n\n"
                "Also build `03_asset_style_bible.md`, time the sequence in `05_animatic_plan.md`, and log final generation attempts.\n",
                encoding="utf-8",
            )

    meta_path = root / "project.json"
    if meta_path.exists():
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
        except Exception:
            meta = {}
        meta["skill_pipeline_version"] = __version__
        meta_path.write_text(
            json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )

    print("Applied. Existing creative files were not overwritten.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
