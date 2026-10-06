"""Shared synthetic fixtures for the code video route. Nothing here is live generation evidence."""

from __future__ import annotations

import os
import sys

from historical_shortfilm_director.gates import update
from historical_shortfilm_director.production.prepare import prepare
from historical_shortfilm_director.runtime.common import load, now, register, save
from tests.support.fixtures import FixtureCase, image

FAKE_CLI = '''\
"""OFFLINE stand-in for the Claude Code CLI: no network, no model, deterministic output."""
import json
import sys
from pathlib import Path

args = sys.argv[1:]
if args == ["--version"]:
    print("0.0.0 (offline fixture)")
elif args == ["--help"]:
    print("-p, --print  --output-format <format>  --permission-mode <mode>")
    print("--tools <tools...>  --max-budget-usd <amount>  --model <model>")
else:
    Path("argv.json").write_text(json.dumps(args))
    scene = Path(__file__).with_name("scene_to_write.json")
    if scene.exists():
        Path("scene.json").write_text(scene.read_text())
    print(json.dumps({"type": "result", "subtype": "success", "is_error": False,
                      "session_id": "offline-fixture", "num_turns": 2, "total_cost_usd": 0.25}))
    status = Path(__file__).with_name("exit_code.txt")
    raise SystemExit(int(status.read_text()) if status.exists() else 0)
'''

SCENE = {
    "schema": "hsd-scene/1",
    "layers": [
        {
            "id": "plate",
            "type": "image",
            "asset": "PLATE",
            "keys": [
                {"t": 0, "scale": 1.0, "ax": 0.5, "ay": 0.5},
                {"t": 2, "scale": 1.3, "ax": 0.4, "ay": 0.45, "ease": "in_out"},
            ],
        }
    ],
}


def fake_cli(directory):
    """An executable fake `claude` for this platform, without a model or network."""
    script = directory / "fake_claude.py"
    script.write_text(FAKE_CLI, encoding="utf-8")
    if os.name == "nt":
        wrapper = directory / "claude.cmd"
        wrapper.write_text(f'@"{sys.executable}" "{script}" %*\r\n', encoding="utf-8")
    else:
        wrapper = directory / "claude"
        wrapper.write_text(f'#!/bin/sh\nexec "{sys.executable}" "{script}" "$@"\n')
        wrapper.chmod(0o755)
    return wrapper


class CodeCase(FixtureCase):
    """A project with one registered plate and one CODE unit, prepared but not rendered."""

    def code_graph(self, **unit):
        return {
            "schema_version": "3.2",
            "title": "OFFLINE code video fixture",
            "external_refs": ["PLATE"],
            "frames": [
                {"id": "A", "route": "SOURCE_LOCKED", "preview_path": "materials/plate.png"}
            ],
            "units": [
                {
                    "id": "U1",
                    "mode": "CODE",
                    "ingredients": ["PLATE"],
                    "duration_s": 2,
                    "edit_s": 1.6,
                    "in_s": 0.2,
                    "action": "Push slowly toward the rectangle.",
                    "camera": "One slow push-in, no rotation.",
                    "keep": "Plate geometry",
                    "change": "Framing only",
                    "preview_frame": "A",
                    **unit,
                }
            ],
            "joins": [],
            "render": {"width": 320, "height": 180, "fps": 25},
        }

    def code_project(self, graph=None, observed=True, limit=6, visual=True):
        plate = image(self.root / "materials/plate.png")
        register(
            self.root,
            "PLATE",
            str(plate),
            status="SOURCE_VERIFIED",
            origin="SYNTHETIC",
            provenance="Original test geometry; not archival evidence",
        )
        save(self.root / "03_production_graph.json", graph or self.code_graph())
        caps = load(self.root / "00_capability_snapshot.json")
        if observed:
            caps["code"] = {
                "available": True,
                "observed_at": now(),
                "evidence": "OFFLINE TEST FIXTURE: no probe was run",
                "execution": "local-render",
            }
        save(self.root / "00_capability_snapshot.json", caps)
        policy = load(self.root / "00_execution_policy.json")
        policy["authorization"]["code_output_limit"] = limit
        save(self.root / "00_execution_policy.json", policy)
        if visual:
            update(
                self.root,
                "G2_VISUAL",
                "APPROVED",
                "Synthetic visual",
                "OFFLINE FIXTURE",
                ["materials/plate.png"],
            )
        prepare(self.root)
        program = self.root / "programs/U1.scene.json"
        save(program, SCENE)
        return "FLOW_U1", "programs/U1.scene.json"

    def allow(self, **authorization):
        policy = load(self.root / "00_execution_policy.json")
        code_render = authorization.pop("code_render", None)
        policy["authorization"].update(authorization)
        if code_render is not None:
            policy["code_render"] = code_render
        save(self.root / "00_execution_policy.json", policy)
