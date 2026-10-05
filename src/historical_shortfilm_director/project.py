#!/usr/bin/env python3
"""Initialize a historical-short-film project workspace.

No third-party dependencies.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from historical_shortfilm_director import __version__
from historical_shortfilm_director.profiles import load_profile, apply_profile
from historical_shortfilm_director.runtime.storage import local

FILES = json.loads((Path(__file__).parent / "data/templates.json").read_text(encoding="utf-8"))


GENERATION_MANIFEST = {
    "schema_version": "1.2",
    "project_title": "",
    "shots": [],
}

GENERATION_LOG_HEADER = (
    "shot_id,route,reachability,prompt_id,prompt_version,provider,model,model_version,attempt,"
    "generation_datetime,operator,start_anchor,end_anchor,reference_asset_ids,carry_frame_id,"
    "seed_or_randomness,duration_seconds,fps,output_asset,boundary_first,boundary_last,"
    "status,rejection_reason,reviewer_note\n"
)


def slugify(text: str) -> str:
    text = text.strip()
    asciiish = re.sub(r"[^A-Za-z0-9._-]+", "-", text).strip("-")
    return asciiish or "historical-film-project"


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--title", required=True)
    p.add_argument("--profile", default="generic", help="Built-in name or profile.json path")
    p.add_argument("--duration", type=int, default=None, help="Hard ceiling in seconds")
    p.add_argument("--orientation", choices=["landscape", "portrait", "either"], default="either")
    p.add_argument("--generator", choices=["generic", "flow"], default="generic")
    p.add_argument("--dir", dest="out_dir", default=None)
    args = p.parse_args()

    profile = load_profile(args.profile)
    duration = args.duration
    if duration is None:
        duration = profile.constraints.get("duration_ceiling_seconds")

    root = Path(args.out_dir or slugify(args.title)).resolve()
    if root.exists() and any(root.iterdir()):
        raise SystemExit("Destination is not empty; choose a new source-first project directory")
    root.mkdir(parents=True, exist_ok=True)

    material_dirs = [
        "00_inbox",
        "01_primary_sources",
        "02_secondary_sources",
        "03_archival_images",
        "04_audio_video",
        "05_brief_and_rules",
        "06_web_sources",
    ]
    materials_root = root / "materials"
    materials_root.mkdir(exist_ok=True)
    for d in material_dirs:
        (materials_root / d).mkdir(exist_ok=True)

    materials_readme = materials_root / "README.md"
    if not materials_readme.exists():
        materials_readme.write_text(
            "# Project materials\n\n"
            "- `00_inbox/`: unsorted material; put everything here if unsure.\n"
            "- `01_primary_sources/`: archives, official documents, scans, letters, yearbooks.\n"
            "- `02_secondary_sources/`: papers, books, articles, research notes.\n"
            "- `03_archival_images/`: historical photos, maps, posters, architecture images.\n"
            "- `04_audio_video/`: interviews, recordings, archival footage.\n"
            "- `05_brief_and_rules/`: contest notice, rules, scoring criteria.\n"
            "- `06_web_sources/`: saved web material and research log.\n\n"
            "The agent should inventory local materials before searching the web.\n",
            encoding="utf-8",
        )
    web_log = materials_root / "06_web_sources" / "web_research_log.md"
    if not web_log.exists():
        web_log.write_text(
            "# Web Research Log\n\n"
            "| Date | Query / question | Source title | URL | Source tier | Claim/evidence IDs | Notes |\n"
            "|---|---|---|---|---|---|---|\n",
            encoding="utf-8",
        )

    meta = {
        "title": args.title,
        "profile": profile.name,
        "duration_ceiling_seconds": duration,
        "orientation": args.orientation,
        "status": "initialized",
        "skill_pipeline_version": __version__,
        "generator": args.generator,
        "ai_generation_constraints": {
            "max_reference_images_per_shot": None,
            "max_clip_duration_seconds": None,
            "duration_strategy": "shortest-currently-supported-duration-covering-edit-plus-handles",
        },
        "chain_prompt_compiler": "scripts/compile_chain_prompts.py",
        "generation_plan_compiler": "scripts/compile_generation_plan.py",
        "endpoint_reachability_required": True,
        "explicit_last_frame_support": "unknown",
        "still_asset_renderer": {
            "preferred": "configured-image-provider",
            "execution": "agent-image-tool-when-available-else-job-pack",
            "exact_pixel_policy": "source-or-code-overlay-for-evidence-critical-regions",
        },
        "assembly_strategy": "seam-first-direct-assembly",
        "production_baseline": "source-only-rebuild",
        "legacy_generated_assets_policy": "ignore-unless-user-explicitly-imports",
        "automation": {
            "default_autonomy": "AUTO",
            "human_gates": ["G1_STORY", "G2_VISUAL", "G3_HERO_MOTION", "G4_PICTURE_LOCK"],
            "candidate_output_caps": {
                "routine_image": 2,
                "hero_image": 4,
                "routine_video": 2,
                "hero_video": 4,
            },
            "blind_reroll_limit_same_failure_dimension": 2,
        },
    }
    meta.update(profile.metadata)
    if args.generator == "flow":
        from historical_shortfilm_director.providers.flow import configuration

        meta["flow"] = configuration()
    (root / "project.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    for name, body in FILES.items():
        path = local(root, name)
        if not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(body, encoding="utf-8")

    for name, body in profile.templates.items():
        path = local(root, name)
        if not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(body, encoding="utf-8")

    automation_dirs = [
        "assets/frames",
        "assets/plates",
        "assets/overlays",
        "assets/candidates",
        "generated/flow_candidates",
        "generated/flow_approved",
        "reviews",
        "exports",
        "archive_legacy_generation",
    ]
    for d in automation_dirs:
        (root / d).mkdir(parents=True, exist_ok=True)

    pipeline_control = root / "00_pipeline_control.json"
    if not pipeline_control.exists():
        pipeline_control.write_text(
            json.dumps(
                {
                    "schema_version": "3.0",
                    "mode": "source-only-rebuild",
                    "gates": {
                        "G1_STORY": {"status": "PENDING", "note": ""},
                        "G2_VISUAL": {"status": "PENDING", "note": ""},
                        "G3_HERO_MOTION": {"status": "PENDING", "note": ""},
                        "G4_PICTURE_LOCK": {"status": "PENDING", "note": ""},
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

    overlay_plan = root / "03e_evidence_overlay_plan.csv"
    if not overlay_plan.exists():
        overlay_plan.write_text(
            "frame_id,target_path,source_path,source_box,target_xy,alpha_mask_path,reason,approval\n",
            encoding="utf-8-sig",
        )

    registry = root / "06n_asset_registry.json"
    if not registry.exists():
        registry.write_text(
            json.dumps({"schema_version": "3.0", "assets": {}}, ensure_ascii=False, indent=2)
            + "\n",
            encoding="utf-8",
        )

    capability_snapshot = root / "00_capability_snapshot.json"
    if not capability_snapshot.exists():
        capability_snapshot.write_text(
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

    policy = root / "00_execution_policy.json"
    policy.write_text(
        json.dumps(
            {
                "schema_version": "3.1",
                "sampling": "adaptive-until-pass",
                "authorization": {
                    "reference": "",
                    "image_output_limit": None,
                    "video_output_limit": None,
                    "flow_output_limit": None,
                },
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    caps = json.loads(capability_snapshot.read_text(encoding="utf-8"))
    caps.update(
        {
            "image": {"available": False},
            "video": {"available": False},
            "flow": {"available": False},
            "local": {},
        }
    )
    capability_snapshot.write_text(
        json.dumps(caps, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    deterministic_queue = root / "06r_deterministic_motion_queue.json"
    if not deterministic_queue.exists():
        deterministic_queue.write_text(
            json.dumps(
                {
                    "schema_version": "3.0",
                    "jobs": [],
                    "supported_motions": [
                        "HOLD",
                        "PUSH_IN",
                        "PULL_OUT",
                        "PAN_LEFT",
                        "PAN_RIGHT",
                        "FADE_TO_BLACK",
                    ],
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

    text_plan = root / "07_text_overlay_plan.csv"
    if not text_plan.exists():
        text_plan.write_text("start_s,end_s,text,style,approval\n", encoding="utf-8-sig")

    audio_plan = root / "07_audio_mix_plan.csv"
    if not audio_plan.exists():
        audio_plan.write_text(
            "track_id,path,start_s,trim_in_s,trim_out_s,gain_db,fade_in_s,fade_out_s,type,approval\n",
            encoding="utf-8-sig",
        )

    generation_manifest = root / "06_generation_manifest.json"
    if not generation_manifest.exists():
        manifest = dict(GENERATION_MANIFEST)
        manifest["project_title"] = args.title
        generation_manifest.write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )

    generation_log = root / "06_generation_log.csv"
    if not generation_log.exists():
        generation_log.write_text(GENERATION_LOG_HEADER, encoding="utf-8")

    brief = root / "00_brief.md"
    existing = brief.read_text(encoding="utf-8")
    header = (
        f"# {args.title}\n\n"
        f"- Profile: `{profile.name}`\n"
        f"- Runtime ceiling: `{duration if duration is not None else 'TBD'} s`\n"
        f"- Orientation: `{args.orientation}`\n"
        f"- Generator: `{args.generator}`\n"
        f"- AI model constraints: `generator-specific; verify current UI`, `use shortest verified provider duration that covers the approved edit + required handles; verify current UI`\n\n"
    )
    if existing.startswith("# Brief"):
        brief.write_text(header + existing[len("# Brief\n\n") :], encoding="utf-8")

    apply_profile(root, profile)
    print(root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
