#!/usr/bin/env python3
"""State/controller for the v3 automation-first film pipeline.

This script never calls external generative services itself. It tells an agent what may
run autonomously and can execute safe local compilers/QC when their inputs exist.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from historical_shortfilm_director.runtime.common import gate_status, ffmpeg

GATES = ["G1_STORY", "G2_VISUAL", "G3_HERO_MOTION", "G4_PICTURE_LOCK"]


def load_json(path: Path, default):
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def status_of(control, gate):
    v = control.get("gates", {}).get(gate, "PENDING")
    if isinstance(v, dict):
        return str(v.get("status", "PENDING")).upper()
    return str(v).upper()


def detect_local(root: Path) -> dict:
    return {
        "local_python": True,
        "pillow": bool(importlib.util.find_spec("PIL")),
        "numpy": bool(importlib.util.find_spec("numpy")),
        "opencv": bool(importlib.util.find_spec("cv2")),
        "ffmpeg": bool(shutil.which("ffmpeg")),
        "ffprobe": bool(shutil.which("ffprobe")),
    }


def nontrivial(path: Path, min_chars=80) -> bool:
    return (
        path.exists()
        and len(path.read_text(encoding="utf-8", errors="ignore").strip()) >= min_chars
    )


def controller_state(root: Path, control: dict) -> dict:
    g = {k: gate_status(root, k) for k in GATES}
    if g["G1_STORY"] != "APPROVED":
        stage = "STORY"
        gate = "G1_STORY"
        actions = [
            "Inventory primary/local sources and fill evidence ledger.",
            "Generate 2–4 genuinely different story mechanisms and run critic/historian/director passes.",
            "Present only the compressed G1 decision board to the user.",
        ]
    elif g["G2_VISUAL"] != "APPROVED":
        stage = "VISUAL_WORLD"
        gate = "G2_VISUAL"
        actions = [
            "Auto-decompose the approved story into shots and frame graph.",
            "Populate frame asset plan with image generation/code routes, risk, autonomy and candidate counts.",
            "Execute routine image generation jobs automatically when the image tool is available; apply P2/P3 code overlays and QC.",
            "Build one hero-frame review board for G2 instead of asking for per-frame approval.",
        ]
    elif g["G3_HERO_MOTION"] not in {"APPROVED", "NOT_REQUIRED"}:
        stage = "MOTION"
        gate = "G3_HERO_MOTION"
        actions = [
            "Design seam graph and endpoint reachability for all shots.",
            "Compile video prompts/jobs; run routine R-A/R-B jobs automatically when a verified provider handoff is available.",
            "Auto-QC/rank candidates; repair with overlay/Omni/local edit/bridge before fresh rerolls.",
            "Escalate only hero/high-risk/R-C ambiguities to G3.",
        ]
    elif g["G4_PICTURE_LOCK"] != "APPROVED":
        stage = "ASSEMBLY"
        gate = "G4_PICTURE_LOCK"
        actions = [
            "Compile direct assembly manifest and build picture master with registered trims/joins.",
            "Add temp VO/music/SFX sufficient to judge rhythm.",
            "Run automated technical/evidence/seam exception checks.",
            "Present picture master + exception report for G4.",
        ]
    else:
        stage = "FINALIZE"
        gate = None
        actions = [
            "Apply deterministic typography, source credits, AI disclosure, captions and final audio.",
            "Render requested aspect/export variants and run final QC/checksums.",
        ]
    return {
        "stage": stage,
        "next_human_gate": gate,
        "blocking_gate": None,
        "gate_status": g,
        "next_actions": actions,
        "note": "A pending gate does not block preparation of its review artifacts or independent jobs. Read production_runtime next for executable jobs.",
    }


def run_safe(root: Path, script: str) -> dict:
    from historical_shortfilm_director.commands import module_command

    cp = subprocess.run(
        [*module_command(script), str(root)],
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
    )
    return {
        "script": script,
        "status": "ok" if cp.returncode == 0 else "nonzero",
        "returncode": cp.returncode,
        "stdout": cp.stdout[-2000:],
        "stderr": cp.stderr[-2000:],
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("project_dir")
    ap.add_argument("--detect-local", action="store_true")
    ap.add_argument(
        "--auto-local", action="store_true", help="Run safe local compilers whose inputs exist"
    )
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    root = Path(args.project_dir).resolve()
    control_path = root / "00_pipeline_control.json"
    control = load_json(
        control_path,
        {"schema_version": "3.0", "gates": {g: {"status": "PENDING", "note": ""} for g in GATES}},
    )

    if args.detect_local:
        caps = load_json(root / "00_capability_snapshot.json", {})
        caps.update(detect_local(root))
        try:
            caps.setdefault("local", {})["ffmpeg_path"] = ffmpeg(root)
            caps["ffmpeg"] = True
        except RuntimeError:
            pass
        (root / "00_capability_snapshot.json").write_text(
            json.dumps(caps, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        control["capabilities"] = caps

    state = controller_state(root, control)
    local_runs = []
    if args.auto_local:
        stage = state["stage"]
        candidates = []
        if (
            stage in {"VISUAL_WORLD", "MOTION", "ASSEMBLY", "FINALIZE"}
            and (root / "03d_frame_asset_plan.md").exists()
        ):
            candidates += ["compile_image25_jobs.py"]
        if stage in {"MOTION", "ASSEMBLY", "FINALIZE"}:
            if (root / "06r_deterministic_motion_queue.json").exists():
                candidates += ["render_deterministic_shots.py"]
            if (root / "05h_join_contracts.md").exists():
                candidates += ["review_join_contracts.py"]
            if (root / "05f_shot_endpoint_plan.md").exists():
                candidates += ["review_flow_endpoints.py"]
            if (root / "04c_flow_prompt_blueprints.md").exists() and (
                root / "05f_shot_endpoint_plan.md"
            ).exists():
                candidates += [
                    "compile_flow_prompts.py",
                    "lint_flow_prompts.py",
                    "compile_flow_jobs.py",
                    "compile_flow_operator_pack.py",
                ]
        if stage in {"ASSEMBLY", "FINALIZE"} and (root / "05h_join_contracts.md").exists():
            candidates += ["compile_direct_assembly.py", "auto_qc_media.py"]
        if stage == "FINALIZE":
            if (root / "07_text_overlay_plan.csv").exists():
                candidates += ["compile_ass_subtitles.py"]
            if (root / "exports/direct_picture_master.mp4").exists():
                candidates += ["mix_final_master.py"]
            candidates += ["qc_project.py"]
        seen = set()
        for s in candidates:
            if s in seen:
                continue
            seen.add(s)
            result = run_safe(root, s)
            local_runs.append(result)
            if result["status"] != "ok":
                break

    control["current_stage"] = state["stage"]
    control["last_controller_run"] = datetime.now(timezone.utc).isoformat()
    control_path.write_text(
        json.dumps(control, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    state["capabilities"] = load_json(root / "00_capability_snapshot.json", {})
    state["local_runs"] = local_runs
    if (root / "06t_execution_state.json").exists():
        from historical_shortfilm_director.runtime.engine import next_jobs

        state["execution"] = next_jobs(root)

    (root / "00_next_actions.json").write_text(
        json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    if args.json:
        print(json.dumps(state, ensure_ascii=False, indent=2))
    else:
        print(f"Stage: {state['stage']}")
        print(f"Blocking gate: {state['blocking_gate'] or 'none'}")
        for i, a in enumerate(state["next_actions"], 1):
            print(f"{i}. {a}")
        if local_runs:
            print("Local automation:")
            for r in local_runs:
                print(f"- {r['script']}: {r['status']}")
    return 2 if any(r["status"] != "ok" for r in local_runs) else 0


if __name__ == "__main__":
    raise SystemExit(main())
