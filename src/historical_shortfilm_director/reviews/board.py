#!/usr/bin/env python3
"""Build compact human review contact sheets for escalated v3 jobs."""

from __future__ import annotations
import argparse
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import cv2

FONT = ImageFont.load_default()


def load(path, default):
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def thumb_image(path: Path, size=(360, 220)):
    try:
        im = Image.open(path).convert("RGB")
        im.thumbnail(size, Image.Resampling.LANCZOS)
        canvas = Image.new("RGB", size, "white")
        canvas.paste(im, ((size[0] - im.width) // 2, (size[1] - im.height) // 2))
        return canvas
    except Exception:
        return None


def video_triptych(path: Path, size=(360, 220)):
    cap = cv2.VideoCapture(str(path))
    n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    if not cap.isOpened() or n < 1:
        return None
    frames = []
    for pos in [0.08, 0.5, 0.92]:
        cap.set(cv2.CAP_PROP_POS_FRAMES, max(0, int((n - 1) * pos)))
        ok, fr = cap.read()
        if ok:
            fr = cv2.cvtColor(fr, cv2.COLOR_BGR2RGB)
            frames.append(Image.fromarray(fr))
    cap.release()
    if not frames:
        return None
    sw = size[0] // len(frames)
    out = Image.new("RGB", size, "white")
    for i, im in enumerate(frames):
        im.thumbnail((sw, size[1]), Image.Resampling.LANCZOS)
        out.paste(im, (i * sw + (sw - im.width) // 2, (size[1] - im.height) // 2))
    return out


def board(cards, title, path):
    if not cards:
        return False
    W = 780
    rowh = 285
    H = 70 + rowh * len(cards)
    im = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(im)
    d.text((20, 20), title, fill="black", font=FONT)
    y = 55
    for label, preview, note in cards:
        d.rectangle((15, y, 765, y + rowh - 10), outline="#999", width=1)
        d.text((25, y + 10), label, fill="black", font=FONT)
        if preview:
            im.paste(preview, (25, y + 38))
        # wrap note simple
        words = note.split()
        lines = []
        cur = ""
        for w in words:
            if len(cur) + len(w) + 1 > 52:
                lines.append(cur)
                cur = w
            else:
                cur = (cur + " " + w).strip()
        if cur:
            lines.append(cur)
        ty = y + 42
        for line in lines[:11]:
            d.text((410, ty), line, fill="#222", font=FONT)
            ty += 16
        y += rowh
    path.parent.mkdir(parents=True, exist_ok=True)
    im.save(path)
    return True


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("project_dir")
    a = ap.parse_args()
    root = Path(a.project_dir).resolve()
    iq = load(root / "06i_image25_job_queue.json", {"jobs": []})
    fq = load(root / "06o_flow_job_queue.json", {"jobs": []})
    qc = load(root / "06q_auto_qc_report.json", {})
    g2 = []
    for j in iq.get("jobs", []):
        if j.get("human_gate") != "G2_VISUAL":
            continue
        cdir = root / j.get("candidate_dir", "")
        files = (
            sorted(
                [
                    p
                    for p in cdir.glob("*")
                    if p.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"}
                ]
            )
            if cdir.exists()
            else []
        )
        for k, p in enumerate(files[: max(2, j.get("candidate_n", 2))], 1):
            g2.append(
                (
                    f"{j.get('frame_id')} · candidate {k}",
                    thumb_image(p),
                    f"Route {j.get('route')}; risk {j.get('risk')}; KEEP: {j.get('keep')}; CHANGE: {j.get('change')}",
                )
            )
    # map qc recommendations for notes
    qmap = {r.get("unit"): r for r in qc.get("flow", {}).get("jobs", [])}
    g3 = []
    for j in fq.get("jobs", []):
        if j.get("human_gate") != "G3_HERO_MOTION":
            continue
        cdir = root / j.get("candidate_dir", "")
        files = (
            sorted(
                [p for p in cdir.glob("*") if p.suffix.lower() in {".mp4", ".mov", ".mkv", ".webm"}]
            )
            if cdir.exists()
            else []
        )
        scores = {
            Path(c.get("path", "")).name: c.get("score")
            for c in qmap.get(j.get("unit"), {}).get("candidates", [])
        }
        for k, p in enumerate(files[: max(2, j.get("candidate_n", 2))], 1):
            g3.append(
                (
                    f"{j.get('unit')} · candidate {k}",
                    video_triptych(p),
                    f"QC score {scores.get(p.name, '-')}; reach {j.get('reachability')}; risk {j.get('risk')}; PATH: {j.get('motion_path')}",
                )
            )
    outdir = root / "reviews"
    outdir.mkdir(exist_ok=True)
    made = []
    if board(g2, "G2 Visual World / Hero Anchor Review", outdir / "G2_visual_review.png"):
        made.append("G2_visual_review.png")
    if board(g3, "G3 Hero Motion / Historical-Risk Review", outdir / "G3_motion_review.png"):
        made.append("G3_motion_review.png")
    md = ["# Human Review Boards — v3", ""]
    if made:
        md += [f"- `{x}`" for x in made]
    else:
        md += [
            "No escalated candidates are currently available. Routine AUTO jobs should continue without human interruption."
        ]
    (outdir / "review_boards.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print("Review boards:", ", ".join(made) if made else "none")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
