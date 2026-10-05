"""Preserved behavioral assertions, using deterministic synthetic fixtures."""

import tests.support.fixtures as prior
from tests.support.fixtures import (
    FixtureCase,
    rt,
)
from historical_shortfilm_director.runtime.common import (
    load,
    save,
    sha,
    register,
)
from historical_shortfilm_director.production.graph import compile_graph, validate
from historical_shortfilm_director.production.prepare import prepare
from historical_shortfilm_director.media.animatic import build, resolve_frame


class TestGraph(FixtureCase):
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

    def test_animatic_missing_frame_does_not_export_partial(self):
        g = self.graph()
        g["frames"][1]["preview_path"] = "materials/missing.png"
        self.store_graph(g)
        compile_graph(self.root)
        with self.assertRaisesRegex(ValueError, "missing"):
            build(self.root)
        self.assertEqual(list((self.root / "previews").glob("*.mp4")), [])

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
