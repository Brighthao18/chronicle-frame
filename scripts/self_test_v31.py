"""Offline behavioral tests. Synthetic provider fixtures are NOT live generation evidence."""

from __future__ import annotations
import argparse
import csv
import json
import subprocess
import sys
import tempfile
import unittest
import wave
from pathlib import Path
from production_common import load
import cv2
import numpy as np
from PIL import Image, ImageDraw
from production_common import (
    save,
    sha,
    now,
    register,
    gate_status,
    media_check,
    ffmpeg,
    local,
)
import production_runtime as rt
from approve_gate import update
from seal_evidence import apply_plan
from render_deterministic_shots import render
from build_review_packet import build
from extract_review_frames import extract

HERE = Path(__file__).resolve().parent
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


class ProductionTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="case_", dir=TEST_BASE)) / "中文 project"
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
                "local": {"ffmpeg_path": ffmpeg()},
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

    def test_pending_plans_compile_without_per_row_human_approval(self):
        base = {
            "Frame ID": "A",
            "Build route": "IMAGE25_SYNTH",
            "Autonomy": "AUTO",
            "Approval": "PENDING",
            "Image 2.5 task": "blue",
            "Risk": "routine",
        }
        table(
            self.root / "03d_frame_asset_plan.md",
            [
                base,
                {**base, "Frame ID": "B", "Autonomy": "REVIEW"},
                {**base, "Frame ID": "C", "Autonomy": "BLOCK"},
            ],
        )
        run("compile_image25_jobs.py", self.root)
        self.assertEqual(
            [x["frame_id"] for x in load(self.root / "06i_image25_job_queue.json")["jobs"]],
            ["A", "B"],
        )

    def test_missing_edit_reference_is_held(self):
        j = self.image_job(route="IMAGE25_EDIT", references=["MISSING"])
        self.queue(j)
        self.assertIn("MISSING_REFERENCE:MISSING", rt.next_jobs(self.root)["jobs"][0]["reasons"])
        with self.assertRaises(ValueError):
            rt.claim(self.root, j["job_id"])

    def test_gates_bind_to_actual_files(self):
        with self.assertRaises(ValueError):
            update(self.root, "G2_VISUAL", "APPROVED", "No real approval")
        self.story.write_text("Changed", encoding="utf-8")
        self.assertEqual(gate_status(self.root, "G1_STORY"), "STALE")

    def test_optional_g3_and_preserved_nonlocal_detection(self):
        save(self.root / "06o_flow_job_queue.json", {"jobs": []})
        update(self.root, "G3_HERO_MOTION", "NOT_REQUIRED", "No motion escalation")
        run("pipeline_controller.py", self.root, "--detect-local", "--json")
        self.assertIs(load(self.root / "00_capability_snapshot.json")["image"]["available"], True)
        self.assertEqual(gate_status(self.root, "G3_HERO_MOTION"), "NOT_REQUIRED")
        with self.assertRaises(ValueError):
            update(self.root, "G2_VISUAL", "NOT_REQUIRED", "No")

    def test_cycle_is_rejected(self):
        a = self.image_job("A", references=["B"])
        b = self.image_job("B", references=["A"])
        save(self.root / "06i_image25_job_queue.json", {"jobs": [a, b]})
        with self.assertRaisesRegex(ValueError, "cycle"):
            rt.sync(self.root)

    def test_claim_is_durable_and_does_not_repeat(self):
        j = self.image_job()
        self.queue(j)
        pkt = rt.claim(self.root, j["job_id"])
        with self.assertRaises(ValueError):
            rt.claim(self.root, j["job_id"])
        rt.sync(self.root)
        self.assertEqual(rt.state(self.root)["jobs"][j["job_id"]]["active_attempt"], pkt["token"])
        j["image_task"] = "new"
        save(self.root / "06i_image25_job_queue.json", {"jobs": [j]})
        with self.assertRaisesRegex(ValueError, "Reconcile"):
            rt.sync(self.root)

    def test_receipt_required_and_fake_bytes_rejected(self):
        j = self.image_job()
        self.queue(j)
        pkt = rt.claim(self.root, j["job_id"])
        p = image(self.root / "work/a.png")
        with self.assertRaisesRegex(ValueError, "receipt"):
            rt.ingest(self.root, j["job_id"], pkt["token"], p)
        bad = self.root / "work/bad.png"
        bad.write_bytes(b"not an image")
        with self.assertRaises(Exception):
            rt.ingest(self.root, j["job_id"], pkt["token"], bad)

    def test_exact_model_mismatch_is_rejected(self):
        caps = load(self.root / "00_capability_snapshot.json")
        caps["image"].update(model_selectable=True, models=["gpt-image-2.5-flare"])
        save(self.root / "00_capability_snapshot.json", caps)
        j = self.image_job()
        self.queue(j)
        pkt = rt.claim(self.root, j["job_id"])
        with self.assertRaisesRegex(ValueError, "model"):
            rt.receipt(
                self.root,
                j["job_id"],
                pkt["token"],
                {"handle": "fixture", "evidence": "fixture", "actual_model": "wrong"},
            )

    def test_no_semantic_review_no_auto_acceptance(self):
        j = self.image_job()
        self.queue(j)
        c = self.generate(j)
        with self.assertRaises(ValueError):
            rt.accept(self.root, j["job_id"])
        self.passing(j, c)
        chosen = rt.accept(self.root, j["job_id"])
        self.assertEqual(chosen["sha256"], c["sha256"])
        self.assertFalse(rt.next_jobs(self.root)["jobs"][0]["ready"])
        self.assertEqual(len(rt.state(self.root)["jobs"][j["job_id"]]["attempts"]), 1)

    def test_changed_reviewed_candidate_rejected(self):
        j = self.image_job()
        self.queue(j)
        c = self.generate(j)
        self.passing(j, c)
        image(self.root / c["path"], "red")
        with self.assertRaisesRegex(ValueError, "changed"):
            rt.accept(self.root, j["job_id"])

    def test_hero_requires_selected_hash_and_board_escapes(self):
        j = self.image_job(human_gate="G2_VISUAL", autonomy="REVIEW")
        self.queue(j)
        c = self.generate(j)
        self.passing(j, c)
        with self.assertRaisesRegex(ValueError, "Human gate"):
            rt.accept(self.root, j["job_id"])
        board = build(self.root, "G2_VISUAL")
        self.assertIn("<img", board.read_text(encoding="utf-8"))
        update(
            self.root,
            "G2_VISUAL",
            "APPROVED",
            "Fixture",
            "OFFLINE FIXTURE",
            [c["path"], str(board)],
        )
        rt.accept(self.root, j["job_id"])

    def test_two_distinct_failures_require_reroute(self):
        j = self.image_job()
        self.queue(j)
        c = self.generate(j)
        self.passing(j, c, "CONTENT_DRIFT")
        self.passing(j, c, "CONTENT_DRIFT")
        self.assertEqual(
            rt.state(self.root)["jobs"][j["job_id"]]["failure_counts"]["CONTENT_DRIFT"], 1
        )
        c = self.generate(j, "red")
        self.passing(j, c, "CONTENT_DRIFT")
        self.assertEqual(rt.state(self.root)["jobs"][j["job_id"]]["status"], "REROUTE_REQUIRED")

    def test_budget_survives_job_revision(self):
        save(
            self.root / "00_execution_policy.json",
            {
                "authorization": {
                    "reference": "OFFLINE",
                    "image_output_limit": 1,
                    "flow_output_limit": 1,
                }
            },
        )
        j = self.image_job()
        self.queue(j)
        c = self.generate(j)
        self.passing(j, c, "CONTENT_DRIFT")
        j["image_task"] = "new route"
        self.queue(j)
        self.assertIn("OUTPUT_LIMIT_REACHED", rt.next_jobs(self.root)["jobs"][0]["reasons"])

    def test_source_change_invalidates_accepted_and_downstream(self):
        src = image(self.root / "materials/src.png")
        register(self.root, "SRC", str(src), status="SOURCE_VERIFIED")
        a = self.image_job("A", references=["SRC"])
        b = self.image_job("B", references=["A"])
        self.queue(a, b)
        c = self.generate(a)
        self.passing(a, c)
        rt.accept(self.root, a["job_id"])
        c = self.generate(b)
        self.passing(b, c)
        rt.accept(self.root, b["job_id"])
        image(src, "red")
        register(self.root, "SRC", str(src), status="SOURCE_VERIFIED")
        rt.sync(self.root)
        self.assertEqual(rt.state(self.root)["jobs"][a["job_id"]]["status"], "QUEUED")
        self.assertEqual(rt.state(self.root)["jobs"][b["job_id"]]["status"], "QUEUED")
        self.assertFalse(
            next(x for x in rt.next_jobs(self.root)["jobs"] if x["job_id"] == b["job_id"])["ready"]
        )

    def test_capability_staleness_and_output_limit(self):
        j = self.image_job()
        self.queue(j)
        caps = load(self.root / "00_capability_snapshot.json")
        caps["image"]["observed_at"] = "2000-01-01T00:00:00+00:00"
        save(self.root / "00_capability_snapshot.json", caps)
        self.assertIn("CAPABILITY_STALE", rt.next_jobs(self.root)["jobs"][0]["reasons"])

    def test_ambiguous_timeout_cannot_release(self):
        j = self.image_job()
        self.queue(j)
        pkt = rt.claim(self.root, j["job_id"])
        with self.assertRaises(ValueError):
            rt.reconcile(
                self.root, j["job_id"], pkt["token"], {"outcome": "TIMEOUT", "evidence": "timeout"}
            )
        rt.receipt(self.root, j["job_id"], pkt["token"], {"handle": "fixture", "evidence": "test"})
        with self.assertRaises(ValueError):
            rt.reconcile(
                self.root,
                j["job_id"],
                pkt["token"],
                {"outcome": "NOT_SUBMITTED", "evidence": "test"},
            )

    def test_sealed_overlay_exact_non_destructive_and_bounds(self):
        base = image(self.root / "assets/raw.png")
        original = sha(base)
        src = self.root / "materials/证据.png"
        Image.new("RGBA", (10, 10), (12, 30, 80, 255)).save(src)
        p = self.root / "03e_evidence_overlay_plan.csv"
        with p.open("w", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(
                f,
                fieldnames=[
                    "frame_id",
                    "target_path",
                    "source_path",
                    "source_box",
                    "target_xy",
                    "approval",
                ],
            )
            w.writeheader()
            w.writerow(
                {
                    "frame_id": "X",
                    "target_path": "assets/raw.png",
                    "source_path": "materials/证据.png",
                    "source_box": "FULL",
                    "target_xy": "20,20",
                    "approval": "READY",
                }
            )
        records = apply_plan(self.root)
        out = self.root / records[0]["path"]
        self.assertEqual(sha(base), original)
        with Image.open(out) as im:
            self.assertEqual(im.getpixel((20, 20)), (12, 30, 80, 255))
        self.assertEqual(apply_plan(self.root)[0]["sha256"], records[0]["sha256"])
        p.write_text(
            p.read_text(encoding="utf-8-sig").replace("20,20", "999,999"), encoding="utf-8-sig"
        )
        with self.assertRaises(ValueError):
            apply_plan(self.root)

    def test_render_push_and_pan_change_pixels(self):
        src = image(self.root / "materials/src.png")
        for mode in ("PUSH_IN", "PAN_LEFT"):
            out = render(
                {
                    "unit": mode,
                    "source": str(src),
                    "output": f"renders/{mode}.mp4",
                    "motion": mode,
                    "duration_s": 1,
                    "fps": 25,
                    "width": 320,
                    "height": 180,
                    "strength": 0.2,
                },
                self.root,
            )
            cap = cv2.VideoCapture(str(out))
            _, first = cap.read()
            cap.set(cv2.CAP_PROP_POS_FRAMES, 24)
            _, last = cap.read()
            cap.release()
            self.assertGreater(float(np.mean(cv2.absdiff(first, last))), 2)

    def test_paths_and_nonempty_initializer(self):
        for p in ("../escape.png", "assets/CON.png", "assets/a:bad.png"):
            with self.assertRaises(ValueError):
                local(self.root, p)
        run("init_project.py", "--title", "no overwrite", "--dir", self.root, good=False)

    def test_flow_compilation_and_end_to_end_assembly_audio(self):
        # Real compilers + durable synthetic execution + actual local codecs.
        src = image(self.root / "materials/frame.png")
        register(self.root, "F", str(src), status="SOURCE_VERIFIED")
        update(
            self.root,
            "G2_VISUAL",
            "APPROVED",
            "Synthetic visual",
            "OFFLINE",
            ["materials/frame.png"],
        )
        endpoints = []
        blueprints = []
        for uid in ("U1", "U2"):
            endpoints.append(
                {
                    "Unit": uid,
                    "Parent shot": uid,
                    "Flow mode": "FRAMES",
                    "Final edit duration": "1",
                    "Duration": "2",
                    "Use in": "0.2",
                    "Use out": "1.2",
                    "Start frame ID": "F",
                    "End frame ID": "F",
                    "End frame needed?": "yes",
                    "KEEP fixed": "box",
                    "CHANGE": "light",
                    "Motion path": "hold",
                    "Reachability": "R-A",
                    "Risk": "routine",
                    "Autonomy": "AUTO",
                    "Candidate N": "2",
                    "Approval": "PENDING",
                }
            )
            blueprints.append(
                {
                    "Unit": uid,
                    "Prompt mode": "FRAMES_PATH",
                    "Story beat": "hold source",
                    "Visual premise": "archival display",
                    "Anchor facts": "box",
                    "ONE primary action": "hold steady",
                    "Environment response": "none",
                    "Camera grammar": "locked camera",
                    "Focus / depth": "deep",
                    "Light / atmosphere": "steady",
                    "Temporal choreography": "stay settled",
                    "Audio intent": "none",
                    "Continuity locks": "box",
                    "Post-only": "text",
                    "Density target": "short",
                    "Approval": "PENDING",
                }
            )
        table(self.root / "05f_shot_endpoint_plan.md", endpoints)
        table(self.root / "04c_flow_prompt_blueprints.md", blueprints)
        table(
            self.root / "05h_join_contracts.md",
            [
                {
                    "Join": "J1",
                    "From unit": "U1",
                    "To unit": "U2",
                    "Join type": "HARD_CUT",
                    "Shared seam frame": "",
                    "Handles": "0.2",
                    "Fallback": "hard cut",
                    "Approval": "READY",
                }
            ],
        )
        run("compile_flow_prompts.py", self.root)
        run("compile_flow_jobs.py", self.root)
        rt.sync(self.root)
        js = rt.jobs(self.root)
        self.assertEqual(len(js), 2)
        run("pipeline_controller.py", self.root, "--auto-local", "--json")
        for j in js.values():
            c = self.generate(j)
            self.passing(j, c)
            rt.accept(self.root, j["job_id"])
            samples = extract(self.root, c["path"], [0, 0.2, 1.16, 1.96])
            self.assertEqual(len(samples), 4)
        run("compile_direct_assembly.py", self.root)
        run("assemble_direct.py", self.root, "--width", "320", "--height", "180", "--execute")
        picture = self.root / "exports/direct_picture_master.mp4"
        self.assertAlmostEqual(media_check(picture, self.root)["duration_s"], 2, places=2)
        self.assertAlmostEqual(media_check(picture, self.root)["fps"], 25, places=2)
        # Short audio must not shorten a two-second picture.
        audio = self.root / "work/voice.wav"
        with wave.open(str(audio), "w") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(24000)
            w.writeframes(np.zeros(6000, dtype=np.int16).tobytes())
        (self.root / "07_audio_mix_plan.csv").write_text(
            "track_id,path,start_s,trim_in_s,trim_out_s,gain_db,fade_in_s,fade_out_s,type,approval\nVO,work/voice.wav,0,0,0.25,0,0,0,voice,READY\n",
            encoding="utf-8-sig",
        )
        (self.root / "07_text_overlay_plan.csv").write_text(
            "start_s,end_s,text,style,approval\n0.1,1.8,校史 2026,CAPTION,READY\n",
            encoding="utf-8-sig",
        )
        run("compile_ass_subtitles.py", self.root, "--width", "320", "--height", "180")
        update(
            self.root,
            "G4_PICTURE_LOCK",
            "APPROVED",
            "Synthetic master",
            "OFFLINE",
            ["exports/direct_picture_master.mp4"],
        )
        run(
            "mix_final_master.py",
            self.root,
            "--picture",
            "generated/flow_approved/U1.mp4",
            "--output",
            "exports/unapproved_master.mp4",
            "--execute",
            good=False,
        )
        run("mix_final_master.py", self.root, "--execute")
        final = self.root / "exports/final_master.mp4"
        self.assertAlmostEqual(media_check(final, self.root)["duration_s"], 2, places=2)
        self.assertEqual(load(final.with_suffix(".qc.json"))["status"], "PASS")
        # Never silently exclude a required held row.
        manifest = self.root / "06k_direct_assembly_manifest.csv"
        t = manifest.read_text(encoding="utf-8-sig")
        manifest.write_text(t.replace("READY", "HOLD", 1), encoding="utf-8-sig")
        run(
            "assemble_direct.py",
            self.root,
            "--output",
            "exports/invalid.mp4",
            "--execute",
            good=False,
        )
        self.assertFalse((self.root / "exports/invalid.mp4").exists())

    def test_subtitle_rollover_and_mixed_fonts(self):
        from compile_ass_subtitles import ass_time, font_runs

        self.assertEqual(ass_time("59.999"), "0:01:00.00")
        self.assertIn("\\fnSimSun", font_runs("中文 2026"))
        self.assertIn("\\fnTimes New Roman", font_runs("中文 2026"))

    def test_runtime_cli_roundtrip(self):
        j = self.image_job()
        self.queue(j)
        run("production_runtime.py", self.root, "sync")
        snapshot = json.loads(run("production_runtime.py", self.root, "next").stdout)
        self.assertTrue(snapshot["jobs"][0]["ready"])
        packet = json.loads(run("production_runtime.py", self.root, "claim", j["job_id"]).stdout)
        save(
            self.root / "work/receipt.json",
            {
                "handle": "OFFLINE_CLI_FIXTURE",
                "evidence": "Synthetic receipt; not actual generation",
            },
        )
        run(
            "production_runtime.py",
            self.root,
            "receipt",
            j["job_id"],
            packet["token"],
            "work/receipt.json",
        )
        source = image(self.root / "work/cli.png")
        c = json.loads(
            run(
                "production_runtime.py", self.root, "ingest", j["job_id"], packet["token"], source
            ).stdout
        )
        data = {
            "sha256": c["sha256"],
            "reviewer": "OFFLINE",
            "evidence": ["synthetic fixture"],
            "checks": {k: "PASS" for k in rt.CHECKS},
            "score": 90,
            "notes": "CLI mechanics only",
        }
        save(self.root / "work/review.json", data)
        run("production_runtime.py", self.root, "review", j["job_id"], "work/review.json")
        run("production_runtime.py", self.root, "accept", j["job_id"])
        self.assertEqual(sha(self.root / j["target_output"]), c["sha256"])

    def test_g3_skip_invalidates_when_escalation_added(self):
        save(self.root / "06o_flow_job_queue.json", {"jobs": []})
        update(self.root, "G3_HERO_MOTION", "NOT_REQUIRED", "No escalations")
        save(self.root / "06o_flow_job_queue.json", {"jobs": [{"human_gate": "G3_HERO_MOTION"}]})
        self.assertEqual(gate_status(self.root, "G3_HERO_MOTION"), "STALE")

    def test_overlay_proof_required_for_exact_job(self):
        j = self.image_job(requires_overlay=True)
        self.queue(j)
        c = self.generate(j)
        self.passing(j, c)
        with self.assertRaisesRegex(ValueError, "overlay proof"):
            rt.accept(self.root, j["job_id"])

    def test_flow_route_duration_and_ingredients_compiler(self):
        table(
            self.root / "05f_shot_endpoint_plan.md",
            [
                {
                    "Unit": "U1",
                    "Flow mode": "INGREDIENTS",
                    "Duration": "4 s",
                    "Autonomy": "AUTO",
                    "Approval": "PENDING",
                    "Ingredient IDs": "F1;F2",
                    "Source video ID": "CLIP",
                }
            ],
        )
        (self.root / "06f_flow_prompt_pack.md").write_text(
            "### U1 — INGREDIENTS\n\n**Paste-ready Flow prompt**\n```text\nKeep the room stable.\n```\n",
            encoding="utf-8",
        )
        run("compile_flow_jobs.py", self.root)
        j = load(self.root / "06o_flow_job_queue.json")["jobs"][0]
        self.assertEqual(j["duration_s"], 4)
        self.assertEqual(j["references"], ["F1", "F2"])
        self.assertEqual(j["source_video_id"], "CLIP")
        run("compile_flow_operator_pack.py", self.root)
        self.assertIn("F1", (self.root / "06p_flow_operator_pack.html").read_text(encoding="utf-8"))


def main():
    global TEST_BASE
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--work-dir", default="work/validation_v31")
    a = p.parse_args()
    TEST_BASE = Path(a.work_dir).resolve()
    TEST_BASE.mkdir(parents=True, exist_ok=True)
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(ProductionTests)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    report = {
        "status": "PASS" if result.wasSuccessful() else "FAIL",
        "tests_run": result.testsRun,
        "failures": [str(t) for t, _ in result.failures],
        "errors": [str(t) for t, _ in result.errors],
        "scope": "Offline synthetic state-machine and real local media execution; no live Image 2.5/Flow calls",
        "evidence_root": str(TEST_BASE),
        "ffmpeg": ffmpeg(),
        "time": now(),
    }
    save(TEST_BASE / "validation_summary.json", report)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
