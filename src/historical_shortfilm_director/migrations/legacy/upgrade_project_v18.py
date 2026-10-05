#!/usr/bin/env python3
"""Non-destructive v1.8 project upgrader.

Adds Google Flow-native script/reference support without overwriting existing
evidence, scripts, storyboards, reachability plans, or prompt packs.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from historical_shortfilm_director import __version__

NEW_FILES = {
    "04a_story_causality_map.md": """# Story Causality / Emotional Progression Map

Use this before locking the scene script. A history film still needs causality; chronology alone is not a story.

| Beat | Before-state / viewer question | Trigger / evidence | Because / Therefore change | After-state / new understanding | Emotional shift | Visual proof | Motif change | Evidence IDs | Why next beat follows |
|---|---|---|---|---|---|---|---|---|---|

## And-then audit

List any transitions that are only “and then another date/photo appears” and redesign them into cause, contrast, escalation, consequence, return, or payoff.
""",
    "04b_flow_scene_script.md": """# Flow-Native Scene Script

This file has two layers. Narrative scenes carry story logic; only selected units are sent to Google Flow.

## A. Narrative scenes

| Scene | Time | Story purpose / turn | Before-state | Trigger / evidence | After-state | Visible proof / action | VO function | VO / dialogue | SFX / ambience / music | On-screen text / post | Evidence IDs | Causal handoff | Production route |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|

Production route: `FLOW / ARCHIVAL_EDIT / MOTION_GRAPHIC / COMPOSITE / LIVE / MIXED`.

## B. Flow generation units

| Unit | Narrative scene | Duration | Flow mode | Story function | Start frame | End frame | Ingredients / Characters | Setting / static context | Look / lighting | ONE primary action | Environment response | Camera | Timing | End behavior | Audio policy | SFX / ambience | Dialogue if native | Continuity locks | Post-only elements | Failure risk | Fallback |
|---|---|---:|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|

Flow mode: `T2V / START_FRAME / FRAMES / INGREDIENTS / EXTEND / OMNI_EDIT / SKIP_FLOW`.
Default historical-film audio policy: `VO_POST + AMBIENCE_SFX_OPTIONAL`.
""",
    "03c_flow_reference_plan.md": """# Google Flow Reference / Ingredient Plan

Use only when the active generator is Google Flow. Do not turn every archival image into an Ingredient.

| Asset ID | Flow role | Source file / approved ref | What it controls | Background clean/simple? | Look & feel match | Historical status | Reuse across units | Post-only? | Approval |
|---|---|---|---|---|---|---|---|---|---|

Flow roles: `INGREDIENT_CHARACTER / INGREDIENT_OBJECT / INGREDIENT_ARCHITECTURE / INGREDIENT_STYLE / START_FRAME / END_FRAME / CARRY_FRAME / COMPOSITE_FRAME / POST_ONLY_TEXT`.
""",
}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("project_dir")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument(
        "--flow",
        action="store_true",
        help="Set Google Flow as the active generator and remove obsolete universal 3-reference hard cap",
    )
    args = ap.parse_args()

    root = Path(args.project_dir).resolve()
    if not root.exists():
        raise SystemExit(f"project directory does not exist: {root}")

    missing = [n for n in NEW_FILES if not (root / n).exists()]
    print(f"Project: {root}")
    for n in missing:
        print(f"  + {n}")
    if args.flow:
        print("  * project generator -> flow")
        print("  * reference capacity -> model/mode-dependent; verify current Flow UI")
    print("Generated Flow prompt/review files are created only after review/compilation.")

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
            if args.flow:
                meta["generator"] = "flow"
                c = meta.setdefault("ai_generation_constraints", {})
                c["max_reference_images_per_shot"] = None
                c.setdefault("max_clip_duration_seconds", 10)
                meta["flow"] = {
                    "capability_snapshot": "verify-current-Flow-UI-before-final-generation",
                    "prompt_language": "English",
                    "allowed_duration_candidates_seconds": [4, 6, 8, 10],
                    "duration_is_model_dependent": True,
                    "reference_limit": "model/mode-dependent; verify current UI",
                    "preferred_tools": [
                        "Ingredients",
                        "Characters",
                        "Frames to Video",
                        "Extend",
                        "Scenebuilder",
                        "Flow Agent",
                    ],
                    "historical_audio_default": "VO_POST + AMBIENCE_SFX_OPTIONAL",
                    "prompt_compiler": "scripts/compile_flow_prompts.py",
                    "script_reviewer": "scripts/review_flow_script.py",
                    "prompt_linter": "scripts/lint_flow_prompts.py",
                }
            meta_path.write_text(
                json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
            )

    notes = root / "V18_UPGRADE_NOTES.md"
    if not notes.exists():
        notes.write_text(
            "# v1.8 Upgrade Notes\n\n"
            "Added story-causality mapping, Google Flow scene/unit separation, Flow reference-role planning, and Flow-native prompt compilation/review support. Existing evidence, scripts, storyboards, endpoint plans, and previous prompt packs were not overwritten.\n\n"
            "Recommended Flow path: fill `04a_story_causality_map.md` -> rewrite/approve `04b_flow_scene_script.md` -> map references in `03c_flow_reference_plan.md` -> run `python scripts/review_flow_script.py <project_dir>` -> run `python scripts/compile_flow_prompts.py <project_dir>`.\n",
            encoding="utf-8",
        )
    print("Applied.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
