"""Compile one production graph into consistent frame, shot, join and preview plans.

No generation or approval occurs here. Work is staged before a recoverable commit;
manual edits to previously compiled files are never silently replaced.
"""

from __future__ import annotations
import argparse
import json
import math
from pathlib import Path
from historical_shortfilm_director.runtime.common import (
    load,
    save,
    local,
    identifier,
    sha,
    digest,
    mutation,
)

GRAPH = "03_production_graph.json"
RECEIPT = "03w_graph_compile_receipt.json"
FRAME_FIELDS = {
    "id",
    "route",
    "refs",
    "role",
    "risk",
    "autonomy",
    "candidate_n",
    "pixel_lock",
    "task",
    "keep",
    "change",
    "composition",
    "post",
    "text_policy",
    "output",
    "model",
    "preview_path",
}
UNIT_FIELDS = {
    "id",
    "shot",
    "mode",
    "start",
    "end",
    "ingredients",
    "source_video",
    "duration_s",
    "edit_s",
    "in_s",
    "risk",
    "autonomy",
    "candidate_n",
    "keep",
    "change",
    "action",
    "camera",
    "environment",
    "light",
    "focus",
    "choreography",
    "audio",
    "reachability",
    "bridge",
    "story_beat",
    "preview_frame",
    "preview_motion",
}
JOIN_FIELDS = {
    "id",
    "from",
    "to",
    "type",
    "seam",
    "exit",
    "entry",
    "direction",
    "handles",
    "fallback",
    "reset",
    "audio",
    "overlay",
}
MODES = {"FRAMES", "START_FRAME", "INGREDIENTS", "EXTEND", "OMNI_EDIT", "T2V", "SKIP_FLOW"}
ROUTES = {
    "SOURCE_LOCKED",
    "CODE_COMPOSITE",
    "IMAGE25_EDIT",
    "IMAGE25_SYNTH",
    "HYBRID_IMAGE25_CODE",
    "POST_GRAPHIC",
    "IMAGE_SYNTH",
    "IMAGE_EDIT",
    "HYBRID_IMAGE_CODE",
}


def finite(value, name, minimum=0):
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not math.isfinite(value)
        or value < minimum
    ):
        raise ValueError(f"{name} must be a finite number >= {minimum}")
    return float(value)


def fields(row, allowed, name):
    extra = set(row) - allowed
    if extra:
        raise ValueError(f"{name}: unknown fields {sorted(extra)}")


