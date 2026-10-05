#!/usr/bin/env python3
"""Validate per-shot Flow endpoint planning before prompt compilation."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from historical_shortfilm_director.runtime.common import plan_allowed


def norm(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").strip().lower())


def split_row(line: str) -> list[str]:
    return [c.strip() for c in line.strip().strip("|").split("|")]


def is_sep(cells: list[str]) -> bool:
    return bool(cells) and all(bool(re.fullmatch(r":?-{3,}:?", c.replace(" ", ""))) for c in cells)


def parse_table(path: Path) -> list[dict[str, str]]:
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    for i in range(len(lines) - 1):
        if "|" not in lines[i] or "|" not in lines[i + 1]:
            continue
        headers = split_row(lines[i])
        sep = split_row(lines[i + 1])
        if not is_sep(sep) or "unit" not in [norm(h) for h in headers]:
            continue
        rows = []
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
    raise ValueError("No endpoint table found")


def get(row: dict[str, str], name: str) -> str:
    return row.get(norm(name), "").strip()


def yes(v: str) -> bool:
    return norm(v) in {"yes", "y", "true", "required", "needed", "1", "是", "需要"}


def approved(v: str) -> bool:
    return norm(v) in {"approved", "approve", "locked", "yes", "pass", "通过", "已批准"}


def duration_policy(root: Path) -> tuple[float, list[float]]:
    p = root / "project.json"
    try:
        meta = json.loads(p.read_text(encoding="utf-8"))
        v = meta.get("ai_generation_constraints", {}).get("max_clip_duration_seconds")
        cand = meta.get("flow", {}).get("allowed_duration_candidates_seconds", [])
        candidates = [float(x) for x in cand if isinstance(x, (int, float))]
        return (float(v) if v else (max(candidates) if candidates else float("inf")), candidates)
    except Exception:
        raise ValueError("Invalid project duration policy")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("project_dir")
    ap.add_argument("--input", default="05f_shot_endpoint_plan.md")
    ap.add_argument("--output", default="05g_shot_endpoint_review.md")
    args = ap.parse_args()

    root = Path(args.project_dir).resolve()
    src = root / args.input
    if not src.exists():
        raise SystemExit(f"Missing: {src}")
    rows = parse_table(src)
    max_dur, duration_candidates = duration_policy(root)

    results: list[tuple[str, str]] = []
    bad = 0
    for row in rows:
        uid = get(row, "Unit")
        if not uid:
            continue
        mode = get(row, "Flow mode").upper()
        issues: list[str] = []
        if mode not in {
            "T2V",
            "START_FRAME",
            "FRAMES",
            "INGREDIENTS",
            "EXTEND",
            "OMNI_EDIT",
            "SKIP_FLOW",
        }:
            issues.append(f"unknown Flow mode {mode or '[blank]'}")
        start = get(row, "Start frame ID")
        end = get(row, "End frame ID")
        if mode in {"START_FRAME", "FRAMES"} and not start:
            issues.append("start frame required")
        if mode == "FRAMES" and not end:
            issues.append("end frame required for FRAMES")
        if yes(get(row, "End frame needed?")) and not end:
            issues.append("end frame marked needed but ID missing")
        if mode in {"START_FRAME", "FRAMES", "EXTEND"} and not get(row, "Motion path"):
            issues.append("Motion path missing")
        if mode == "FRAMES" and not get(row, "KEEP fixed"):
            issues.append("KEEP fixed missing")
        if mode == "FRAMES" and not get(row, "CHANGE"):
            issues.append("CHANGE missing")
        reach = get(row, "Reachability").upper()
        bridge = get(row, "Bridge/reset")
        if mode == "FRAMES" and reach == "R-D":
            issues.append("R-D should normally split/reset instead of direct FRAMES morph")
        if mode == "FRAMES" and reach == "R-C" and not bridge:
            issues.append("R-C Frames pair needs bridge/reset consideration")
        m = re.search(r"(\d+(?:\.\d+)?)", get(row, "Duration"))
        if m:
            dur = float(m.group(1))
            if dur > max_dur:
                issues.append(f"duration exceeds {max_dur:g}s project ceiling")
            if duration_candidates and dur not in duration_candidates:
                issues.append(
                    f"duration {dur:g}s is not in configured Flow candidate set {duration_candidates}; verify current model/UI"
                )
        final_m = re.search(r"(\d+(?:\.\d+)?)", get(row, "Final edit duration"))
        if final_m and m and float(final_m.group(1)) > float(m.group(1)):
            issues.append("Final edit duration exceeds Flow source duration")
        carry_in = get(row, "Carry-in")
        if carry_in and start and carry_in != start:
            issues.append("carry-in and Start frame ID differ; confirm reset vs inheritance")
        carry_out = get(row, "Carry-out")
        if carry_out and not get(row, "Extraction rule"):
            issues.append("Carry-out planned but Extraction rule missing")
        if mode != "SKIP_FLOW" and not plan_allowed(
            get(row, "Approval"), get(row, "Autonomy") or "AUTO"
        ):
            issues.append("endpoint row not approved")
        result = "; ".join(issues) if issues else "PASS"
        if issues:
            bad += 1
        results.append((uid, result))

    report = [
        "# Flow Shot Endpoint Review — v3.0",
        "",
        "This checks **single-shot** Flow start/end conditioning. It does not evaluate the whole-film opening/ending design.",
        "",
        "| Unit | Result |",
        "|---|---|",
    ]
    for uid, result in results:
        report.append(f"| {uid.replace('|', '/')} | {result.replace('|', '/')} |")
    if not results:
        report.append("| - | No populated endpoint rows detected |")
    (root / args.output).write_text("\n".join(report) + "\n", encoding="utf-8")
    print(f"Wrote: {root / args.output}")
    print(f"Units: {len(results)} | With issues: {bad}")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
