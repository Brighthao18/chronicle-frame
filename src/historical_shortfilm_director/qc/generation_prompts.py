#!/usr/bin/env python3
"""Heuristic linter for v1.7 compiled generation prompts.

It detects prompt overload and common I2V failure patterns. It is not a model
quality evaluator and does not replace visual review.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

CAMERA_TERMS = [
    "dolly",
    "push-in",
    "push in",
    "pull-back",
    "pull back",
    "pan",
    "tilt",
    "orbit",
    "arc",
    "zoom",
    "crane",
    "jib",
    "truck",
    "handheld",
    "steadicam",
    "tracking",
]
VAGUE = [
    "epic",
    "beautiful",
    "dynamic camera",
    "cinematic dynamic",
    "masterpiece",
    "stunning",
    "dramatic camera",
]
STATIC_REPEAT = [
    "wearing",
    "hair",
    "skin",
    "color palette",
    "beautiful lighting",
    "photorealistic",
    "8k",
    "highly detailed",
]
HUMAN_MOTION = [
    "blink",
    "smile",
    "talk",
    "speak",
    "walk",
    "turns her head",
    "turns his head",
    "waves",
    "laugh",
]
ARCHIVE_IDS = ["A089", "A090", "A091", "A092", "A176", "A177", "A184"]


def sections(text: str):
    # yield heading, body
    hits = list(re.finditer(r"^###\s+(.+)$", text, re.M))
    for i, m in enumerate(hits):
        end = hits[i + 1].start() if i + 1 < len(hits) else len(text)
        yield m.group(1).strip(), text[m.end() : end]


def prompt_blocks(body: str):
    return re.findall(r"\*\*Prompt[^\n]*:\*\*\s*\n\s*```text\n(.*?)\n```", body, re.S | re.I)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("project_dir")
    ap.add_argument("--input", default="06b_generation_prompt_pack.md")
    ap.add_argument("--output", default="06e_prompt_lint_report.md")
    args = ap.parse_args()
    root = Path(args.project_dir).resolve()
    src = root / args.input
    if not src.exists():
        raise SystemExit(f"Missing: {src}")
    text = src.read_text(encoding="utf-8", errors="replace")
    rows = []
    total = 0
    for head, body in sections(text):
        for idx, prompt in enumerate(prompt_blocks(body), 1):
            total += 1
            low = prompt.lower()
            issues = []
            wc = len(re.findall(r"\b[\w'-]+\b", prompt))
            if wc > 130:
                issues.append(f"prompt too long ({wc} words)")
            cams = [t for t in CAMERA_TERMS if t in low]
            if len(cams) > 2:
                issues.append("too many camera motion terms: " + ", ".join(cams))
            vague = [t for t in VAGUE if t in low]
            if vague:
                issues.append("vague camera/aesthetic filler: " + ", ".join(vague))
            sequential = sum(
                low.count(x) for x in [" then ", " after ", " finally ", " subsequently "]
            )
            if sequential > 2:
                issues.append(f"too many sequential clauses ({sequential}); consider splitting")
            neg = sum(low.count(x) for x in [" no ", " do not ", " without ", " avoid "])
            if neg > 3:
                issues.append(
                    "many negative instructions inside prose; move forbidden states to structured/adapted controls"
                )
            static = [t for t in STATIC_REPEAT if t in low]
            if len(static) >= 3:
                issues.append("possible I2V static-description repetition: " + ", ".join(static))
            if any(a.lower() in body.lower() for a in ARCHIVE_IDS):
                bad = [t for t in HUMAN_MOTION if t in low]
                if bad:
                    issues.append("archival-person motion risk: " + ", ".join(bad))
            rows.append(
                (
                    head + (f" / block {idx}" if idx > 1 else ""),
                    wc,
                    "; ".join(issues) if issues else "PASS",
                )
            )
    report = "# Prompt Lint Report\n\nHeuristic only. PASS means no obvious overload pattern was detected; visual/model review is still required.\n\n| Prompt | Words | Result |\n|---|---:|---|\n"
    for h, w, r in rows:
        report += f"| {h.replace('|', '/')} | {w} | {r.replace('|', '/')} |\n"
    report += f"\nTotal prompt blocks: {total}\n"
    (root / args.output).write_text(report, encoding="utf-8")
    print(f"Wrote: {root / args.output}")
    bad = sum(1 for _, _, r in rows if r != "PASS")
    print(f"Prompts: {total} | With warnings: {bad}")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
