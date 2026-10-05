#!/usr/bin/env python3
"""Check v3 local automation dependencies without installing anything."""

from __future__ import annotations
import importlib.util
import json
import shutil
import sys
from historical_shortfilm_director.runtime.common import ffmpeg


def main() -> int:
    py = {m: bool(importlib.util.find_spec(m)) for m in ["PIL", "numpy", "cv2"]}
    bins = {b: bool(shutil.which(b)) for b in ["ffmpeg", "ffprobe"]}
    try:
        bins["ffmpeg_path"] = ffmpeg()
        bins["ffmpeg"] = True
    except RuntimeError:
        bins["ffmpeg_path"] = None
    data = {
        "python": sys.version.split()[0],
        "modules": py,
        "binaries": bins,
        "ready_core": True,
        "ready_image_code": py["PIL"],
        "ready_video_qc": py["cv2"] and py["numpy"] and bins["ffmpeg"],
        "ready_final_post": bins["ffmpeg"],
    }
    print(json.dumps(data, indent=2))
    return 0 if data["ready_video_qc"] and data["ready_image_code"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
