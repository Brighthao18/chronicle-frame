#!/usr/bin/env python3
"""Heuristic review of the v1.8 Flow-native screenplay tables.

This does not replace a human story editor. It catches structural omissions that
commonly cause weak Flow prompts: missing causal handoff, unchanged state,
overloaded Flow units, and narration-density risks.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path


def norm(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").strip().lower())


def split_row(line: str) -> list[str]:
    return [c.strip() for c in line.strip().strip("|").split("|")]


def is_sep(cells: list[str]) -> bool:
    return bool(cells) and all(bool(re.fullmatch(r":?-{3,}:?", c.replace(" ", ""))) for c in cells)


def parse_tables(path: Path):
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    out = []
    i = 0
    while i < len(lines) - 1:
        if "|" in lines[i] and "|" in lines[i + 1]:
            h = split_row(lines[i])
            sep = split_row(lines[i + 1])
            if is_sep(sep):
                rows = []
                j = i + 2
                while j < len(lines) and lines[j].strip().startswith("|"):
                    c = split_row(lines[j])
                    c += [""] * (len(h) - len(c))
                    if not is_sep(c):
                        rows.append({norm(x): c[k].strip() for k, x in enumerate(h)})
                    j += 1
                out.append((h, rows))
                i = j
                continue
        i += 1
    return out


def find_table(path: Path, col: str):
    n = norm(col)
    for h, r in parse_tables(path):
        if n in [norm(x) for x in h]:
            return h, r
    return [], []


def get(r, *names):
    for n in names:
        v = r.get(norm(n), "").strip()
        if v:
            return v
    return ""


def sec(s):
    m = re.search(r"(\d+(?:\.\d+)?)", s or "")
    return float(m.group(1)) if m else None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("project_dir")
    ap.add_argument("--input", default="04b_flow_scene_script.md")
    ap.add_argument("--output", default="04c_flow_script_review.md")
    args = ap.parse_args()
    root = Path(args.project_dir).resolve()
    src = root / args.input
    if not src.exists():
        raise SystemExit(f"Missing: {src}")
    _, scenes = find_table(src, "Scene")
    _, units = find_table(src, "Unit")
    issues = []

    for r in scenes:
        sid = get(r, "Scene") or "[unnamed]"
        before = get(r, "Before-state")
        after = get(r, "After-state")
        hand = get(r, "Causal handoff")
        purpose = get(r, "Story purpose / turn")
        visual = get(r, "Visible proof / action")
        vo = get(r, "VO / dialogue")
        if not purpose:
            issues.append((sid, "scene", "missing story purpose/turn"))
        if not before or not after:
            issues.append((sid, "scene", "missing before-state or after-state"))
        elif norm(before) == norm(after):
            issues.append(
                (
                    sid,
                    "scene",
                    "before-state and after-state are identical; no narrative state change",
                )
            )
        if not hand:
            issues.append((sid, "scene", "missing causal handoff to the next scene"))
        if not visual:
            issues.append((sid, "scene", "missing visible proof/action"))
        if len(vo) > 120 and "。" not in vo and "." not in vo:
            issues.append(
                (sid, "scene", "VO/dialogue is a long unbroken sentence; read-aloud risk")
            )
        slogans = ["薪火相传", "弦歌不辍", "砥砺前行", "时代洪流", "历史车轮"]
        hit = [x for x in slogans if x in vo]
        if len(hit) >= 2:
            issues.append((sid, "scene", "slogan-chain risk: " + " / ".join(hit)))

    for r in units:
        uid = get(r, "Unit") or "[unnamed]"
        mode = get(r, "Flow mode").upper()
        dur = sec(get(r, "Duration"))
        action = get(r, "ONE primary action")
        cam = get(r, "Camera")
        timing = get(r, "Timing")
        if mode != "SKIP_FLOW" and not action:
            issues.append((uid, "flow unit", "missing ONE primary action"))
        if mode != "SKIP_FLOW" and not cam:
            issues.append((uid, "flow unit", "missing camera instruction"))
        if mode != "SKIP_FLOW" and not timing:
            issues.append((uid, "flow unit", "missing timing/pace"))
        if dur is not None and dur > 10:
            issues.append(
                (uid, "flow unit", f"duration {dur:g}s exceeds current 10s planning ceiling")
            )
        seq = sum(
            norm(action).count(x)
            for x in [" then ", " after ", " finally ", "随后", "然后", "最后"]
        )
        if seq > 2:
            issues.append(
                (uid, "flow unit", f"action sequence contains {seq} transitions; likely overloaded")
            )
        camera_terms = [
            "dolly",
            "pan",
            "tilt",
            "orbit",
            "arc",
            "zoom",
            "crane",
            "jib",
            "tracking",
            "handheld",
        ]
        cams = [x for x in camera_terms if x in norm(cam)]
        if len(cams) > 2:
            issues.append((uid, "flow unit", "too many camera axes/terms: " + ", ".join(cams)))

    report = "# Flow Script Structural Review\n\nHeuristic only. Run separate WRITER / EDITOR / HISTORIAN / DIRECTOR / NARRATOR passes for substantive review.\n\n| ID | Layer | Issue |\n|---|---|---|\n"
    if issues:
        for a, b, c in issues:
            report += f"| {a.replace('|', '/')} | {b} | {c.replace('|', '/')} |\n"
    else:
        report += "| - | - | PASS: no obvious structural omissions detected |\n"
    (root / args.output).write_text(report, encoding="utf-8")
    print(f"Wrote: {root / args.output}")
    print(f"Issues: {len(issues)}")
    return 1 if issues else 0


if __name__ == "__main__":
    raise SystemExit(main())
