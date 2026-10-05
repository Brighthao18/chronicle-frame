#!/usr/bin/env python3
"""Compile machine-readable video jobs from approved endpoint plan + compiled prompt pack."""

from __future__ import annotations
import argparse
import json
import re
from pathlib import Path
from historical_shortfilm_director.runtime.common import plan_allowed, identifier, load


def norm(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").strip()).lower()


def cells(line: str) -> list[str]:
    return [c.strip() for c in line.strip().strip("|").split("|")]


def sep(c: list[str]) -> bool:
    return bool(c) and all(bool(re.fullmatch(r":?-{3,}:?", x.replace(" ", ""))) for x in c)


def parse_table(path: Path, key: str) -> list[dict[str, str]]:
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    for i in range(len(lines) - 1):
        if not lines[i].strip().startswith("|") or not lines[i + 1].strip().startswith("|"):
            continue
        h = cells(lines[i])
        if norm(key) not in [norm(x) for x in h] or not sep(cells(lines[i + 1])):
            continue
        out = []
        for ln in lines[i + 2 :]:
            if not ln.strip().startswith("|"):
                break
            c = cells(ln)
            if sep(c):
                continue
            c += [""] * max(0, len(h) - len(c))
            r = {norm(x): c[j] if j < len(c) else "" for j, x in enumerate(h)}
            if any(r.values()):
                out.append(r)
        return out
    raise ValueError(f"No {key} table in {path}")


def get(r, name):
    return r.get(norm(name), "").strip()


def approved(v):
    return norm(v) in {"approved", "locked", "yes", "pass", "通过", "已批准", "批准"}


def intval(v, default):
    m = re.search(r"\d+", v or "")
    return int(m.group()) if m else default


def seconds(v, allow_blank=True):
    if not v and allow_blank:
        return ""
    m = re.fullmatch(r"(\d+(?:\.\d+)?)\s*(?:s|sec|seconds|秒)?", str(v).strip(), re.I)
    if not m:
        raise ValueError("Invalid seconds: " + str(v))
    return float(m.group(1))


def parse_prompt_pack(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    text = path.read_text(encoding="utf-8", errors="replace")
    out = {}
    # each block starts ### UNIT — ... then a Paste-ready Flow prompt fenced block
    heads = list(re.finditer(r"^###\s+([^\s—]+)\s+—[^\n]*$", text, re.M))
    for i, m in enumerate(heads):
        uid = m.group(1).strip()
        end = heads[i + 1].start() if i + 1 < len(heads) else len(text)
        block = text[m.end() : end]
        pm = re.search(r"\*\*Paste-ready Flow prompt\*\*\s*```text\s*(.*?)\s*```", block, re.S)
        if pm:
            out[uid] = pm.group(1).strip()
    return out


def registry_paths(root: Path) -> dict[str, str]:
    p = root / "06n_asset_registry.json"
    if not p.exists():
        return {}
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return {
        k: str(v.get("path", "")) for k, v in data.get("assets", {}).items() if isinstance(v, dict)
    }


def default_n(risk, reach, autonomy):
    s = (risk + " " + reach + " " + autonomy).lower()
    return (
        4
        if any(k in s for k in ["hero", "high", "r-c", "r-d", "review", "opening", "ending"])
        else 2
    )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("project_dir")
    ap.add_argument("--endpoints", default="05f_shot_endpoint_plan.md")
    ap.add_argument("--prompts", default="06f_flow_prompt_pack.md")
    ap.add_argument("--joins", default="05h_join_contracts.md")
    ap.add_argument("--json-output", default="06o_flow_job_queue.json")
    ap.add_argument("--md-output", default="06o_flow_job_queue.md")
    a = ap.parse_args()
    root = Path(a.project_dir).resolve()
    ep = root / a.endpoints
    provider = "flow" if load(root / "project.json", {}).get("generator") == "flow" else "video"
    if not ep.exists():
        raise SystemExit(f"Missing: {ep}")
    rows = parse_table(ep, "Unit")
    prompts = parse_prompt_pack(root / a.prompts)
    refs = registry_paths(root)
    joins = []
    if (root / a.joins).exists():
        try:
            joins = parse_table(root / a.joins, "Join")
        except Exception:
            joins = []
    incoming = {get(j, "To unit"): j for j in joins if get(j, "To unit")}
    outgoing = {get(j, "From unit"): j for j in joins if get(j, "From unit")}
    jobs = []
    skipped = []
    for idx, r in enumerate(rows, 1):
        uid = get(r, "Unit")
        mode = (get(r, "Flow mode") or "START_FRAME").upper()
        if not uid or mode == "SKIP_FLOW":
            continue
        identifier(uid)
        if not plan_allowed(get(r, "Approval"), get(r, "Autonomy") or "AUTO"):
            skipped.append(uid)
            continue
        risk = get(r, "Risk") or "routine"
        autonomy = (get(r, "Autonomy") or "AUTO").upper()
        reach = get(r, "Reachability").upper()
        n = intval(get(r, "Candidate N"), default_n(risk, reach, autonomy))
        sid = get(r, "Start frame ID")
        eid = get(r, "End frame ID")
        start_path = refs.get(sid, "") if sid else ""
        end_path = refs.get(eid, "") if eid else ""
        dur = seconds(get(r, "Duration"), False)
        prompt = prompts.get(uid, "")
        human_gate = (
            "G3_HERO_MOTION"
            if autonomy == "REVIEW"
            or any(k in (risk + " " + reach).lower() for k in ["hero", "high", "r-c", "r-d"])
            else None
        )
        jin = incoming.get(uid, {})
        jout = outgoing.get(uid, {})
        dep = []
        if get(jin, "Join type").upper() == "FLOW_EXTEND":
            dep = [get(jin, "From unit")]
        job = {
            "provider": provider,
            "job_id": f"FLOW_{uid}",
            "order": idx,
            "unit": uid,
            "parent_shot": get(r, "Parent shot"),
            "mode": mode,
            "duration_s": dur,
            "final_edit_duration_s": seconds(get(r, "Final edit duration")),
            "use_in_s": seconds(get(r, "Use in")),
            "use_out_s": seconds(get(r, "Use out")),
            "start_frame_id": sid,
            "start_frame_path": start_path,
            "end_frame_id": eid,
            "end_frame_path": end_path,
            "references": [
                x.strip() for x in re.split(r"[,;，；]+", get(r, "Ingredient IDs")) if x.strip()
            ],
            "source_video_id": get(r, "Source video ID"),
            "sampling_policy": "adaptive-until-pass",
            "priority": 10 if risk.lower() in {"hero", "high"} else 0,
            "prompt": prompt,
            "keep": get(r, "KEEP fixed"),
            "change": get(r, "CHANGE"),
            "motion_path": get(r, "Motion path"),
            "reachability": reach,
            "risk": risk,
            "autonomy": autonomy,
            "candidate_n": n,
            "bridge_reset": get(r, "Bridge/reset"),
            "join_in": get(jin, "Join"),
            "join_in_type": get(jin, "Join type"),
            "join_out": get(jout, "Join"),
            "join_out_type": get(jout, "Join type"),
            "dependencies": [x for x in dep if x],
            "candidate_dir": f"generated/{provider}_candidates/{uid}",
            "approved_output": f"generated/{provider}_approved/{uid}.mp4",
            "human_gate": human_gate,
            "status": "QUEUED" if prompt else "HOLD_PROMPT_MISSING",
        }
        jobs.append(job)
    payload = {
        "schema_version": "3.1",
        "provider": provider,
        "execution_preference": "browser-or-operator"
        if provider == "flow"
        else "agent-tool-or-operator",
        "jobs": jobs,
        "skipped_unapproved": skipped,
        "notes": [
            "Verify live Flow mode/model/duration availability at execution time.",
            "If browser automation is unavailable, use 06p_flow_operator_pack.html.",
        ],
    }
    (root / a.json_output).write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    md = [
        "# Video Job Queue — v3",
        "",
        "Preferred route: authenticated browser/computer-use automation. Fallback: `06p_flow_operator_pack.html`.",
        "",
        "| # | Unit | Mode | Duration | Start | End | Reach | Risk | Autonomy | N | Gate | Status |",
        "|---:|---|---|---:|---|---|---|---|---|---:|---|---|",
    ]
    for j in jobs:
        md.append(
            f"| {j['order']} | {j['unit']} | {j['mode']} | {j['duration_s']} | {j['start_frame_id']} | {j['end_frame_id']} | {j['reachability']} | {j['risk']} | {j['autonomy']} | {j['candidate_n']} | {j['human_gate'] or '-'} | {j['status']} |"
        )
    if skipped:
        md += ["", "Skipped unapproved endpoint rows: " + ", ".join(f"`{x}`" for x in skipped)]
    (root / a.md_output).write_text("\n".join(md) + "\n", encoding="utf-8")
    print(f"Wrote: {root / a.json_output}")
    print(f"Wrote: {root / a.md_output}")
    print(f"Jobs: {len(jobs)} | Skipped: {len(skipped)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
