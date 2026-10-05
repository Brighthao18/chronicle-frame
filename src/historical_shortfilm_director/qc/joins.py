#!/usr/bin/env python3
"""Validate v2 shot join contracts before final Flow generation."""

from __future__ import annotations

import argparse
import re
from pathlib import Path
from historical_shortfilm_director.runtime.common import plan_allowed

ALLOWED = {"EXACT_SEAM", "FLOW_EXTEND", "MATCH_CUT", "OCCLUSION_RESET", "GRAPHIC_RESET", "HARD_CUT"}


def norm(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").strip()).lower()


def split_row(line: str) -> list[str]:
    return [c.strip() for c in line.strip().strip("|").split("|")]


def is_sep(c: list[str]) -> bool:
    return bool(c) and all(bool(re.fullmatch(r":?-{3,}:?", x.replace(" ", ""))) for x in c)


def parse(path: Path) -> list[dict[str, str]]:
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    for i in range(len(lines) - 1):
        headers = split_row(lines[i]) if lines[i].strip().startswith("|") else []
        if (
            "join" not in [norm(h) for h in headers]
            or not lines[i + 1].strip().startswith("|")
            or not is_sep(split_row(lines[i + 1]))
        ):
            continue
        out = []
        for ln in lines[i + 2 :]:
            if not ln.strip().startswith("|"):
                break
            c = split_row(ln)
            if is_sep(c):
                continue
            c += [""] * max(0, len(headers) - len(c))
            row = {norm(h): c[j] if j < len(c) else "" for j, h in enumerate(headers)}
            if any(row.values()):
                out.append(row)
        return out
    raise ValueError("No join-contract table found")


def get(r: dict[str, str], name: str) -> str:
    return r.get(norm(name), "").strip()


def approved(s: str) -> bool:
    return norm(s) in {"approved", "locked", "yes", "pass", "通过", "已批准", "批准"}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("project_dir")
    ap.add_argument("--input", default="05h_join_contracts.md")
    ap.add_argument("--output", default="05i_join_contract_review.md")
    a = ap.parse_args()
    root = Path(a.project_dir).resolve()
    src = root / a.input
    if not src.exists():
        raise SystemExit(f"Missing: {src}")
    rows = parse(src)
    results = []
    bad = 0
    seen_pairs = set()
    for r in rows:
        jid = get(r, "Join")
        if not jid:
            continue
        frm = get(r, "From unit")
        to = get(r, "To unit")
        typ = get(r, "Join type").upper()
        issues = []
        if not frm or not to:
            issues.append("From/To unit required")
        pair = (frm, to)
        if frm and to and pair in seen_pairs:
            issues.append("duplicate From→To contract")
        seen_pairs.add(pair)
        if typ not in ALLOWED:
            issues.append(f"unknown join type {typ or '[blank]'}")
        seam = get(r, "Shared seam frame")
        if typ == "EXACT_SEAM":
            if not seam:
                issues.append("EXACT_SEAM requires Shared seam frame")
            if not get(r, "Exit state"):
                issues.append("EXACT_SEAM exit state missing")
            if not get(r, "Entry state"):
                issues.append("EXACT_SEAM entry state missing")
        if typ == "FLOW_EXTEND" and get(r, "Reset/occluder"):
            issues.append("FLOW_EXTEND should not simultaneously depend on reset/occluder")
        if typ == "OCCLUSION_RESET" and not get(r, "Reset/occluder"):
            issues.append("OCCLUSION_RESET requires reset/occluder")
        if typ == "GRAPHIC_RESET" and not (
            seam or get(r, "Reset/occluder") or get(r, "Post overlay at join")
        ):
            issues.append("GRAPHIC_RESET needs a graphic/reset surface")
        if typ in {"EXACT_SEAM", "MATCH_CUT"} and not get(r, "Screen direction"):
            issues.append("screen direction missing")
        if not get(r, "Handles"):
            issues.append("handles not specified")
        if not get(r, "Fallback"):
            issues.append("fallback missing")
        if not plan_allowed(get(r, "Approval")):
            issues.append("join not approved")
        res = "; ".join(issues) if issues else "PASS"
        if issues:
            bad += 1
        results.append((jid, frm, to, typ, res))
    out = [
        "# Shot Join Contract Review — v2",
        "",
        "| Join | From | To | Type | Result |",
        "|---|---|---|---|---|",
    ]
    for vals in results:
        out.append("| " + " | ".join(v.replace("|", "/") for v in vals) + " |")
    if not results:
        out.append("| - | - | - | - | No populated join rows detected |")
    (root / a.output).write_text("\n".join(out) + "\n", encoding="utf-8")
    print(f"Wrote: {root / a.output}")
    print(f"Joins: {len(results)} | With issues: {bad}")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
