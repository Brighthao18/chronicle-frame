"""Durable agent-tool bridge for image/Flow jobs; never pretends to call a provider.

sync -> next -> claim -> actual agent tool/UI operation -> receipt -> ingest ->
review -> accept. Every claim reserves ONE output; ambiguous requests remain active.
"""

from __future__ import annotations
import argparse
import json
import shutil
import uuid
from pathlib import Path
from historical_shortfilm_director.runtime.common import (
    now,
    load,
    save,
    digest,
    sha,
    local,
    relative,
    identifier,
    mutation,
    media_check,
    gate_status,
    gate_covers,
    register,
)

from historical_shortfilm_director.providers.capabilities import capability

STATE = "06t_execution_state.json"
QUEUES = [("06i_image25_job_queue.json", "image"), ("06o_flow_job_queue.json", "flow")]
VIDEO_PROVIDERS = {"flow", "video", "code"}
NEXT_STEP = {
    "code": "Author a scene for this contract, then run `hsd code render` with this job; it records the receipt and ingests the output. Do not hand code jobs to an external generator.",
}
HANDOFF_STEP = "Execute actual agent image tool or observed Flow UI; record receipt; import real returned file. Do not auto-resubmit after timeout."
CHECKS = [
    "contract",
    "identity_geometry",
    "text_evidence",
    "composition",
    "continuity",
    "historical",
]
FAILURES = {
    "CONTENT_DRIFT",
    "IDENTITY_GEOMETRY_DRIFT",
    "TEXT_EVIDENCE_DRIFT",
    "MOTION_PATH_FAIL",
    "CAMERA_FAIL",
    "ENDPOINT_SNAP",
    "SEAM_FAIL",
    "LOCAL_ARTIFACT",
    "AUDIO_FAIL",
    "TECHNICAL_FAIL",
    "PROVIDER_FAILED",
}


def state(root):
    return load(
        Path(root) / STATE, {"schema_version": "3.1", "jobs": {}, "history": [], "events": []}
    )


def event(s, action, **details):
    s["events"].append({"time": now(), "action": action, **details})


def jobs(root):
    out = {}
    for q, provider in QUEUES:
        for j in load(Path(root) / q, {"jobs": []})["jobs"]:
            j = dict(j, provider=j.get("provider", provider))
            jid = identifier(j["job_id"])
            if jid in out:
                raise ValueError("Duplicate job: " + jid)
            if j.get("autonomy") not in {"AUTO", "REVIEW", "BLOCK"}:
                raise ValueError("Invalid autonomy: " + jid)
            if not 1 <= int(j.get("candidate_n", 2)) <= 16:
                raise ValueError("Candidate cap must be 1..16")
            local(root, j["candidate_dir"])
            local(root, j.get("target_output") or j.get("approved_output"))
            out[jid] = j
    return out


def ref_ids(j):
    refs = list(j.get("references", []))
    refs += [j.get(k) for k in ("start_frame_id", "end_frame_id", "source_video_id") if j.get(k)]
    return list(dict.fromkeys(refs))


def dependencies(j):
    return [
        d if d.startswith(("IMG25_", "FLOW_")) else "FLOW_" + d for d in j.get("dependencies", [])
    ]


def inputs(root, j):
    reg = load(Path(root) / "06n_asset_registry.json", {"assets": {}})["assets"]
    found = []
    errors = []
    for aid in ref_ids(j):
        item = reg.get(aid)
        if not item:
            errors.append("MISSING_REFERENCE:" + aid)
            continue
        p = local(root, item["path"])
        if item.get("status") not in {"APPROVED", "SOURCE_VERIFIED"}:
            errors.append("REFERENCE_NOT_READY:" + aid)
            continue
        if not p.is_file() or sha(p) != item.get("sha256"):
            errors.append("REFERENCE_CHANGED:" + aid)
            continue
        found.append({"asset_id": aid, "path": relative(root, p), "sha256": item["sha256"]})
    return found, errors


