"""Offline behavioral tests. Synthetic provider fixtures are NOT live generation evidence."""

from __future__ import annotations
import argparse
import csv
import json
import os
import subprocess
import sys
import tempfile
import unittest
import wave
from pathlib import Path
from PIL import Image, ImageDraw
from historical_shortfilm_director.runtime.common import (
    load,
    save,
    sha,
    now,
    register,
    gate_status,
    media_check,
    ffmpeg,
    local,
)
import historical_shortfilm_director.runtime.engine as rt
from historical_shortfilm_director.gates import update
from historical_shortfilm_director.evidence.overlays import apply_plan
from historical_shortfilm_director.reviews.packet import build


def render(*args, **kwargs):
    from historical_shortfilm_director.media.deterministic import render as implementation

    return implementation(*args, **kwargs)


def extract(*args, **kwargs):
    from historical_shortfilm_director.media.frames import extract as implementation

    return implementation(*args, **kwargs)


HERE = Path(__file__).resolve().parents[2] / "scripts"
TEST_BASE = None


def run(script, *args, good=True):
    cp = subprocess.run(
        [sys.executable, "-X", "utf8", str(HERE / script), *map(str, args)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if good and cp.returncode:
        raise AssertionError(script + " failed:\n" + cp.stdout + "\n" + cp.stderr[-3000:])
    if not good and not cp.returncode:
        raise AssertionError(script + " unexpectedly succeeded")
    return cp


def image(path, color="navy"):
    path.parent.mkdir(parents=True, exist_ok=True)
    im = Image.new("RGB", (320, 180), color)
    d = ImageDraw.Draw(im)
    d.rectangle((90, 35, 215, 150), outline="white", width=6)
    d.line((0, 0, 319, 179), fill="yellow", width=3)
    im.save(path)
    return path


def table(path, rows):
    h = list(rows[0])
    lines = ["| " + " | ".join(h) + " |", "| " + " | ".join("---" for _ in h) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(str(row.get(k, "")) for k in h) + " |")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


class FixtureCase(unittest.TestCase):
    def setUp(self):
        self._case = tempfile.TemporaryDirectory(prefix="hsd_case_")
        self.addCleanup(self._case.cleanup)
        self.root = Path(self._case.name) / "中文 project"
        run(
            "init_project.py",
            "--title",
            "offline synthetic test",
            "--generator",
            "flow",
            "--dir",
            self.root,
        )
        save(
            self.root / "00_capability_snapshot.json",
            {
                "image": {
                    "available": True,
                    "observed_at": now(),
                    "evidence": "OFFLINE TEST FIXTURE: no real provider",
                    "model_selectable": False,
                },
                "flow": {
                    "available": True,
                    "observed_at": now(),
                    "evidence": "OFFLINE TEST FIXTURE: no real Flow",
                    "modes": {
                        "FRAMES": {
                            "model": "TEST_MODEL",
                            "durations_s": [2, 4],
                            "max_references": 2,
                        }
                    },
                },
                "local": {},
            },
        )
        save(
            self.root / "00_execution_policy.json",
            {
                "authorization": {
                    "reference": "OFFLINE TEST ONLY",
                    "image_output_limit": 30,
                    "flow_output_limit": 20,
                }
            },
        )
        self.story = self.root / "reviews/story.txt"
        self.story.write_text("Synthetic story fixture; no historical claims.", encoding="utf-8")
        update(
            self.root,
            "G1_STORY",
            "APPROVED",
            "Synthetic test approval",
            "OFFLINE FIXTURE",
            ["reviews/story.txt"],
        )

    def image_job(self, fid="A", **kw):
        j = {
            "job_id": "IMG25_" + fid,
            "frame_id": fid,
            "route": "IMAGE25_SYNTH",
            "provider": "image",
            "references": [],
            "candidate_n": 3,
            "autonomy": "AUTO",
            "image_task": "Synthetic blue box",
            "pixel_lock": "P0_FREE",
            "target_output": f"assets/frames/{fid}.png",
            "candidate_dir": f"assets/candidates/{fid}",
            "model_preference": "gpt-image-2.5-flare",
            "human_gate": None,
            "status": "QUEUED",
        }
        j.update(kw)
        return j

    def queue(self, *jobs):
        for q, provider in rt.QUEUES:
            save(
                self.root / q,
                {"schema_version": "3.1", "jobs": [j for j in jobs if j["provider"] == provider]},
            )
        rt.sync(self.root)

    def generate(self, j, color="navy"):
        k = j["job_id"]
        pkt = rt.claim(self.root, k)
        receipt = {
            "handle": "OFFLINE_FAKE_" + pkt["token"],
            "evidence": "Synthetic local test; NOT a tool execution",
            "actual_model": pkt["selection"].get("model"),
        }
        if j["provider"] == "flow":
            receipt["actual_mode"] = j["mode"]
        rt.receipt(self.root, k, pkt["token"], receipt)
        if j["provider"] == "image":
            p = image(self.root / "work" / ("raw_" + pkt["token"] + ".png"), color)
        else:
            src = image(self.root / "work" / ("raw_" + pkt["token"] + ".png"), color)
            p = render(
                {
                    "unit": pkt["token"],
                    "source": str(src),
                    "output": f"work/{pkt['token']}.mp4",
                    "width": 320,
                    "height": 180,
                    "fps": 25,
                    "duration_s": 2,
                    "motion": "HOLD",
                },
                self.root,
            )
        return rt.ingest(self.root, k, pkt["token"], p)

    def passing(self, j, c, fail=None):
        checks = {
            k: "PASS"
            for k in rt.CHECKS + (["motion_camera", "join"] if j["provider"] == "flow" else [])
        }
        if fail:
            checks["contract"] = "FAIL"
        data = {
            "sha256": c["sha256"],
            "reviewer": "OFFLINE_TEST",
            "evidence": ["synthetic fixture checked by test; not VLM proof"],
            "checks": checks,
            "score": 90,
            "notes": "Fixture-specific test of state transitions only; not a historical judgment.",
        }
        if fail:
            data["failure_code"] = fail
        return rt.review(self.root, j["job_id"], data)

    def graph(self):
        image(self.root / "materials/a.png")
        image(self.root / "materials/b.png", "teal")
        return {
            "schema_version": "3.2",
            "title": "OFFLINE preview fixture",
            "external_refs": [],
            "frames": [
                {
                    "id": "A",
                    "route": "IMAGE25_SYNTH",
                    "task": "Synthetic blue room",
                    "preview_path": "materials/a.png",
                },
                {
                    "id": "B",
                    "route": "IMAGE25_SYNTH",
                    "task": "Synthetic green room",
                    "preview_path": "materials/b.png",
                },
            ],
            "units": [
                {
                    "id": uid,
                    "mode": "FRAMES",
                    "start": fid,
                    "end": fid,
                    "duration_s": 2,
                    "edit_s": 1,
                    "in_s": 0.2,
                    "action": "Hold the composition.",
                    "camera": "Locked camera.",
                    "keep": "Rectangle",
                    "change": "None",
                    "preview_motion": "HOLD",
                }
                for uid, fid in [("U1", "A"), ("U2", "B")]
            ],
            "joins": [
                {
                    "id": "J",
                    "from": "U1",
                    "to": "U2",
                    "type": "HARD_CUT",
                    "fallback": "Use the planned hard cut",
                    "handles": "0.2",
                }
            ],
            "preview": {"width": 320, "height": 180, "fps": 25},
        }

    def store_graph(self, g):
        save(self.root / "03_production_graph.json", g)
