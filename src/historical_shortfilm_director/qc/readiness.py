#!/usr/bin/env python3
"""Structural/readiness QC for historical-shortfilm-director projects.

This cannot validate historical truth or artistic quality. It detects missing
production gates, obvious slideshow patterns, weak generation bookkeeping, and
profile/runtime metadata problems.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path
from historical_shortfilm_director.profiles import load_profile, profile_qc, project_profile
from historical_shortfilm_director import __version__

REQUIRED_CORE = [
    "00_brief.md",
    "00_human_gates.md",
    "01_evidence_ledger.md",
    "02_angle_matrix.md",
    "03_story_bible.md",
    "03_asset_style_bible.md",
    "04_script.md",
    "05_storyboard.md",
    "05a_film_opening_ending.md",
    "05b_attention_map.md",
    "05c_shot_chaining_plan.md",
    "05d_endpoint_reachability.md",
    "05e_bridge_keyframe_plan.md",
    "05_animatic_plan.md",
    "07_shot_list.md",
    "08_asset_manifest.md",
    "09_edit_plan.md",
    "10_qc_report.md",
    "06d_generation_review.md",
]

AI_FILES = [
    "06_ai_prompts.md",
    "06_generation_manifest.json",
    "06_generation_log.csv",
]

PLACEHOLDER_PATTERNS = [r"\bTBD\b", r"\bTODO\b"]


def nontrivial_lines(text: str) -> int:
    count = 0
    for line in text.splitlines():
        s = line.strip()
        if not s or s.startswith("#") or re.fullmatch(r"[|:\- ]+", s):
            continue
        count += 1
    return count


def storyboard_creativity_warnings(text: str) -> list[str]:
    """Heuristic anti-slideshow checks. This is not aesthetic judgment."""
    out: list[str] = []
    rows = [
        ln.strip()
        for ln in text.splitlines()
        if re.match(r"^\|\s*(?:S?\d+(?:[-.]\d+)?|P\d+|\d+)\s*\|", ln.strip(), flags=re.I)
    ]
    shot_rows = [r for r in rows if len(r.split("|")) >= 8]

    if len(shot_rows) >= 6 and "Sequence Design" not in text:
        out.append(
            "storyboard has many shot rows but no Sequence Design section; redesign sequence-first before asset-by-asset shots"
        )

    required_header_terms = [
        "Purpose / director intent",
        "Lens feel",
        "ONE primary action",
        "Reference IDs",
        "Why this cut",
        "Gen risk",
        "Safer fallback",
    ]
    missing = [term for term in required_header_terms if term.lower() not in text.lower()]
    if missing:
        out.append("production storyboard schema is missing required fields: " + ", ".join(missing))

    drift_terms = [
        "缓慢推",
        "慢推",
        "缓慢推进",
        "轻微推",
        "推近",
        "缓慢横移",
        "极慢横移",
        "横移",
        "缓慢拉",
        "拉远",
        "叠化",
        "慢慢叠化",
        "几乎不动",
        "稳定停留",
        "固定机位",
        "slow push",
        "push-in",
        "slow pan",
        "pan across",
        "slow pull",
        "dissolve",
        "locked-off",
    ]
    simple = []
    for row in shot_rows:
        low = row.lower()
        simple.append(any(t.lower() in low for t in drift_terms))
    if shot_rows:
        ratio = sum(simple) / len(shot_rows)
        if len(shot_rows) >= 8 and ratio >= 0.45:
            out.append(
                f"{sum(simple)}/{len(shot_rows)} storyboard rows rely on slow drift/dissolve language ({ratio:.0%}); likely slideshow risk"
            )
        run = 0
        max_run = 0
        for flag in simple:
            run = run + 1 if flag else 0
            max_run = max(max_run, run)
        if max_run >= 3:
            out.append(
                f"detected a run of {max_run} consecutive slow-drift/dissolve-style rows; anti-slideshow rule allows at most 2 unless deliberately justified"
            )
    return out


def asset_bible_warnings(text: str) -> list[str]:
    out: list[str] = []
    if "APPROVED" not in text:
        out.append(
            "asset/style bible has no APPROVED state; continuity-critical references may not be frozen"
        )
    ids = re.findall(
        r"\b(?:CHAR|COSTUME|PROP|ARCH|ENV|DOC|STYLE|AUDIO|REF)\d{1,4}\b", text, flags=re.I
    )
    if nontrivial_lines(text) >= 5 and not ids:
        out.append(
            "asset/style bible has content but no stable asset IDs (CHAR/ARCH/ENV/STYLE/etc.)"
        )
    return out


def animatic_warnings(text: str, project_status: str) -> list[str]:
    out: list[str] = []
    upper = text.upper()
    if "SCRATCH VO" not in upper:
        out.append("animatic plan does not mention scratch VO")
    if "TEMP MUSIC" not in upper and "TEMPORARY MUSIC" not in upper:
        out.append("animatic plan does not mention temp music/rhythm")
    generation_ready = project_status.lower() in {
        "generation-ready",
        "generation_ready",
        "ready",
        "production-ready",
        "production_ready",
    }
    if generation_ready and "ANIMATIC_APPROVED" not in upper:
        out.append(
            "project status claims ready/generation-ready but animatic is not marked ANIMATIC_APPROVED"
        )
    return out


def film_opening_ending_warnings(text: str) -> list[str]:
    out: list[str] = []
    low = text.lower()
    if "first-frame" not in low and "first frame" not in low and "首帧" not in text:
        out.append("whole-film opening/ending plan does not define opening variants")
    if "final-frame" not in low and "final frame" not in low and "尾帧" not in text:
        out.append("whole-film opening/ending plan does not define ending variants")
    if "selected anchor pair" not in low and "selected" not in low and "选定" not in text:
        out.append("whole-film opening/ending plan has no selected opening/ending pair")
    return out


def attention_map_warnings(text: str) -> list[str]:
    out: list[str] = []
    required = ["Viewer question", "New information", "Visual state change", "Unresolved gap"]
    missing = [x for x in required if x.lower() not in text.lower()]
    if missing:
        out.append("attention/state-change map missing fields: " + ", ".join(missing))
    return out


def shot_chaining_warnings(text: str, root: Path) -> list[str]:
    out: list[str] = []
    required = [
        "Chain role",
        "Start anchor",
        "End anchor target",
        "Ref1",
        "Ref2",
        "Ref3",
        "Inherit prev carry?",
        "Export carry to next?",
        "Extraction rule",
        "Reset conditions",
    ]
    missing = [x for x in required if x.lower() not in text.lower()]
    if missing:
        out.append("shot chaining plan missing v1.6 fields: " + ", ".join(missing))
    generator = ""
    meta_path = root / "project.json"
    if meta_path.exists():
        try:
            generator = str(json.loads(meta_path.read_text(encoding="utf-8")).get("generator", ""))
        except Exception:
            generator = ""
    if generator != "flow" and "3 reference" not in text.lower() and "Ref1" not in text:
        out.append(
            "shot chaining plan does not clearly address the configured reference-budget constraint"
        )
    if (
        generator != "flow"
        and "10 seconds" not in text.lower()
        and "10 s" not in text.lower()
        and "max 10" not in text.lower()
    ):
        meta_ok = False
        meta_path = root / "project.json"
        if meta_path.exists():
            try:
                meta = json.loads(meta_path.read_text(encoding="utf-8"))
                meta_ok = (
                    float(
                        meta.get("ai_generation_constraints", {}).get(
                            "max_clip_duration_seconds", 0
                        )
                    )
                    == 10
                )
            except Exception:
                meta_ok = False
        if not meta_ok:
            out.append("legacy non-Flow chaining plan does not establish its clip-duration ceiling")
    # Detect at least one populated shot row (first cell contains an id beyond the header/separator).
    shot_rows = []
    for ln in text.splitlines():
        s = ln.strip()
        if not s.startswith("|"):
            continue
        cells = [c.strip() for c in s.strip("|").split("|")]
        if not cells:
            continue
        first = cells[0]
        if (
            first
            and first.lower() != "shot"
            and not re.fullmatch(r":?-+:?", first.replace(" ", ""))
        ):
            shot_rows.append(cells)
    if shot_rows:
        plan_path = root / "05c_shot_chaining_plan.md"
        for generated in ["06b_generation_prompt_pack.md", "06c_generation_runbook.md"]:
            gp = root / generated
            if not gp.exists():
                out.append(
                    f"shot chaining plan has populated rows but compiled output is missing: {generated}; run scripts/compile_generation_plan.py"
                )
            elif plan_path.exists() and gp.stat().st_mtime < plan_path.stat().st_mtime:
                out.append(
                    f"compiled chain output is older than 05c plan: {generated}; re-run scripts/compile_generation_plan.py"
                )
    return out


def endpoint_reachability_warnings(text: str, root: Path, profile: str) -> list[str]:
    out: list[str] = []
    required = [
        "Start anchor",
        "End anchor",
        "Reachability",
        "Route",
        "Target duration",
        "AI value",
    ]
    missing = [x for x in required if x.lower() not in text.lower()]
    if missing:
        out.append("endpoint reachability plan missing v1.7 fields: " + ", ".join(missing))

    rows = []
    for ln in text.splitlines():
        s = ln.strip()
        if not s.startswith("|"):
            continue
        cells = [c.strip() for c in s.strip("|").split("|")]
        if (
            not cells
            or cells[0].lower() in {"shot", "---"}
            or re.fullmatch(r":?-+:?", cells[0].replace(" ", ""))
        ):
            continue
        if len(cells) >= 19:
            rows.append(cells)
    for cells in rows:
        sid = cells[0]
        reach = cells[13].upper()
        route = cells[14].upper()
        bridge = cells[15]
        dur = cells[16]
        ai_value = cells[17].upper()
        if ("R-C" in reach or "R-D" in reach) and route in {"I2V_START", "FLF"}:
            out.append(
                f"{sid}: {reach} is routed directly to {route}; consider bridge/occlusion/edit instead of forcing one clip"
            )
        if "R-C" in reach and route == "BRIDGE_2STEP" and not bridge:
            out.append(f"{sid}: R-C BRIDGE_2STEP has no bridge frame")
        if ai_value == "LOW" and route in {"I2V_START", "FLF", "BRIDGE_2STEP", "OCCLUSION_2STEP"}:
            out.append(
                f"{sid}: AI value LOW but route still uses primary AI generation; deterministic route may be safer"
            )
        m = re.search(r"(\d+(?:\.\d+)?)", dur)
        if (
            m
            and float(m.group(1)) > 10
            and route
            not in {
                "BRIDGE_2STEP",
                "OCCLUSION_2STEP",
                "MATCH_CUT_EDIT",
                "COMPOSITE_2_5D",
                "MOTION_GRAPHIC",
                "ARCHIVAL_HOLD",
                "LIVE_OR_EXISTING_VIDEO",
            }
        ):
            out.append(f"{sid}: target duration {m.group(1)}s exceeds current 10s clip limit")
        config = (
            project_profile(root)
            if (root / "project.json").exists()
            else load_profile(profile or "generic")
        )
        protected = config.qc.get("protected_asset_ids", [])
        if config.qc.get("prefer_deterministic_routes") and any(
            a in "|".join(cells) for a in protected
        ):
            if route in {"I2V_START", "FLF"} and ai_value != "LOW":
                out.append(
                    f"{sid}: profile-protected archival material is routed as primary generated video; review deterministic alternatives"
                )

    if rows:
        reach_path = root / "05d_endpoint_reachability.md"
        chain_path = root / "05c_shot_chaining_plan.md"
        for generated in ["06b_generation_prompt_pack.md", "06c_generation_runbook.md"]:
            gp = root / generated
            if not gp.exists():
                out.append(
                    f"reachability plan has populated rows but compiled output is missing: {generated}; run scripts/compile_generation_plan.py"
                )
            else:
                newest = max([p.stat().st_mtime for p in [reach_path, chain_path] if p.exists()])
                if gp.stat().st_mtime < newest:
                    out.append(
                        f"compiled generation output is older than reach/chain plan: {generated}; re-run scripts/compile_generation_plan.py"
                    )
        prompt_pack = root / "06b_generation_prompt_pack.md"
        lint = root / "06e_prompt_lint_report.md"
        if prompt_pack.exists():
            if not lint.exists():
                out.append(
                    "compiled prompt pack exists but prompt lint report is missing; run scripts/lint_generation_prompts.py"
                )
            elif lint.stat().st_mtime < prompt_pack.stat().st_mtime:
                out.append(
                    "prompt lint report is older than compiled prompt pack; re-run scripts/lint_generation_prompts.py"
                )
    return out


def validate_generation_manifest(path: Path) -> tuple[list[str], dict]:
    out: list[str] = []
    data: dict = {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return [f"generation manifest invalid JSON: {exc}"], {}
    if not isinstance(data, dict) or not isinstance(data.get("shots", []), list):
        out.append("generation manifest must contain a top-level shots array")
        return out, data if isinstance(data, dict) else {}
    required = {"shot_id", "prompt_id", "provider", "model", "attempt", "status"}
    for i, shot in enumerate(data.get("shots", []), 1):
        if not isinstance(shot, dict):
            out.append(f"generation manifest shot #{i} is not an object")
            continue
        missing = sorted(k for k in required if shot.get(k) in (None, ""))
        if missing:
            out.append(f"generation manifest shot #{i} missing: {', '.join(missing)}")
    return out, data


def generation_log_warnings(path: Path, manifest: dict) -> list[str]:
    out: list[str] = []
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as f:
            rows = list(csv.DictReader(f))
    except Exception as exc:
        return [f"generation log unreadable CSV: {exc}"]
    manifest_shots = manifest.get("shots", []) if isinstance(manifest, dict) else []
    if manifest_shots and not rows:
        out.append("generation manifest contains shots but generation log has no attempts")
    return out


def automation_gate_warnings(root: Path, project_status: str) -> list[str]:
    out = []
    pc = root / "00_pipeline_control.json"
    if not pc.exists():
        out.append("missing 00_pipeline_control.json; v3 autonomy/human gates are not tracked")
        return out
    try:
        data = json.loads(pc.read_text(encoding="utf-8"))
    except Exception:
        return ["00_pipeline_control.json is invalid JSON"]
    ready = project_status.lower() in {
        "generation-ready",
        "generation_ready",
        "ready",
        "production-ready",
        "production_ready",
        "final",
        "locked",
    }
    gates = data.get("gates", {})
    if ready:
        for g in ["G1_STORY", "G2_VISUAL", "G3_HERO_MOTION", "G4_PICTURE_LOCK"]:
            v = gates.get(g, {})
            st = (v.get("status") if isinstance(v, dict) else v) or "PENDING"
            if str(st).upper() not in {"APPROVED", "NOT_REQUIRED"}:
                out.append(f"project claims ready but {g} is {st}")
    for f in ["03e_evidence_overlay_plan.csv", "06n_asset_registry.json"]:
        if not (root / f).exists():
            out.append(f"missing v3 automation file: {f}")
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("project_dir")
    args = ap.parse_args()
    root = Path(args.project_dir)

    errors: list[str] = []
    warnings: list[str] = []

    if not root.exists():
        print(f"ERROR: project directory does not exist: {root}")
        return 2

    meta_path = root / "project.json"
    meta: dict = {}
    if not meta_path.exists():
        warnings.append("project.json missing; runtime/profile checks skipped")
    else:
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
        except Exception as exc:
            errors.append(f"project.json invalid: {exc}")

    warnings.extend(automation_gate_warnings(root, str(meta.get("status", ""))))

    for name in REQUIRED_CORE:
        path = root / name
        if not path.exists():
            errors.append(f"missing required project file: {name}")
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        if nontrivial_lines(text) < 2:
            warnings.append(f"{name} appears largely empty")

    ledger = root / "01_evidence_ledger.md"
    if ledger.exists():
        txt = ledger.read_text(encoding="utf-8", errors="replace")
        unresolved = len(re.findall(r"\bUNRESOLVED\b", txt))
        if unresolved:
            warnings.append(f"evidence ledger contains {unresolved} UNRESOLVED marker(s)")

    for name in REQUIRED_CORE + ["06_ai_prompts.md"]:
        path = root / name
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for pat in PLACEHOLDER_PATTERNS:
            if re.search(pat, text, flags=re.M):
                warnings.append(f"{name} contains placeholder matching {pat}")

    storyboard = root / "05_storyboard.md"
    if storyboard.exists():
        warnings.extend(
            storyboard_creativity_warnings(storyboard.read_text(encoding="utf-8", errors="replace"))
        )

    film_arc = root / "05a_film_opening_ending.md"
    if film_arc.exists():
        warnings.extend(
            film_opening_ending_warnings(film_arc.read_text(encoding="utf-8", errors="replace"))
        )

    attention_map = root / "05b_attention_map.md"
    if attention_map.exists():
        warnings.extend(
            attention_map_warnings(attention_map.read_text(encoding="utf-8", errors="replace"))
        )

    shot_chain = root / "05c_shot_chaining_plan.md"
    if shot_chain.exists():
        warnings.extend(
            shot_chaining_warnings(shot_chain.read_text(encoding="utf-8", errors="replace"), root)
        )

    endpoint_plan = root / "05d_endpoint_reachability.md"
    if endpoint_plan.exists():
        warnings.extend(
            endpoint_reachability_warnings(
                endpoint_plan.read_text(encoding="utf-8", errors="replace"),
                root,
                str(meta.get("profile", "")),
            )
        )

    asset_bible = root / "03_asset_style_bible.md"
    if asset_bible.exists():
        warnings.extend(
            asset_bible_warnings(asset_bible.read_text(encoding="utf-8", errors="replace"))
        )

    animatic = root / "05_animatic_plan.md"
    if animatic.exists():
        warnings.extend(
            animatic_warnings(
                animatic.read_text(encoding="utf-8", errors="replace"), str(meta.get("status", ""))
            )
        )

    ai_prompts = root / "06_ai_prompts.md"
    manifest_path = root / "06_generation_manifest.json"
    log_path = root / "06_generation_log.csv"
    manifest: dict = {}
    if ai_prompts.exists() or manifest_path.exists() or log_path.exists():
        for name in AI_FILES:
            if not (root / name).exists():
                warnings.append(f"AI production package missing: {name}")
        if manifest_path.exists():
            manifest_warnings, manifest = validate_generation_manifest(manifest_path)
            warnings.extend(manifest_warnings)
        if log_path.exists():
            warnings.extend(generation_log_warnings(log_path, manifest))

    from historical_shortfilm_director.providers import provider_qc

    warnings.extend(provider_qc(root, meta))

    extra_errors, extra_warnings = profile_qc(root, project_profile(root, meta), meta)
    errors.extend(extra_errors)
    warnings.extend(extra_warnings)

    print(f"Historical Short Film Project QC {__version__}")
    print(f"Project: {root.resolve()}")
    print(f"Errors: {len(errors)} | Warnings: {len(warnings)}")
    for item in errors:
        print(f"ERROR: {item}")
    for item in warnings:
        print(f"WARN: {item}")

    if errors:
        return 2
    if warnings:
        return 1
    print(
        "PASS: structural/readiness QC found no obvious issues. Historical truth and artistic judgment still require evidence/human review."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
