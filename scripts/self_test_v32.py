"""3.2 behavioral suite, including every 3.1 regression and real preview encoding."""

import argparse
import json
import unittest
import wave
from pathlib import Path
from production_common import load
from historical_shortfilm_director import __version__
import numpy as np
import self_test_v31 as prior
from production_common import save, sha, register, ffmpeg, now
from compile_scene_graph import compile_graph, validate
from build_animatic import build, resolve_frame
from prepare_production import prepare
import production_runtime as rt


class GraphTests(prior.ProductionTests):
    def test_preview_rejects_stale_reviewed_candidate(self):
        src = prior.image(self.root / "materials/src.png")
        register(self.root, "SRC", str(src), status="SOURCE_VERIFIED")
        a = self.image_job("A", references=["SRC"])
        self.queue(a)
        c = self.generate(a)
        self.passing(a, c)
        self.assertEqual(
            resolve_frame(self.root, "A", None)[1], "reviewed-candidate-not-human-approved"
        )
        prior.image(src, "maroon")
        with self.assertRaisesRegex(ValueError, "Stale preview"):
            resolve_frame(self.root, "A", None)

    def test_preview_rejects_changed_registered_producer(self):
        a = self.image_job("A")
        self.queue(a)
        c = self.generate(a)
        self.passing(a, c)
        rt.accept(self.root, a["job_id"])
        self.assertEqual(resolve_frame(self.root, "A", None)[1], "registered")
        a["image_task"] = "Different intended frame"
        save(self.root / "06i_image25_job_queue.json", {"jobs": [a]})
        with self.assertRaisesRegex(ValueError, "Stale preview"):
            resolve_frame(self.root, "A", None)

    def test_preview_resume_rejects_same_duration_swapped_picture(self):
        from unittest.mock import patch
        import shutil

        self.store_graph(self.graph())
        compile_graph(self.root)
        original = shutil.copy2

        def interrupt_copy(src, dst, *args, **kwargs):
            if Path(src).name == "picture.mp4":
                raise RuntimeError("OFFLINE interrupted final export")
            return original(src, dst, *args, **kwargs)

        with patch("shutil.copy2", side_effect=interrupt_copy):
            with self.assertRaisesRegex(RuntimeError, "interrupted"):
                build(self.root)
        picture = next((self.root / "work/animatic").glob("*/picture.mp4"))
        # Keep a valid same-duration video but alter bytes: no full-decode/duration-only check can detect this.
        with picture.open("ab") as f:
            f.write(b"OFFLINE_CACHE_TAMPER")
        with self.assertRaisesRegex(ValueError, "provenance mismatch"):
            build(self.root)

    def graph(self):
        prior.image(self.root / "materials/a.png")
        prior.image(self.root / "materials/b.png", "teal")
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

    def test_graph_compiles_consistent_trim_and_preview(self):
        g = self.graph()
        self.store_graph(g)
        report = compile_graph(self.root)
        self.assertEqual(report["unit_count"], 2)
        self.assertEqual(report["planned_duration_s"], 2)
        result = prepare(self.root)
        self.assertEqual(result["status"], "READY_WORK")
        self.assertEqual({x["job_id"] for x in result["ready"]}, {"IMG25_A", "IMG25_B"})
        q = load(self.root / "06o_flow_job_queue.json")["jobs"]
        self.assertEqual(q[0]["use_out_s"], 1.2)
        self.assertEqual(
            load(self.root / "05v_animatic_timeline.json")["units"][0]["duration_s"], 1
        )

    def test_graph_recompile_is_idempotent_and_keeps_active_receipt(self):
        self.store_graph(self.graph())
        prepare(self.root)
        p = rt.claim(self.root, "IMG25_A")
        rt.receipt(
            self.root,
            "IMG25_A",
            p["token"],
            {"handle": "OFFLINE", "evidence": "Fixture, not provider"},
        )
        again = prepare(self.root)
        self.assertTrue(again["compilation"]["unchanged"])
        self.assertEqual(again["existing_attempts"][0]["receipt"]["handle"], "OFFLINE")

    def test_graph_manual_plan_edits_are_not_overwritten(self):
        g = self.graph()
        self.store_graph(g)
        compile_graph(self.root)
        p = self.root / "05f_shot_endpoint_plan.md"
        p.write_text(p.read_text(encoding="utf-8") + "Manual annotation\n", encoding="utf-8")
        before = sha(p)
        g["units"][0]["action"] = "Changed action"
        self.store_graph(g)
        with self.assertRaisesRegex(ValueError, "manually edited"):
            compile_graph(self.root)
        self.assertEqual(sha(p), before)

    def test_graph_rejects_unknown_fields_and_nonfinite_timing(self):
        g = self.graph()
        g["units"][0]["duraton_s"] = 4
        with self.assertRaisesRegex(ValueError, "unknown"):
            validate(self.root, g)
        g = self.graph()
        g["units"][0]["edit_s"] = float("nan")
        with self.assertRaisesRegex(ValueError, "finite"):
            validate(self.root, g)

    def test_graph_rejects_bad_trims_missing_joins_and_cycles(self):
        g = self.graph()
        g["units"][0]["in_s"] = 1.8
        with self.assertRaisesRegex(ValueError, "Trim"):
            validate(self.root, g)
        g = self.graph()
        g["joins"] = []
        with self.assertRaisesRegex(ValueError, "adjacent"):
            validate(self.root, g)
        g = self.graph()
        g["frames"][0]["refs"] = ["B"]
        g["frames"][1]["refs"] = ["A"]
        with self.assertRaisesRegex(ValueError, "cycle"):
            validate(self.root, g)

    def test_graph_exact_seam_is_not_just_a_label(self):
        g = self.graph()
        g["joins"][0].update(type="EXACT_SEAM", seam="A")
        with self.assertRaisesRegex(ValueError, "EXACT_SEAM"):
            validate(self.root, g)

    def test_graph_invalid_text_leaves_existing_plans_intact(self):
        g = self.graph()
        self.store_graph(g)
        compile_graph(self.root)
        before = sha(self.root / "03d_frame_asset_plan.md")
        g["frames"][0]["task"] = "Contains | a broken table cell"
        self.store_graph(g)
        with self.assertRaisesRegex(ValueError, "single-line"):
            compile_graph(self.root)
        self.assertEqual(sha(self.root / "03d_frame_asset_plan.md"), before)

    def test_animatic_real_encode_audio_and_no_gate_mutation(self):
        g = self.graph()
        audio = self.root / "work/scratch.wav"
        with wave.open(str(audio), "w") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(24000)
            w.writeframes(np.zeros(6000, dtype=np.int16).tobytes())
        g["preview"]["audio"] = "work/scratch.wav"
        self.store_graph(g)
        compile_graph(self.root)
        gates = sha(self.root / "00_pipeline_control.json")
        result = build(self.root)
        self.assertEqual(result["status"], "PREVIEW_ONLY")
        self.assertAlmostEqual(result["duration_s"], 2, places=2)
        self.assertEqual(result["fps"], 25)
        self.assertEqual(result["full_decode"], "PASS")
        import cv2

        cap = cv2.VideoCapture(str(self.root / result["path"]))
        _, first = cap.read()
        cap.set(cv2.CAP_PROP_POS_FRAMES, 40)
        _, last = cap.read()
        cap.release()
        self.assertLess(int(first[5, 160, 1]), 20)
        self.assertGreater(int(last[5, 160, 1]), 80)  # the second state really appears, in order
        self.assertEqual(len(result["markers"]), 2)
        self.assertEqual(sha(self.root / "00_pipeline_control.json"), gates)
        self.assertTrue(build(self.root)["unchanged"])

    def test_animatic_missing_frame_does_not_export_partial(self):
        g = self.graph()
        g["frames"][1]["preview_path"] = "materials/missing.png"
        self.store_graph(g)
        compile_graph(self.root)
        with self.assertRaisesRegex(ValueError, "missing"):
            build(self.root)
        self.assertEqual(list((self.root / "previews").glob("*.mp4")), [])

    def test_animatic_changed_inputs_make_new_version(self):
        self.store_graph(self.graph())
        compile_graph(self.root)
        a = build(self.root)
        prior.image(self.root / "materials/b.png", "maroon")
        b = build(self.root)
        self.assertNotEqual(a["path"], b["path"])
        self.assertTrue((self.root / a["path"]).exists())

    def test_dispatch_detects_transitive_stale_source_without_sync(self):
        src = prior.image(self.root / "materials/src.png")
        register(self.root, "SRC", str(src), status="SOURCE_VERIFIED")
        a = self.image_job("A", references=["SRC"])
        b = self.image_job("B", references=["A"])
        self.queue(a, b)
        c = self.generate(a)
        self.passing(a, c)
        rt.accept(self.root, a["job_id"])
        prior.image(src, "maroon")  # no sync and no registry refresh
        with self.assertRaisesRegex(ValueError, "PRODUCER_STALE"):
            rt.claim(self.root, b["job_id"])

    def test_dispatch_detects_changed_parent_contract_without_sync(self):
        a = self.image_job("A")
        b = self.image_job("B", references=["A"])
        self.queue(a, b)
        c = self.generate(a)
        self.passing(a, c)
        rt.accept(self.root, a["job_id"])
        a["image_task"] = "Different approved intent"
        save(self.root / "06i_image25_job_queue.json", {"jobs": [a, b]})
        with self.assertRaisesRegex(ValueError, "PRODUCER_STALE"):
            rt.claim(self.root, b["job_id"])

    def test_new_cli_commands_and_documented_example(self):
        import re

        reference = Path(__file__).resolve().parents[1] / "references/PRODUCTION_GRAPH.md"
        example = json.loads(
            re.search(r"```json\n(.*?)\n```", reference.read_text(encoding="utf-8"), re.S).group(1)
        )
        validate(self.root, example)
        self.store_graph(self.graph())
        prepared = json.loads(prior.run("prepare_production.py", self.root).stdout)
        self.assertEqual(prepared["status"], "READY_WORK")
        preview = json.loads(prior.run("build_animatic.py", self.root).stdout)
        self.assertEqual(preview["status"], "PREVIEW_ONLY")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--work-dir", default="work/validation_v32")
    a = p.parse_args()
    prior.TEST_BASE = Path(a.work_dir).resolve()
    prior.TEST_BASE.mkdir(parents=True, exist_ok=True)
    result = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(GraphTests)
    )
    report = {
        "release": __version__,
        "status": "PASS" if result.wasSuccessful() else "FAIL",
        "tests_run": result.testsRun,
        "failures": [str(t) for t, _ in result.failures],
        "errors": [str(t) for t, _ in result.errors],
        "scope": "All 3.1 regressions + graph compilation, preservation, transitive freshness and actual still-based animatic/audio encoding. No live provider calls.",
        "ffmpeg": ffmpeg(),
        "time": now(),
        "evidence_root": str(prior.TEST_BASE),
    }
    save(prior.TEST_BASE / "validation_summary.json", report)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
