#!/usr/bin/env python3
"""Non-destructive v1.5 project upgrader.

Adds shot-chaining / reference-budget support without replacing existing
creative, evidence, script, storyboard, or prompt files.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from historical_shortfilm_director import __version__

NEW_FILES = {
    "05c_shot_chaining_plan.md": """# Shot Chaining / Reference Budget Plan

Use this file when AI-generated shots need continuity or when the model has hard limits such as max 3 reference images and max 10 seconds per clip.

| Shot | Duration | Chain role | Prev shot / source | Start anchor | End anchor target | Reference budget (1/2/3) | Carry-forward allowed? | Extraction rule | Reset conditions | Notes |
|---|---:|---|---|---|---|---|---|---|---|---|

## Carry-frame naming

Use stable IDs such as `CF_S03_v2`.

## Composite-anchor needs

List shots that require pre-composited anchor frames because more than 3 conceptual source assets are needed.

## High-risk resets

List shots that must reset to an authoritative archival/keyframe reference instead of inheriting the prior shot tail frame.
""",
}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("project_dir")
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    root = Path(args.project_dir).resolve()
    if not root.exists():
        raise SystemExit(f"project directory does not exist: {root}")

    meta_path = root / "project.json"
    meta = {}
    if meta_path.exists():
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
        except Exception:
            pass

    missing = [name for name in NEW_FILES if not (root / name).exists()]
    print(f"Project: {root}")
    print("Missing support files:")
    for name in missing:
        print(f"  + {name}")

    if not args.apply:
        print("Dry run only. Re-run with --apply to create missing files and update metadata.")
        return 0

    for name in missing:
        (root / name).write_text(NEW_FILES[name], encoding="utf-8")

    if meta_path.exists() and isinstance(meta, dict):
        meta["skill_pipeline_version"] = __version__
        meta.setdefault(
            "ai_generation_constraints",
            {
                "max_reference_images_per_shot": 3,
                "max_clip_duration_seconds": 10,
            },
        )
        meta_path.write_text(
            json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )

    notes = root / "V15_UPGRADE_NOTES.md"
    if not notes.exists():
        notes.write_text(
            "# v1.5 Upgrade Notes\n\n"
            "Added non-destructive shot-chaining support for AI-heavy workflows, including a dedicated planning file for extracted tail-frame continuity, reset points, and 3-reference budgeting under max-10-second clip constraints.\n"
            "Existing evidence, script, storyboard, prompts, and assets were not overwritten.\n",
            encoding="utf-8",
        )
    print("Applied.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
