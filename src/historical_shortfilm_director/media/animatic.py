"""Render a complete timed preview from real stills; never promote it as generated motion."""

from __future__ import annotations
import argparse
import csv
import html
import json
import subprocess
from pathlib import Path
from historical_shortfilm_director.commands import module_command
from historical_shortfilm_director.runtime.common import (
    load,
    save,
    local,
    relative,
    sha,
    digest,
    media_check,
    ffmpeg,
)
from historical_shortfilm_director.media.deterministic import render
import historical_shortfilm_director.runtime.engine as runtime


def fresh_entry(root, fid):
    state = load(Path(root) / "06t_execution_state.json", {"jobs": {}})
    key = "IMG25_" + str(fid)
    entry = state["jobs"].get(key)
    current = runtime.jobs(root)
    if not entry and key not in current:
        return None
    if not entry or key not in current or entry.get("spec_hash") != digest(current[key]):
        raise ValueError("Stale preview producer: " + str(fid))
    fingerprint, _, errors = runtime.fingerprint(root, current[key], state)
    if errors or fingerprint != entry.get("input_hash"):
        raise ValueError("Stale preview inputs: " + str(fid))
    return entry


def resolve_frame(root, fid, explicit):
    if explicit:
        p = local(root, explicit)
        if not p.is_file():
            raise ValueError("Preview image missing: " + explicit)
        return p, "explicit-preview"
    reg = load(Path(root) / "06n_asset_registry.json", {"assets": {}})["assets"].get(fid)
    if reg and reg.get("status") in {"APPROVED", "SOURCE_VERIFIED"}:
        fresh_entry(root, fid)
        p = local(root, reg["path"])
        if not p.is_file() or sha(p) != reg.get("sha256"):
            raise ValueError("Registered preview image changed: " + fid)
        return p, "registered"
    e = fresh_entry(root, fid) or {}
    reviews = {r["sha256"]: r for r in e.get("reviews", [])}
    candidates = [
        c
        for c in e.get("candidates", [])
        if reviews.get(c["sha256"], {}).get("verdict") == "PASS"
        and reviews[c["sha256"]].get("input_hash") == e.get("input_hash")
    ]
    candidates.sort(key=lambda c: float(reviews[c["sha256"]]["score"]), reverse=True)
    if candidates:
        c = candidates[0]
        p = local(root, c["path"])
        if not p.is_file() or sha(p) != c["sha256"]:
            raise ValueError("Reviewed preview image changed: " + fid)
        return p, "reviewed-candidate-not-human-approved"
    raise ValueError("No real image available for preview state: " + str(fid))