def fingerprint(root, j, s, _stack=None):
    stack = set() if _stack is None else set(_stack)
    if j["job_id"] in stack:
        raise ValueError("Dependency cycle while checking current inputs")
    stack.add(j["job_id"])
    refs, errors = inputs(root, j)
    current = jobs(root)
    producers = {x.get("frame_id") or x.get("unit"): k for k, x in current.items()}

    def fresh(producer):
        entry = s["jobs"].get(producer, {})
        if producer not in current or entry.get("spec_hash") != digest(current[producer]):
            return False
        fp, _, upstream = fingerprint(root, current[producer], s, stack)
        return not upstream and fp == entry.get("input_hash") and valid_selected(root, entry)

    for r in refs:
        producer = producers.get(r["asset_id"])
        if producer:
            entry = s["jobs"].get(producer, {})
            if (
                entry.get("status") != "ACCEPTED"
                or entry.get("selected", {}).get("sha256") != r["sha256"]
            ):
                errors.append("PRODUCER_NOT_ACCEPTED:" + producer)
            elif not fresh(producer):
                errors.append("PRODUCER_STALE:" + producer)
    deps = {}
    for d in dependencies(j):
        entry = s["jobs"].get(d, {})
        deps[d] = entry.get("selected", {}).get("sha256")
        if entry.get("status") != "ACCEPTED":
            errors.append("DEPENDENCY:" + d)
        elif not valid_selected(root, entry):
            errors.append("DEPENDENCY_CHANGED:" + d)
        elif not fresh(d):
            errors.append("DEPENDENCY_STALE:" + d)
    return digest({"spec": j, "refs": refs, "dependencies": deps}), refs, errors


def valid_selected(root, entry):
    a = entry.get("selected", {})
    p = local(root, a["path"]) if a.get("path") else None
    return bool(p and p.is_file() and sha(p) == a.get("sha256"))


def sync(root):
    current = jobs(root)
    # Detect cycles through both explicit clip dependencies and generated frame references.
    producers = {j.get("frame_id") or j.get("unit"): k for k, j in current.items()}
    graph = {
        k: dependencies(j) + [producers[r] for r in ref_ids(j) if r in producers]
        for k, j in current.items()
    }
    visiting = set()
    done = set()
    order = []

    def visit(k):
        if k in visiting:
            raise ValueError("Dependency cycle: " + k)
        if k in done:
            return
        visiting.add(k)
        for d in graph.get(k, []):
            if d not in current:
                raise ValueError("Unknown dependency: " + d)
            visit(d)
        visiting.remove(k)
        done.add(k)
        order.append(k)

    for k in current:
        visit(k)
    with mutation(root):
        s = state(root)
        for k, e in list(s["jobs"].items()):
            if k not in current:
                if e["status"] == "ACTIVE":
                    raise ValueError("Cannot remove active job: " + k)
                s["history"].append({"job_id": k, **e})
                del s["jobs"][k]
        for k, j in current.items():
            old = s["jobs"].get(k)
            spec_hash = digest(j)
            if old and old["spec_hash"] == spec_hash:
                continue
            if old:
                if old["status"] == "ACTIVE":
                    raise ValueError("Reconcile active request before changing: " + k)
                s["history"].append({"job_id": k, **old})
            s["jobs"][k] = {
                "spec_hash": spec_hash,
                "provider": j["provider"],
                "status": "QUEUED",
                "attempts": [],
                "candidates": [],
                "failure_counts": {},
            }
        # Re-anchor derived work when a registered source or predecessor changes.
        for k in order:
            e = s["jobs"][k]
            if e.get("input_hash"):
                fp, _, errors = fingerprint(root, current[k], s)
                if fp != e["input_hash"] or errors:
                    if e["status"] == "ACTIVE":
                        continue  # retain actual handle for reconciliation
                    s["history"].append({"job_id": k, **e})
                    s["jobs"][k] = {
                        "spec_hash": digest(current[k]),
                        "provider": current[k]["provider"],
                        "status": "QUEUED",
                        "attempts": [],
                        "candidates": [],
                        "failure_counts": {},
                    }
        event(s, "SYNC", jobs=len(current))
        save(Path(root) / STATE, s)
    return {"jobs": len(current)}


def budget_errors(root, j, s):
    auth = load(Path(root) / "00_execution_policy.json", {}).get("authorization", {})
    if not auth.get("reference"):
        return ["EXECUTION_SCOPE_MISSING"]
    cap = auth.get(j["provider"] + "_output_limit")
    if not isinstance(cap, int) or cap < 1:
        return ["OUTPUT_LIMIT_MISSING"]
    used = sum(
        len(e.get("attempts", []))
        for e in list(s["jobs"].values()) + s["history"]
        if e.get("provider") == j["provider"]
    )
    return ["OUTPUT_LIMIT_REACHED"] if used >= cap else []


