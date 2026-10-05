#!/usr/bin/env python3
"""Add v3 automation controls to an existing project without adopting legacy generated outputs.

Default is non-destructive: existing generated files remain on disk but project policy marks
them ignored. Use --apply to write. No file is deleted.
"""

from __future__ import annotations
import argparse
import json
from pathlib import Path
from historical_shortfilm_director import __version__
from historical_shortfilm_director.project import FILES

NEW_FILES = [
    "00_human_gates.md",
    "03d_frame_asset_plan.md",
    "05f_shot_endpoint_plan.md",
    "05h_join_contracts.md",
]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("project_dir")
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    root = Path(a.project_dir).resolve()
    if not root.exists():
        raise SystemExit(f"Missing project: {root}")
    actions = []
    for name in NEW_FILES:
        if not (root / name).exists():
            actions.append(("write", name))
    for d in [
        "assets/frames",
        "assets/plates",
        "assets/overlays",
        "assets/candidates",
        "generated/flow_candidates",
        "generated/flow_approved",
        "reviews",
        "exports",
        "archive_legacy_generation",
    ]:
        if not (root / d).exists():
            actions.append(("mkdir", d))
    for name in [
        "00_pipeline_control.json",
        "00_capability_snapshot.json",
        "03e_evidence_overlay_plan.csv",
        "06n_asset_registry.json",
        "V3_SOURCE_FIRST_POLICY.md",
    ]:
        if not (root / name).exists():
            actions.append(("write-special", name))
    print("Planned v3 source-first additions:")
    for op, name in actions:
        print(f"- {op}: {name}")
    print(
        f"- project.json: set skill_pipeline_version={__version__} and ignore legacy generated outputs unless explicitly imported"
    )
    if not a.apply:
        print("Dry run. Re-run with --apply.")
        return 0
    for op, name in actions:
        if op == "mkdir":
            (root / name).mkdir(parents=True, exist_ok=True)
        elif op == "write":
            (root / name).write_text(FILES[name], encoding="utf-8")
        elif name == "00_pipeline_control.json":
            (root / name).write_text(
                json.dumps(
                    {
                        "schema_version": "3.0",
                        "mode": "source-only-rebuild",
                        "gates": {
                            g: {"status": "PENDING", "note": ""}
                            for g in ["G1_STORY", "G2_VISUAL", "G3_HERO_MOTION", "G4_PICTURE_LOCK"]
                        },
                        "capabilities": {},
                        "current_stage": "INGEST",
                        "last_controller_run": None,
                    },
                    ensure_ascii=False,
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )
        elif name == "00_capability_snapshot.json":
            (root / name).write_text(
                json.dumps(
                    {
                        "image_tool_direct": "unknown",
                        "flow_browser_automation": "unknown",
                        "local_python": True,
                        "ffmpeg": "unknown",
                        "vision_review": "unknown",
                        "web_research": "unknown",
                        "notes": [],
                    },
                    ensure_ascii=False,
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )
        elif name == "03e_evidence_overlay_plan.csv":
            (root / name).write_text(
                "frame_id,target_path,source_path,source_box,target_xy,alpha_mask_path,reason,approval\n",
                encoding="utf-8-sig",
            )
        elif name == "06n_asset_registry.json":
            (root / name).write_text(
                json.dumps({"schema_version": "3.0", "assets": {}}, ensure_ascii=False, indent=2)
                + "\n",
                encoding="utf-8",
            )
        elif name == "V3_SOURCE_FIRST_POLICY.md":
            (root / name).write_text(
                "# v3 Source-First Policy\n\nLegacy generated images, videos, old prompt packs and AI composites remain on disk but are **not authoritative production inputs**. Rebuild new Image 2.5 frames and Flow renders from verified sources and current approved story decisions. Import a legacy generated asset only if the user explicitly selects it.\n",
                encoding="utf-8",
            )
    pj = root / "project.json"
    meta = {}
    if pj.exists():
        try:
            meta = json.loads(pj.read_text(encoding="utf-8"))
        except Exception:
            meta = {}
    meta["skill_pipeline_version"] = __version__
    meta["production_baseline"] = "source-only-rebuild"
    meta["legacy_generated_assets_policy"] = "ignore-unless-user-explicitly-imports"
    meta["assembly_strategy"] = "seam-first-direct-assembly"
    meta.setdefault("automation", {}).update(
        {
            "default_autonomy": "AUTO",
            "human_gates": ["G1_STORY", "G2_VISUAL", "G3_HERO_MOTION", "G4_PICTURE_LOCK"],
            "best_of_n": {"routine_image": 2, "hero_image": 4, "routine_flow": 2, "hero_flow": 4},
            "blind_reroll_limit_same_failure_dimension": 2,
        }
    )
    pj.write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("Applied v3 source-first automation controls. Legacy generated files were not modified.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
