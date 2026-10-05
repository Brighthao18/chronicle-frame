"""Retained Flow-specific planning policy; no provider execution."""

import re
from pathlib import Path


def flow_shot_endpoint_warnings(root: Path) -> list[str]:
    out: list[str] = []
    ep = root / "05f_shot_endpoint_plan.md"
    if not ep.exists():
        return [
            "Google Flow project missing 05f_shot_endpoint_plan.md; per-shot Start/End Frames are not planned"
        ]
    txt = ep.read_text(encoding="utf-8", errors="replace")
    required = [
        "Unit",
        "Flow mode",
        "Start frame ID",
        "End frame needed?",
        "End frame ID",
        "KEEP fixed",
        "CHANGE",
        "Motion path",
        "Reachability",
        "Carry-in",
        "Carry-out",
    ]
    missing = [x for x in required if x.lower() not in txt.lower()]
    if missing:
        out.append("05f_shot_endpoint_plan.md missing fields: " + ", ".join(missing))

    populated = False
    for ln in txt.splitlines():
        s = ln.strip()
        if not s.startswith("|"):
            continue
        cells = [c.strip() for c in s.strip("|").split("|")]
        if not cells:
            continue
        first = cells[0]
        if (
            first
            and first.lower() != "unit"
            and not re.fullmatch(r":?-+:?", first.replace(" ", ""))
        ):
            populated = True
            break
    if populated:
        review = root / "05g_shot_endpoint_review.md"
        if not review.exists():
            out.append(
                "05f endpoint plan has populated rows but 05g_shot_endpoint_review.md is missing; run scripts/review_flow_endpoints.py"
            )
        elif review.stat().st_mtime < ep.stat().st_mtime:
            out.append(
                "05g_shot_endpoint_review.md is older than 05f_shot_endpoint_plan.md; re-run scripts/review_flow_endpoints.py"
            )
    return out


