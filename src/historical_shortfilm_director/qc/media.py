#!/usr/bin/env python3
"""Technical/endpoint/seam QC and low-risk auto-promotion for v3 media queues.

This script is intentionally conservative. It can auto-promote only AUTO jobs whose
technical + endpoint checks pass. Semantic/historical VLM review remains an agent step.
"""

from __future__ import annotations
import argparse
import json
from pathlib import Path
from typing import Any
import cv2
import numpy as np


def load(path: Path, default):
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def resolve(root: Path, p: str) -> Path | None:
    if not p:
        return None
    q = Path(p)
    return q if q.is_absolute() else root / q


def phash(img: np.ndarray) -> np.ndarray:
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if img.ndim == 3 else img
    gray = cv2.resize(gray, (32, 32), interpolation=cv2.INTER_AREA).astype(np.float32)
    d = cv2.dct(gray)[:8, :8]
    med = np.median(d[1:, :])
    return (d > med).astype(np.uint8).flatten()


def phash_dist(a, b) -> int:
    return int(np.count_nonzero(phash(a) != phash(b)))


def read_image(path: Path) -> np.ndarray | None:
    if not path or not path.exists():
        return None
    return cv2.imdecode(np.fromfile(str(path), dtype=np.uint8), cv2.IMREAD_COLOR)


def frame_at(cap, idx: int):
    cap.set(cv2.CAP_PROP_POS_FRAMES, max(0, idx))
    ok, fr = cap.read()
    return fr if ok else None


def inspect_video(
    path: Path, start_ref: Path | None, end_ref: Path | None, expected_duration: float | None
) -> dict[str, Any]:
    cap = cv2.VideoCapture(str(path))
    if not cap.isOpened():
        return {"path": str(path), "status": "FAIL", "errors": ["unreadable video"]}
    n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = float(cap.get(cv2.CAP_PROP_FPS) or 0)
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    duration = n / fps if fps > 0 else 0
    first = frame_at(cap, 0)
    last = frame_at(cap, max(0, n - 1))
    errors = []
    warns = []
    if n < 2 or first is None or last is None:
        errors.append("too few readable frames")
    if expected_duration and abs(duration - expected_duration) > max(0.6, expected_duration * 0.15):
        warns.append(f"duration {duration:.2f}s differs from requested {expected_duration:.2f}s")
    start_d = end_d = None
    sr = read_image(start_ref) if start_ref else None
    er = read_image(end_ref) if end_ref else None
    if sr is not None and first is not None:
        start_d = phash_dist(first, sr)
        warns += [f"start endpoint pHash distance {start_d}"] if start_d > 24 else []
    if er is not None and last is not None:
        end_d = phash_dist(last, er)
        warns += [f"end endpoint pHash distance {end_d}"] if end_d > 24 else []
    # boundary snap heuristic: compare adjacent-frame MAD in last 10%, flag final jump outlier
    diffs = []
    if n > 8:
        begin = max(0, int(n * 0.88))
        prev = frame_at(cap, begin)
        for idx in range(begin + 1, n):
            cur = frame_at(cap, idx)
            if prev is not None and cur is not None:
                a = cv2.resize(prev, (320, 180))
                b = cv2.resize(cur, (320, 180))
                diffs.append(float(np.mean(cv2.absdiff(a, b))) / 255.0)
            prev = cur
    snap = False
    final_diff = None
    med = None
    if diffs:
        final_diff = diffs[-1]
        med = float(np.median(diffs[:-1] or diffs))
        snap = final_diff > max(0.055, med * 3.5)
        if snap:
            warns.append(f"possible endpoint snap: final MAD {final_diff:.4f} vs median {med:.4f}")
    cap.release()
    hard_endpoint_fail = (start_d is not None and start_d > 38) or (
        end_d is not None and end_d > 38
    )
    status = "FAIL" if errors or hard_endpoint_fail else ("WARN" if warns else "PASS")
    score = 100
    if start_d is not None:
        score -= min(25, start_d * 0.7)
    if end_d is not None:
        score -= min(30, end_d * 0.8)
    if snap:
        score -= 20
    score -= 8 * len(errors) + 3 * len([x for x in warns if "duration" in x])
    return {
        "path": str(path),
        "status": status,
        "score": round(max(0, score), 1),
        "width": w,
        "height": h,
        "fps": round(fps, 3),
        "frames": n,
        "duration_s": round(duration, 3),
        "start_phash_distance": start_d,
        "end_phash_distance": end_d,
        "boundary_final_mad": final_diff,
        "boundary_median_mad": med,
        "endpoint_snap": snap,
        "warnings": warns,
        "errors": errors,
    }


