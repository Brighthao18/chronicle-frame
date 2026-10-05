#!/usr/bin/env python3
"""Compile provider-neutral image jobs from the v3 Frame Asset Plan.

Outputs both a human-readable pack and a machine-readable queue. The queue is the
preferred handoff for agents that can call the image tool directly.
"""

from __future__ import annotations
import argparse
import json
import re
from pathlib import Path
from historical_shortfilm_director.runtime.common import plan_allowed, identifier

IMAGE_ROUTES = {
    "IMAGE25_EDIT",
    "IMAGE25_SYNTH",
    "HYBRID_IMAGE25_CODE",
    "IMAGE_SYNTH",
    "IMAGE_EDIT",
    "HYBRID_IMAGE_CODE",
}


def norm(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").strip()).lower()


def cells(line: str) -> list[str]:
    return [c.strip() for c in line.strip().strip("|").split("|")]


def is_sep(row: list[str]) -> bool:
    return bool(row) and all(bool(re.fullmatch(r":?-{3,}:?", c.replace(" ", ""))) for c in row)


def parse_table(path: Path) -> list[dict[str, str]]:
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    for i in range(len(lines) - 1):
        if not lines[i].strip().startswith("|") or not lines[i + 1].strip().startswith("|"):
            continue
        headers = cells(lines[i])
        nh = [norm(h) for h in headers]
        if "frame id" not in nh or not is_sep(cells(lines[i + 1])):
            continue
        out = []
        for ln in lines[i + 2 :]:
            if not ln.strip().startswith("|"):
                break
            c = cells(ln)
            if is_sep(c):
                continue
            c += [""] * max(0, len(headers) - len(c))
            row = {norm(h): c[j] if j < len(c) else "" for j, h in enumerate(headers)}
            if any(row.values()):
                out.append(row)
        return out
    raise ValueError("No Frame Asset Plan table found")


def get(r, name):
    return r.get(norm(name), "").strip()


def approved(v):
    return norm(v) in {"approved", "locked", "yes", "pass", "通过", "已批准", "批准"}


def intval(v, default):
    m = re.search(r"\d+", v or "")
    return int(m.group()) if m else default


def default_n(risk: str, role: str) -> int:
    x = (risk + " " + role).lower()
    return (
        4 if any(k in x for k in ["hero", "high", "opening", "ending", "p3", "主视觉", "高"]) else 2
    )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("project_dir")
    ap.add_argument("--input", default="03d_frame_asset_plan.md")
    ap.add_argument("--output", default="06i_image25_job_pack.md")
    ap.add_argument("--json-output", default="06i_image25_job_queue.json")
    ap.add_argument("--include-unapproved-auto", action="store_true")
    a = ap.parse_args()
    root = Path(a.project_dir).resolve()
    src = root / a.input
    if not src.exists():
        raise SystemExit(f"Missing: {src}")
    rows = parse_table(src)
    jobs = []
    skipped = []
    for row in rows:
        fid = get(row, "Frame ID")
        route = get(row, "Build route").upper()
        if not fid or route not in IMAGE_ROUTES:
            continue
        autonomy = (get(row, "Autonomy") or "AUTO").upper()
        identifier(fid)
        if not plan_allowed(get(row, "Approval"), autonomy):
            skipped.append(fid)
            continue
        risk = get(row, "Risk") or "routine"
        role = get(row, "Role")
        n = intval(get(row, "Candidate N"), default_n(risk, role))
        lock = get(row, "Pixel lock") or "P0_FREE"
        target = get(row, "Output path") or f"assets/frames/{fid}.png"
        job = {
            "job_id": f"IMG25_{fid}",
            "frame_id": fid,
            "route": route,
            "used_by": get(row, "Used by shot/unit"),
            "role": role,
            "model_preference": get(row, "Model preference") or None,
            "sampling_policy": "adaptive-until-pass",
            "priority": 10 if risk.lower() in {"hero", "high"} else 0,
            "references": [
                x.strip()
                for x in re.split(r"[,;，；]+", get(row, "Source/reference IDs"))
                if x.strip()
            ],
            "pixel_lock": lock,
            "risk": risk,
            "autonomy": autonomy,
            "candidate_n": n,
            "keep": get(row, "Exact KEEP"),
            "change": get(row, "Allowed CHANGE"),
            "composition": get(row, "Composition / crop contract"),
            "image_task": get(row, "Image task") or get(row, "Image 2.5 task"),
            "code_post_task": get(row, "Code/post task"),
            "text_policy": get(row, "Text policy")
            or "No important generated text; exact text is post/source overlay.",
            "target_output": target,
            "candidate_dir": f"assets/candidates/{fid}",
            "requires_overlay": route in {"HYBRID_IMAGE25_CODE", "HYBRID_IMAGE_CODE"}
            or lock.upper() in {"P2_EVIDENCE_LOCK", "P3_TEXT_IDENTITY_LOCK"},
            "human_gate": "G2_VISUAL"
            if autonomy == "REVIEW"
            or any(k in (risk + " " + role).lower() for k in ["hero", "opening", "ending", "high"])
            else None,
            "status": "QUEUED",
        }
        jobs.append(job)
    payload = {
        "schema_version": "3.1",
        "provider": "image",
        "execution_preference": "direct-agent-image-tool",
        "jobs": jobs,
        "skipped_unapproved": skipped,
    }
    (root / a.json_output).write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    out = [
        "# Image Job Pack — v3",
        "",
        "Machine queue: `06i_image25_job_queue.json`. If a direct image tool is available, the agent should execute the queue instead of asking the user to manually copy prompts.",
        "",
        "**Execution loop:** generate adaptive candidates → agent visual review → deterministic P2/P3 overlay → QC → register → auto-accept or escalate only top candidates.",
        "",
    ]
    for i, j in enumerate(jobs, 1):
        out += [
            f"## {i:03d} — {j['frame_id']}",
            "",
            f"- Route: `{j['route']}` | Risk: `{j['risk']}` | Autonomy: `{j['autonomy']}` | Candidates: `{j['candidate_n']}`",
            f"- Role / used by: `{j['role']}` / `{j['used_by'] or '-'}`",
            f"- References: `{', '.join(j['references']) or '-'}`",
            f"- Pixel lock: `{j['pixel_lock']}` | Overlay after generation: `{j['requires_overlay']}`",
            f"- Candidate dir: `{j['candidate_dir']}`",
            f"- Approved target: `{j['target_output']}`",
            "",
            "### Paste/direct-call prompt contract",
            "",
            "```text",
            f"PURPOSE\n{j['image_task'] or 'Create the approved visual state for this frame.'}",
            f"\nKEEP\n{j['keep'] or '[derive from approved reference contract]'}",
            f"\nCHANGE\n{j['change'] or '[only the requested visual change]'}",
            f"\nCOMPOSITION\n{j['composition'] or '[follow approved frame composition]'}",
            f"\nTEXT POLICY\n{j['text_policy']}",
            f"\nPOST / SOURCE OVERLAY\n{j['code_post_task'] or '[none]'}",
            "```",
            "",
            "Acceptance: choose the candidate that best satisfies the contract, not the most decorative image. P3 identity/text failures are hard rejects.",
            "",
        ]
    if skipped:
        out += ["## Skipped pending rows", "", ", ".join(f"`{x}`" for x in skipped), ""]
    (root / a.output).write_text("\n".join(out), encoding="utf-8")
    print(f"Wrote: {root / a.output}")
    print(f"Wrote: {root / a.json_output}")
    print(f"Jobs: {len(jobs)} | Skipped: {len(skipped)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
