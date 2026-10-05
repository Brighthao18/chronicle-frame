"""Preserved local production invariants."""

from __future__ import annotations
import os
import shutil
import subprocess
from pathlib import Path
from historical_shortfilm_director.runtime.storage import load, sha


def ffmpeg(root=None):
    config = load(Path(root) / "00_capability_snapshot.json", {}) if root else {}
    explicit = config.get("local", {}).get("ffmpeg_path") or os.environ.get("HSD_FFMPEG")
    candidate = explicit or shutil.which("ffmpeg")
    if not candidate:
        try:
            import imageio_ffmpeg

            candidate = imageio_ffmpeg.get_ffmpeg_exe()
        except ImportError:
            pass
    if not candidate or not Path(candidate).is_file():
        raise RuntimeError(
            "FFmpeg missing. Set HSD_FFMPEG or local.ffmpeg_path, or install imageio-ffmpeg in a local environment."
        )
    return str(candidate)


def media_check(path, root=None):
    p = Path(path)
    if not p.is_file() or not p.stat().st_size:
        raise ValueError(f"Media missing/empty: {p}")
    meta = {"sha256": sha(p), "bytes": p.stat().st_size}
    if p.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp", ".tif", ".tiff"}:
        from PIL import Image

        with Image.open(p) as im:
            im.load()
            meta.update(kind="image", width=im.width, height=im.height, mode=im.mode)
    elif p.suffix.lower() in {".mp4", ".mov", ".mkv", ".webm"}:
        import cv2

        cap = cv2.VideoCapture(str(p))
        try:
            if not cap.isOpened():
                raise ValueError("Unreadable video")
            fps = cap.get(cv2.CAP_PROP_FPS)
            n = cap.get(cv2.CAP_PROP_FRAME_COUNT)
            if fps <= 0 or n < 2:
                raise ValueError("Invalid video duration")
            meta.update(
                kind="video",
                width=int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
                height=int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
                fps=fps,
                duration_s=n / fps,
            )
        finally:
            cap.release()
        cp = subprocess.run(
            [ffmpeg(root), "-v", "error", "-xerror", "-i", str(p), "-f", "null", "-"],
            capture_output=True,
        )
        if cp.returncode or cp.stderr.strip():
            raise ValueError(
                "Full media decode failed: " + cp.stderr.decode("utf-8", "replace")[-1000:]
            )
        meta["full_decode"] = "PASS"
    else:
        raise ValueError(f"Unsupported media: {p.suffix}")
    return meta
