#!/usr/bin/env python3
"""Non-destructive v2 upgrade for an existing historical-shortfilm-director project."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from historical_shortfilm_director import __version__

FRAME = """# Frame Asset Plan — v2\n\n| Frame ID | Used by shot/unit | Role | Build route | Source/reference IDs | Pixel lock | Exact KEEP | Allowed CHANGE | Composition / crop contract | Image 2.5 task | Code/post task | Text policy | Output path | Approval |\n|---|---|---|---|---|---|---|---|---|---|---|---|---|---|\n"""
JOIN = """# Shot Join Contracts — v2\n\n| Join | From unit | To unit | Join type | Shared seam frame | Exit state | Entry state | Exit motion | Entry motion | Screen direction | Audio bridge | Handles | Reset/occluder | Post overlay at join | Fallback | Approval |\n|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|\n\nJoin types: `EXACT_SEAM / FLOW_EXTEND / MATCH_CUT / OCCLUSION_RESET / GRAPHIC_RESET / HARD_CUT`.\n"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("project_dir")
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    root = Path(a.project_dir).resolve()
    if not root.exists():
        raise SystemExit(f"Missing project: {root}")
    actions = []
    for name, body in [("03d_frame_asset_plan.md", FRAME), ("05h_join_contracts.md", JOIN)]:
        p = root / name
        if not p.exists():
            actions.append(("create", p, body))
    pj = root / "project.json"
    meta = {}
    if pj.exists():
        try:
            meta = json.loads(pj.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"WARN project.json unreadable: {e}")
    if isinstance(meta, dict):
        meta["skill_pipeline_version"] = __version__
        meta["assembly_strategy"] = "seam-first-direct-assembly"
        meta["still_asset_renderer"] = {
            "preferred": "chatgpt-image-2.5",
            "execution": "agent-image-tool-when-available-else-job-pack",
            "exact_pixel_policy": "source-or-code-overlay-for-evidence-critical-regions",
        }
        if meta.get("generator") == "flow":
            f = meta.setdefault("flow", {})
            f.update(
                {
                    "frame_asset_plan": "03d_frame_asset_plan.md",
                    "join_contract_plan": "05h_join_contracts.md",
                    "image_job_compiler": "scripts/compile_image25_jobs.py",
                    "join_contract_reviewer": "scripts/review_join_contracts.py",
                    "assembly_compiler": "scripts/compile_direct_assembly.py",
                    "picture_master_assembler": "scripts/assemble_direct.py",
                    "duration_strategy": "shortest-supported-duration-covering-edit-plus-handles",
                }
            )
        actions.append(("project.json", pj, json.dumps(meta, ensure_ascii=False, indent=2) + "\n"))
    print("Planned v2 upgrade (non-destructive):")
    for kind, p, _ in actions:
        print(f"- {kind}: {p.name}")
    print(
        "- preserve all existing approved project files, prompts, animatics, anchors and generated assets"
    )
    print(
        "- legacy fixed-10s / 3-reference assumptions remain historical records, not v2 hard rules"
    )
    if not a.apply:
        print("Dry run only. Re-run with --apply to write.")
        return 0
    for kind, p, body in actions:
        if kind == "create" and p.exists():
            continue
        p.write_text(body, encoding="utf-8")
    print("Applied v2 additive upgrade.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
