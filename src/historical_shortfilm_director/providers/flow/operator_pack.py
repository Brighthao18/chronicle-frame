#!/usr/bin/env python3
"""Build a low-friction HTML operator pack for Flow when direct browser automation is unavailable."""

from __future__ import annotations
import argparse
import html
import json
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("project_dir")
    ap.add_argument("--queue", default="06o_flow_job_queue.json")
    ap.add_argument("--output", default="06p_flow_operator_pack.html")
    a = ap.parse_args()
    root = Path(a.project_dir).resolve()
    qp = root / a.queue
    if not qp.exists():
        raise SystemExit(f"Missing: {qp}; run compile_flow_jobs.py first")
    data = json.loads(qp.read_text(encoding="utf-8"))
    jobs = data.get("jobs", [])
    registry = (
        json.loads((root / "06n_asset_registry.json").read_text(encoding="utf-8")).get("assets", {})
        if (root / "06n_asset_registry.json").exists()
        else {}
    )
    css = """body{font-family:system-ui,Segoe UI,sans-serif;max-width:1100px;margin:24px auto;padding:0 16px;background:#f6f7f8;color:#111}.job{background:#fff;border:1px solid #ddd;border-radius:12px;padding:16px;margin:18px 0}.meta{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:8px}.prompt{white-space:pre-wrap;background:#111;color:#eee;padding:12px;border-radius:8px}.path{font-family:ui-monospace,Consolas,monospace;word-break:break-all;background:#f2f2f2;padding:6px}.warn{color:#8a4b00}.copy{padding:6px 10px}"""
    js = """function cp(id){const text=document.getElementById(id).innerText;navigator.clipboard?.writeText(text).catch(()=>{const r=document.createRange();r.selectNodeContents(document.getElementById(id));const s=window.getSelection();s.removeAllRanges();s.addRange(r);});}"""
    cards = []
    for i, j in enumerate(jobs, 1):
        pid = f"p{i}"
        refs = [
            (rid, registry.get(rid, {}).get("path", "MISSING"))
            for rid in j.get("references", [])
            + ([j["source_video_id"]] if j.get("source_video_id") else [])
        ]
        extra = html.escape(
            json.dumps(
                {"ingredients_and_source": refs, "predecessor_jobs": j.get("dependencies", [])},
                ensure_ascii=False,
            )
        )
        cards.append(
            f'''<section class="job"><h2>{i:03d} · {html.escape(j.get("unit", ""))}</h2><div class="meta"><div><b>Mode</b><br>{html.escape(j.get("mode", ""))}</div><div><b>Duration</b><br>{html.escape(str(j.get("duration_s", "")))} s</div><div><b>Candidates</b><br>{j.get("candidate_n", 2)}</div><div><b>Autonomy</b><br>{html.escape(j.get("autonomy", ""))}</div></div><h3>Start frame</h3><div class="path">{html.escape(j.get("start_frame_path") or j.get("start_frame_id") or "-")}</div><h3>End frame</h3><div class="path">{html.escape(j.get("end_frame_path") or j.get("end_frame_id") or "-")}</div><h3>Ingredients / source clip / dependencies</h3><div class="path">{extra}</div><h3>Prompt <button class="copy" onclick="cp('{pid}')">Copy</button></h3><div class="prompt" id="{pid}">{html.escape(j.get("prompt", ""))}</div><h3>Download target</h3><div class="path">{html.escape(j.get("candidate_dir", ""))}</div><p class="warn">N is the maximum candidate count; start with one and continue only if QC needs another. Do not choose by decoration alone; downstream QC ranks endpoint, motion and seam compliance.</p></section>'''
        )
    doc = f"""<!doctype html><html><head><meta charset="utf-8"><title>Flow Operator Pack</title><style>{css}</style><script>{js}</script></head><body><h1>Google Flow Operator Pack — v3</h1><p>This page is only a fallback when authenticated browser automation is unavailable. Creative decisions are already locked upstream.</p>{"".join(cards)}</body></html>"""
    (root / a.output).write_text(doc, encoding="utf-8")
    print(f"Wrote: {root / a.output} ({len(jobs)} jobs)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
