#!/usr/bin/env python3
"""Compile Flow generation queue and a near-direct assembly manifest from v2 endpoint/join plans."""

from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path
from historical_shortfilm_director.runtime.common import plan_allowed, local, load


def norm(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").strip()).lower()


def split(line: str) -> list[str]:
    return [c.strip() for c in line.strip().strip("|").split("|")]


def sep(c: list[str]) -> bool:
    return bool(c) and all(bool(re.fullmatch(r":?-{3,}:?", x.replace(" ", ""))) for x in c)


def parse(path: Path, key: str) -> list[dict[str, str]]:
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    for i in range(len(lines) - 1):
        if not lines[i].strip().startswith("|") or not lines[i + 1].strip().startswith("|"):
            continue
        h = split(lines[i])
        if norm(key) not in [norm(x) for x in h] or not sep(split(lines[i + 1])):
            continue
        out = []
        for ln in lines[i + 2 :]:
            if not ln.strip().startswith("|"):
                break
            c = split(ln)
            if sep(c):
                continue
            c += [""] * max(0, len(h) - len(c))
            r = {norm(x): c[j] if j < len(c) else "" for j, x in enumerate(h)}
            if any(r.values()):
                out.append(r)
        return out
    raise ValueError(f"No table keyed by {key} in {path.name}")


def get(r: dict[str, str], name: str) -> str:
    return r.get(norm(name), "").strip()


def approved(v: str) -> bool:
    return norm(v) in {"approved", "locked", "yes", "pass", "通过", "已批准", "批准"}


def num(v: str) -> str:
    m = re.search(r"\d+(?:\.\d+)?", v or "")
    return m.group(0) if m else ""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("project_dir")
    ap.add_argument("--endpoints", default="05f_shot_endpoint_plan.md")
    ap.add_argument("--joins", default="05h_join_contracts.md")
    a = ap.parse_args()
    root = Path(a.project_dir).resolve()
    ep = root / a.endpoints
    jp = root / a.joins
    if not ep.exists() or not jp.exists():
        raise SystemExit("Missing endpoint or join plan")
    units = [r for r in parse(ep, "Unit") if get(r, "Unit")]
    joins = [r for r in parse(jp, "Join") if get(r, "Join")]
    by_from = {get(j, "From unit"): j for j in joins if get(j, "From unit")}
    by_to = {get(j, "To unit"): j for j in joins if get(j, "To unit")}
    # Each provider writes accepted clips to its own path; read it from the compiled queue.
    queued = {
        j.get("unit"): j
        for j in load(root / "06o_flow_job_queue.json", {"jobs": []}).get("jobs", [])
        if j.get("unit")
    }
    schedule = None

    queue = [
        "# Flow Generation Queue — v3",
        "",
        "Generate in story order unless a dependency note says otherwise. Approved frame assets and join contracts are authoritative.",
        "",
        "| Order | Unit | Mode | Start frame | End frame | Edit duration | Flow source duration | Join-in | Join-out | Status |",
        "|---:|---|---|---|---|---:|---:|---|---|---|",
    ]
    manifest_rows = []
    for idx, u in enumerate(units, 1):
        uid = get(u, "Unit")
        mode = get(u, "Flow mode").upper()
        start = get(u, "Start frame ID")
        end = get(u, "End frame ID")
        ed = num(get(u, "Final edit duration")) or num(get(u, "Duration"))
        src = num(get(u, "Duration"))
        use_in = num(get(u, "Use in")) or "0"
        use_out = num(get(u, "Use out")) or (str(float(use_in) + float(ed)) if ed else "")
        jin = by_to.get(uid, {})
        jout = by_from.get(uid, {})
        jin_id = get(jin, "Join")
        jout_id = get(jout, "Join")
        status = (
            "READY"
            if plan_allowed(get(u, "Approval"), get(u, "Autonomy") or "AUTO")
            else "HOLD_ENDPOINT_BLOCKED"
        )
        if jin and not plan_allowed(get(jin, "Approval")):
            status = "HOLD_JOIN_BLOCKED"
        if jout and not plan_allowed(get(jout, "Approval")):
            status = "HOLD_JOIN_BLOCKED"
        queue.append(
            f"| {idx} | {uid} | {mode} | {start} | {end} | {ed} | {src} | {jin_id} | {jout_id} | {status} |"
        )
        seam = get(jout, "Shared seam frame") or get(jin, "Shared seam frame")
        overlay = get(jout, "Post overlay at join") or get(jin, "Post overlay at join")
        audio = get(jout, "Audio bridge") or get(jin, "Audio bridge")
        fallback = get(u, "Bridge/reset") or get(jout, "Fallback") or get(jin, "Fallback")
        job = queued.get(uid, {})
        source_clip = (
            f"renders/{uid}.mp4"
            if mode == "SKIP_FLOW"
            else job.get("approved_output") or f"generated/flow_approved/{uid}.mp4"
        )
        clip = local(root, source_clip)
        if not clip.is_file():
            status = "HOLD_MEDIA_MISSING"
        if mode != "SKIP_FLOW":
            if schedule is None:
                from historical_shortfilm_director.runtime.engine import next_jobs

                schedule = {x["job_id"]: x for x in next_jobs(root)["jobs"]}
            entry = schedule.get(job.get("job_id") or "FLOW_" + uid)
            if not entry or entry["reasons"] != ["ACCEPTED"]:
                status = "HOLD_MEDIA_NOT_ACCEPTED"
        manifest_rows.append(
            {
                "order": idx,
                "unit": uid,
                "parent_shot": get(u, "Parent shot"),
                "flow_mode": mode,
                "source_clip": source_clip,
                "flow_source_duration_s": src,
                "final_edit_duration_s": ed,
                "use_in_s": use_in,
                "use_out_s": use_out,
                "start_frame_id": start,
                "end_frame_id": end,
                "join_in": jin_id,
                "join_in_type": get(jin, "Join type"),
                "join_out": jout_id,
                "join_out_type": get(jout, "Join type"),
                "seam_frame": seam,
                "post_overlay": overlay,
                "audio_bridge": audio,
                "fallback": fallback,
                "status": status,
            }
        )

    (root / "06j_flow_generation_queue.md").write_text("\n".join(queue) + "\n", encoding="utf-8")
    fields = (
        list(manifest_rows[0].keys())
        if manifest_rows
        else [
            "order",
            "unit",
            "parent_shot",
            "flow_mode",
            "source_clip",
            "flow_source_duration_s",
            "final_edit_duration_s",
            "use_in_s",
            "use_out_s",
            "start_frame_id",
            "end_frame_id",
            "join_in",
            "join_in_type",
            "join_out",
            "join_out_type",
            "seam_frame",
            "post_overlay",
            "audio_bridge",
            "fallback",
            "status",
        ]
    )
    with (root / "06k_direct_assembly_manifest.csv").open(
        "w", encoding="utf-8-sig", newline=""
    ) as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(manifest_rows)

    runbook = [
        "# Direct Assembly Runbook — v3",
        "",
        "Objective: after approved Flow renders are placed at the manifest paths, assemble in manifest order with only the trims/joins already designed upstream.",
        "",
        "## Rules",
        "",
        "1. Do not invent new transitions in the NLE to rescue an incompatible pair; repair the join contract or regenerate the relevant endpoint.",
        "2. For `EXACT_SEAM`, trim both clips to the approved shared junction state; use a straight cut unless the contract explicitly says otherwise.",
        "3. For `FLOW_EXTEND`, preserve continuity and remove duplicated hold frames if needed.",
        "4. For `MATCH_CUT`, use the specified screen direction/geometry and the registered trim points.",
        "5. For `OCCLUSION_RESET` / `GRAPHIC_RESET`, cut inside the approved reset surface.",
        "6. Apply deterministic text, dates, map labels, credits and sealed archival pixel overlays after picture lock or as pre-approved overlays.",
        "7. Audio bridges may cross cuts; picture continuity must not depend on unplanned dissolves.",
        "",
        "## Outputs",
        "",
        "- `06j_flow_generation_queue.md` — generation/dependency order",
        "- `06k_direct_assembly_manifest.csv` — edit manifest",
        "- final NLE/ffmpeg assembly should consume the approved clips and exact trim values from this manifest",
        "",
    ]
    (root / "06l_direct_assembly_runbook.md").write_text("\n".join(runbook), encoding="utf-8")
    print(f"Wrote: {root / '06j_flow_generation_queue.md'}")
    print(f"Wrote: {root / '06k_direct_assembly_manifest.csv'}")
    print(f"Wrote: {root / '06l_direct_assembly_runbook.md'}")
    print(f"Units: {len(units)} | Joins: {len(joins)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
