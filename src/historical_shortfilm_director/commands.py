"""Legacy command routing without a shell or duplicated implementations."""

from __future__ import annotations
from importlib import import_module
import sys
from pathlib import Path
from contextlib import contextmanager

MODULES = {
    "production_common": "runtime.common",
    "production_runtime": "runtime.engine",
    "pipeline_controller": "runtime.controller",
    "approve_gate": "gates",
    "register_asset": "assets",
    "seal_evidence": "evidence.overlays",
    "apply_locked_overlays": "evidence.apply_overlays",
    "init_project": "project",
    "compile_scene_graph": "production.graph",
    "prepare_production": "production.prepare",
    "compile_image25_jobs": "production.image_jobs",
    "compile_flow_jobs": "production.video_jobs",
    "compile_generation_plan": "production.generation_plan",
    "compile_direct_assembly": "production.assembly_plan",
    "compile_flow_prompts": "prompts.video",
    "compile_chain_prompts": "prompts.chain",
    "lint_flow_prompts": "qc.video_prompts",
    "lint_generation_prompts": "qc.generation_prompts",
    "qc_project": "qc.readiness",
    "review_flow_endpoints": "qc.endpoints",
    "review_flow_script": "qc.screenplay",
    "review_join_contracts": "qc.joins",
    "auto_qc_media": "qc.media",
    "build_animatic": "media.animatic",
    "assemble_direct": "media.assembly",
    "render_deterministic_shots": "media.deterministic",
    "mix_final_master": "media.finishing",
    "compile_ass_subtitles": "media.subtitles",
    "extract_review_frames": "media.frames",
    "build_review_board": "reviews.board",
    "build_review_packet": "reviews.packet",
    "compile_flow_operator_pack": "providers.flow.operator_pack",
    "code_video": "providers.code.command",
    "check_dependencies": "dependencies",
    "validate_skill": "validation",
    "upgrade_project_v110": "migrations.legacy.upgrade_project_v110",
    "upgrade_project_v13": "migrations.legacy.upgrade_project_v13",
    "upgrade_project_v14": "migrations.legacy.upgrade_project_v14",
    "upgrade_project_v15": "migrations.legacy.upgrade_project_v15",
    "upgrade_project_v16": "migrations.legacy.upgrade_project_v16",
    "upgrade_project_v17": "migrations.legacy.upgrade_project_v17",
    "upgrade_project_v18": "migrations.legacy.upgrade_project_v18",
    "upgrade_project_v19": "migrations.legacy.upgrade_project_v19",
    "upgrade_project_v20": "migrations.legacy.upgrade_project_v20",
    "upgrade_project_v30": "migrations.legacy.upgrade_project_v30",
}


def module_command(script):
    key = script.removesuffix(".py")
    if key not in MODULES:
        raise ValueError("Unknown local command: " + key)
    return [sys.executable, "-X", "utf8", str(Path(__file__).with_name("_command.py")), key]


@contextmanager
def arguments(name, args):
    previous = sys.argv
    sys.argv = [name, *args]
    try:
        yield
    finally:
        sys.argv = previous


def legacy_main(script, args):
    key = script.removesuffix(".py")
    if key not in MODULES:
        raise ValueError("Unknown local command: " + key)
    with arguments(key, args):
        try:
            module = import_module("historical_shortfilm_director." + MODULES[key])
            entry = getattr(module, "main", None)
            return entry() or 0 if entry else 0
        except SystemExit as result:
            return result.code or 0
    return 0
