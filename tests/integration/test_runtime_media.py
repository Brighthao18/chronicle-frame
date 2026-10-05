"""Preserved behavioral assertions, using deterministic synthetic fixtures."""

import wave
from tests.support.fixtures import (
    FixtureCase,
    run,
    image,
    table,
    rt,
    update,
    render,
    extract,
)
from historical_shortfilm_director.runtime.common import (
    load,
    register,
    media_check,
)
import pytest

cv2 = pytest.importorskip("cv2")
np = pytest.importorskip("numpy")

pytestmark = pytest.mark.slow


class TestRuntimeMedia(FixtureCase):
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
