"""Code video route with real local encoding: render, review, accept and assemble."""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

import historical_shortfilm_director.runtime.engine as rt
from historical_shortfilm_director.providers.code.claude import author, probe_claude
from historical_shortfilm_director.providers.code.render import render
from historical_shortfilm_director.providers.code.scene import SceneError
from historical_shortfilm_director.runtime.common import load, media_check, register, save, sha
from tests.support.code_video import SCENE, CodeCase, fake_cli
from tests.support.fixtures import render as prior_render
from tests.support.fixtures import run

cv2 = pytest.importorskip("cv2")
np = pytest.importorskip("numpy")

pytestmark = pytest.mark.slow

PROGRAM = """\
import json
import os
import sys
from PIL import Image, ImageDraw

context = json.load(open(sys.argv[1], encoding="utf-8"))
with open("environment.json", "w", encoding="utf-8") as handle:
    json.dump(sorted(os.environ), handle)
plate = Image.open(context["inputs"]["PLATE"]["path"]).convert("RGB")
for index in context["frame_indices"][: context.get("limit")]:
    frame = plate.resize((context["width"], context["height"]))
    ImageDraw.Draw(frame).rectangle((index * 4, 10, index * 4 + 20, 30), fill=(255, 200, 0))
    frame.save(os.path.join(context["frames_dir"], f"{index:06d}.png"), compress_level=1)
"""


def frame(path, index):
    capture = cv2.VideoCapture(str(path))
    capture.set(cv2.CAP_PROP_POS_FRAMES, index)
    ok, image = capture.read()
    capture.release()
    assert ok
    return image