def flow_project_warnings(root: Path, meta: dict) -> list[str]:
    out: list[str] = []
    out.extend(flow_shot_endpoint_warnings(root))
    required = [
        "03c_flow_reference_plan.md",
        "03d_frame_asset_plan.md",
        "04a_story_causality_map.md",
        "04b_flow_scene_script.md",
        "04c_flow_prompt_blueprints.md",
        "05f_shot_endpoint_plan.md",
        "05h_join_contracts.md",
    ]
    for name in required:
        if not (root / name).exists():
            out.append(f"Google Flow generator missing support file: {name}")

    scene = root / "04b_flow_scene_script.md"
    populated_units = False
    if scene.exists():
        txt = scene.read_text(encoding="utf-8", errors="replace")
        # Detect data rows whose first cell is not header/separator.
        in_units = "## B. Flow generation units" in txt
        if in_units:
            after = txt.split("## B. Flow generation units", 1)[1]
            for ln in after.splitlines():
                s = ln.strip()
                if not s.startswith("|"):
                    continue
                cells = [c.strip() for c in s.strip("|").split("|")]
                if not cells:
                    continue
                first = cells[0]
                if (
                    first
                    and first.lower() != "unit"
                    and not re.fullmatch(r":?-+:?", first.replace(" ", ""))
                ):
                    populated_units = True
                    break
        if populated_units:
            review = root / "04c_flow_script_review.md"
            prompts = root / "06f_flow_prompt_pack.md"
            sb = root / "06g_flow_scenebuilder_plan.md"
            lint = root / "06h_flow_prompt_lint.md"
            if not review.exists():
                out.append(
                    "Flow generation units are populated but 04c_flow_script_review.md is missing; run scripts/review_flow_script.py"
                )
            elif review.stat().st_mtime < scene.stat().st_mtime:
                out.append(
                    "Flow script review is older than 04b_flow_scene_script.md; re-run scripts/review_flow_script.py"
                )
            deps = [
                scene,
                root / "04c_flow_prompt_blueprints.md",
                root / "05f_shot_endpoint_plan.md",
            ]
            newest_dep = max([d.stat().st_mtime for d in deps if d.exists()])
            for f in [prompts, sb]:
                if not f.exists():
                    out.append(
                        f"Flow generation units are populated but compiled output is missing: {f.name}; run scripts/compile_flow_prompts.py"
                    )
                elif f.stat().st_mtime < newest_dep:
                    out.append(
                        f"Flow compiled output is older than script/blueprint/shot-endpoint inputs: {f.name}; re-run scripts/compile_flow_prompts.py"
                    )
            if prompts.exists():
                if not lint.exists():
                    out.append(
                        "Flow prompt pack exists but Flow prompt lint is missing; run scripts/lint_flow_prompts.py"
                    )
                elif lint.stat().st_mtime < prompts.stat().st_mtime:
                    out.append(
                        "Flow prompt lint is older than 06f_flow_prompt_pack.md; re-run scripts/lint_flow_prompts.py"
                    )

    # v2 seam-first still/join/assembly checks
    frame_plan = root / "03d_frame_asset_plan.md"
    if frame_plan.exists():
        ftxt = frame_plan.read_text(encoding="utf-8", errors="replace")
        if any(route in ftxt for route in ["IMAGE25_EDIT", "IMAGE25_SYNTH", "HYBRID_IMAGE25_CODE"]):
            # Do not require a compiled job pack when the agent executed image jobs directly.
            if "| APPROVED |" in ftxt.upper() and not (root / "06i_image25_job_pack.md").exists():
                out.append(
                    "approved Image 2.5 frame routes detected; if image jobs were not executed directly, run scripts/compile_image25_jobs.py"
                )

    join_plan = root / "05h_join_contracts.md"
    populated_joins = False
    if join_plan.exists():
        jtxt = join_plan.read_text(encoding="utf-8", errors="replace")
        for ln in jtxt.splitlines():
            ss = ln.strip()
            if not ss.startswith("|"):
                continue
            cc = [c.strip() for c in ss.strip("|").split("|")]
            if (
                cc
                and cc[0]
                and cc[0].lower() != "join"
                and not re.fullmatch(r":?-+:?", cc[0].replace(" ", ""))
            ):
                populated_joins = True
                break
        if populated_joins:
            jr = root / "05i_join_contract_review.md"
            manifest = root / "06k_direct_assembly_manifest.csv"
            if not jr.exists():
                out.append(
                    "join contracts are populated but 05i_join_contract_review.md is missing; run scripts/review_join_contracts.py"
                )
            elif jr.stat().st_mtime < join_plan.stat().st_mtime:
                out.append(
                    "join contract review is older than 05h_join_contracts.md; re-run scripts/review_join_contracts.py"
                )
            if not manifest.exists():
                out.append(
                    "join contracts are populated but direct-assembly manifest is missing; run scripts/compile_direct_assembly.py"
                )

    flow = meta.get("flow", {}) if isinstance(meta, dict) else {}
    if not flow:
        out.append("project generator is flow but project.json has no flow capability/config block")
    else:
        if str(flow.get("prompt_language", "")).lower() != "english":
            out.append(
                "Flow prompt language is not set to English; current project best-practice profile expects audited English production prompts"
            )
        if "reference_limit" not in flow:
            out.append(
                "Flow config does not state that reference capacity is model/mode-dependent; verify current UI before final generation"
            )
        if str(flow.get("shot_endpoint_plan", "")) != "05f_shot_endpoint_plan.md":
            out.append(
                "Flow config does not point to 05f_shot_endpoint_plan.md as the per-shot endpoint authority"
            )
        if str(flow.get("frame_asset_plan", "")) != "03d_frame_asset_plan.md":
            out.append("Flow config does not point to 03d_frame_asset_plan.md")
        if str(flow.get("join_contract_plan", "")) != "05h_join_contracts.md":
            out.append("Flow config does not point to 05h_join_contracts.md")
    return out
