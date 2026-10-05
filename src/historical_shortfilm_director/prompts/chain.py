#!/usr/bin/env python3
"""Compile a shot-chaining markdown plan into ready-to-use I2V prompt blocks.

The compiler is intentionally model-neutral. It assumes a hard production profile
of max 3 reference images per shot and max 10 seconds per generated clip unless
overridden by project.json.

No third-party dependencies.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

DEFAULT_MAX_REFS = 3
DEFAULT_MAX_SECONDS = 10.0

ALIASES = {
    "shot": ["shot", "shot id", "镜头", "镜号"],
    "duration": ["duration", "时长"],
    "chain_role": ["chain role", "role", "链式角色"],
    "prev": ["prev shot / source", "prev shot", "previous shot", "上一镜", "前镜"],
    "start": ["start anchor", "start", "首帧", "起始锚点"],
    "end_target": ["end anchor target", "end target", "尾帧目标", "结束锚点"],
    "ref1": ["ref1", "ref 1", "reference 1", "参考1", "参考位1"],
    "ref2": ["ref2", "ref 2", "reference 2", "参考2", "参考位2"],
    "ref3": ["ref3", "ref 3", "reference 3", "参考3", "参考位3"],
    "inherit": [
        "inherit prev carry?",
        "inherit previous carry?",
        "inherit carry?",
        "继承上一镜尾帧?",
        "继承前镜?",
    ],
    "export": ["export carry to next?", "export carry?", "输出尾帧给下一镜?", "产出尾帧?"],
    "carry_legacy": [
        "carry-forward allowed?",
        "carry-forward",
        "carry forward",
        "允许继承",
        "尾帧继承",
    ],
    "extraction": ["extraction rule", "抽帧规则", "尾帧抽取规则"],
    "reset": ["reset conditions", "reset condition", "重置条件", "reset"],
    "subject_motion": ["subject motion", "主体运动"],
    "environment_motion": [
        "environment / layer motion",
        "environmental motion",
        "layer motion",
        "环境/图层运动",
        "环境运动",
    ],
    "camera_motion": ["camera motion", "镜头运动", "摄影机运动"],
    "timing": ["timing", "时间节奏", "运动节奏"],
    "end_state": ["end state", "结束状态"],
    "locks": ["continuity locks", "连续性锁定", "锁定项"],
    "negative": ["negative constraints", "negative", "禁止项", "负面约束"],
}


def norm(s: str) -> str:
    return re.sub(r"\s+", " ", s.strip().lower())


def split_md_row(line: str) -> list[str]:
    s = line.strip()
    if s.startswith("|"):
        s = s[1:]
    if s.endswith("|"):
        s = s[:-1]
    return [x.strip() for x in s.split("|")]


def is_separator(cells: list[str]) -> bool:
    if not cells:
        return False
    return all(bool(re.fullmatch(r":?-{3,}:?", c.replace(" ", ""))) for c in cells)


def header_map(headers: list[str]) -> dict[str, int]:
    mapped: dict[str, int] = {}
    nh = [norm(x) for x in headers]
    for key, aliases in ALIASES.items():
        for i, h in enumerate(nh):
            if any(h == norm(a) for a in aliases):
                mapped[key] = i
                break
    return mapped


def find_table(text: str) -> tuple[list[str], list[list[str]]]:
    lines = text.splitlines()
    for i in range(len(lines) - 1):
        if "|" not in lines[i] or "|" not in lines[i + 1]:
            continue
        headers = split_md_row(lines[i])
        sep = split_md_row(lines[i + 1])
        if not is_separator(sep):
            continue
        hm = header_map(headers)
        if "shot" not in hm:
            continue
        rows: list[list[str]] = []
        for line in lines[i + 2 :]:
            if not line.strip().startswith("|"):
                if rows:
                    break
                continue
            cells = split_md_row(line)
            if is_separator(cells):
                continue
            if len(cells) < len(headers):
                cells += [""] * (len(headers) - len(cells))
            rows.append(cells[: len(headers)])
        return headers, rows
    raise ValueError(
        "No markdown shot-chaining table found. Expected a table with a 'Shot' column."
    )


def cell(row: list[str], hm: dict[str, int], key: str, default: str = "") -> str:
    idx = hm.get(key)
    if idx is None or idx >= len(row):
        return default
    return row[idx].strip()


def parse_seconds(value: str) -> float | None:
    if not value:
        return None
    m = re.search(r"(\d+(?:\.\d+)?)", value)
    return float(m.group(1)) if m else None


def yesish(value: str) -> bool:
    v = norm(value)
    return (
        v in {"yes", "y", "true", "1", "是", "允许", "allow", "allowed"} or "yes" in v or "是" == v
    )


def noneish(value: str) -> bool:
    return norm(value) in {"", "-", "none", "n/a", "na", "无", "不需要"}


def load_constraints(root: Path) -> tuple[int, float]:
    max_refs = DEFAULT_MAX_REFS
    max_secs = DEFAULT_MAX_SECONDS
    meta = root / "project.json"
    if meta.exists():
        try:
            data = json.loads(meta.read_text(encoding="utf-8"))
            c = data.get("ai_generation_constraints", {})
            max_refs = int(c.get("max_reference_images_per_shot", max_refs))
            max_secs = float(c.get("max_clip_duration_seconds", max_secs))
        except Exception:
            pass
    return max_refs, max_secs


def role_default(inherit: bool, prev: str) -> str:
    if not prev or noneish(prev):
        return "CHAIN_START"
    return "CHAIN_CONTINUE" if inherit else "CHAIN_RESET"


def render_prompt(shot: dict[str, str], max_refs: int, max_secs: float) -> str:
    refs = [shot.get(f"ref{i}", "") for i in range(1, max_refs + 1)]
    ref_lines = []
    for i, ref in enumerate(refs, 1):
        ref_lines.append(f"REF{i}: {ref or '[UNASSIGNED]'}")

    return (
        f"""SHOT ID: {shot["shot"]}\nCHAIN ROLE: {shot["chain_role"]}\nPREVIOUS SHOT / SOURCE: {shot["prev"] or "[NONE / RESET]"}\nINHERIT PREVIOUS CARRY: {shot["inherit"] or "no"}\nEXPORT CARRY TO NEXT: {shot["export"] or "no"}\nSTART ANCHOR: {shot["start"] or "[DEFINE APPROVED START FRAME]"}\nEND ANCHOR TARGET: {shot["end_target"] or "[DEFINE DESIRED END STATE]"}\nDURATION: {shot["duration"] or "[SET DURATION]"} (hard maximum {max_secs:g}s)\n\nREFERENCE SLOTS — hard maximum {max_refs} images:\n"""
        + "\n".join(ref_lines)
        + f"""\n\nSUBJECT MOTION:\n{shot["subject_motion"] or "[Describe only the one primary subject action. Use NONE when archival people must remain still.]"}\n\nENVIRONMENTAL / LAYER MOTION:\n{shot["environment_motion"] or "[Describe paper layers, light, focus, particles, map lines, or environmental motion only if needed.]"}\n\nCAMERA MOTION:\n{shot["camera_motion"] or "[Describe one controlled camera path.]"}\n\nTIMING:\n{shot["timing"] or "[Describe the motion progression within the clip.]"}\n\nEND STATE:\n{shot["end_state"] or shot["end_target"] or "[Describe the stable visual state needed for the cut / next shot.]"}\n\nCONTINUITY LOCKS:\n{shot["locks"] or "[List geometry / identity / signage / screen-direction invariants.]"}\n\nNEGATIVE CONSTRAINTS:\n{shot["negative"] or "[No geometry drift, no text mutation, no extra people/objects, no invented historical action, no uncontrolled camera motion.]"}\n\nNEXT-SHOT CARRY RULE:\n{shot["extraction"] or "[Inspect the final second and extract the cleanest low-blur frame with intact geometry; save as a stable CF_<SHOT>_vN ID.]"}\n\nRESET CONDITIONS:\n{shot["reset"] or "[Reset if geometry/text/identity drifts, if the end state is not cuttable, or if the next shot needs a new authoritative composition.]"}\n"""
    )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("project_dir")
    ap.add_argument("--plan", default="05c_shot_chaining_plan.md")
    ap.add_argument("--output", default="06b_chain_prompt_pack.md")
    ap.add_argument("--runbook", default="06c_chain_generation_runbook.md")
    args = ap.parse_args()

    root = Path(args.project_dir).resolve()
    plan = root / args.plan
    if not plan.exists():
        raise SystemExit(f"Missing chaining plan: {plan}")

    max_refs, max_secs = load_constraints(root)
    headers, rows = find_table(plan.read_text(encoding="utf-8", errors="replace"))
    hm = header_map(headers)

    shots: list[dict[str, str]] = []
    errors: list[str] = []
    warnings: list[str] = []

    for row in rows:
        sid = cell(row, hm, "shot")
        if not sid or sid.lower() in {"shot", "..."}:
            continue
        legacy_carry = cell(row, hm, "carry_legacy")
        inherit_raw = cell(row, hm, "inherit") or legacy_carry
        inherit = yesish(inherit_raw)
        prev = cell(row, hm, "prev")
        role = cell(row, hm, "chain_role") or role_default(inherit, prev)
        export_raw = cell(row, hm, "export")
        if not export_raw:
            export_raw = "no" if role.upper() == "CHAIN_END" else "yes"
        export = yesish(export_raw)
        shot = {
            "shot": sid,
            "duration": cell(row, hm, "duration"),
            "chain_role": role,
            "prev": prev,
            "start": cell(row, hm, "start"),
            "end_target": cell(row, hm, "end_target"),
            "inherit": inherit_raw,
            "export": export_raw,
            "extraction": cell(row, hm, "extraction"),
            "reset": cell(row, hm, "reset"),
            "subject_motion": cell(row, hm, "subject_motion"),
            "environment_motion": cell(row, hm, "environment_motion"),
            "camera_motion": cell(row, hm, "camera_motion"),
            "timing": cell(row, hm, "timing"),
            "end_state": cell(row, hm, "end_state"),
            "locks": cell(row, hm, "locks"),
            "negative": cell(row, hm, "negative"),
        }
        for i in range(1, max_refs + 1):
            shot[f"ref{i}"] = cell(row, hm, f"ref{i}")

        secs = parse_seconds(shot["duration"])
        if secs is not None and secs > max_secs:
            errors.append(f"{sid}: duration {secs:g}s exceeds model maximum {max_secs:g}s")
        assigned = [shot[f"ref{i}"] for i in range(1, max_refs + 1) if not noneish(shot[f"ref{i}"])]
        if len(assigned) > max_refs:
            errors.append(f"{sid}: {len(assigned)} references exceed max {max_refs}")
        if inherit and not shot["ref1"]:
            warnings.append(
                f"{sid}: inherits previous carry but REF1 is empty; expected a CF_<prev> frame or explicit placeholder"
            )
        r = role.upper()
        if r == "CHAIN_RESET" and inherit:
            warnings.append(f"{sid}: CHAIN_RESET should not inherit the previous carry frame")
        if r in {"CHAIN_CONTINUE", "CHAIN_REVEAL"} and not inherit:
            warnings.append(
                f"{sid}: {r} normally inherits the previous carry frame; verify this is intentional"
            )
        if r == "CHAIN_START" and inherit:
            warnings.append(f"{sid}: CHAIN_START cannot inherit a previous carry frame")
        if r == "CHAIN_END" and export:
            warnings.append(
                f"{sid}: CHAIN_END exports a carry frame even though no next chained shot is expected; verify this is intentional"
            )
        shots.append(shot)

    if not shots:
        raise SystemExit("No shot rows found in chaining plan.")

    prompt_lines = [
        "# Chain Prompt Pack",
        "",
        f"Compiled from `{args.plan}`.",
        f"Hard limits: **max {max_refs} reference images / shot**, **max {max_secs:g}s / clip**.",
        "",
        "> Replace carry-frame placeholders only after the previous shot is approved. Do not propagate a bad tail frame.",
        "",
    ]
    for shot in shots:
        prompt_lines += [
            f"## {shot['shot']}",
            "",
            "```text",
            render_prompt(shot, max_refs, max_secs).rstrip(),
            "```",
            "",
        ]

    if warnings:
        prompt_lines += ["## Compiler warnings", ""] + [f"- {w}" for w in warnings] + [""]
    if errors:
        prompt_lines += (
            ["## Compiler errors — fix before generation", ""] + [f"- {e}" for e in errors] + [""]
        )

    (root / args.output).write_text("\n".join(prompt_lines), encoding="utf-8")

    run = [
        "# Chain Generation Runbook",
        "",
        f"Limits: {max_refs} references / shot; {max_secs:g}s maximum clip duration.",
        "",
        "## Sequential execution",
        "",
    ]
    for idx, shot in enumerate(shots, 1):
        inherit = yesish(shot["inherit"])
        export = yesish(shot["export"])
        run += [
            f"### {idx}. Generate {shot['shot']}",
            "",
            f"- Chain role: `{shot['chain_role']}`",
            f"- Previous source: `{shot['prev'] or 'NONE'}`",
            f"- Inherit previous carry: `{shot['inherit'] or 'no'}`",
            f"- Export carry to next: `{shot['export'] or 'no'}`",
            f"- Start anchor: `{shot['start'] or 'DEFINE'}`",
            f"- REF1: `{shot['ref1'] or 'UNASSIGNED'}`",
            f"- REF2: `{shot.get('ref2', '') or 'UNASSIGNED'}`",
            f"- REF3: `{shot.get('ref3', '') or 'UNASSIGNED'}`",
            f"- Generate using the corresponding block in `{args.output}`.",
            "- Review the clip before allowing continuity to propagate.",
        ]
        if export:
            run += [
                f"- If approved: inspect the final second, choose the cleanest continuity frame, save it as `CF_{shot['shot']}_vN`, and assign it to the next shot's carry slot if required.",
                f"- Extraction rule: {shot['extraction'] or 'cleanest low-blur tail/near-tail frame with intact geometry'}",
            ]
        else:
            run += [
                "- This shot is not required to propagate a tail frame; follow the next shot's reset/start-anchor plan."
            ]
        run += [
            f"- Reset if: {shot['reset'] or 'geometry/text/identity drift or uncuttable end state'}",
            "",
        ]

    if errors:
        run += ["## Blocking errors", ""] + [f"- {e}" for e in errors] + [""]
    (root / args.runbook).write_text("\n".join(run), encoding="utf-8")

    print(root / args.output)
    print(root / args.runbook)
    print(f"Shots compiled: {len(shots)} | Warnings: {len(warnings)} | Errors: {len(errors)}")
    return 2 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
