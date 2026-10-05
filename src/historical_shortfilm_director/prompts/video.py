#!/usr/bin/env python3
"""Compile Flow cinematic blueprints + per-shot endpoint plans into prompts.

v2.0 separates whole-film opening/ending, per-shot start/end conditioning,
and post-generation carry frames. `05f_shot_endpoint_plan.md` is authoritative
for single-shot endpoints.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from historical_shortfilm_director.runtime.common import plan_allowed

PROMPT_MODES = {
    "T2V_RICH",
    "I2V_BALANCED",
    "FRAMES_PATH",
    "EXTEND_CONTINUITY",
    "OMNI_EDIT_LOCAL",
    "SKIP_FLOW",
}
FLOW_TO_PROMPT = {
    "T2V": "T2V_RICH",
    "START_FRAME": "I2V_BALANCED",
    "FRAMES": "FRAMES_PATH",
    "INGREDIENTS": "I2V_BALANCED",
    "EXTEND": "EXTEND_CONTINUITY",
    "OMNI_EDIT": "OMNI_EDIT_LOCAL",
    "SKIP_FLOW": "SKIP_FLOW",
}


def norm(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").strip().lower())


def split_row(line: str) -> list[str]:
    return [c.strip() for c in line.strip().strip("|").split("|")]


def is_sep(cells: list[str]) -> bool:
    return bool(cells) and all(bool(re.fullmatch(r":?-{3,}:?", c.replace(" ", ""))) for c in cells)


def parse_table(path: Path, required_col: str) -> list[dict[str, str]]:
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    req = norm(required_col)
    for i in range(len(lines) - 1):
        if "|" not in lines[i] or "|" not in lines[i + 1]:
            continue
        headers = split_row(lines[i])
        sep = split_row(lines[i + 1])
        if not is_sep(sep) or req not in [norm(h) for h in headers]:
            continue
        rows: list[dict[str, str]] = []
        j = i + 2
        while j < len(lines) and lines[j].strip().startswith("|"):
            cells = split_row(lines[j])
            if not is_sep(cells):
                cells += [""] * max(0, len(headers) - len(cells))
                row = {
                    norm(h): cells[k].strip() if k < len(cells) else ""
                    for k, h in enumerate(headers)
                }
                if any(row.values()):
                    rows.append(row)
            j += 1
        return rows
    raise ValueError(f"No table with column '{required_col}' in {path.name}")


def get(row: dict[str, str], *names: str) -> str:
    for name in names:
        v = row.get(norm(name), "").strip()
        if v:
            return v
    return ""


def sent(x: str) -> str:
    x = (x or "").strip()
    if not x:
        return ""
    if x[-1] not in ".!?\"'”’":
        x += "."
    if x[0].islower() and x[0].isascii():
        x = x[0].upper() + x[1:]
    return x


def yes(v: str) -> bool:
    return norm(v) in {"yes", "y", "true", "required", "needed", "1", "是", "需要"}


def approved(v: str) -> bool:
    return norm(v) in {"approved", "approve", "locked", "yes", "pass", "通过", "已批准"}


def compact_anchor(anchor: str) -> str:
    bits = [b.strip() for b in re.split(r"[;,；]", anchor or "") if b.strip()]
    return "; ".join(bits[:4])


def load_max_duration(root: Path) -> float:
    path = root / "project.json"
    if not path.exists():
        return float("inf")
    try:
        meta = json.loads(path.read_text(encoding="utf-8"))
        value = meta.get("ai_generation_constraints", {}).get("max_clip_duration_seconds")
        return float(value) if value else float("inf")
    except Exception:
        raise ValueError("Invalid project generation constraints")


def duration_number(v: str) -> float | None:
    m = re.search(r"(\d+(?:\.\d+)?)", v or "")
    return float(m.group(1)) if m else None


def build_prompt(bp: dict[str, str], ep: dict[str, str], mode: str) -> str:
    premise = get(bp, "Visual premise")
    anchors = compact_anchor(get(bp, "Anchor facts"))
    action = get(bp, "ONE primary action", "Primary action")
    env = get(bp, "Environment response")
    camera = get(bp, "Camera grammar", "Camera")
    focus = get(bp, "Focus / depth", "Focus")
    light = get(bp, "Light / atmosphere", "Atmosphere")
    timing = get(bp, "Temporal choreography", "Timing")
    audio = get(bp, "Audio intent")
    locks = get(bp, "Continuity locks")

    start_id = get(ep, "Start frame ID")
    end_target = get(ep, "End target state")
    keep = get(ep, "KEEP fixed", "KEEP")
    change = get(ep, "CHANGE")
    path = get(ep, "Motion path")

    parts: list[str] = []
    if premise:
        parts.append(sent(premise))

    if mode == "T2V_RICH":
        for item in [anchors, action, env, camera, focus, light, timing]:
            if item:
                parts.append(sent(item))
        if end_target:
            parts.append(sent(f"By the final seconds, {end_target}"))

    elif mode == "I2V_BALANCED":
        if start_id:
            parts.append("Use the supplied start frame as the exact visual starting state.")
        if keep:
            parts.append(sent(f"Keep stable throughout: {keep}"))
        elif anchors:
            parts.append(sent(f"Preserve these visual anchors: {anchors}"))
        if change:
            parts.append(sent(f"The intended visual change is: {change}"))
        if path:
            parts.append(sent(path))
        elif action:
            parts.append(sent(action))
        for item in [env, camera, focus, light, timing]:
            if item:
                parts.append(sent(item))
        if end_target:
            parts.append(sent(f"By the end, settle into this target state: {end_target}"))

    elif mode == "FRAMES_PATH":
        parts.append(
            "Use the supplied first and final frames as fixed visual endpoints of one continuous shot."
        )
        if keep:
            parts.append(sent(f"Keep unchanged between the endpoints: {keep}"))
        elif anchors:
            parts.append(sent(f"Keep invariant: {anchors}"))
        if change:
            parts.append(sent(f"Only this visual state should change: {change}"))
        if path:
            parts.append(sent(path))
        elif action:
            parts.append(sent(action))
        for item in [env, camera, timing]:
            if item:
                parts.append(sent(item))
        if end_target:
            parts.append(
                sent(
                    f"Progressively converge on the supplied final frame. Intended final state: {end_target}. Avoid any abrupt last-frame snap"
                )
            )
        else:
            parts.append(
                "Approach the supplied final frame progressively and settle into it naturally without an abrupt last-frame snap."
            )

    elif mode == "EXTEND_CONTINUITY":
        parts.append(
            "Continue the approved existing clip seamlessly from its current final visual state."
        )
        if keep:
            parts.append(sent(f"Preserve: {keep}"))
        if change:
            parts.append(sent(f"Continue by changing only: {change}"))
        if path:
            parts.append(sent(path))
        elif action:
            parts.append(sent(action))
        for item in [env, camera, timing]:
            if item:
                parts.append(sent(item))
        if end_target:
            parts.append(sent(f"By the end, settle into this target state: {end_target}"))

    elif mode == "OMNI_EDIT_LOCAL":
        parts.append(
            "Preserve the approved clip and change only the localized element specified below."
        )
        if keep:
            parts.append(sent(f"Keep unchanged: {keep}"))
        if change:
            parts.append(sent(f"Change only: {change}"))
        elif action:
            parts.append(sent(action))
        if end_target:
            parts.append(sent(f"The edited clip should finish in this state: {end_target}"))

    if locks and mode != "OMNI_EDIT_LOCAL":
        parts.append(sent(f"Maintain continuity in {locks}"))
    if audio:
        parts.append(sent(f"Audio: {audio}"))
    return " ".join(p for p in parts if p).strip()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("project_dir")
    ap.add_argument("--blueprints", default="04c_flow_prompt_blueprints.md")
    ap.add_argument("--endpoints", default="05f_shot_endpoint_plan.md")
    ap.add_argument("--output", default="06f_flow_prompt_pack.md")
    ap.add_argument("--scenebuilder", default="06g_flow_scenebuilder_plan.md")
    args = ap.parse_args()

    root = Path(args.project_dir).resolve()
    bp_path = root / args.blueprints
    ep_path = root / args.endpoints
    if not bp_path.exists():
        raise SystemExit(f"Missing: {bp_path}")
    if not ep_path.exists():
        raise SystemExit(f"Missing: {ep_path}")

    blueprints = parse_table(bp_path, "Unit")
    endpoints = parse_table(ep_path, "Unit")
    ep_by_id = {get(r, "Unit"): r for r in endpoints if get(r, "Unit")}
    max_duration = load_max_duration(root)

    warnings: list[str] = []
    errors: list[str] = []
    blocks: list[str] = []
    assembly_rows: list[str] = []

    density = {
        "T2V_RICH": (70, 180),
        "I2V_BALANCED": (50, 160),
        "FRAMES_PATH": (45, 150),
        "EXTEND_CONTINUITY": (25, 100),
        "OMNI_EDIT_LOCAL": (20, 100),
    }

    for bp in blueprints:
        uid = get(bp, "Unit")
        if not uid:
            continue
        ep = ep_by_id.get(uid)
        if ep is None:
            errors.append(f"{uid}: no matching row in 05f_shot_endpoint_plan.md")
            continue

        flow_mode = (get(ep, "Flow mode") or "START_FRAME").upper()
        if flow_mode not in FLOW_TO_PROMPT:
            errors.append(f"{uid}: unknown Flow mode {flow_mode}")
            continue
        canonical = FLOW_TO_PROMPT[flow_mode]
        requested = (get(bp, "Prompt mode") or "").upper()
        mode = requested or canonical
        if mode not in PROMPT_MODES:
            errors.append(f"{uid}: unknown prompt mode {mode}")
            continue
        if requested and requested != canonical and flow_mode != "INGREDIENTS":
            warnings.append(
                f"{uid}: prompt mode {requested} differs from Flow-mode default {canonical}"
            )

        if flow_mode == "SKIP_FLOW" or mode == "SKIP_FLOW":
            blocks.append(f"### {uid} — SKIP_FLOW\n\nDo not generate this unit in Flow.\n")
            assembly_rows.append(
                f"| {uid} | {get(ep, 'Parent shot') or '-'} | {get(ep, 'Duration') or '-'} | SKIP_FLOW | - | - | - | deterministic / post route |"
            )
            continue

        start_id = get(ep, "Start frame ID")
        end_id = get(ep, "End frame ID")
        end_needed = yes(get(ep, "End frame needed?"))
        if flow_mode in {"START_FRAME", "FRAMES"} and not start_id:
            errors.append(f"{uid}: {flow_mode} requires Start frame ID")
        if flow_mode == "FRAMES" and not end_id:
            errors.append(f"{uid}: FRAMES requires End frame ID")
        if end_needed and not end_id:
            errors.append(f"{uid}: End frame needed? is yes but End frame ID is empty")

        dur = duration_number(get(ep, "Duration"))
        if dur is not None and dur > max_duration:
            errors.append(
                f"{uid}: duration {dur:g}s exceeds configured clip ceiling {max_duration:g}s"
            )

        reach = get(ep, "Reachability").upper()
        bridge = get(ep, "Bridge/reset")
        if flow_mode == "FRAMES" and reach in {"R-C", "R-D"} and not bridge:
            warnings.append(f"{uid}: {reach} FRAMES pair has no bridge/reset strategy")
        if flow_mode == "FRAMES" and reach == "R-D":
            warnings.append(
                f"{uid}: R-D transition should usually be split/reset, not direct Frames morph"
            )

        if not plan_allowed(get(bp, "Approval")):
            warnings.append(f"{uid}: Flow prompt blueprint is not approved")
        if not plan_allowed(get(ep, "Approval"), get(ep, "Autonomy") or "AUTO"):
            warnings.append(f"{uid}: shot endpoint plan is not approved")
        if not get(bp, "Visual premise"):
            warnings.append(f"{uid}: visual premise missing")
        if not get(ep, "Motion path") and mode in {
            "I2V_BALANCED",
            "FRAMES_PATH",
            "EXTEND_CONTINUITY",
        }:
            warnings.append(f"{uid}: endpoint Motion path missing")

        prompt = build_prompt(bp, ep, mode)
        wc = len(re.findall(r"\b[\w'-]+\b", prompt))
        lo, hi = density[mode]
        if wc < lo:
            warnings.append(f"{uid}: prompt is only {wc} words for {mode}; may be under-specified")
        if wc > hi:
            warnings.append(f"{uid}: prompt is {wc} words for {mode}; may be over-specified")

        block_lines = [
            f"### {uid} — {flow_mode} / {mode}",
            "",
            "**Single-shot endpoint contract**",
            f"- Start frame: `{start_id or '[none]'}` — {get(ep, 'Start role') or '[not specified]'}",
            f"- End frame: `{end_id or '[not required]'}`",
            f"- End target: {get(ep, 'End target state') or '[textual end state not specified]'}",
            f"- KEEP: {get(ep, 'KEEP fixed') or '[not specified]'}",
            f"- CHANGE: {get(ep, 'CHANGE') or '[not specified]'}",
            f"- PATH: {get(ep, 'Motion path') or '[not specified]'}",
            f"- Reachability: `{reach or '[unset]'}`",
            f"- Bridge/reset: {bridge or '[none]'}",
            f"- Carry-in: {get(ep, 'Carry-in') or '[none]'}",
            f"- Carry-out: {get(ep, 'Carry-out') or '[none]'}",
            f"- Extraction rule: {get(ep, 'Extraction rule') or '[none]'}",
            "",
            "**Paste-ready Flow prompt**",
            "",
            "```text",
            prompt,
            "```",
            "",
            "**Director check before generation**",
            "- Does this prompt describe the path, rather than redescribe the endpoint images?",
            "- Is the A→B change locally reachable in this duration?",
            "- Are KEEP and CHANGE non-contradictory?",
            "- If carry-out is planned, is the last 10–20% likely to contain a clean handoff frame?",
        ]
        blocks.append("\n".join(block_lines))
        assembly_rows.append(
            f"| {uid} | {get(ep, 'Parent shot') or '-'} | {get(ep, 'Duration') or '-'} | {flow_mode} | {start_id or '-'} | {end_id or '-'} | {get(ep, 'Carry-out') or '-'} | {get(bp, 'Story beat') or get(bp, 'Visual premise') or '-'} |"
        )

    bp_ids = {get(r, "Unit") for r in blueprints if get(r, "Unit")}
    for eid, ep in ep_by_id.items():
        if eid not in bp_ids and (get(ep, "Flow mode") or "").upper() != "SKIP_FLOW":
            warnings.append(f"{eid}: endpoint row has no matching Flow prompt blueprint")

    out = (
        "# Google Flow Shot Prompt Pack — v2.0\n\n"
        "Compiled by joining `04c_flow_prompt_blueprints.md` with the authoritative per-shot endpoint plan `05f_shot_endpoint_plan.md`. "
        "Whole-film opening/ending design is intentionally separate.\n\n"
        + "\n\n".join(blocks)
        + "\n"
    )
    (root / args.output).write_text(out, encoding="utf-8")

    scenebuilder = (
        "# Google Flow / Scenebuilder Assembly Plan — v2.0\n\n"
        "| Unit | Parent shot | Duration | Flow mode | Start frame | End frame | Carry-out | Editorial role |\n"
        "|---|---|---:|---|---|---|---|---|\n" + "\n".join(assembly_rows) + "\n"
    )
    (root / args.scenebuilder).write_text(scenebuilder, encoding="utf-8")

    for w in warnings:
        print("WARN:", w)
    for e in errors:
        print("ERROR:", e)
    print("Wrote:", root / args.output)
    print("Wrote:", root / args.scenebuilder)
    return 2 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