def num(v):
    try:
        return float(v)
    except Exception:
        import re

        m = re.search(r"\d+(?:\.\d+)?", str(v or ""))
        return float(m.group()) if m else None


def inspect_flow(root: Path, promote: bool) -> dict:
    q = load(root / "06o_flow_job_queue.json", {"jobs": []})
    results = []
    for j in q.get("jobs", []):
        cdir = resolve(root, j.get("candidate_dir", ""))
        files = []
        if cdir and cdir.exists():
            files = sorted(
                [p for p in cdir.iterdir() if p.suffix.lower() in {".mp4", ".mov", ".mkv", ".webm"}]
            )
        approved = resolve(root, j.get("approved_output", ""))
        if approved and approved.exists() and approved not in files:
            files.append(approved)
        start = resolve(root, j.get("start_frame_path", ""))
        end = resolve(root, j.get("end_frame_path", ""))
        cand = [inspect_video(p, start, end, num(j.get("duration_s"))) for p in files]
        cand.sort(key=lambda x: x.get("score", 0), reverse=True)
        top = cand[0] if cand else None
        auto = False
        if promote:
            from historical_shortfilm_director.runtime.engine import accept

            try:
                accept(root, j["job_id"])
                auto = True
            except (ValueError, RuntimeError, KeyError) as exc:
                if top:
                    top.setdefault("warnings", []).append("Not promoted: " + str(exc))
        results.append(
            {
                "unit": j.get("unit"),
                "autonomy": j.get("autonomy"),
                "human_gate": j.get("human_gate"),
                "candidate_count": len(cand),
                "recommended": top,
                "candidates": cand,
                "auto_promoted": auto,
            }
        )
    return {"jobs": results}


def inspect_stills(root: Path) -> dict:
    q = load(root / "06i_image25_job_queue.json", {"jobs": []})
    out = []
    for j in q.get("jobs", []):
        cdir = resolve(root, j.get("candidate_dir", ""))
        files = []
        if cdir and cdir.exists():
            files = sorted(
                [
                    p
                    for p in cdir.iterdir()
                    if p.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"}
                ]
            )
        items = []
        for p in files:
            im = read_image(p)
            if im is None:
                items.append({"path": str(p), "status": "FAIL"})
                continue
            h, w = im.shape[:2]
            items.append(
                {
                    "path": str(p),
                    "status": "PASS",
                    "width": w,
                    "height": h,
                    "sharpness": round(
                        float(
                            cv2.Laplacian(cv2.cvtColor(im, cv2.COLOR_BGR2GRAY), cv2.CV_64F).var()
                        ),
                        2,
                    ),
                }
            )
        out.append(
            {
                "frame_id": j.get("frame_id"),
                "autonomy": j.get("autonomy"),
                "human_gate": j.get("human_gate"),
                "candidate_count": len(items),
                "technical_candidates": items,
                "note": "Semantic/identity ranking should be completed by agent vision against KEEP/CHANGE contract.",
            }
        )
    return {"jobs": out}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("project_dir")
    ap.add_argument("--promote-auto", action="store_true")
    ap.add_argument("--json-output", default="06q_auto_qc_report.json")
    ap.add_argument("--md-output", default="06q_auto_qc_report.md")
    a = ap.parse_args()
    root = Path(a.project_dir).resolve()
    data = {
        "schema_version": "3.0",
        "stills": inspect_stills(root),
        "flow": inspect_flow(root, a.promote_auto),
    }
    (root / a.json_output).write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    md = [
        "# Automated Media QC — v3",
        "",
        "This is a technical/endpoint pre-screen. Agent vision/historical checks remain authoritative for semantic accuracy.",
        "",
        "## Flow",
    ]
    for r in data["flow"]["jobs"]:
        top = r.get("recommended") or {}
        md.append(
            f"- `{r.get('unit')}`: {r.get('candidate_count')} candidates; top `{top.get('status', 'MISSING')}` score `{top.get('score', '-')}`; auto-promoted `{r.get('auto_promoted')}`; gate `{r.get('human_gate') or '-'}`"
        )
    md += ["", "## Stills"]
    for r in data["stills"]["jobs"]:
        md.append(
            f"- `{r.get('frame_id')}`: {r.get('candidate_count')} candidates; autonomy `{r.get('autonomy')}`; gate `{r.get('human_gate') or '-'}`"
        )
    (root / a.md_output).write_text("\n".join(md) + "\n", encoding="utf-8")
    print(f"Wrote: {root / a.json_output}")
    print(f"Wrote: {root / a.md_output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
