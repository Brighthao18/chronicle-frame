#!/usr/bin/env python3
"""Assemble an approved straight-cut picture master from 06k_direct_assembly_manifest.csv.

This intentionally does not invent transitions. v2 join contracts must make every
boundary cuttable upstream. Audio, subtitles and deterministic overlays can be baked
into source clips or added as later registered tracks.
"""

from __future__ import annotations

import argparse
import csv
import shlex
import subprocess
from pathlib import Path
from historical_shortfilm_director.runtime.common import ffmpeg, media_check, save, sha, local


def fnum(v: str, default: float = 0.0) -> float:
    try:
        return float(v)
    except Exception:
        return default


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("project_dir")
    ap.add_argument("--manifest", default="06k_direct_assembly_manifest.csv")
    ap.add_argument("--output", default="exports/direct_picture_master.mp4")
    ap.add_argument("--fps", type=float, default=25.0)
    ap.add_argument("--width", type=int, default=1920)
    ap.add_argument("--height", type=int, default=1080)
    ap.add_argument(
        "--execute", action="store_true", help="Run ffmpeg; default only writes command file"
    )
    args = ap.parse_args()

    root = Path(args.project_dir).resolve()
    manifest = root / args.manifest
    if not manifest.exists():
        raise SystemExit(f"Missing: {manifest}")
    with manifest.open("r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    held = [r.get("unit") for r in rows if (r.get("status") or "").upper() != "READY"]
    if held:
        raise SystemExit("Assembly is incomplete; held units: " + ", ".join(held))
    if not rows:
        raise SystemExit("No READY rows in assembly manifest")

    inputs: list[Path] = []
    for r in rows:
        p = local(root, r.get("source_clip") or "")
        inputs.append(p)
    missing = [str(p) for p in inputs if not p.exists()]
    if missing:
        print("Missing approved source clips:")
        for x in missing:
            print(f"- {x}")
        print(
            "Place approved renders at the manifest paths, then re-run. The command file will still be written."
        )

    cmd = [ffmpeg(root), "-n"]
    for p in inputs:
        cmd += ["-i", str(p)]

    filters = []
    labels = []
    expected = 0.0
    for i, r in enumerate(rows):
        start = fnum(r.get("use_in_s") or "0", 0.0)
        end = fnum(r.get("use_out_s") or "", 0.0)
        edit = fnum(r.get("final_edit_duration_s") or "", 0.0)
        if end <= start and edit > 0:
            end = start + edit
        if end <= start:
            raise SystemExit(f"Invalid trim for {r.get('unit')}: {start} → {end}")
        if start < 0 or (edit > 0 and abs(end - start - edit) > 1 / args.fps):
            raise SystemExit("Trim/edit duration mismatch: " + r.get("unit", ""))
        if args.execute and inputs[i].exists():
            meta = media_check(inputs[i], root)
            if end > meta["duration_s"] + 1 / meta["fps"]:
                raise SystemExit("Trim exceeds media: " + r.get("unit", ""))
        label = f"v{i}"
        start_frame = round(start * args.fps)
        end_frame = round(end * args.fps)
        expected += (end_frame - start_frame) / args.fps
        filters.append(
            f"[{i}:v]fps={args.fps:g}:eof_action=pass,trim=start_frame={start_frame}:end_frame={end_frame},setpts=PTS-STARTPTS,"
            f"scale={args.width}:{args.height}:force_original_aspect_ratio=decrease,"
            f"pad={args.width}:{args.height}:(ow-iw)/2:(oh-ih)/2,"
            f"setsar=1,format=yuv420p[{label}]"
        )
        labels.append(f"[{label}]")
    filters.append("".join(labels) + f"concat=n={len(labels)}:v=1:a=0[vout]")
    cmd += [
        "-filter_complex",
        ";".join(filters),
        "-map",
        "[vout]",
        "-r",
        str(args.fps),
        "-fps_mode",
        "cfr",
        "-c:v",
        "libx264",
        "-crf",
        "18",
        "-preset",
        "medium",
        "-pix_fmt",
        "yuv420p",
        str(root / args.output),
    ]

    out_path = local(root, args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    command_file = root / "06m_direct_assembly_ffmpeg.txt"
    command_file.write_text(shlex.join(cmd) + "\n", encoding="utf-8")
    print(f"Wrote: {command_file}")
    if not args.execute:
        print("Dry run: ffmpeg not executed. Use --execute after all source clips exist.")
        return 1 if missing else 0
    if missing:
        return 2
    subprocess.run(cmd, check=True)
    meta = media_check(out_path, root)
    if (
        abs(meta["duration_s"] - expected) > 1 / args.fps + 0.001
        or abs(meta["fps"] - args.fps) > 0.01
    ):
        raise RuntimeError("Picture master duration/fps mismatch")
    save(
        out_path.with_suffix(".qc.json"),
        {
            "status": "PASS",
            "manifest_sha256": sha(manifest),
            "sources": [{"path": str(p), "sha256": sha(p)} for p in inputs],
            **meta,
        },
    )
    print(f"Wrote: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