class TestCodeVideoMedia(CodeCase):
    def review(self, result, failed=None, failure_code=None):
        data = load(self.root / result["review_template"])
        data.update(
            reviewer="OFFLINE_TEST",
            notes="Fixture-specific test of state transitions only; not a historical judgment.",
            score=90,
            checks={check: "PASS" for check in data["checks"]},
        )
        if failed:
            data["checks"][failed] = "FAIL"
            data["failure_code"] = failure_code
        return rt.review(self.root, result["job_id"], data)

    def test_render_review_accept_and_assemble(self):
        job_id, program = self.code_project()
        result = render(self.root, job_id, program, author="OFFLINE TEST")
        candidate = self.root / result["candidate"]["path"]
        meta = media_check(candidate, self.root)
        self.assertEqual((meta["width"], meta["height"], meta["fps"]), (320, 180, 25))
        self.assertEqual(round(meta["duration_s"] * meta["fps"]), 50)
        self.assertGreater(
            float(np.mean(cv2.absdiff(frame(candidate, 0), frame(candidate, 49)))), 2
        )
        receipt = load(self.root / result["render_receipt"])
        self.assertEqual(receipt["status"], "RENDERED")
        self.assertEqual(receipt["program"]["sha256"], sha(self.root / program))
        self.assertEqual(receipt["author"], {"declared": "OFFLINE TEST"})
        self.assertEqual([item["asset_id"] for item in receipt["inputs"]], ["PLATE"])
        self.assertTrue(receipt["toolchain"]["libx264"])
        self.assertNotIn(str(self.root), json.dumps(receipt["encoder"]))
        attempt = rt.state(self.root)["jobs"][job_id]["attempts"][-1]
        self.assertEqual(attempt["receipt"]["handle"], "local-render:" + result["render_id"])
        self.assertEqual(attempt["receipt"]["actual_mode"], "CODE")
        self.assertEqual(
            attempt["receipt"]["render_receipt_sha256"], sha(self.root / result["render_receipt"])
        )
        self.assertTrue((self.root / result["contact_sheet"]).is_file())
        # The template cannot pass as a review until a reviewer fills in real judgments.
        with self.assertRaises(ValueError):
            rt.review(self.root, job_id, load(self.root / result["review_template"]))
        self.review(result)
        asset = rt.accept(self.root, job_id)
        self.assertEqual(asset["path"], "generated/code_approved/U1.mp4")
        self.assertEqual(asset["provider_receipt"]["handle"], "local-render:" + result["render_id"])
        entry = next(j for j in rt.next_jobs(self.root)["jobs"] if j["job_id"] == job_id)
        self.assertEqual(entry["reasons"], ["ACCEPTED"])
        run("compile_direct_assembly.py", self.root)
        run("assemble_direct.py", self.root, "--width", "320", "--height", "180", "--execute")
        picture = self.root / "exports/direct_picture_master.mp4"
        self.assertAlmostEqual(media_check(picture, self.root)["duration_s"], 1.6, places=2)

    def test_failures_leave_no_attempt_and_rerendering_is_deterministic(self):
        job_id, program = self.code_project()
        save(self.root / "programs/broken.scene.json", {"schema": "hsd-scene/1", "layers": []})
        with self.assertRaises(SceneError):
            render(self.root, job_id, "programs/broken.scene.json")
        self.assertEqual(rt.state(self.root)["jobs"][job_id]["attempts"], [])
        self.assertFalse((self.root / "work/code_renders").exists())
        first = render(self.root, job_id, program)
        self.review(first, failed="motion_camera", failure_code="CAMERA_FAIL")
        self.assertEqual(rt.state(self.root)["jobs"][job_id]["status"], "QUEUED")
        second = render(self.root, job_id, program)
        self.assertNotEqual(first["render_id"], second["render_id"])
        self.assertEqual(first["candidate"]["sha256"], second["candidate"]["sha256"])
        self.assertEqual(len(rt.state(self.root)["jobs"][job_id]["attempts"]), 2)

    def test_python_program_contract_and_clean_environment(self):
        job_id, _ = self.code_project()
        (self.root / "programs/u1.py").write_text(PROGRAM, encoding="utf-8")
        self.allow(code_render={"python_programs": True, "timeout_s": 120})
        with patch.dict(os.environ, {"HSD_TEST_SECRET": "must-not-reach-programs"}):
            result = render(self.root, job_id, "programs/u1.py", author="OFFLINE TEST")
        bundle = (self.root / result["render_receipt"]).parent
        environment = json.loads((bundle / "environment.json").read_text(encoding="utf-8"))
        self.assertNotIn("HSD_TEST_SECRET", environment)
        self.assertFalse(any(name.startswith(("CLAUDE", "ANTHROPIC")) for name in environment))
        self.assertFalse((bundle / "frames").exists())
        self.assertEqual(load(self.root / result["render_receipt"])["program"]["kind"], "python")
        candidate = self.root / result["candidate"]["path"]
        self.assertEqual(round(media_check(candidate, self.root)["duration_s"] * 25), 50)
        # A program that skips requested frames is rejected before any attempt exists.
        self.review(result, failed="motion_camera", failure_code="MOTION_PATH_FAIL")
        (self.root / "programs/short.py").write_text(
            PROGRAM.replace('context.get("limit")', "10"), encoding="utf-8"
        )
        attempts = len(rt.state(self.root)["jobs"][job_id]["attempts"])
        with self.assertRaisesRegex(ValueError, "do not match"):
            render(self.root, job_id, "programs/short.py")
        self.assertEqual(len(rt.state(self.root)["jobs"][job_id]["attempts"]), attempts)

    def test_an_active_claim_is_fulfilled_and_endpoints_are_enforced(self):
        graph = self.code_graph(start="A")
        self.code_project(graph=graph)
        register(self.root, "A", str(self.root / "materials/plate.png"), status="SOURCE_VERIFIED")
        rt.sync(self.root)
        packet = rt.claim(self.root, "FLOW_U1")
        self.assertIn("hsd code render", packet["next"])
        away = {
            "schema": "hsd-scene/1",
            "layers": [{"type": "image", "asset": "PLATE", "scale": 4, "ax": 0.04, "ay": 0.06}],
        }
        save(self.root / "programs/away.scene.json", away)
        result = render(self.root, "FLOW_U1", "programs/away.scene.json")
        self.assertEqual(result["token"], packet["token"])
        self.review(result)
        with self.assertRaisesRegex(ValueError, "Endpoint/technical pre-screen"):
            rt.accept(self.root, "FLOW_U1")

    def test_receipts_cannot_be_replayed_and_only_the_rendered_file_ingests(self):
        job_id, program = self.code_project()
        with patch.object(rt, "ingest", side_effect=RuntimeError("OFFLINE interrupted ingest")):
            with self.assertRaisesRegex(RuntimeError, "interrupted"):
                render(self.root, job_id, program)
        attempt = rt.state(self.root)["jobs"][job_id]["attempts"][-1]
        staged = (self.root / attempt["receipt"]["evidence"]).parent / "output.mp4"
        other = prior_render(
            {
                "unit": "OTHER",
                "source": str(self.root / "materials/plate.png"),
                "output": "work/other.mp4",
                "width": 320,
                "height": 180,
                "fps": 25,
                "duration_s": 2,
            },
            self.root,
        )
        with self.assertRaisesRegex(ValueError, "Only the rendered output"):
            rt.ingest(self.root, job_id, attempt["token"], other)
        with self.assertRaisesRegex(ValueError, "already has a receipt"):
            render(self.root, job_id, program)
        candidate = rt.ingest(self.root, job_id, attempt["token"], staged)
        self.assertEqual(candidate["sha256"], attempt["receipt"]["output_sha256"])
        # A failed review re-queues the job; the old receipt cannot be replayed on a new claim.
        data = {
            "sha256": candidate["sha256"],
            "reviewer": "OFFLINE_TEST",
            "evidence": [candidate["path"]],
            "checks": {**{c: "PASS" for c in rt.CHECKS}, "motion_camera": "FAIL", "join": "PASS"},
            "score": 40,
            "notes": "Fixture-specific state transition test; not a historical judgment.",
            "failure_code": "CAMERA_FAIL",
        }
        rt.review(self.root, job_id, data)
        token = rt.claim(self.root, job_id)["token"]
        replay = {k: v for k, v in attempt["receipt"].items() if k != "recorded_at"}
        with self.assertRaisesRegex(ValueError, "already receipted"):
            rt.receipt(self.root, job_id, token, replay)

    def test_headless_author_then_render(self):
        job_id, _ = self.code_project()
        directory = tempfile.TemporaryDirectory(prefix="hsd_fake_cli_")
        self.addCleanup(directory.cleanup)
        cli = Path(directory.name)
        (cli / "scene_to_write.json").write_text(json.dumps(SCENE), encoding="utf-8")
        with patch.dict(os.environ, {"HSD_CLAUDE": str(fake_cli(cli))}):
            os.environ.pop("CLAUDECODE", None)
            probe_claude(self.root)
            self.allow(claude_code_session_limit=1)
            result = author(self.root, job_id, then_render=True)
        self.assertEqual(result["status"], "REVIEW_REQUIRED")
        receipt = load(self.root / result["render"]["render_receipt"])
        self.assertEqual(receipt["author"]["kind"], "claude-code-headless")
        self.assertEqual(receipt["author"]["session_id"], "offline-fixture")
        self.assertEqual(receipt["program"]["sha256"], result["session"]["program_sha256"])
