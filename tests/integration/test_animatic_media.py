"""Preserved behavioral assertions, using deterministic synthetic fixtures."""

import json
import wave
from pathlib import Path
import tests.support.fixtures as prior
from tests.support.fixtures import (
    FixtureCase,
)
from historical_shortfilm_director.runtime.common import (
    sha,
)
from historical_shortfilm_director.production.graph import compile_graph, validate
from historical_shortfilm_director.media.animatic import build
import pytest

cv2 = pytest.importorskip("cv2")
np = pytest.importorskip("numpy")

pytestmark = pytest.mark.slow


class TestGraphMedia(FixtureCase):
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

    def test_animatic_changed_inputs_make_new_version(self):
        self.store_graph(self.graph())
        compile_graph(self.root)
        a = build(self.root)
        prior.image(self.root / "materials/b.png", "maroon")
        b = build(self.root)
        self.assertNotEqual(a["path"], b["path"])
        self.assertTrue((self.root / a["path"]).exists())

    def test_new_cli_commands_and_documented_example(self):
        import re

        reference = Path(__file__).resolve().parents[2] / "references/PRODUCTION_GRAPH.md"
        example = json.loads(
            re.search(r"```json\n(.*?)\n```", reference.read_text(encoding="utf-8"), re.S).group(1)
        )
        validate(self.root, example)
        self.store_graph(self.graph())
        prepared = json.loads(prior.run("prepare_production.py", self.root).stdout)
        self.assertEqual(prepared["status"], "READY_WORK")
        preview = json.loads(prior.run("build_animatic.py", self.root).stdout)
        self.assertEqual(preview["status"], "PREVIEW_ONLY")
