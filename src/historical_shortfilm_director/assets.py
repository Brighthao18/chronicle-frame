#!/usr/bin/env python3
"""Register generated/source media with hashes and basic technical metadata."""

from __future__ import annotations
import argparse
import hashlib
import json
import subprocess
from pathlib import Path
from historical_shortfilm_director.runtime.common import register, mutation, local

try:
    from PIL import Image
except Exception:
    Image = None


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda: f.read(1024 * 1024), b""):
            h.update(b)
    return h.hexdigest()


def probe(path: Path) -> dict:
    ext = path.suffix.lower()
    if Image and ext in {".png", ".jpg", ".jpeg", ".webp", ".tif", ".tiff"}:
        with Image.open(path) as im:
            return {"kind": "image", "width": im.width, "height": im.height, "mode": im.mode}
    try:
        cp = subprocess.run(
            [
                "ffprobe",
                "-v",
                "error",
                "-show_entries",
                "format=duration:stream=codec_type,width,height,r_frame_rate",
                "-of",
                "json",
                str(path),
            ],
            capture_output=True,
            text=True,
            check=True,
        )
        return {"kind": "media", **json.loads(cp.stdout)}
    except Exception:
        return {"kind": "file"}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("project_dir")
    ap.add_argument("asset_id")
    ap.add_argument("path")
    ap.add_argument("--type", default="generated")
    ap.add_argument("--status", default="CANDIDATE")
    ap.add_argument("--refs", default="")
    ap.add_argument("--prompt-id", default="")
    ap.add_argument("--attempt", type=int, default=1)
    a = ap.parse_args()
    root = Path(a.project_dir).resolve()
    p = Path(a.path)
    p = p if p.is_absolute() else root / p
    if not p.exists():
        raise SystemExit(f"Missing asset: {p}")
    local(root, str(p))
    try:
        rel = str(p.relative_to(root))
    except Exception:
        rel = str(p)
    with mutation(root):
        register(
            root,
            a.asset_id,
            str(p),
            type=a.type,
            status=a.status,
            bytes=p.stat().st_size,
            metadata=probe(p),
            refs=[x.strip() for x in a.refs.split(",") if x.strip()],
            prompt_id=a.prompt_id,
            attempt=a.attempt,
        )
    print(f"Registered {a.asset_id}: {rel}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