def validate(root, g):
    fields(
        g,
        {"schema_version", "title", "external_refs", "frames", "units", "joins", "preview"},
        "graph",
    )
    if g.get("schema_version") != "3.2":
        raise ValueError("Graph schema_version must be 3.2")
    if not g.get("frames") or not g.get("units"):
        raise ValueError("Graph needs actual frames and units")
    ids = set()
    frame_ids = set()
    unit_ids = set()
    for kind, allowed in [("frames", FRAME_FIELDS), ("units", UNIT_FIELDS), ("joins", JOIN_FIELDS)]:
        for row in g.get(kind, []):
            fields(row, allowed, kind)
            k = identifier(row["id"])
            if k in ids:
                raise ValueError("Duplicate graph ID: " + k)
            ids.add(k)
            if kind == "frames":
                frame_ids.add(k)
            if kind == "units":
                unit_ids.add(k)
    external = g.get("external_refs", [])
    if not isinstance(external, list) or len(set(external)) != len(external):
        raise ValueError("external_refs must be unique IDs")
    for r in external:
        identifier(r)
        if r in ids:
            raise ValueError("External source ID collides with generated graph: " + r)
    refs = frame_ids | set(external)
    for f in g["frames"]:
        if f.get("route") not in ROUTES:
            raise ValueError("Unknown image route: " + f["id"])
        if not f.get("task") and f["route"].startswith(("IMAGE", "HYBRID")):
            raise ValueError("Image task missing: " + f["id"])
        if not isinstance(f.get("refs", []), list):
            raise ValueError("Frame refs must be a list")
        if any(r not in refs for r in f.get("refs", [])):
            raise ValueError("Undeclared frame reference: " + f["id"])
        if f["route"] in {
            "IMAGE25_EDIT",
            "HYBRID_IMAGE25_CODE",
            "IMAGE_EDIT",
            "HYBRID_IMAGE_CODE",
        } and not f.get("refs"):
            raise ValueError("Edit references missing: " + f["id"])
        if f.get("risk", "routine") not in {"routine", "medium", "high", "hero"}:
            raise ValueError("Invalid risk")
        if f.get("autonomy", "AUTO") not in {"AUTO", "REVIEW", "BLOCK"}:
            raise ValueError("Invalid autonomy")
        if f.get("pixel_lock", "P0_FREE") not in {
            "P0_FREE",
            "P1_GEOMETRY_LOCK",
            "P2_EVIDENCE_LOCK",
            "P3_TEXT_IDENTITY_LOCK",
        }:
            raise ValueError("Invalid pixel lock")
        local(root, f.get("output", f"assets/frames/{f['id']}.png"))
        if f.get("preview_path"):
            local(root, f["preview_path"])
        n = f.get("candidate_n", 4 if f.get("risk") in {"hero", "high"} else 2)
        if isinstance(n, bool) or not isinstance(n, int) or not 1 <= n <= 16:
            raise ValueError("candidate_n must be 1..16")
    prior = set()
    joins = g.get("joins", [])
    pairs = {}
    for join in joins:
        pair = (join["from"], join["to"])
        if pair in pairs:
            raise ValueError("Duplicate join pair")
        if not set(pair) <= unit_ids:
            raise ValueError("Join references unknown unit")
        if join.get("type") not in {
            "EXACT_SEAM",
            "FLOW_EXTEND",
            "MATCH_CUT",
            "OCCLUSION_RESET",
            "GRAPHIC_RESET",
            "HARD_CUT",
        }:
            raise ValueError("Unknown join type")
        if not join.get("fallback"):
            raise ValueError("Explicit fallback required: " + join["id"])
        pairs[pair] = join
    expected = {(a["id"], b["id"]) for a, b in zip(g["units"], g["units"][1:])}
    if set(pairs) != expected:
        raise ValueError("Exactly one explicit join per adjacent unit is required")
    for u in g["units"]:
        if u.get("mode") not in MODES:
            raise ValueError("Unknown video mode")
        duration = finite(u["duration_s"], "duration_s", 0.04)
        edit = finite(u["edit_s"], "edit_s", 0.04)
        tin = finite(u.get("in_s", 0), "in_s")
        if tin + edit > duration + 1e-8:
            raise ValueError("Trim exceeds generation duration: " + u["id"])
        if u.get("autonomy", "AUTO") not in {"AUTO", "REVIEW", "BLOCK"}:
            raise ValueError("Invalid unit autonomy")
        if u.get("risk", "routine") not in {"routine", "medium", "high", "hero"}:
            raise ValueError("Invalid unit risk")
        n = u.get("candidate_n", 4 if u.get("risk") in {"hero", "high"} else 2)
        if isinstance(n, bool) or not isinstance(n, int) or not 1 <= n <= 16:
            raise ValueError("Invalid candidate_n")
        for key in ("start", "end", "preview_frame"):
            if u.get(key) and u[key] not in refs:
                raise ValueError("Unknown " + key + ": " + u[key])
        if any(r not in refs for r in u.get("ingredients", [])):
            raise ValueError("Unknown ingredient")
        if u["mode"] in {"START_FRAME", "FRAMES"} and not u.get("start"):
            raise ValueError("Start required")
        if u["mode"] == "FRAMES" and not u.get("end"):
            raise ValueError("End required")
        if u["mode"] == "INGREDIENTS" and not u.get("ingredients"):
            raise ValueError("Ingredients required")
        if u.get("source_video") and u["source_video"] not in prior | set(external):
            raise ValueError("Source video must be external or earlier unit")
        incoming = next((j for j in joins if j["to"] == u["id"]), {})
        if (
            u["mode"] == "EXTEND"
            and not u.get("source_video")
            and incoming.get("type") != "FLOW_EXTEND"
        ):
            raise ValueError("Extend needs explicit predecessor/source")
        if u["mode"] == "OMNI_EDIT" and not u.get("source_video"):
            raise ValueError("Video edit needs source_video")
        if u["mode"] != "SKIP_FLOW" and (not u.get("action") or not u.get("camera")):
            raise ValueError("Concrete action and camera required: " + u["id"])
        if u["mode"] == "FRAMES" and u.get("reachability") == "R-D":
            raise ValueError("Split/reset an R-D morph instead of direct Frames")
        if u.get("preview_motion", "HOLD") not in {
            "HOLD",
            "PUSH_IN",
            "PULL_OUT",
            "PAN_LEFT",
            "PAN_RIGHT",
            "FADE_TO_BLACK",
        }:
            raise ValueError("Unsupported preview motion")
        prior.add(u["id"])
    by = {u["id"]: u for u in g["units"]}
    for j in joins:
        if j["type"] == "EXACT_SEAM":
            if (
                not j.get("seam")
                or by[j["from"]].get("end") != j["seam"]
                or by[j["to"]].get("start") != j["seam"]
            ):
                raise ValueError("EXACT_SEAM must bind the same end/start state")
    graph = {f["id"]: list(f.get("refs", [])) for f in g["frames"]}
    for u in g["units"]:
        graph[u["id"]] = [
            x
            for x in [
                u.get("start"),
                u.get("end"),
                u.get("source_video"),
                *u.get("ingredients", []),
            ]
            if x
        ]
        graph[u["id"]] += [
            j["from"] for j in joins if j["to"] == u["id"] and j["type"] == "FLOW_EXTEND"
        ]
    done = set()
    visiting = set()

    def visit(k):
        if k in visiting:
            raise ValueError("Dependency cycle: " + k)
        if k in done or k not in graph:
            return
        visiting.add(k)
        for child in graph[k]:
            visit(child)
        visiting.remove(k)
        done.add(k)

    for k in graph:
        visit(k)
    preview = g.get("preview", {})
    fields(preview, {"width", "height", "fps", "audio"}, "preview")
    for key, default in [("width", 640), ("height", 360), ("fps", 25)]:
        finite(preview.get(key, default), key, 1)
    for key in ("width", "height"):
        v = preview.get(key, 640 if key == "width" else 360)
        if int(v) != v or int(v) % 2:
            raise ValueError("Preview dimensions must be even integers")
    if preview.get("audio"):
        local(root, preview["audio"])
    return g


