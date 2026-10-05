"""Preserved behavioral assertions, using deterministic synthetic fixtures."""

import csv
import json
from PIL import Image
from tests.support.fixtures import (
    FixtureCase,
    run,
    image,
    table,
    rt,
    update,
    apply_plan,
)
from historical_shortfilm_director.runtime.common import (
    local,
    load,
    save,
    sha,
    register,
    gate_status,
)
from historical_shortfilm_director.reviews.packet import build


class TestRuntime(FixtureCase):
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

    def test_paths_and_nonempty_initializer(self):
        for p in ("../escape.png", "assets/CON.png", "assets/a:bad.png"):
            with self.assertRaises(ValueError):
                local(self.root, p)
        run("init_project.py", "--title", "no overwrite", "--dir", self.root, good=False)

    def test_subtitle_rollover_and_mixed_fonts(self):
        from historical_shortfilm_director.media.subtitles import ass_time, font_runs

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
