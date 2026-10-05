#!/usr/bin/env python3
"""Render simple exact/source-driven shots from 06r_deterministic_motion_queue.json.

Supported motions deliberately stay simple and auditable: HOLD, PUSH_IN, PULL_OUT,
PAN_LEFT, PAN_RIGHT, FADE_TO_BLACK. Complex history-sensitive graphics should be
pre-rendered as exact stills/layers and then animated here or in a dedicated code pass.
"""

from __future__ import annotations
import argparse
import json
from pathlib import Path
from historical_shortfilm_director.runtime.common import local, sha, digest, load, save, media_check


def ease(t: float) -> float:
    return t * t * (3 - 2 * t)


def render(job, root: Path):
    import cv2
    import numpy as np

    src = local(root, job["source"])
    out = local(root, job.get("output") or f"renders/{job['unit']}.mp4")
    out.parent.mkdir(parents=True, exist_ok=True)
    im = cv2.imdecode(np.fromfile(str(src), dtype=np.uint8), cv2.IMREAD_COLOR)
    if im is None:
        raise RuntimeError(f"Unreadable source: {src}")
    W = int(job.get("width", 1920))
    H = int(job.get("height", 1080))
    fps = float(job.get("fps", 25))
    dur = float(job.get("duration_s", 4))
    n = max(1, int(round(fps * dur)))
    motion = str(job.get("motion", "HOLD")).upper()
    strength = float(job.get("strength", 0.08))
    if min(W, H, fps, dur) <= 0 or not 0 <= strength <= 0.5:
        raise ValueError("Invalid render dimensions/timing/strength")
    if motion not in {"HOLD", "PUSH_IN", "PULL_OUT", "PAN_LEFT", "PAN_RIGHT", "FADE_TO_BLACK"}:
        raise ValueError("Unknown motion")
    signature = digest({"job": job, "source": sha(src)})
    rp = out.with_suffix(".render.json")
    previous = load(rp, {})
    if out.exists():
        if previous.get("signature") == signature and previous.get("sha256") == sha(out):
            return out
        raise ValueError("Render exists with different content; choose a versioned output")
    sh, sw = im.shape[:2]
    # fill-crop master coordinates
    scale = max(W / sw, H / sh) * (1 + 2 * strength if motion in {"PAN_LEFT", "PAN_RIGHT"} else 1)
    rw, rh = max(W, int(round(sw * scale))), max(H, int(round(sh * scale)))
    base = cv2.resize(im, (rw, rh), interpolation=cv2.INTER_LANCZOS4)
    writer = cv2.VideoWriter(str(out), cv2.VideoWriter_fourcc(*"mp4v"), fps, (W, H))
    if not writer.isOpened():
        raise RuntimeError("Video encoder could not open output")
    for i in range(n):
        t = ease(i / (n - 1)) if n > 1 else 0
        zoom = 1.0
        panx = 0.0
        if motion == "PUSH_IN":
            zoom = 1 + strength * t
        elif motion == "PULL_OUT":
            zoom = 1 + strength * (1 - t)
        elif motion == "PAN_LEFT":
            panx = (1 - 2 * t) * strength
        elif motion == "PAN_RIGHT":
            panx = (-1 + 2 * t) * strength
        # crop from base, optionally zoom by taking smaller crop
        cw = max(2, min(rw, int(W / zoom)))
        ch = max(2, min(rh, int(H / zoom)))
        maxx = max(0, rw - cw)
        maxy = max(0, rh - ch)
        cx = (rw - cw) // 2 + int(panx * maxx)
        cy = (rh - ch) // 2
        cx = max(0, min(maxx, cx))
        cy = max(0, min(maxy, cy))
        crop = base[cy : cy + ch, cx : cx + cw]
        fr = cv2.resize(crop, (W, H), interpolation=cv2.INTER_LANCZOS4)
        if motion == "FADE_TO_BLACK":
            fr = (fr.astype(np.float32) * (1 - t)).astype(np.uint8)
        writer.write(fr)
    writer.release()
    meta = media_check(out, root)
    save(rp, {"signature": signature, **meta})
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("project_dir")
    ap.add_argument("--queue", default="06r_deterministic_motion_queue.json")
    a = ap.parse_args()
    root = Path(a.project_dir).resolve()
    qp = root / a.queue
    if not qp.exists():
        raise SystemExit(f"Missing: {qp}")
    data = json.loads(qp.read_text(encoding="utf-8"))
    jobs = data.get("jobs", [])
    done = []
    for j in jobs:
        if str(j.get("status", "READY")).upper() not in {"READY", "APPROVED"}:
            continue
        out = render(j, root)
        done.append(str(out))
        print(f"Rendered {j.get('unit')}: {out}")
    print(f"Rendered: {len(done)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