def md(rows, headers):
    def cell(v):
        s = str(v)
        # Old table readers cannot round-trip pipes/newlines safely. Fail, never silently change intent.
        if "|" in s or "\n" in s or "\r" in s:
            raise ValueError("Plan cells must be single-line and cannot contain |")
        return s

    return (
        "\n".join(
            ["| " + " | ".join(headers) + " |", "| " + " | ".join("---" for _ in headers) + " |"]
            + ["| " + " | ".join(cell(r.get(h, "")) for h in headers) + " |" for r in rows]
        )
        + "\n"
    )


def compile_files(g):
    frames = []
    endpoints = []
    blueprints = []
    joins = []
    timeline = []
    for f in g["frames"]:
        used = [
            u["id"]
            for u in g["units"]
            if f["id"]
            in [u.get("start"), u.get("end"), u.get("preview_frame"), *u.get("ingredients", [])]
        ]
        frames.append(
            {
                "Frame ID": f["id"],
                "Used by shot/unit": ",".join(used),
                "Role": f.get("role", "STATE"),
                "Build route": f["route"],
                "Source/reference IDs": ",".join(f.get("refs", [])),
                "Pixel lock": f.get("pixel_lock", "P0_FREE"),
                "Risk": f.get("risk", "routine"),
                "Autonomy": f.get("autonomy", "AUTO"),
                "Candidate N": f.get("candidate_n", 4 if f.get("risk") in {"hero", "high"} else 2),
                "Exact KEEP": f.get("keep", ""),
                "Allowed CHANGE": f.get("change", ""),
                "Composition / crop contract": f.get("composition", ""),
                "Image 2.5 task": f.get("task", ""),
                "Code/post task": f.get("post", ""),
                "Text policy": f.get(
                    "text_policy", "Exact historical text is a source/post layer."
                ),
                "Output path": f.get("output", f"assets/frames/{f['id']}.png"),
                "Model preference": f.get("model", ""),
                "Approval": "READY",
            }
        )
    prompt_modes = {
        "FRAMES": "FRAMES_PATH",
        "START_FRAME": "I2V_BALANCED",
        "INGREDIENTS": "I2V_BALANCED",
        "EXTEND": "EXTEND_CONTINUITY",
        "OMNI_EDIT": "OMNI_EDIT_LOCAL",
        "T2V": "T2V_RICH",
        "SKIP_FLOW": "SKIP_FLOW",
    }
    for u in g["units"]:
        endpoints.append(
            {
                "Unit": u["id"],
                "Parent shot": u.get("shot", u["id"]),
                "Flow mode": u["mode"],
                "Duration": u["duration_s"],
                "Final edit duration": u["edit_s"],
                "Use in": u.get("in_s", 0),
                "Use out": u.get("in_s", 0) + u["edit_s"],
                "Start frame ID": u.get("start", ""),
                "End frame ID": u.get("end", ""),
                "End frame needed?": "yes" if u.get("end") else "no",
                "Ingredient IDs": ",".join(u.get("ingredients", [])),
                "Source video ID": u.get("source_video", ""),
                "KEEP fixed": u.get("keep", ""),
                "CHANGE": u.get("change", ""),
                "Motion path": u.get("action", ""),
                "Reachability": u.get("reachability", "R-A"),
                "Risk": u.get("risk", "routine"),
                "Autonomy": u.get("autonomy", "AUTO"),
                "Candidate N": u.get("candidate_n", 4 if u.get("risk") in {"hero", "high"} else 2),
                "Bridge/reset": u.get("bridge", ""),
                "Approval": "READY",
            }
        )
        blueprints.append(
            {
                "Unit": u["id"],
                "Prompt mode": prompt_modes[u["mode"]],
                "Story beat": u.get("story_beat", ""),
                "Visual premise": u.get("story_beat", ""),
                "Anchor facts": u.get("keep", ""),
                "ONE primary action": u.get("action", ""),
                "Environment response": u.get("environment", ""),
                "Camera grammar": u.get("camera", ""),
                "Focus / depth": u.get("focus", ""),
                "Light / atmosphere": u.get("light", ""),
                "Temporal choreography": u.get("choreography", ""),
                "Audio intent": u.get("audio", ""),
                "Continuity locks": u.get("keep", ""),
                "Post-only": "exact text",
                "Density target": "adaptive",
                "Approval": "READY",
            }
        )
        timeline.append(
            {
                "unit": u["id"],
                "frame_id": u.get("preview_frame") or u.get("start"),
                "duration_s": u["edit_s"],
                "motion": u.get("preview_motion", "HOLD"),
            }
        )
    for j in g.get("joins", []):
        joins.append(
            {
                "Join": j["id"],
                "From unit": j["from"],
                "To unit": j["to"],
                "Join type": j["type"],
                "Shared seam frame": j.get("seam", ""),
                "Exit state": j.get("exit", ""),
                "Entry state": j.get("entry", ""),
                "Screen direction": j.get("direction", ""),
                "Handles": j.get("handles", "0"),
                "Fallback": j["fallback"],
                "Reset/occluder": j.get("reset", ""),
                "Audio bridge": j.get("audio", ""),
                "Post overlay at join": j.get("overlay", ""),
                "Approval": "READY",
            }
        )
    result = {
        "03d_frame_asset_plan.md": md(frames, list(frames[0])),
        "05f_shot_endpoint_plan.md": md(endpoints, list(endpoints[0])),
        "04c_flow_prompt_blueprints.md": md(blueprints, list(blueprints[0])),
        "05h_join_contracts.md": md(
            joins,
            list(joins[0])
            if joins
            else ["Join", "From unit", "To unit", "Join type", "Shared seam frame", "Approval"],
        ),
        "05v_animatic_timeline.json": json.dumps(
            {
                "schema_version": "3.2",
                "status": "PREVIEW_ONLY",
                "settings": g.get("preview", {}),
                "frames": {f["id"]: f.get("preview_path") for f in g["frames"]},
                "units": timeline,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
    }
    return result


def compile_graph(root, graph_path=GRAPH):
    root = Path(root).resolve()
    src = local(root, graph_path)
    g = validate(root, load(src))
    generated = compile_files(g)
    signature = digest(g)
    previous = load(root / RECEIPT, {})
    old_hashes = previous.get("outputs", {})
    with mutation(root):
        for name in generated:
            p = local(root, name)
            if p.exists() and name in old_hashes and sha(p) != old_hashes[name]:
                raise ValueError(
                    "Compiled plan was manually edited; reconcile into graph before recompiling: "
                    + name
                )
            if p.exists() and name not in old_hashes:
                # Only pristine init_project templates may be adopted automatically.
                from historical_shortfilm_director.project import FILES

                legacy = load(
                    Path(__file__).resolve().parents[1] / "data/legacy-templates.json", {}
                )
                pristine = {FILES.get(name), legacy.get(name)}
                if p.read_text(encoding="utf-8") not in pristine:
                    raise ValueError("Existing authored plan is not owned by compiler: " + name)
        if previous.get("graph_hash") == signature and all(
            local(root, n).exists() and sha(local(root, n)) == h for n, h in old_hashes.items()
        ):
            return {**previous, "unchanged": True}
        dest = local(root, "work/graph_versions") / signature[:16]
        dest.mkdir(parents=True, exist_ok=True)
        backups = {}
        try:
            for name, text in generated.items():
                p = local(root, name)
                backups[name] = p.read_bytes() if p.exists() else None
                if p.exists():
                    before = dest / (name + ".before")
                    if not before.exists():
                        before.write_bytes(backups[name])
                p.write_text(text, encoding="utf-8", newline="\n")
            report = {
                "schema_version": "3.2",
                "graph_hash": signature,
                "source_sha256": sha(src),
                "outputs": {n: sha(local(root, n)) for n in generated},
                "frame_count": len(g["frames"]),
                "unit_count": len(g["units"]),
                "planned_duration_s": sum(u["edit_s"] for u in g["units"]),
            }
            save(root / RECEIPT, report)
        except Exception:
            for name, data in backups.items():
                p = local(root, name)
                if data is None:
                    p.unlink(missing_ok=True)
                else:
                    p.write_bytes(data)
            raise
    return report


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("project_dir")
    p.add_argument("--graph", default=GRAPH)
    a = p.parse_args()
    print(json.dumps(compile_graph(a.project_dir, a.graph), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
