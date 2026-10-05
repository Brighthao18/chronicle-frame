"""Preserved local production invariants."""

from __future__ import annotations
from pathlib import Path
from .storage import load, local, sha


def gate_status(root, gate):
    value = load(Path(root) / "00_pipeline_control.json", {}).get("gates", {}).get(gate, {})
    if not isinstance(value, dict):
        return str(value)
    status = value.get("status", "PENDING")
    if status == "APPROVED":
        if gate != "G1_STORY" and gate_status(root, "G1_STORY") != "APPROVED":
            return "STALE"
        if (
            gate in {"G3_HERO_MOTION", "G4_PICTURE_LOCK"}
            and gate_status(root, "G2_VISUAL") != "APPROVED"
        ):
            return "STALE"
    if status == "NOT_REQUIRED" and gate == "G3_HERO_MOTION":
        queue = load(Path(root) / "06o_flow_job_queue.json", {"jobs": []})
        if any(j.get("human_gate") == gate for j in queue["jobs"]):
            return "STALE"
    if status in {"APPROVED", "NOT_REQUIRED"}:
        for item in value.get("artifacts", []):
            p = local(root, item["path"])
            if not p.is_file() or sha(p) != item["sha256"]:
                return "STALE"
    return status


def gate_covers(root, gate, asset_sha):
    if gate_status(root, gate) != "APPROVED":
        return False
    g = load(Path(root) / "00_pipeline_control.json", {}).get("gates", {}).get(gate, {})
    return isinstance(g, dict) and any(a.get("sha256") == asset_sha for a in g.get("artifacts", []))


def plan_allowed(approval, autonomy="AUTO"):
    """A plan approval is an agent's readiness label, not a human gate."""
    return str(autonomy).upper() in {"AUTO", "REVIEW"} and str(approval).strip().upper() not in {
        "BLOCK",
        "BLOCKED",
        "REJECTED",
        "REVISE",
    }
