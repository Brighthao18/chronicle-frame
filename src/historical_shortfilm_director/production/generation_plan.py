#!/usr/bin/env python3
"""Compile reachability + chaining plans into production-ready generation blocks.

v1.7 is reachability-first: it can decide that a shot should be generated,
split with a bridge/occlusion, or handled deterministically in edit/compositing.
No third-party dependencies.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from historical_shortfilm_director.profiles import load_profile, project_profile

DEFAULT_MAX_REFS = 3
DEFAULT_MAX_SECONDS = 10.0
DETERMINISTIC_ROUTES = {
    "MATCH_CUT_EDIT",
    "COMPOSITE_2_5D",
    "MOTION_GRAPHIC",
    "ARCHIVAL_HOLD",
    "LIVE_OR_EXISTING_VIDEO",
}
SPLIT_ROUTES = {"BRIDGE_2STEP", "OCCLUSION_2STEP"}


def norm(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").strip().lower())


def split_row(line: str) -> list[str]:
    s = line.strip().strip("|")
    return [c.strip() for c in s.split("|")]


def is_sep(cells: list[str]) -> bool:
    return bool(cells) and all(bool(re.fullmatch(r":?-{3,}:?", c.replace(" ", ""))) for c in cells)


def parse_first_table(path: Path, required: str = "shot") -> tuple[list[str], list[dict[str, str]]]:
    text = path.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()
    for i in range(len(lines) - 1):
        if "|" not in lines[i] or "|" not in lines[i + 1]:
            continue
        headers = split_row(lines[i])
        sep = split_row(lines[i + 1])
        if not is_sep(sep) or required not in [norm(h) for h in headers]:
            continue
        rows: list[dict[str, str]] = []
        for ln in lines[i + 2 :]:
            if not ln.strip().startswith("|"):
                if rows:
                    break
                continue
            cells = split_row(ln)
            if is_sep(cells):
                continue
            cells += [""] * (len(headers) - len(cells))
            row = {norm(h): cells[j].strip() for j, h in enumerate(headers)}
            if any(v for v in row.values()):
                rows.append(row)
        return headers, rows
    raise ValueError(f"No table with '{required}' column found in {path.name}")


def get(row: dict[str, str], *names: str) -> str:
    for name in names:
        v = row.get(norm(name), "").strip()
        if v:
            return v
    return ""


def yesish(s: str) -> bool:
    return norm(s) in {"yes", "y", "true", "1", "是", "允许", "allow", "allowed"}


def noneish(s: str) -> bool:
    return norm(s) in {"", "-", "none", "n/a", "na", "无", "不需要", "none."}


def seconds(s: str) -> float | None:
    m = re.search(r"(\d+(?:\.\d+)?)", s or "")
    return float(m.group(1)) if m else None


def load_meta(root: Path) -> dict:
    p = root / "project.json"
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}


def constraints(meta: dict) -> tuple[int | None, float]:
    c = meta.get("ai_generation_constraints", {}) if isinstance(meta, dict) else {}
    raw_refs = c.get("max_reference_images_per_shot", DEFAULT_MAX_REFS)
    if raw_refs is None:
        max_refs = None
    else:
        try:
            max_refs = int(raw_refs)
        except Exception:
            max_refs = DEFAULT_MAX_REFS
    try:
        max_secs = float(c.get("max_clip_duration_seconds", DEFAULT_MAX_SECONDS))
    except Exception:
        max_secs = DEFAULT_MAX_SECONDS
    return max_refs, max_secs


def infer_route(reach: str, ai_value: str, profile: str) -> str:
    if norm(ai_value) == "low":
        return "MATCH_CUT_EDIT"
    r = reach.upper().replace(" ", "")
    if "R-A" in r or r == "RA":
        return "I2V_START"
    if "R-B" in r or r == "RB":
        return "FLF"
    if "R-C" in r or r == "RC":
        return "BRIDGE_2STEP"
    if "R-D" in r or r == "RD":
        return (profile if hasattr(profile, "routing") else load_profile(profile)).routing.get(
            "R-D", "MATCH_CUT_EDIT"
        )
    return "I2V_START"


def join_sentences(items: list[str]) -> str:
    out = []
    for s in items:
        s = (s or "").strip()
        if noneish(s):
            continue
        # Remove low-information timing fillers when they add nothing.
        if norm(s) in {"continuous", "uniform", "smooth", "steady"}:
            continue
        if s and s[0].islower():
            s = s[0].upper() + s[1:]
        if not s.endswith((".", "!", "?")):
            s += "."
        out.append(s)
    return " ".join(out)


def build_motion_prompt(
    chain: dict[str, str], route: str, profile: str, phase_path: str = "", end_override: str = ""
) -> str:
    camera = get(chain, "camera motion", "镜头运动", "摄影机运动")
    subject = get(chain, "subject motion", "主体运动")
    env = get(
        chain, "environment / layer motion", "environmental motion", "环境/图层运动", "环境运动"
    )
    timing = get(chain, "timing", "时间节奏", "运动节奏")
    end_state = end_override or get(chain, "end state", "结束状态", "end anchor target")

    items = []
    if route == "FLF":
        items.append(
            "Use one continuous shot and follow a natural causal path toward the supplied end state, maintaining even motion and arriving smoothly in the final composition"
        )
    if phase_path:
        items.append(phase_path)
    else:
        if camera:
            items.append(camera)
        if subject and not noneish(subject):
            items.append(subject)
        if env and not noneish(env):
            items.append(env)
    if timing:
        items.append(timing)
    if end_state:
        prior = (" ".join([phase_path or "", timing or ""])).lower()
        if "settle" in prior or "stop" in prior or "hold" in prior:
            items.append(f"End on a stable final composition: {end_state}")
        else:
            items.append(
                f"The motion decelerates and settles into a stable final composition: {end_state}"
            )
    items.append("Continuous single shot")
    return join_sentences(items)


def ref_list(chain: dict[str, str], max_refs: int | None) -> list[str]:
    refs = []
    # Flow may expose model/mode-dependent reference capacity. The legacy chain table
    # records the first three highest-priority references, not necessarily a hard Flow limit.
    count = max_refs if isinstance(max_refs, int) and max_refs > 0 else 3
    for i in range(1, count + 1):
        refs.append(get(chain, f"ref{i}", f"ref {i}", f"reference {i}", f"参考{i}", f"参考位{i}"))
    return refs


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("project_dir")
    ap.add_argument("--chain", default="05c_shot_chaining_plan.md")
    ap.add_argument("--reach", default="05d_endpoint_reachability.md")
    ap.add_argument("--bridge", default="05e_bridge_keyframe_plan.md")
    ap.add_argument("--output", default="06b_generation_prompt_pack.md")
    ap.add_argument("--runbook", default="06c_generation_runbook.md")
    args = ap.parse_args()

    root = Path(args.project_dir).resolve()
    chain_path = root / args.chain
    reach_path = root / args.reach
    bridge_path = root / args.bridge
    if not chain_path.exists():
        raise SystemExit(f"Missing: {chain_path}")
    if not reach_path.exists():
        raise SystemExit(f"Missing: {reach_path}")

    meta = load_meta(root)
    profile = project_profile(root, meta)
    max_refs, max_secs = constraints(meta)
    _, chain_rows = parse_first_table(chain_path)
    _, reach_rows = parse_first_table(reach_path)
    bridge_rows = []
    if bridge_path.exists():
        try:
            _, bridge_rows = parse_first_table(bridge_path)
        except Exception:
            bridge_rows = []

    chains = {
        get(r, "shot", "shot id", "镜头"): r
        for r in chain_rows
        if get(r, "shot", "shot id", "镜头")
    }
    reaches = {
        get(r, "shot", "shot id", "镜头"): r
        for r in reach_rows
        if get(r, "shot", "shot id", "镜头")
    }
    bridges = {
        get(r, "shot", "shot id", "镜头"): r
        for r in bridge_rows
        if get(r, "shot", "shot id", "镜头")
    }

    warnings = []
    errors = []
    blocks = []
    steps = []
    for sid, chain in chains.items():
        reach = reaches.get(sid, {})
        reachability = get(reach, "reachability", "可达性")
        route = (
            (
                get(reach, "route", "production route", "路线")
                or infer_route(reachability, get(reach, "ai value", "ai价值"), profile)
            )
            .upper()
            .strip()
        )
        ai_value = get(reach, "ai value", "ai价值") or "MEDIUM"
        duration_s = seconds(
            get(reach, "target duration", "duration", "目标时长") or get(chain, "duration", "时长")
        )
        if (
            duration_s is not None
            and duration_s > max_secs
            and route not in SPLIT_ROUTES
            and route not in DETERMINISTIC_ROUTES
        ):
            errors.append(
                f"{sid}: target duration {duration_s:g}s exceeds max {max_secs:g}s for route {route}"
            )
        start = get(reach, "start anchor", "首帧") or get(chain, "start anchor", "start", "首帧")
        end = get(reach, "end anchor", "尾帧") or get(
            chain, "end anchor target", "end target", "尾帧目标"
        )
        refs = ref_list(chain, max_refs)
        locks = get(chain, "continuity locks", "连续性锁定")
        forbidden = get(chain, "negative constraints", "forbidden", "禁止项", "负面约束")
        reset = get(chain, "reset conditions", "重置条件")
        extraction = get(chain, "extraction rule", "抽帧规则")
        inherit = get(chain, "inherit prev carry?", "继承上一镜尾帧?")
        export = get(chain, "export carry to next?", "输出尾帧给下一镜?")

        header = f"### {sid} — {route}\n\n- Reachability: `{reachability or '[UNASSESSED]'}`\n- AI value: `{ai_value}`\n- Start anchor: `{start or '[UNSET]'}`\n- End anchor: `{end or '[UNSET]'}`\n- Duration target: `{duration_s if duration_s is not None else '[UNSET]'} s`\n- Inherit previous carry: `{inherit or 'no'}`\n- Export carry to next: `{export or 'no'}`\n"
        header += (
            "- Reference slots:\n"
            + "\n".join(f"  - REF{i}: `{r or '[UNASSIGNED]'}`" for i, r in enumerate(refs, 1))
            + "\n"
        )

        if route in DETERMINISTIC_ROUTES:
            recipe = {
                "MATCH_CUT_EDIT": "Use a deterministic match cut / editorial transition; preserve verified pixels and move the discontinuity into the cut.",
                "COMPOSITE_2_5D": "Build an approved layered composite first; animate camera/layers deterministically in edit or a 2.5D tool.",
                "MOTION_GRAPHIC": "Animate map/line/date/document geometry deterministically; do not ask a video model to redraw precise text or cartography.",
                "ARCHIVAL_HOLD": "Keep the archival evidence still; use editorial hold, crop, sound, or restrained deterministic movement only.",
                "LIVE_OR_EXISTING_VIDEO": "Use live/existing footage as the master shot; AI may support cleanup or non-critical inserts only.",
            }[route]
            blocks.append(
                header
                + f"\n**Generation decision:** NO primary AI-video generation.\n\n**Deterministic recipe:** {recipe}\n"
            )
            steps.append(
                f"- {sid}: `{route}` — prepare/approve deterministic shot; no video-model generation required."
            )
            continue

        if route in SPLIT_ROUTES:
            b = bridges.get(sid, {})
            bridge_id = get(b, "bridge id", "bridge", "桥接id", "桥接帧") or get(
                reach, "bridge frame", "桥接帧"
            )
            bridge_state = get(b, "bridge visual state", "visual state", "桥接视觉状态")
            p_a = get(b, "phase a motion path", "phase a", "a path", "a段运动路径")
            p_b = get(b, "phase b motion path", "phase b", "b path", "b段运动路径")
            da = seconds(get(b, "phase a duration", "a duration", "a段时长"))
            db = seconds(get(b, "phase b duration", "b duration", "b段时长"))
            if da is None or db is None:
                total = duration_s or min(8.0, max_secs)
                da = round(total / 2, 2)
                db = round(total - da, 2)
            if da > max_secs or db > max_secs:
                errors.append(f"{sid}: split phase exceeds {max_secs:g}s ({da:g}s/{db:g}s)")
            if not bridge_id or not bridge_state:
                warnings.append(
                    f"{sid}: {route} needs a bridge/occlusion state in 05e_bridge_keyframe_plan.md"
                )
            prompt_a = build_motion_prompt(
                chain, "I2V_START", profile, p_a, bridge_state or bridge_id
            )
            prompt_b = build_motion_prompt(
                chain, "I2V_START", profile, p_b, get(chain, "end state", "结束状态") or end
            )
            block = (
                header
                + f"\n**Bridge / occlusion:** `{bridge_id or '[UNSET]'}` — {bridge_state or '[DEFINE A REACHABLE MIDPOINT/OCCLUSION]'}\n\n"
            )
            block += f"#### {sid}-A ({da:g}s)\n\n**Prompt (motion-first):**\n\n```text\n{prompt_a}\n```\n\n"
            block += f"**Refs:** start/carry + authoritative geometry + `{bridge_id or 'bridge frame'}`.\n\n"
            block += f"#### {sid}-B ({db:g}s)\n\n**Prompt (motion-first):**\n\n```text\n{prompt_b}\n```\n\n"
            block += f"**Refs:** `{bridge_id or 'bridge frame'}` as new start + authoritative geometry + end/control reference.\n\n"
            block += f"**Continuity locks (structured, not prose filler):** {locks or '[DEFINE]'}\n\n**Forbidden / reset states:** {forbidden or reset or '[DEFINE]'}\n"
            blocks.append(block)
            steps.append(
                f"- {sid}: `{route}` — approve bridge `{bridge_id or '[UNSET]'}` → generate A → boundary review → reset/continue from bridge → generate B → boundary review."
            )
            continue

        prompt = build_motion_prompt(chain, route, profile)
        word_count = len(re.findall(r"\b[\w'-]+\b", prompt))
        budget = 120 if route == "FLF" else 90
        if word_count > budget:
            warnings.append(
                f"{sid}: motion prompt has {word_count} words; recommended <= {budget} for {route}"
            )
        if route == "FLF":
            warnings.append(
                f"{sid}: FLF route assumes the active model truly supports explicit first+last frame; otherwise use bridge or I2V start+end-target reference"
            )
        block = (
            header
            + f"\n**Prompt (motion-first, {word_count} words):**\n\n```text\n{prompt}\n```\n\n"
        )
        block += f"**Continuity locks (prefer refs/structured control):** {locks or '[DEFINE]'}\n\n"
        block += f"**Forbidden / reset states (adapter decides whether these belong in negativePrompt):** {forbidden or reset or '[DEFINE]'}\n\n"
        block += f"**Carry extraction:** {extraction or 'Inspect final 10–20%; export the cleanest stable pre-snap frame, not automatically the literal final frame.'}\n"
        blocks.append(block)
        steps.append(
            f"- {sid}: `{route}` — generate 1–3 candidates → inspect first/last 10% → approve or redesign constraints → export carry only from a stable cuttable frame."
        )

    out = "# v1.7 Reachability-First Generation Prompt Pack\n\n"
    refs_label = str(max_refs) if max_refs is not None else "model/mode-dependent"
    out += f"Project profile: `{profile.name}` | Max references: `{refs_label}` | Max clip: `{max_secs:g}s`\n\n"
    out += (
        "Principle: frames define appearance; prompts define motion/path. Do not solve unreachable endpoints by adding adjectives.\n\n"
        + "\n\n".join(blocks)
        + "\n"
    )
    (root / args.output).write_text(out, encoding="utf-8")

    run = "# v1.7 Generation Runbook\n\n"
    run += "Before any hero-shot generation, confirm `05d_endpoint_reachability.md` and any required bridge/occlusion state.\n\n"
    run += "\n".join(steps) + "\n\n"
    run += "## Failure policy\n\nIf 3 hero-shot candidates fail on the same dimension, change endpoint, route, bridge, reference allocation, or prompt. Do not keep rerolling identical constraints.\n"
    (root / args.runbook).write_text(run, encoding="utf-8")

    for w in warnings:
        print(f"WARN: {w}")
    for e in errors:
        print(f"ERROR: {e}")
    print(f"Wrote: {root / args.output}")
    print(f"Wrote: {root / args.runbook}")
    return 2 if errors else (1 if warnings else 0)


if __name__ == "__main__":
    raise SystemExit(main())
