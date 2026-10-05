"""The authoring brief for one code job: contract, exact format, inputs and prior reviews.

The same brief serves an interactive Claude Code session (`hsd code brief`) and a headless
`claude -p` session (`hsd code author`). It embeds the scene format reference, so an author
needs nothing else from this repository to write a valid program.
"""

from __future__ import annotations

from pathlib import Path

import historical_shortfilm_director.runtime.engine as runtime
from historical_shortfilm_director.providers.code.scene import FORMAT_REFERENCE
from historical_shortfilm_director.runtime.common import load, local

PROVENANCE_FIELDS = ("origin", "historical_status", "provenance", "type")

PYTHON_CONTRACT = """\
This project also allows Python render programs (`.py`), executed with this runtime's
interpreter in isolated mode, a minimal environment and a time limit. The program receives
one argument: a JSON context file with `width`, `height`, `fps`, `duration_s`,
`frame_count`, `frame_indices`, `frames_dir`, `inputs` ({ID: {path, sha256}}) and `seed`.
It must write exactly `frames_dir/{index:06d}.png` for every requested index, each
`width` x `height`, and nothing else there. Seed any randomness from `seed`. Prefer a
scene unless the shot genuinely needs procedural drawing, and move archival pixels only.
"""


def cell(value, limit=160):
    text = " ".join(str(value).split())
    text = text.replace("|", "/")
    return text if len(text) <= limit else text[: limit - 1] + "…"


def image_size(path):
    try:
        from PIL import Image

        with Image.open(path) as image:
            return f"{image.width}x{image.height}"
    except (ImportError, OSError, ValueError):
        return "not an image" if Path(path).suffix.lower() in {".ttf", ".otf"} else "unknown"


def joins_for(root, unit):
    graph = load(Path(root) / "03_production_graph.json", {}) or {}
    rows = []
    for join in graph.get("joins", []):
        if unit not in (join.get("from"), join.get("to")):
            continue
        side = "Incoming" if join.get("to") == unit else "Outgoing"
        details = [
            f"{label} {join[key]}"
            for key, label in (
                ("seam", "seam frame"),
                ("exit", "exit state:"),
                ("entry", "entry state:"),
                ("direction", "screen direction:"),
                ("handles", "handles:"),
                ("fallback", "fallback:"),
            )
            if join.get(key)
        ]
        rows.append(
            f"- {side} join `{join.get('id')}` ({join.get('type')})"
            + (": " + "; ".join(cell(item) for item in details) if details else "")
        )
    return rows


def history(root, k):
    """Reviews of earlier attempts and invalid headless scenes for this job revision."""
    execution = runtime.state(root)
    entry = execution["jobs"].get(k, {})
    tokens = {c["sha256"]: c.get("token") for c in entry.get("candidates", [])}
    receipts = {a["token"]: a.get("receipt", {}) for a in entry.get("attempts", [])}
    lines = []
    for review in entry.get("reviews", []):
        token = tokens.get(review.get("sha256"))
        evidence = str(receipts.get(token, {}).get("evidence") or "")
        bundle = {}
        if evidence.startswith("work/code_renders/"):
            try:
                bundle = load(local(root, evidence), {}) or {}
            except (ValueError, OSError):
                bundle = {}
        sheet = bundle.get("contact_sheet", {}).get("path")
        lines.append(
            f"- Attempt `{token}`: {review.get('verdict')}"
            + (f" `{review['failure_code']}`" if review.get("failure_code") else "")
            + f", score {review.get('score')}."
            + (f" Contact sheet: `{sheet}`." if sheet else "")
            + f" Reviewer notes: {cell(review.get('notes', ''), 600)}"
        )
    for session in execution.get("authoring", []):
        if session.get("job_id") == k and session.get("program_problems"):
            problems = "; ".join(session["program_problems"][:8])
            lines.append(
                f"- Headless session `{session['token']}` wrote an invalid scene: {cell(problems, 600)}"
            )
    return lines


