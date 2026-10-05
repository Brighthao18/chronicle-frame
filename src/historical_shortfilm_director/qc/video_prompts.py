#!/usr/bin/env python3
"""Heuristic linter for v2.0 Google Flow prompt packs."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

CAMERA = [
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
    "steadicam",
    "truck",
    "pedestal",
]
STATIC = [
    "wearing",
    "hairstyle",
    "skin tone",
    "8k",
    "highly detailed",
    "masterpiece",
    "photorealistic",
]
VAGUE = [
    "epic",
    "dynamic camera",
    "cinematic dynamic",
    "stunning",
    "beautiful shot",
    "dramatic camera",
    "majestic",
    "inspiring",
]
TECH = ["24 fps", "fps", "1080p", "4k", "seed", "cfg", "steps", "guidance", "scheduler"]


def prompt_blocks(text: str):
    pat = re.compile(
        r"^###\s+(.+?)$.*?\*\*Paste-ready(?:\s+English)?\s+Flow\s+prompt\*\*\s*\n\s*```text\n(.*?)\n```",
        re.M | re.S | re.I,
    )
    # backward-compatible pattern for older packs
    old = re.compile(
        r"^###\s+(.+?)$.*?\*\*Paste-ready English prompt[^\n]*\*\*\s*\n\s*```text\n(.*?)\n```",
        re.M | re.S | re.I,
    )
    seen = set()
    for regex in [pat, old]:
        for m in regex.finditer(text):
            key = (m.start(), m.group(1).strip())
            if key in seen:
                continue
            seen.add(key)
            yield m.group(1).strip(), m.group(2).strip()


def mode_from_header(head: str) -> tuple[str, str]:
    tail = head.split("—")[-1].strip() if "—" in head else head.strip()
    if "/" in tail:
        flow_mode, prompt_mode = [x.strip().upper() for x in tail.split("/", 1)]
        return flow_mode, prompt_mode
    return tail.upper(), ""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("project_dir")
    ap.add_argument("--input", default="06f_flow_prompt_pack.md")
    ap.add_argument("--output", default="06h_flow_prompt_lint.md")
    ap.add_argument(
        "--strict",
        action="store_true",
        help="Treat editorial heuristic warnings as a failing exit code",
    )
    args = ap.parse_args()

    root = Path(args.project_dir).resolve()
    src = root / args.input
    if not src.exists():
        raise SystemExit(f"Missing: {src}")
    text = src.read_text(encoding="utf-8", errors="replace")

    rows = []
    for head, prompt in prompt_blocks(text):
        low = prompt.lower()
        issues = []
        wc = len(re.findall(r"\b[\w'-]+\b", prompt))
        flow_mode, prompt_mode = mode_from_header(head)

        bands = {
            "T2V_RICH": (70, 180),
            "I2V_BALANCED": (50, 160),
            "FRAMES_PATH": (45, 150),
            "EXTEND_CONTINUITY": (25, 100),
            "OMNI_EDIT_LOCAL": (20, 100),
        }
        if prompt_mode in bands:
            lo, hi = bands[prompt_mode]
            if wc < lo:
                issues.append(f"under-specified for {prompt_mode} ({wc} words)")
            if wc > hi:
                issues.append(f"over-specified for {prompt_mode} ({wc} words)")

        camera_scan = re.sub(
            r"\b(?:no|not|without)\s+(?:a\s+)?(?:dolly|pan|tilt|orbit|arc|zoom|crane|jib|tracking|handheld|steadicam|truck|pedestal)\b",
            "",
            low,
        )
        cams = [x for x in CAMERA if re.search(r"\b" + re.escape(x) + r"\b", camera_scan)]
        if len(cams) > 2:
            issues.append("too many positive camera motion terms: " + ", ".join(cams))
        vague = [x for x in VAGUE if x in low]
        if vague:
            issues.append("vague filler: " + ", ".join(vague))
        static = [x for x in STATIC if x in low]
        if flow_mode in {"START_FRAME", "FRAMES", "EXTEND"} and len(static) >= 2:
            issues.append(
                "reference-conditioned prompt repeats too many static details: " + ", ".join(static)
            )
        tech = [x for x in TECH if x in low]
        if tech:
            issues.append(
                "structured technical parameter leaked into prose prompt: "
                + ", ".join(sorted(set(tech)))
            )
        seq = sum(
            low.count(x) for x in [" then ", " after ", " finally ", " subsequently ", " next "]
        )
        if seq > 3:
            issues.append(f"too many sequential events ({seq}); split the Flow unit")
        if flow_mode == "FRAMES":
            if "first and final frames" not in low and "first and last frames" not in low:
                issues.append("FRAMES prompt does not acknowledge supplied endpoint frames")
            if "final frame" not in low and "final state" not in low:
                issues.append("FRAMES prompt lacks final-state convergence language")
        if re.search(r"[\u3400-\u9fff]", prompt) and "Dialogue:" not in prompt:
            issues.append(
                "Chinese text appears in paste-ready Flow prompt outside explicit dialogue; verify intentional"
            )
        rows.append((head, wc, "; ".join(issues) if issues else "PASS"))

    report = [
        "# Google Flow Prompt Lint — v2.0",
        "",
        "Heuristic only. This linter checks the paste-ready Flow prompt, while `05g_shot_endpoint_review.md` checks the single-shot start/end contract.",
        "",
        "| Unit | Words | Result |",
        "|---|---:|---|",
    ]
    for h, w, r in rows:
        report.append(f"| {h.replace('|', '/')} | {w} | {r.replace('|', '/')} |")
    if not rows:
        report.append("| - | 0 | No compiled Flow prompts detected |")
    (root / args.output).write_text("\n".join(report) + "\n", encoding="utf-8")
    bad = sum(1 for _, _, r in rows if r != "PASS")
    print(f"Wrote: {root / args.output}")
    print(f"Prompts: {len(rows)} | With warnings: {bad}")
    return 1 if bad and args.strict else 0


if __name__ == "__main__":
    raise SystemExit(main())
