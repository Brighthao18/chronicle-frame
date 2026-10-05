#!/usr/bin/env python3
"""Non-destructive upgrade to v1.10 Flow shot-endpoint architecture."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from historical_shortfilm_director import __version__

FILM_ARC = """# Film Opening / Ending Design

This file is about the **whole film**, not per-shot AI first/last-frame conditioning.

## Opening variants

| Variant | Visual proposition | Single focal point | Question / tension | Reference IDs | Evidence/reconstruction status | Production method | Risk | Decision |
|---|---|---|---|---|---|---|---|---|

## Selected opening contract

## Ending variants

| Variant | Payoff function | Relationship to opening | Motif transformation | Reference IDs | Production method | Risk | Decision |
|---|---|---|---|---|---|---|---|

## Selected opening / ending pair

## Silent side-by-side test

Do not use this file as the source of Flow shot start/end frames. Use `05f_shot_endpoint_plan.md` for that.
"""

SHOT_ENDPOINTS = """# Flow Shot Endpoint Plan

This file controls **single-shot** start/end conditioning for Google Flow. It is separate from the whole-film opening/ending design.

| Unit | Parent shot | Flow mode | Duration | Start frame source | Start frame ID | Start role | End frame needed? | End frame source | End frame ID | End target state | KEEP fixed | CHANGE | Motion path | Endpoint distance | Reachability | Bridge/reset | Carry-in | Carry-out | Extraction rule | Approval |
|---|---|---|---:|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|

Flow endpoint rules:
- `T2V`: start/end frames usually optional.
- `START_FRAME`: start frame required; end frame optional.
- `FRAMES`: both start and end frames required; prompt describes the path, not the pictures.
- `INGREDIENTS`: endpoints optional; Ingredients carry identity/appearance.
- `EXTEND`: continuation inherits the approved clip state; manual end frame usually optional.
- `OMNI_EDIT`: preserve the clip and define only the localized change.
- `SKIP_FLOW`: no Flow endpoints required.

Carry frames are generated-output handoff assets, not planned film-level ending frames. Choose the cleanest stable frame from the final 10–20% only after the previous shot is approved.
"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("project_dir")
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    root = Path(args.project_dir).resolve()
    if not root.exists():
        raise SystemExit(f"project directory does not exist: {root}")

    wanted = {
        "05a_film_opening_ending.md": FILM_ARC,
        "05f_shot_endpoint_plan.md": SHOT_ENDPOINTS,
    }
    missing = [name for name in wanted if not (root / name).exists()]

    print(f"Project: {root}")
    print("v1.10 additions:")
    for name in wanted:
        print(("  + " if name in missing else "  = ") + name)
    if (root / "05a_anchor_frame_plan.md").exists():
        print(
            "  ! legacy 05a_anchor_frame_plan.md retained; review it only as whole-film opening/ending material"
        )

    if not args.apply:
        print("Dry run only. Re-run with --apply.")
        return 0

    for name in missing:
        (root / name).write_text(wanted[name], encoding="utf-8")

    meta_path = root / "project.json"
    if meta_path.exists():
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
            meta["skill_pipeline_version"] = __version__
            if meta.get("generator") == "flow" or isinstance(meta.get("flow"), dict):
                meta.setdefault("flow", {})["shot_endpoint_plan"] = "05f_shot_endpoint_plan.md"
                meta["flow"]["film_opening_ending_plan"] = "05a_film_opening_ending.md"
                meta["flow"]["endpoint_reviewer"] = "scripts/review_flow_endpoints.py"
                meta["flow"]["prompt_compiler"] = "scripts/compile_flow_prompts.py"
                meta["flow"]["endpoint_authority"] = "per-shot; film opening/ending is separate"
            meta_path.write_text(
                json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
            )
        except Exception:
            pass

    notes = root / "V110_UPGRADE_NOTES.md"
    if not notes.exists():
        notes.write_text(
            "# v1.10 Upgrade Notes\n\n"
            "v1.10 separates three concepts that earlier versions could conflate:\n\n"
            "1. `05a_film_opening_ending.md` — whole-film opening/ending story design.\n"
            "2. `05f_shot_endpoint_plan.md` — per-Flow-shot Start/End conditioning.\n"
            "3. Carry frames — extracted only after an approved generated shot.\n\n"
            "Existing `05a_anchor_frame_plan.md`, screenplay, storyboard, evidence, and prompts are preserved. Do not use the legacy 05a file as the per-shot Flow endpoint source.\n\n"
            "Before compiling new Flow prompts, populate 05f and run:\n\n"
            "```bash\n"
            "python scripts/review_flow_endpoints.py <project_dir>\n"
            "python scripts/compile_flow_prompts.py <project_dir>\n"
            "python scripts/lint_flow_prompts.py <project_dir>\n"
            "```\n",
            encoding="utf-8",
        )

    print("Applied.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
