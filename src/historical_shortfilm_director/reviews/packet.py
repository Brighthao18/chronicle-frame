"""Build one linked HTML review board from actual candidates and recorded decisions."""

import argparse
import html
from pathlib import Path
from urllib.parse import quote
from historical_shortfilm_director.runtime.common import local, sha, save, relative
from historical_shortfilm_director.runtime.engine import jobs, state


def build(root, gate):
    js = jobs(root)
    st = state(root)
    cards = []
    artifacts = []
    for k, j in js.items():
        if gate != "ALL" and j.get("human_gate") != gate:
            continue
        e = st["jobs"].get(k, {})
        reviews = {r["sha256"]: r for r in e.get("reviews", [])}
        items = sorted(
            e.get("candidates", []),
            key=lambda c: float(reviews.get(c["sha256"], {}).get("score", -1)),
            reverse=True,
        )[:2]
        for c in items:
            p = local(root, c["path"])
            if not p.is_file() or sha(p) != c["sha256"]:
                raise ValueError("Candidate missing/changed: " + c["path"])
            url = quote("../" + relative(root, p), safe="/")
            r = reviews.get(c["sha256"], {})
            media = (
                f'<img src="{url}" alt="{html.escape(k)}">'
                if c.get("kind") == "image"
                else f'<video src="{url}" controls preload="metadata"></video>'
            )
            cards.append(
                f"<article><h2>{html.escape(k)}</h2>{media}<p>{html.escape(str(r.get('verdict', 'UNREVIEWED')))} · {html.escape(str(r.get('score', '—')))}</p><p>{html.escape(str(r.get('notes', 'Content review still required')))}</p><code>{c['sha256']}</code></article>"
            )
            artifacts.append({"path": relative(root, p), "sha256": c["sha256"]})
    if not cards:
        raise ValueError("No real candidates for this review gate")
    out = local(root, "reviews") / (gate.lower() + "_review.html")
    out.parent.mkdir(parents=True, exist_ok=True)
    body = (
        '<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>Production review</title><style>body{background:#131920;color:#eee;font-family:SimSun,serif;margin:32px}main{display:grid;grid-template-columns:repeat(auto-fit,minmax(320px,1fr));gap:24px}article{background:#202b36;padding:20px;border-radius:10px}img,video{width:100%;max-height:65vh;object-fit:contain}code{word-break:break-all;font-family:monospace}h1{font-size:28px}</style><h1>'
        + html.escape(gate)
        + " · 候选审阅</h1><p>请按叙事、史实、构图与衔接判断。图像生成不能证明史实。代理已筛选前两名；确认以文件哈希绑定。</p><main>"
        + "".join(cards)
        + "</main></html>"
    )
    out.write_text(body, encoding="utf-8")
    save(out.with_suffix(".json"), {"gate": gate, "artifacts": artifacts, "board_sha256": sha(out)})
    return out


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("project_dir")
    p.add_argument("--gate", choices=["G2_VISUAL", "G3_HERO_MOTION", "ALL"], default="G2_VISUAL")
    a = p.parse_args()
    print(build(Path(a.project_dir).resolve(), a.gate))
