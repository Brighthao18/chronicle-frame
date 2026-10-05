"""Observed capabilities, never inferred vendor APIs or model limits."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from historical_shortfilm_director.runtime.common import load

HANDOFF_KINDS = {"agent-tool", "agent-image-tool", "browser", "operator"}
LOCAL_RENDER = "local-render"


def observation_errors(caps):
    """Availability and the runtime's 24-hour freshness policy for one observed slot."""
    if caps.get("available") is not True:
        return ["CAPABILITY_UNAVAILABLE"]
    try:
        age = (
            datetime.now(timezone.utc) - datetime.fromisoformat(caps["observed_at"])
        ).total_seconds()
    except (ValueError, KeyError, TypeError):
        return ["CAPABILITY_UNVERIFIED"]
    if age < -300 or age > 86400 or not caps.get("evidence"):
        return ["CAPABILITY_STALE"]
    return []


def references(job):
    return list(
        dict.fromkeys(
            [
                *job.get("references", []),
                *[
                    job[k]
                    for k in ("start_frame_id", "end_frame_id", "source_video_id")
                    if job.get(k)
                ],
            ]
        )
    )


def capability(root, job):
    """A checked dispatch selection or explicit blockers; no external execution."""
    caps = load(Path(root) / "00_capability_snapshot.json", {}).get(job["provider"], {})
    errors = observation_errors(caps)
    if errors:
        return None, errors
    if job["provider"] == "code":
        # The runtime itself renders code jobs; no external handoff kind applies.
        if caps.get("execution") != LOCAL_RENDER:
            return None, ["EXECUTION_UNSUPPORTED"]
        if job.get("mode") != "CODE":
            return None, ["CODE_MODE_REQUIRED"]
        if float(job.get("duration_s") or 0) <= 0:
            return None, ["DURATION_UNSUPPORTED"]
        return {
            "execution": LOCAL_RENDER,
            "toolchain": caps.get("toolchain", {}),
            "duration_s": float(job.get("duration_s") or 0),
        }, []
    execution = caps.get("execution", "browser" if job["provider"] == "flow" else "agent-tool")
    if execution not in HANDOFF_KINDS:
        return None, ["EXECUTION_UNSUPPORTED"]
    if job["provider"] in {"flow", "video"}:
        mode = caps.get("modes", {}).get(job["mode"])
        if not mode or not mode.get("model"):
            return None, [
                "FLOW_MODE_UNVERIFIED" if job["provider"] == "flow" else "VIDEO_MODE_UNVERIFIED"
            ]
        requested = float(job.get("duration_s") or 0)
        eligible = [
            float(value) for value in mode.get("durations_s", []) if float(value) >= requested
        ]
        if requested <= 0 or not eligible:
            return None, ["DURATION_UNSUPPORTED"]
        limit = mode.get("max_references")
        if limit is not None and len(references(job)) > int(limit):
            return None, ["REFERENCE_LIMIT"]
        required = {
            "START_FRAME": {"first_frame"},
            "FRAMES": {"first_frame", "first_last_frames"},
            "INGREDIENTS": {"reference_assets"},
            "EXTEND": {"extend"},
            "OMNI_EDIT": {"video_edit"},
        }.get(job["mode"], set())
        for flag in required:
            if mode.get(flag) is False:
                return None, ["CONDITIONING_UNSUPPORTED:" + flag]
            if job["provider"] == "video" and mode.get(flag) is not True:
                return None, ["CONDITIONING_UNVERIFIED:" + flag]
        return {**mode, "duration_s": min(eligible), "execution": execution}, []
    wanted = job.get("model_preference") or caps.get("default_model")
    if caps.get("model_selectable") and wanted:
        if wanted not in caps.get("models", []):
            return None, ["REQUESTED_MODEL_UNAVAILABLE"]
        return {"model": wanted, "execution": execution}, []
    return {
        "model": None,
        "model_observation": "not selected/exposed by tool",
        "requested_model": wanted,
        "execution": execution,
    }, []