def build(root, timeline_path="05v_animatic_timeline.json"):
    root = Path(root).resolve()
    timeline = load(local(root, timeline_path))
    settings = timeline.get("settings", {})
    width = int(settings.get("width", 640))
    height = int(settings.get("height", 360))
    fps = float(settings.get("fps", 25))
    if min(width, height, fps) <= 0 or width % 2 or height % 2:
        raise ValueError("Invalid preview dimensions/fps")
    units = timeline.get("units", [])
    if not units:
        raise ValueError("No preview units; not a complete animatic")
    sources = []
    for u in units:
        if float(u["duration_s"]) <= 0:
            raise ValueError("Preview duration must be positive")
        p, kind = resolve_frame(
            root, u.get("frame_id"), timeline.get("frames", {}).get(u.get("frame_id"))
        )
        meta = media_check(p, root)
        if meta["kind"] != "image":
            raise ValueError("Animatic frames must be still images")
        sources.append(
            {
                "unit": u["unit"],
                "frame_id": u["frame_id"],
                "path": relative(root, p),
                "sha256": sha(p),
                "origin": kind,
            }
        )
    audio = local(root, settings["audio"]) if settings.get("audio") else None
    if audio and not audio.is_file():
        raise ValueError("Scratch audio missing")
    signature = digest(
        {"timeline": timeline, "sources": sources, "audio_sha256": sha(audio) if audio else None}
    )
    stage = local(root, "work/animatic") / signature[:16]
    stage.mkdir(parents=True, exist_ok=True)
    out = local(root, "previews") / ("animatic_" + signature[:16] + ".mp4")
    out.parent.mkdir(parents=True, exist_ok=True)
    receipt = out.with_suffix(".json")
    old = load(receipt, {})
    if out.exists():
        if old.get("signature") == signature and old.get("sha256") == sha(out):
            return {**old, "unchanged": True}
        raise ValueError("Existing animatic differs from its receipt")
    rows = []
    markers = []
    at = 0.0
    for index, (u, source) in enumerate(zip(units, sources)):
        frames = max(1, round(float(u["duration_s"]) * fps))
        duration = frames / fps
        clip = render(
            {
                "unit": u["unit"],
                "source": source["path"],
                "output": relative(root, stage / f"{index:04d}.mp4"),
                "motion": u.get("motion", "HOLD"),
                "duration_s": duration,
                "fps": fps,
                "width": width,
                "height": height,
            },
            root,
        )
        rows.append(
            {
                "unit": u["unit"],
                "source_clip": relative(root, clip),
                "use_in_s": 0,
                "use_out_s": duration,
                "final_edit_duration_s": duration,
                "status": "READY",
            }
        )
        markers.append(
            {
                "unit": u["unit"],
                "start_s": at,
                "end_s": at + duration,
                "frame_id": source["frame_id"],
            }
        )
        at += duration
    manifest = stage / "preview_assembly.csv"
    with manifest.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    picture = stage / "picture.mp4"
    if not picture.exists():
        command = [
            *module_command("assemble_direct.py"),
            str(root),
            "--manifest",
            relative(root, manifest),
            "--output",
            relative(root, picture),
            "--width",
            str(width),
            "--height",
            str(height),
            "--fps",
            str(fps),
            "--execute",
        ]
        subprocess.run(command, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    picmeta = media_check(picture, root)
    picture_receipt = load(picture.with_suffix(".qc.json"), {})
    expected_sources = [
        {"path": str(local(root, r["source_clip"])), "sha256": sha(local(root, r["source_clip"]))}
        for r in rows
    ]
    if (
        picture_receipt.get("status") != "PASS"
        or picture_receipt.get("sha256") != sha(picture)
        or picture_receipt.get("manifest_sha256") != sha(manifest)
        or picture_receipt.get("sources") != expected_sources
    ):
        raise ValueError(
            "Cached preview picture provenance mismatch; preserve it and inspect the interrupted run"
        )
    if abs(picmeta["duration_s"] - at) > 1 / fps + 0.001:
        raise ValueError("Cached preview picture duration mismatch")
    if audio:
        command = [
            ffmpeg(root),
            "-v",
            "error",
            "-xerror",
            "-n",
            "-i",
            str(picture),
            "-i",
            str(audio),
            "-map",
            "0:v:0",
            "-map",
            "1:a:0",
            "-af",
            "apad",
            "-t",
            str(at),
            "-c:v",
            "copy",
            "-c:a",
            "aac",
            str(out),
        ]
        subprocess.run(command, check=True)
    else:
        import shutil

        shutil.copy2(picture, out)
    meta = media_check(out, root)
    if abs(meta["duration_s"] - at) > 1 / fps + 0.001:
        raise ValueError("Animatic duration mismatch")
    report = {
        "status": "PREVIEW_ONLY",
        "signature": signature,
        "path": relative(root, out),
        **meta,
        "sources": sources,
        "markers": markers,
        "audio": relative(root, audio) if audio else None,
        "limitations": [
            "Still-based timed preview; not provider-generated motion or final footage.",
            "No human gate or asset approval is changed.",
        ],
    }
    save(receipt, report)
    page = (
        '<!doctype html><html lang="zh-CN"><meta charset="utf-8"><title>Animatic preview</title><style>body{margin:32px;background:#18212b;color:#eee;font-family:"Times New Roman",SimSun,serif}video{width:min(100%,1100px)}td{padding:8px 18px;border-bottom:1px solid #53606b}</style><h1>动态分镜预览 · PREVIEW ONLY</h1><p>用于检查节奏、视觉顺序与临时声音；不代表 已生成视频镜头。</p><video controls src="'
        + html.escape(out.name)
        + '"></video><table>'
        + "".join(
            f"<tr><td>{html.escape(m['unit'])}</td><td>{m['start_s']:.2f}–{m['end_s']:.2f} s</td></tr>"
            for m in markers
        )
        + "</table></html>"
    )
    out.with_suffix(".html").write_text(page, encoding="utf-8")
    return report


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("project_dir")
    p.add_argument("--timeline", default="05v_animatic_timeline.json")
    a = p.parse_args()
    print(json.dumps(build(a.project_dir, a.timeline), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