def readiness(root, k, j, s):
    e = s["jobs"].get(k)
    if not e or e["spec_hash"] != digest(j):
        return ["SYNC_REQUIRED"]
    if e["status"] in {"ACTIVE", "REVIEW", "ACCEPTED", "REROUTE_REQUIRED"}:
        return [e["status"]]
    reasons = []
    if j.get("autonomy") == "BLOCK":
        reasons.append("PLAN_BLOCKED")
    if str(j.get("status", "")).startswith("HOLD"):
        reasons.append(j["status"])
    g = "G1_STORY" if j["provider"] == "image" else "G2_VISUAL"
    if gate_status(root, g) != "APPROVED":
        reasons.append(g)
    if not j.get("prompt") and not j.get("image_task"):
        reasons.append("PROMPT_MISSING")
    if j.get("route") in {
        "IMAGE25_EDIT",
        "HYBRID_IMAGE25_CODE",
        "IMAGE_EDIT",
        "HYBRID_IMAGE_CODE",
    } and not ref_ids(j):
        reasons.append("EDIT_REFERENCE_MISSING")
    if j.get("mode") in {"FRAMES", "START_FRAME"} and not j.get("start_frame_id"):
        reasons.append("START_MISSING")
    if j.get("mode") == "FRAMES" and not j.get("end_frame_id"):
        reasons.append("END_MISSING")
    if j.get("mode") == "INGREDIENTS" and not ref_ids(j):
        reasons.append("INGREDIENT_MISSING")
    if (
        j.get("mode") in {"EXTEND", "OMNI_EDIT"}
        and not j.get("source_video_id")
        and not dependencies(j)
    ):
        reasons.append("SOURCE_CLIP_MISSING")
    if len(e["attempts"]) >= int(j.get("candidate_n", 2)):
        reasons.append("CANDIDATE_LIMIT")
    _, _, errs = fingerprint(root, j, s)
    reasons += errs
    _, errs = capability(root, j)
    reasons += errs
    return reasons + budget_errors(root, j, s)


def next_jobs(root):
    js = jobs(root)
    s = state(root)
    out = []
    for k, j in js.items():
        e = s["jobs"].get(k, {})
        why = readiness(root, k, j, s)
        if e.get("status") == "ACCEPTED":
            fp, _, errors = fingerprint(root, j, s)
            if not valid_selected(root, e) or fp != e.get("input_hash") or errors:
                why = ["STALE_ACCEPTANCE"] + errors
        out.append(
            {
                "job_id": k,
                "provider": j["provider"],
                "status": e.get("status", "UNSYNCED"),
                "ready": not why,
                "reasons": why,
                "active_attempt": e.get("active_attempt"),
                "priority": j.get("priority", 0),
            }
        )
    out.sort(key=lambda x: (not x["ready"], -int(x["priority"]), x["job_id"]))
    return {
        "jobs": out,
        "note": "ACTIVE is recorded intent, not proof of a live remote process. Observe its receipt before waiting.",
    }


def claim(root, k, expected_input_hash=None):
    """Reserve one output. A caller that already rendered locally passes the input hash it
    used, so a concurrent input change refuses the claim instead of mislabelling the output."""
    js = jobs(root)
    j = js[k]
    with mutation(root):
        s = state(root)
        errors = readiness(root, k, j, s)
        if errors:
            raise ValueError("; ".join(errors))
        fp, refs, _ = fingerprint(root, j, s)
        if expected_input_hash is not None and fp != expected_input_hash:
            raise ValueError("Inputs changed after the render began; nothing was claimed")
        selected, _ = capability(root, j)
        token = uuid.uuid4().hex
        e = s["jobs"][k]
        attempt = {
            "token": token,
            "status": "CLAIMED",
            "created_at": now(),
            "input_hash": fp,
            "provider": j["provider"],
            "selection": selected,
        }
        e["attempts"].append(attempt)
        e["status"] = "ACTIVE"
        e["active_attempt"] = token
        e["input_hash"] = fp
        prompt = j.get("prompt") or "\n\n".join(
            f"{label}\n{j.get(field, '')}"
            for label, field in [
                ("TASK", "image_task"),
                ("KEEP", "keep"),
                ("CHANGE", "change"),
                ("COMPOSITION", "composition"),
                ("TEXT", "text_policy"),
            ]
        )
        packet = {
            "job_id": k,
            "token": token,
            "provider": j["provider"],
            "one_output_only": True,
            "selection": selected,
            "prompt": prompt,
            "references": [{**r, "absolute_path": str(local(root, r["path"]))} for r in refs],
            "contract": j,
            "dependency_clips": [s["jobs"][d]["selected"] for d in dependencies(j)],
            "next": NEXT_STEP.get(j["provider"], HANDOFF_STEP),
        }
        event(s, "CLAIM", job_id=k, token=token)
        save(Path(root) / STATE, s)
        save(Path(root) / "work/dispatch" / f"{token}.json", packet)
    return packet


