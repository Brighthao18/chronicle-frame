#!/usr/bin/env python3
"""Compile deterministic Chinese/English text overlays from 07_text_overlay_plan.csv to ASS."""

from __future__ import annotations
import argparse
import csv
import re
from pathlib import Path


def ass_time(v):
    ticks = round(float(v) * 100)
    if ticks < 0:
        raise ValueError("Negative text timestamp")
    h, ticks = divmod(ticks, 360000)
    m, ticks = divmod(ticks, 6000)
    s, cs = divmod(ticks, 100)
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"


def esc(t):
    return (
        (t or "").replace("\\", "\\\\").replace("\n", "\\N").replace("{", "\\{").replace("}", "\\}")
    )


def font_runs(text, chinese="SimSun", western="Times New Roman"):
    parts = re.findall(r"[\x00-\x7f]+|[^\x00-\x7f]+", text)
    return "".join(
        "{\\fn" + (western if all(ord(c) < 128 for c in part) else chinese) + "}" + esc(part)
        for part in parts
    )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("project_dir")
    ap.add_argument("--input", default="07_text_overlay_plan.csv")
    ap.add_argument("--output", default="exports/text_overlay.ass")
    ap.add_argument("--font", default="SimSun")
    ap.add_argument("--western-font", default="Times New Roman")
    ap.add_argument("--width", type=int, default=1920)
    ap.add_argument("--height", type=int, default=1080)
    a = ap.parse_args()
    root = Path(a.project_dir).resolve()
    ip = root / a.input
    if not ip.exists():
        raise SystemExit(f"Missing: {ip}")
    with ip.open("r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    styles = {
        "CAPTION": ("44", "&H00FFFFFF", "2", "60"),
        "TITLE": ("76", "&H00FFFFFF", "5", "80"),
        "NOTE": ("30", "&H00E0E0E0", "2", "50"),
        "TOP": ("40", "&H00FFFFFF", "8", "45"),
    }
    out = [
        "[Script Info]",
        "ScriptType: v4.00+",
        "WrapStyle: 2",
        f"PlayResX: {a.width}",
        f"PlayResY: {a.height}",
        "ScaledBorderAndShadow: yes",
        "",
        "[V4+ Styles]",
        "Format: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,BackColour,Bold,Italic,Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,BorderStyle,Outline,Shadow,Alignment,MarginL,MarginR,MarginV,Encoding",
    ]
    for name, (size, color, align, mv) in styles.items():
        out.append(
            f"Style: {name},{a.font},{size},{color},&H000000FF,&H80000000,&H40000000,0,0,0,0,100,100,0,0,1,1.5,0,{align},60,60,{mv},1"
        )
    out += [
        "",
        "[Events]",
        "Format: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text",
    ]
    count = 0
    for r in rows:
        if str(r.get("approval", "APPROVED")).strip().upper() not in {"APPROVED", "READY", "YES"}:
            continue
        st = ass_time(r.get("start_s", "0"))
        en = ass_time(r.get("end_s", "0"))
        if float(r.get("end_s", "0")) <= float(r.get("start_s", "0")):
            raise ValueError("Invalid subtitle interval")
        style = (r.get("style") or "CAPTION").upper()
        style = style if style in styles else "CAPTION"
        text = font_runs(r.get("text", ""), a.font, a.western_font)
        if not text:
            continue
        out.append(f"Dialogue: 0,{st},{en},{style},,0,0,0,,{text}")
        count += 1
    op = root / a.output
    op.parent.mkdir(parents=True, exist_ok=True)
    op.write_text("\n".join(out) + "\n", encoding="utf-8-sig")
    print(f"Wrote: {op} ({count} events)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
