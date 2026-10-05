#!/usr/bin/env python3
"""Non-destructive v1.7 project upgrader.

Adds endpoint-reachability, bridge-keyframe, generation-review and v1.7 compiler
support without overwriting existing evidence/script/storyboard/chaining plans.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from historical_shortfilm_director import __version__

NEW_FILES = {
    "05d_endpoint_reachability.md": """# Endpoint Reachability / Production Routing

Do this before final video-prompt compilation. Start/end frames are a motion problem, not two independent pretty images.

| Shot | Start anchor | End anchor | Intended change | Identity | Camera/view | Composition/scale | Geometry/topology | Lighting/style | Scene/semantic | Occlusion | Start clean? | End natural? | Reachability | Route | Bridge frame | Target duration | AI value | Decision / notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---:|---|---|

Reachability: `R-A` small / `R-B` medium / `R-C` high same-world / `R-D` semantic or scene transition.

Routes: `I2V_START / FLF / BRIDGE_2STEP / OCCLUSION_2STEP / MATCH_CUT_EDIT / COMPOSITE_2_5D / MOTION_GRAPHIC / ARCHIVAL_HOLD / LIVE_OR_EXISTING_VIDEO`.

AI value: `HIGH / MEDIUM / LOW`.
""",
    "05e_bridge_keyframe_plan.md": """# Bridge Keyframe / Occlusion Plan

Only populate rows for `BRIDGE_2STEP` or `OCCLUSION_2STEP` shots.

| Shot | Route | Bridge ID | Position % | Bridge visual state | Phase A motion path | Phase B motion path | Phase A duration | Phase B duration | Bridge/reference IDs | Invariants | Approval |
|---|---|---|---:|---|---|---|---:|---:|---|---|---|
""",
    "06d_generation_review.md": """# Generation Candidate Review

| Shot | Candidate | Route | Endpoint adherence | First 10% boundary | Last 10% boundary | Identity / geometry | Motion smoothness | Camera obedience | Prompt adherence | Artifacts / flicker | Cuttability / carry frame | Decision | Rejection reason | Change next |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|

If 3 hero-shot candidates fail on the same dimension, redesign endpoint/path/route/reference/prompt before further rerolls.
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

    missing = [n for n in NEW_FILES if not (root / n).exists()]
    print(f"Project: {root}")
    for n in missing:
        print(f"  + {n}")
    print("Generated prompt-pack/lint files are created only after compilation/linting.")
    if not args.apply:
        print("Dry run only. Re-run with --apply.")
        return 0

    for n in missing:
        (root / n).write_text(NEW_FILES[n], encoding="utf-8")

    meta_path = root / "project.json"
    if meta_path.exists():
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
        except Exception:
            meta = {}
        if isinstance(meta, dict):
            meta["skill_pipeline_version"] = __version__
            meta.setdefault(
                "ai_generation_constraints",
                {
                    "max_reference_images_per_shot": 3,
                    "max_clip_duration_seconds": 10,
                },
            )
            meta["generation_plan_compiler"] = "scripts/compile_generation_plan.py"
            meta["prompt_linter"] = "scripts/lint_generation_prompts.py"
            meta["endpoint_reachability_required"] = True
            meta_path.write_text(
                json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
            )

    notes = root / "V17_UPGRADE_NOTES.md"
    if not notes.exists():
        notes.write_text(
            "# v1.7 Upgrade Notes\n\n"
            "Added endpoint reachability and AI-value routing before prompt compilation. Existing evidence, scripts, storyboards, anchor frames, and chaining plans were not overwritten.\n\n"
            "Next: fill `05d_endpoint_reachability.md`; for R-C/R-D split routes fill `05e_bridge_keyframe_plan.md`; then run `python scripts/compile_generation_plan.py <project_dir>` and `python scripts/lint_generation_prompts.py <project_dir>`.\n",
            encoding="utf-8",
        )
    print("Applied.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
