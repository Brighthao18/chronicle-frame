#!/usr/bin/env python3
"""Apply exact source-pixel overlays from 03e_evidence_overlay_plan.csv.

This is the deterministic half of HYBRID_IMAGE25_CODE. It never invents pixels.
"""

from __future__ import annotations
import argparse
import csv
import re
from pathlib import Path

APPROVED = {"approved", "locked", "yes", "pass", "通过", "已批准", "批准"}


def box(v: str, full_size=None):
    v = (v or "").strip()
    if not v or v.upper() == "FULL":
        if full_size is None:
            return None
        return (0, 0, full_size[0], full_size[1])
    nums = [int(float(x.strip())) for x in re.split(r"[, x]+", v) if x.strip()]
    if len(nums) != 4:
        raise ValueError(f"Invalid source_box: {v}")
    return tuple(nums)


def xy(v: str):
    nums = [int(float(x.strip())) for x in re.split(r"[, x]+", (v or "0,0")) if x.strip()]
    if len(nums) != 2:
        raise ValueError(f"Invalid target_xy: {v}")
    return tuple(nums)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("project_dir")
    ap.add_argument("--plan", default="03e_evidence_overlay_plan.csv")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    root = Path(a.project_dir).resolve()
    pp = root / a.plan
    if not pp.exists():
        raise SystemExit(f"Missing: {pp}")
    with pp.open("r", encoding="utf-8-sig", newline="") as f:
        list(csv.DictReader(f))
    if a.dry_run:
        print(f"Plan ready for inspection: {pp}")
        return 0
    from historical_shortfilm_director.evidence.overlays import apply_plan

    for record in apply_plan(root, a.plan):
        print(record)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