def local_render_proof(root, k, data, entry, attempt):
    """Code jobs accept only a receipt `hsd code render` wrote for this job, inputs and output."""
    evidence = str(data.get("evidence", ""))
    handle = str(data.get("handle", ""))
    if not handle.startswith("local-render:") or not evidence.startswith("work/code_renders/"):
        raise ValueError("Code jobs take receipts from `hsd code render` only")
    record_path = local(root, evidence)
    if not record_path.is_file() or sha(record_path) != data.get("render_receipt_sha256"):
        raise ValueError("Render receipt is missing or changed: " + evidence)
    record = load(record_path)
    if (
        record.get("status") != "RENDERED"
        or record.get("job_id") != k
        or handle != "local-render:" + str(record.get("render_id"))
        or record.get("input_hash") != attempt.get("input_hash")
        or record.get("output", {}).get("sha256") != data.get("output_sha256")
    ):
        raise ValueError("Render receipt does not describe this attempt's rendered output")
    if any(a.get("receipt", {}).get("handle") == handle for a in entry["attempts"]):
        raise ValueError("This render was already receipted by another attempt")


def active(s, k, token):
    e = s["jobs"][k]
    if e.get("status") != "ACTIVE" or e.get("active_attempt") != token:
        raise ValueError("No matching active attempt")
    return e, e["attempts"][-1]


def receipt(root, k, token, data):
    if not data.get("handle") or not data.get("evidence"):
        raise ValueError("Receipt requires actual tool/UI handle and evidence")
    with mutation(root):
        s = state(root)
        e, a = active(s, k, token)
        selected = a["selection"]
        if selected.get("model") and data.get("actual_model") != selected["model"]:
            raise ValueError("Receipt model does not match selected model")
        if e["provider"] in VIDEO_PROVIDERS and data.get("actual_mode") != jobs(root)[k]["mode"]:
            raise ValueError("Receipt requires actual video mode")
        if e["provider"] == "code":
            local_render_proof(root, k, data, e, a)
        a["receipt"] = {**data, "recorded_at": now()}
        a["status"] = "SUBMITTED"
        event(s, "RECEIPT", job_id=k, token=token)
        save(Path(root) / STATE, s)
    return a


def ingest(root, k, token, source):
    src = Path(source).resolve()
    j = jobs(root)[k]
    meta = media_check(src, root)
    if meta["kind"] != ("image" if j["provider"] == "image" else "video"):
        raise ValueError("Wrong provider output media type")
    with mutation(root):
        s = state(root)
        e, a = active(s, k, token)
        if not a.get("receipt"):
            raise ValueError("Record real generation receipt before ingestion")
        if e["provider"] == "code" and meta["sha256"] != a["receipt"].get("output_sha256"):
            raise ValueError("Only the rendered output named in the receipt can be ingested")
        fp, _, errors = fingerprint(root, j, s)
        if fp != a["input_hash"] or errors:
            raise ValueError(
                "Inputs changed while job ran; reconcile result as obsolete, do not reuse silently"
            )
        dst = local(root, j["candidate_dir"]) / (token + src.suffix.lower())
        dst.parent.mkdir(parents=True, exist_ok=True)
        if dst.exists() and sha(dst) != meta["sha256"]:
            raise ValueError("Candidate collision")
        if not dst.exists():
            shutil.copy2(src, dst)
        candidate = {"path": relative(root, dst), **meta, "token": token}
        e["candidates"].append(candidate)
        e["status"] = "REVIEW"
        a["status"] = "DOWNLOADED"
        a["output"] = candidate
        e.pop("active_attempt", None)
        event(s, "INGEST", job_id=k, token=token, sha256=meta["sha256"])
        save(Path(root) / STATE, s)
    return candidate