def build_brief(root, k, program_path, input_files=None, python_allowed=False):
    """Markdown brief; `input_files` maps input IDs to files the author can open."""
    from historical_shortfilm_director.providers.code.render import job_context

    root = Path(root).resolve()
    job, refs, assets, settings = job_context(root, k)
    registry = load(root / "06n_asset_registry.json", {"assets": {}})["assets"]
    fps = settings["fps"]
    last = (settings["frames"] - 1) / fps
    lines = [
        f"# Render brief — {k} (unit {job.get('unit')})",
        "",
        "You are writing a deterministic render program for one shot of an evidence-grounded"
        " historical short film. The ChronicleFrame runtime renders it locally, records a"
        " receipt, and a reviewer judges the result against this contract. Generated media"
        " never becomes historical evidence.",
        "",
        "## Contract",
        "",
        job.get("prompt") or "[No compiled contract; ask for the unit's action and camera.]",
        "",
    ]
    for label, key in (
        ("KEEP", "keep"),
        ("CHANGE", "change"),
        ("Motion path", "motion_path"),
        ("Risk / autonomy", "risk"),
    ):
        if job.get(key):
            value = job[key] if key != "risk" else f"{job['risk']} / {job.get('autonomy')}"
            lines.append(f"- {label}: {cell(value, 400)}")
    if job.get("human_gate"):
        lines.append(f"- Acceptance also needs the human gate `{job['human_gate']}`.")
    lines += joins_for(root, job.get("unit"))
    lines += [
        "",
        "## Format",
        "",
        f"- {settings['width']}x{settings['height']} at {fps:g} fps: {settings['frames']} frames"
        f" covering {settings['duration_s']:g} s. Frame i is shown at t = i / {fps:g}; the last"
        f" frame is at t = {last:.3f} s.",
        f"- The edit uses {settings['use_in_s']:g}-{settings['use_out_s']:g} s; keep the decisive"
        " action inside it and let the handles outside it stay calm.",
    ]
    if job.get("start_frame_id"):
        lines.append(
            f"- The first frame must reproduce start frame `{job['start_frame_id']}`"
            " (cover fit, scale 1, centred) because acceptance compares the endpoints."
        )
    if job.get("end_frame_id"):
        lines.append(f"- The last frame must settle on end frame `{job['end_frame_id']}`.")
    lines += [
        "",
        "## Inputs",
        "",
        "| ID | File | Size | Status | Provenance |",
        "| --- | --- | --- | --- | --- |",
    ]
    for ref in refs:
        record = registry.get(ref["asset_id"], {})
        provenance = "; ".join(
            f"{field}: {cell(record[field], 120)}"
            for field in PROVENANCE_FIELDS
            if record.get(field)
        )
        visible = (input_files or {}).get(ref["asset_id"])
        lines.append(
            f"| `{ref['asset_id']}` | {f'`{visible}`' if visible else 'not shared'} |"
            f" {image_size(assets[ref['asset_id']])} | {record.get('status', '?')} |"
            f" {provenance or '-'} |"
        )
    if not refs:
        lines.append("| - | - | - | - | This job has no inputs: use text and rect layers only. |")
    if input_files is None and refs:
        lines += [
            "",
            "Input images are not shared with this session. Compose from their sizes and notes;"
            " the contact sheet of the render will show the result to the reviewer.",
        ]
    lines += [
        "",
        "## Rules",
        "",
        f"1. Write exactly one file: `{program_path}`. Create or change nothing else.",
        "2. Use only the inputs listed above. Move, scale, rotate and fade them; never try to"
        " synthesize, retouch, recolour or restore imagery.",
        "3. On-screen text must be exact wording the contract states or the evidence ledger"
        " allows. Add no dates, names, places or claims of your own.",
        "4. Key every animated property on the first key. A cover-fit image must cover the"
        " frame for the whole clip; the renderer reports frames where it does not.",
        "5. One primary motion, eased (`in_out`) unless the contract asks otherwise. If a join"
        " needs a stable seam, keep the first and last 0.2 s calm.",
    ]
    previous = history(root, k)
    if previous:
        lines += ["", "## Previous attempts", "", *previous]
    lines += ["", "## Scene format (hsd-scene/1)", "", FORMAT_REFERENCE.rstrip()]
    if python_allowed:
        lines += ["", "## Python programs (enabled in this project)", "", PYTHON_CONTRACT.rstrip()]
    return "\n".join(lines) + "\n"


def write_brief(root, k):
    """Write and return the interactive brief, saved under work/code_briefs/."""
    from historical_shortfilm_director.providers.code.render import job_context, render_policy

    root = Path(root).resolve()
    job, refs, _, _ = job_context(root, k)
    text = build_brief(
        root,
        k,
        program_path=f"programs/{job.get('unit') or k}.scene.json",
        input_files={r["asset_id"]: r["path"] for r in refs},
        python_allowed=render_policy(root)["python_programs"],
    )
    path = local(root, "work/code_briefs") / f"{k}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")
    return path, text
