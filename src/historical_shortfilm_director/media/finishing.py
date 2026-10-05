#!/usr/bin/env python3
"""Mix registered audio timeline and optional ASS overlays onto the direct picture master."""

from __future__ import annotations
import argparse
import csv
import shlex
import subprocess
from pathlib import Path
from historical_shortfilm_director.runtime.common import (
    ffmpeg,
    media_check,
    save,
    sha,
    gate_covers,
    local,
)


def f(v, d=0.0):
    try:
        return float(v)
    except (ValueError, TypeError):
        return d


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("project_dir")
    ap.add_argument("--picture", default="exports/direct_picture_master.mp4")
    ap.add_argument("--audio-plan", default="07_audio_mix_plan.csv")
    ap.add_argument("--ass", default="exports/text_overlay.ass")
    ap.add_argument("--output", default="exports/final_master.mp4")
    ap.add_argument("--execute", action="store_true")
    a = ap.parse_args()
    root = Path(a.project_dir).resolve()
    picture = root / a.picture
    if not picture.exists():
        raise SystemExit(f"Missing picture master: {picture}")
    rows = []
    apath = root / a.audio_plan
    if apath.exists():
        with apath.open("r", encoding="utf-8-sig", newline="") as fp:
            rows = [
                r
                for r in csv.DictReader(fp)
                if str(r.get("approval", "APPROVED")).upper() in {"APPROVED", "READY", "YES"}
                and (r.get("path") or "").strip()
            ]
    picture_meta = media_check(picture, root)
    duration = picture_meta["duration_s"]
    if a.execute and not gate_covers(root, "G4_PICTURE_LOCK", sha(picture)):
        raise SystemExit("G4 picture lock must cover this exact picture file before final export")
    cmd = [ffmpeg(root), "-n", "-i", str(picture)]
    valid = []
    for r in rows:
        p = Path(r["path"])
        p = p if p.is_absolute() else root / p
        if not p.is_file():
            raise SystemExit(f"Missing planned audio: {p}")
        cmd += ["-i", str(p)]
        valid.append(r)
    filters = []
    alabels = []
    for i, r in enumerate(valid, 1):
        tin = f(r.get("trim_in_s"), 0)
        tout = r.get("trim_out_s")
        start = f(r.get("start_s"), 0)
        gain = f(r.get("gain_db"), 0)
        fi = f(r.get("fade_in_s"), 0)
        fo = f(r.get("fade_out_s"), 0)
        parts = [f"[{i}:a]"]
        filt = f"atrim=start={tin}"
        if tout not in {None, ""}:
            filt += f":end={f(tout)}"
        filt += ",asetpts=PTS-STARTPTS"
        if gain:
            filt += f",volume={gain}dB"
        if fi > 0:
            filt += f",afade=t=in:st=0:d={fi}"
        if fo > 0:
            dur = (f(tout) - tin) if tout not in {None, ""} else None
            if dur and dur > fo:
                filt += f",afade=t=out:st={max(0, dur - fo)}:d={fo}"
        delay = max(0, int(round(start * 1000)))
        filt += f",adelay={delay}|{delay}[a{i}]"
        filters.append(parts[0] + filt)
        alabels.append(f"[a{i}]")
    if alabels:
        filters.append(
            "".join(alabels)
            + f"amix=inputs={len(alabels)}:duration=longest:normalize=0,apad,atrim=duration={duration},alimiter=limit=0.95[aout]"
        )
    ass = root / a.ass
    vf = None
    if ass.exists():
        # ffmpeg filter path escaping for ':' and '\\'
        import shutil

        staged = local(root, "work/post") / ("text_" + sha(ass)[:12] + ".ass")
        staged.parent.mkdir(parents=True, exist_ok=True)
        if not staged.exists():
            shutil.copy2(ass, staged)
        vf = "ass='" + staged.relative_to(root).as_posix() + "'"
    if filters:
        cmd += ["-filter_complex", ";".join(filters)]
    if vf:
        cmd += ["-vf", vf, "-c:v", "libx264", "-crf", "18", "-preset", "medium"]
    else:
        cmd += ["-c:v", "copy"]
    if alabels:
        cmd += ["-map", "0:v:0", "-map", "[aout]", "-c:a", "aac", "-b:a", "192k"]
    else:
        cmd += ["-map", "0:v:0", "-map", "0:a?", "-c:a", "aac"]
    out = local(root, a.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    cmd += ["-t", str(duration), str(out)]
    cfile = root / "07_final_master_ffmpeg.txt"
    cfile.write_text(shlex.join(cmd) + "\n", encoding="utf-8")
    print(f"Wrote: {cfile}")
    if not a.execute:
        print("Dry run. Use --execute to render.")
        return 0
    subprocess.run(cmd, check=True, cwd=root)
    meta = media_check(out, root)
    if abs(meta["duration_s"] - duration) > 0.12:
        raise RuntimeError("Audio mix changed picture duration")
    save(
        out.with_suffix(".qc.json"),
        {"status": "PASS", "picture_sha256": sha(picture), "audio_tracks": len(valid), **meta},
    )
    print(f"Wrote: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