def review(root, k, data):
    j = jobs(root)[k]
    with mutation(root):
        s = state(root)
        e = s["jobs"][k]
        if e["status"] not in {"REVIEW", "QUEUED", "REROUTE_REQUIRED"}:
            raise ValueError("No reviewable job")
        candidate = next((c for c in e["candidates"] if c["sha256"] == data.get("sha256")), None)
        if not candidate or sha(local(root, candidate["path"])) != data.get("sha256"):
            raise ValueError("Review hash must match current ingested candidate")
        required = CHECKS + (["motion_camera", "join"] if j["provider"] in VIDEO_PROVIDERS else [])
        checks = data.get("checks", {})
        if any(checks.get(c) not in {"PASS", "FAIL", "UNCERTAIN"} for c in required):
            raise ValueError("Missing semantic checks: " + ",".join(required))
        if not data.get("reviewer") or not data.get("evidence") or not data.get("notes"):
            raise ValueError("Reviewer, inspected evidence and substantive notes required")
        if not 0 <= float(data.get("score", -1)) <= 100:
            raise ValueError("Score must be 0..100")
        verdict = "PASS" if all(checks[c] == "PASS" for c in required) else "FAIL"
        if verdict == "FAIL" and data.get("failure_code") not in FAILURES:
            raise ValueError("Classify failure before retry")
        review_item = {
            **data,
            "verdict": verdict,
            "recorded_at": now(),
            "input_hash": e.get("input_hash"),
        }
        e.setdefault("reviews", []).append(review_item)
        # Re-recording the same review cannot consume another failure or retry.
        if verdict == "FAIL" and not any(
            r.get("sha256") == data["sha256"] and r.get("verdict") == "FAIL"
            for r in e["reviews"][:-1]
        ):
            code = data["failure_code"]
            counts = e["failure_counts"]
            counts[code] = counts.get(code, 0) + 1
        e["status"] = (
            "REVIEW"
            if verdict == "PASS"
            else (
                "REROUTE_REQUIRED"
                if max(e["failure_counts"].values(), default=0) >= 2
                or len(e["attempts"]) >= int(j["candidate_n"])
                else "QUEUED"
            )
        )
        event(s, "REVIEW", job_id=k, sha256=data["sha256"], verdict=verdict)
        save(Path(root) / STATE, s)
    return review_item


def accept(root, k):
    j = jobs(root)[k]
    with mutation(root):
        s = state(root)
        e = s["jobs"][k]
        prerequisite = "G1_STORY" if j["provider"] == "image" else "G2_VISUAL"
        if gate_status(root, prerequisite) != "APPROVED":
            raise ValueError("Approval prerequisite changed: " + prerequisite)
        if e["status"] == "ACCEPTED" and valid_selected(root, e):
            fp, _, errors = fingerprint(root, j, s)
            if fp == e.get("input_hash") and not errors:
                return e["selected"]
            raise ValueError("Accepted job is stale; revise/sync before accepting again")
        if e["status"] != "REVIEW":
            raise ValueError("No passing review to accept")
        fp, _, errors = fingerprint(root, j, s)
        if errors or fp != e["input_hash"]:
            raise ValueError("Changed inputs invalidate selection")
        latest = {r["sha256"]: r for r in e.get("reviews", [])}
        candidates = [
            (c, latest[c["sha256"]])
            for c in e["candidates"]
            if c["sha256"] in latest
            and latest[c["sha256"]]["verdict"] == "PASS"
            and latest[c["sha256"]]["input_hash"] == fp
        ]
        if not candidates:
            raise ValueError("No passing semantic review")
        c, r = max(candidates, key=lambda pair: float(pair[1]["score"]))
        p = local(root, c["path"])
        meta = media_check(p, root)
        if meta["sha256"] != c["sha256"]:
            raise ValueError("Candidate changed after review")
        if j.get("human_gate") and not gate_covers(root, j["human_gate"], c["sha256"]):
            raise ValueError("Human gate must cover this candidate: " + j["human_gate"])
        if j.get("requires_overlay"):
            overlays = load(Path(root) / "06s_overlay_receipts.json", {"outputs": {}})["outputs"]
            proof = overlays.get(c["sha256"])
            if not proof or any(
                not local(root, x["path"]).is_file() or sha(local(root, x["path"])) != x["sha256"]
                for x in proof["sources"]
            ):
                raise ValueError("Exact overlay proof missing/stale")
        if j["provider"] in VIDEO_PROVIDERS:
            if meta["duration_s"] + 1 / meta["fps"] < float(
                j.get("use_out_s") or j.get("final_edit_duration_s") or 0
            ):
                raise ValueError("Video too short for selected trim")
            from historical_shortfilm_director.qc.media import inspect_video

            refpaths = {x["asset_id"]: local(root, x["path"]) for x in inputs(root, j)[0]}
            tech = inspect_video(
                p, refpaths.get(j.get("start_frame_id")), refpaths.get(j.get("end_frame_id")), None
            )
            if tech["status"] != "PASS":
                raise ValueError(
                    "Endpoint/technical pre-screen requires repair or explicit contract revision: "
                    + str(tech)
                )
        dst = local(root, j.get("target_output") or j.get("approved_output"))
        dst.parent.mkdir(parents=True, exist_ok=True)
        if dst.suffix.lower() != p.suffix.lower():
            raise ValueError(
                "Selected output extension differs; create a decoded/verified derivative with the target format first"
            )
        if dst.exists() and sha(dst) != c["sha256"]:
            backup = local(root, "work/versions") / (sha(dst) + dst.suffix)
            backup.parent.mkdir(parents=True, exist_ok=True)
            if not backup.exists():
                shutil.copy2(dst, backup)
        if not dst.exists() or sha(dst) != c["sha256"]:
            shutil.copy2(p, dst)
        attempt = next(a for a in e["attempts"] if a["token"] == c["token"])
        asset = register(
            root,
            j.get("frame_id") or j.get("unit"),
            str(dst),
            type=j["provider"],
            status="APPROVED",
            job_id=k,
            review=r,
            refs=ref_ids(j),
            metadata=meta,
            provider_receipt=attempt.get("receipt"),
        )
        e["selected"] = asset
        e["status"] = "ACCEPTED"
        event(s, "ACCEPT", job_id=k, sha256=asset["sha256"])
        save(Path(root) / STATE, s)
    return asset


