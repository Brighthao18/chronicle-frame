"""Code-rendered video: an agent such as Claude Code authors a program; the runtime renders it.

The renderer runs locally and deterministically, so the runtime itself can attest to the
operation it performed. This package stays standard-library only at import time; media
modules load Pillow, NumPy, OpenCV and FFmpeg lazily.
"""

from __future__ import annotations

import math

PROVIDER = "code"
MODE = "CODE"
EXECUTION = "local-render"
AUTHOR_SLOT = "claude_code"
AUTHOR_EXECUTION = "headless-cli"
RENDER_DEFAULTS = {"width": 1920, "height": 1080, "fps": 25}
RENDER_LIMITS = {"width": 8192, "height": 8192, "fps": 120}
MAX_FRAMES = 25 * 120


def render_settings(graph):
    """One validated production format for every CODE unit in a film."""
    block = (graph or {}).get("render", {})
    if not isinstance(block, dict):
        raise ValueError("render must be an object")
    extra = set(block) - set(RENDER_DEFAULTS)
    if extra:
        raise ValueError(f"render: unknown fields {sorted(extra)}")
    settings = {}
    for key, default in RENDER_DEFAULTS.items():
        value = block.get(key, default)
        if (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(value)
            or not 1 <= value <= RENDER_LIMITS[key]
        ):
            raise ValueError(f"render {key} must be a finite number in 1..{RENDER_LIMITS[key]}")
        if key != "fps" and (int(value) != value or int(value) % 2):
            raise ValueError("Render dimensions must be even integers")
        settings[key] = (
            int(value) if key != "fps" else (int(value) if value == int(value) else value)
        )
    return settings


def frame_count(duration_s, fps):
    """Frames covering a unit's full generation duration; frame i is shown at t = i / fps."""
    count = round(float(duration_s) * float(fps))
    if count < 2:
        raise ValueError("A code-rendered unit needs at least two frames")
    if count > MAX_FRAMES:
        raise ValueError(f"A code-rendered unit is limited to {MAX_FRAMES} frames")
    return count