def reconcile(root, k, token, data):
    """Only observed provider-terminal failure or observed never-submitted state can release a claim."""
    if data.get("outcome") not in {"FAILED", "NOT_SUBMITTED", "OBSOLETE"} or not data.get(
        "evidence"
    ):
        raise ValueError("Need terminal observation/evidence; timeout alone is insufficient")
    with mutation(root):
        s = state(root)
        e, a = active(s, k, token)
        if data["outcome"] == "NOT_SUBMITTED" and a.get("receipt"):
            raise ValueError("Submitted attempt cannot be treated as never submitted")
        a["status"] = data["outcome"]
        a["reconciliation"] = {**data, "time": now()}
        e["status"] = "QUEUED"
        e.pop("active_attempt", None)
        if data["outcome"] == "FAILED":
            e["failure_counts"]["PROVIDER_FAILED"] = (
                e["failure_counts"].get("PROVIDER_FAILED", 0) + 1
            )
            if e["failure_counts"]["PROVIDER_FAILED"] >= 2:
                e["status"] = "REROUTE_REQUIRED"
        event(s, "RECONCILE", job_id=k, token=token)
        save(Path(root) / STATE, s)
    return a


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("project_dir")
    sub = ap.add_subparsers(dest="command", required=True)
    for cmd in ("sync", "next"):
        sub.add_parser(cmd)
    for cmd in ("claim", "accept"):
        p = sub.add_parser(cmd)
        p.add_argument("job_id")
    for cmd in ("receipt", "reconcile"):
        p = sub.add_parser(cmd)
        p.add_argument("job_id")
        p.add_argument("token")
        p.add_argument("json_file")
    p = sub.add_parser("ingest")
    p.add_argument("job_id")
    p.add_argument("token")
    p.add_argument("file")
    p = sub.add_parser("review")
    p.add_argument("job_id")
    p.add_argument("json_file")
    a = ap.parse_args()
    root = Path(a.project_dir).resolve()
    if a.command == "sync":
        out = sync(root)
    elif a.command == "next":
        out = next_jobs(root)
    elif a.command == "claim":
        out = claim(root, a.job_id)
    elif a.command == "accept":
        out = accept(root, a.job_id)
    elif a.command == "ingest":
        out = ingest(root, a.job_id, a.token, a.file)
    elif a.command == "review":
        out = review(root, a.job_id, load(local(root, a.json_file)))
    else:
        out = globals()[a.command](root, a.job_id, a.token, load(local(root, a.json_file)))
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValueError, RuntimeError, KeyError) as exc:
        raise SystemExit(str(exc))
