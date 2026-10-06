"""Code video route without FFmpeg or OpenCV: planning, policy, scenes, previews and authoring."""

import csv
import json
import os
import re
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
from PIL import Image, ImageChops

import historical_shortfilm_director.runtime.engine as rt
from historical_shortfilm_director.cli import main
from historical_shortfilm_director.production.graph import validate
from historical_shortfilm_director.providers.capabilities import capability
from historical_shortfilm_director.providers.code import render_settings
from historical_shortfilm_director.providers.code.brief import write_brief
from historical_shortfilm_director.providers.code.claude import author, probe_claude
from historical_shortfilm_director.providers.code.render import preview, probe, read_program, render
from historical_shortfilm_director.providers.code.scene import (
    FORMAT_REFERENCE,
    SceneError,
    SceneRenderer,
    validate_scene,
    value_at,
)
from historical_shortfilm_director.runtime.common import load, save, sha
from tests.support.code_video import SCENE, CodeCase, fake_cli
from tests.support.fixtures import image, run

REPOSITORY = Path(__file__).resolve().parents[2]


def scene(*layers, **top):
    return {"schema": "hsd-scene/1", "layers": list(layers), **top}


def frames(document, size=(320, 180), count=25, assets=None, inputs=("P",)):
    normalized = validate_scene(document, count / 25, set(inputs))
    renderer = SceneRenderer(normalized, size[0], size[1], 25, count, assets or {})
    return renderer, [renderer.frame(index) for index in range(count)]


class TestCodePlanning(CodeCase):
    def test_code_unit_compiles_to_a_local_render_job(self):
        job_id, _ = self.code_project()
        job = rt.jobs(self.root)[job_id]
        assert (job["provider"], job["mode"]) == ("code", "CODE")
        assert (job["width"], job["height"], job["fps"]) == (320, 180, 25)
        assert job["approved_output"] == "generated/code_approved/U1.mp4"
        assert job["references"] == ["PLATE"]
        assert job["prompt"].startswith("Render this unit locally")
        assert "Push slowly toward the rectangle." in job["prompt"]
        assert "CODE / CODE_PROGRAM" in (self.root / "06f_flow_prompt_pack.md").read_text(
            encoding="utf-8"
        )
        run("review_flow_endpoints.py", self.root)

    def test_graph_rejects_what_a_local_renderer_cannot_honour(self):
        image(self.root / "materials/plate.png")
        with pytest.raises(ValueError, match="source video"):
            validate(self.root, self.code_graph(source_video="PLATE"))
        graph = self.code_graph()
        graph["units"].insert(0, {**graph["units"][0], "id": "U0", "mode": "T2V"})
        graph["joins"] = [
            {"id": "J", "from": "U0", "to": "U1", "type": "FLOW_EXTEND", "fallback": "Cut"}
        ]
        with pytest.raises(ValueError, match="FLOW_EXTEND"):
            validate(self.root, graph)
        for render_block, message in (
            ({"width": 321}, "even"),
            ({"fps": 0}, "fps"),
            ({"codec": "h264"}, "unknown"),
            ({"width": True}, "width"),
        ):
            with pytest.raises(ValueError, match=message):
                validate(self.root, {**self.code_graph(), "render": render_block})
        assert render_settings({}) == {"width": 1920, "height": 1080, "fps": 25}

    def test_code_job_readiness_needs_g2_budget_and_an_observed_renderer(self):
        job_id, _ = self.code_project(observed=False, limit=None, visual=False)
        reasons = next(j for j in rt.next_jobs(self.root)["jobs"] if j["job_id"] == job_id)
        assert reasons["provider"] == "code"
        assert {"G2_VISUAL", "CAPABILITY_UNAVAILABLE", "OUTPUT_LIMIT_MISSING"} <= set(
            reasons["reasons"]
        )

    def test_code_capability_is_local_render_only(self):
        job_id, _ = self.code_project()
        job = rt.jobs(self.root)[job_id]
        selected, errors = capability(self.root, job)
        assert errors == [] and selected["execution"] == "local-render"
        caps = load(self.root / "00_capability_snapshot.json")
        caps["code"]["execution"] = "operator"
        caps["video"] = {**caps["code"], "execution": "local-render"}
        save(self.root / "00_capability_snapshot.json", caps)
        assert capability(self.root, job)[1] == ["EXECUTION_UNSUPPORTED"]
        video_job = {"provider": "video", "mode": "FRAMES", "duration_s": 2}
        assert capability(self.root, video_job)[1] == ["EXECUTION_UNSUPPORTED"]
        caps["code"].update(execution="local-render", observed_at="2000-01-01T00:00:00+00:00")
        save(self.root / "00_capability_snapshot.json", caps)
        assert capability(self.root, job)[1] == ["CAPABILITY_STALE"]

    def test_assembly_reads_each_providers_approved_output(self):
        job_id, _ = self.code_project()
        run("compile_direct_assembly.py", self.root)
        with (self.root / "06k_direct_assembly_manifest.csv").open(encoding="utf-8-sig") as f:
            (row,) = list(csv.DictReader(f))
        assert row["source_clip"] == "generated/code_approved/U1.mp4"
        assert row["status"] == "HOLD_MEDIA_NOT_ACCEPTED"


def test_neutral_video_projects_assemble_from_their_own_approved_path(tmp_path):
    project = tmp_path / "project"
    assert main(["init", "--title", "Generic", "--dir", str(project)]) == 0
    image(project / "materials/a.png")
    graph = {
        "schema_version": "3.2",
        "title": "Generic",
        "external_refs": [],
        "frames": [{"id": "A", "route": "IMAGE_SYNTH", "task": "Synthetic"}],
        "units": [
            {
                "id": "U1",
                "mode": "START_FRAME",
                "start": "A",
                "duration_s": 2,
                "edit_s": 2,
                "action": "Hold.",
                "camera": "Locked.",
            }
        ],
        "joins": [],
    }
    save(project / "03_production_graph.json", graph)
    assert main(["prepare", str(project)]) == 0
    run("compile_direct_assembly.py", project)
    with (project / "06k_direct_assembly_manifest.csv").open(encoding="utf-8-sig") as f:
        (row,) = list(csv.DictReader(f))
    assert row["source_clip"] == "generated/video_approved/U1.mp4"


def test_scene_validation_reports_every_problem_with_its_path():
    with pytest.raises(SceneError) as caught:
        validate_scene(
            {
                "schema": "hsd-scene/2",
                "layers": [
                    {"type": "image", "asset": "SECRET", "keys": [{"t": 1, "zoom": 2}]},
                    {"type": "text", "text": "", "keys": [{"t": 0.5, "opacity": 2}]},
                    {"type": "rect", "keys": [{"t": 0.5, "w": 0.2}, {"t": 0.5, "w": 0.4}]},
                    {"type": "video"},
                ],
            },
            1,
            {"P"},
        )
    problems = "\n".join(caught.value.problems)
    for expected in (
        "schema: must be 'hsd-scene/1'",
        "layers[0].asset: must be one of this job's inputs ['P']",
        "layers[0].keys[0]: unknown fields ['zoom']",
        "layers[0].keys[0]: sets no animatable property",
        "layers[1].text",
        "layers[1].keys[0].opacity: must be in 0..1",
        "layers[2].keys[1].t: must be greater than the previous key's t",
        "layers[3].type",
    ):
        assert expected in problems
    with pytest.raises(SceneError, match="finite"):
        validate_scene(scene({"type": "rect", "x": float("nan")}), 1, set())


def test_documented_scene_examples_validate():
    example = FORMAT_REFERENCE.split("fading caption.\n", 1)[1]
    validate_scene(json.loads(example), 4, {"SRC_GATE"})
    reference = (REPOSITORY / "references/providers/CLAUDE_CODE_VIDEO.md").read_text("utf-8")
    documented = [
        json.loads(block) for block in re.findall(r"```json\n(.*?)\n```", reference, re.S)
    ]
    scenes = [block for block in documented if block.get("schema") == "hsd-scene/1"]
    assert scenes
    for document in scenes:
        validate_scene(document, 4, {"SRC_GATE", "SRC_LETTER", "FONT_SERIF"})


def test_keyframes_ease_hold_and_layer_constants():
    track = [(0.0, 0.0, "linear"), (1.0, 10.0, "in_out"), (2.0, 20.0, "hold")]
    assert value_at(track, -1, 99) == 0.0
    assert value_at(track, 0.25, 99) == pytest.approx(0.625)
    assert value_at(track, 0.5, 99) == 5.0
    assert value_at(track, 1.25, 99) == 10.0
    assert value_at(track, 1.999, 99) == 10.0
    assert value_at(track, 2.0, 99) == 20.0
    assert value_at([], 1, 99) == 99
    layer = validate_scene(
        scene({"type": "rect", "opacity": 0.5, "keys": [{"t": 0, "w": 0.5}]}), 1, set()
    )
    from historical_shortfilm_director.providers.code.scene import state_at

    state = state_at(layer["layers"][0], 0.5)
    assert state["opacity"] == 0.5 and state["w"] == 0.5 and state["h"] == 1.0


def test_scene_frames_preserve_pixels_move_and_report_gaps(tmp_path):
    source = image(tmp_path / "plate.png")
    _, (still, *_) = frames(
        scene({"type": "image", "asset": "P", "fit": "none"}), count=2, assets={"P": source}
    )
    assert ImageChops.difference(still, Image.open(source).convert("RGB")).getbbox() is None
    push = scene(
        {
            "type": "image",
            "asset": "P",
            "keys": [{"t": 0, "scale": 1}, {"t": 0.96, "scale": 1.5, "ease": "in_out"}],
        }
    )
    renderer, shown = frames(push, assets={"P": source})
    assert ImageChops.difference(shown[0], shown[-1]).getbbox() is not None
    assert renderer.warnings() == []
    renderer, _ = frames(scene({"type": "image", "asset": "P", "scale": 0.8}), assets={"P": source})
    assert "cover-fit layers leave the background visible in 25 frame(s)" in renderer.warnings()[0]
    titled = scene(
        {"type": "rect", "color": "#204060"},
        {"type": "text", "text": "Synthetic", "size": 0.2, "start_s": 0.4},
        {"type": "rect", "color": "#FF0000", "x": 0, "y": 0, "w": 0.1, "h": 0.1, "end_s": 0.2},
    )
    renderer, shown = frames(titled, inputs=())
    assert shown[0].getpixel((5, 5)) == (255, 0, 0)
    assert shown[10].getpixel((5, 5)) == (32, 64, 96)
    assert shown[0].getpixel((160, 90)) == (32, 64, 96)
    assert any(shown[20].getpixel((x, 90)) != (32, 64, 96) for x in range(100, 220))
    assert renderer.fonts and renderer.fonts[0]["default"].startswith("Pillow")
    # Centred multi-line text has fractional layout offsets; it must still rasterize.
    centred = scene({"type": "text", "text": "Two\ncentred lines", "align": "center"})
    _, shown = frames(centred, count=2, inputs=())
    assert shown[0].getbbox() is not None


class TestCodeLocalCommands(CodeCase):
    def test_preview_records_nothing(self):
        job_id, program = self.code_project()
        state = sha(self.root / "06t_execution_state.json")
        result = preview(self.root, job_id, program, [0, 1.96])
        assert result["status"] == "PREVIEW_ONLY"
        assert [still["index"] for still in result["stills"]] == [0, 49]
        for still in result["stills"]:
            assert Image.open(self.root / still["path"]).size == (320, 180)
        assert (self.root / result["contact_sheet"]).is_file()
        assert sha(self.root / "06t_execution_state.json") == state
        assert not (self.root / "work/code_renders").exists()

    def test_python_programs_are_opt_in(self):
        job_id, _ = self.code_project()
        (self.root / "programs/u1.py").write_text("print('frames')\n", encoding="utf-8")
        with pytest.raises(ValueError, match="disabled"):
            preview(self.root, job_id, "programs/u1.py")
        self.allow(code_render={"python_programs": True, "timeout_s": 60})
        from historical_shortfilm_director.providers.code.render import render_policy

        settings = {"duration_s": 2.0}
        item = read_program(
            self.root, "programs/u1.py", {"PLATE"}, settings, render_policy(self.root)
        )
        assert item["kind"] == "python"
        with pytest.raises(ValueError, match="outside project"):
            read_program(self.root, "../escape.json", set(), settings, render_policy(self.root))

    def test_hand_written_code_receipts_are_rejected(self):
        job_id, _ = self.code_project()
        token = rt.claim(self.root, job_id)["token"]
        forged = {"handle": "manual", "evidence": "Rendered elsewhere", "actual_mode": "CODE"}
        with pytest.raises(ValueError, match="hsd code render"):
            rt.receipt(self.root, job_id, token, forged)
        forged.update(
            handle="local-render:abc",
            evidence="work/code_renders/abc/render.json",
            render_receipt_sha256="0" * 64,
        )
        with pytest.raises(ValueError, match="missing or changed"):
            rt.receipt(self.root, job_id, token, forged)
        assert "receipt" not in rt.state(self.root)["jobs"][job_id]["attempts"][-1]

    def test_render_refuses_an_unready_job_without_touching_state(self):
        job_id, program = self.code_project(visual=False)
        state = sha(self.root / "06t_execution_state.json")
        with pytest.raises(ValueError, match="G2_VISUAL"):
            render(self.root, job_id, program)
        assert sha(self.root / "06t_execution_state.json") == state
        assert not (self.root / "work/code_renders").exists()

    def test_brief_carries_contract_format_inputs_and_format_reference(self):
        job_id, _ = self.code_project()
        path, text = write_brief(self.root, job_id)
        # Compare files, not spellings: Windows may resolve 8.3 short names in temp paths.
        assert path.samefile(self.root / "work/code_briefs/FLOW_U1.md")
        for expected in (
            "Render this unit locally",
            "320x180 at 25 fps: 50 frames covering 2 s",
            "the last frame is at t = 1.960 s",
            "| `PLATE` | `materials/plate.png` | 320x180 | SOURCE_VERIFIED |",
            "Write exactly one file: `programs/U1.scene.json`",
            "hsd-scene/1",
        ):
            assert expected in text
        assert "Python programs" not in text
        assert main(["code", "brief", str(self.root), job_id]) == 0

    def test_probe_records_an_unavailable_toolchain_instead_of_guessing(self):
        self.code_project()
        with patch.dict(os.environ, {"HSD_FFMPEG": str(self.root / "work/no-ffmpeg")}):
            observation = probe(self.root)
        assert observation["available"] is False and "FFmpeg missing" in observation["evidence"]
        assert load(self.root / "00_capability_snapshot.json")["code"] == observation


class TestCodeAuthoring(CodeCase):
    """Headless sessions against an offline fake CLI; no model, network or paid call."""

    def setUp(self):
        super().setUp()
        directory = tempfile.TemporaryDirectory(prefix="hsd_fake_cli_")
        self.addCleanup(directory.cleanup)
        self.cli = Path(directory.name)
        environment = patch.dict(os.environ, {"HSD_CLAUDE": str(fake_cli(self.cli))})
        environment.start()
        self.addCleanup(environment.stop)
        os.environ.pop("CLAUDECODE", None)

    def writes(self, document):
        (self.cli / "scene_to_write.json").write_text(json.dumps(document), encoding="utf-8")

    def test_author_is_refused_inside_claude_code_and_before_observation(self):
        job_id, _ = self.code_project()
        self.allow(claude_code_session_limit=2)
        with patch.dict(os.environ, {"CLAUDECODE": "1"}):
            with self.assertRaisesRegex(RuntimeError, "nested"):
                author(self.root, job_id)
        with self.assertRaisesRegex(ValueError, "probe"):
            author(self.root, job_id)
        self.assertNotIn("authoring", rt.state(self.root))

    def test_headless_session_is_budgeted_confined_and_recorded(self):
        job_id, _ = self.code_project()
        observation = probe_claude(self.root)
        self.assertTrue(observation["available"], observation)
        self.assertEqual(
            observation["flags"],
            [
                "--max-budget-usd",
                "--model",
                "--output-format",
                "--permission-mode",
                "--print",
                "--tools",
            ],
        )
        with self.assertRaisesRegex(ValueError, "claude_code_session_limit"):
            author(self.root, job_id)
        self.allow(claude_code_session_limit=2, claude_code_max_budget_usd=0.5)
        self.writes(SCENE)
        result = author(self.root, job_id, model="sonnet")
        self.assertEqual(result["status"], "SCENE_WRITTEN")
        session = result["session"]
        self.assertEqual((session["status"], session["program_problems"]), ("COMPLETED", []))
        self.assertEqual(session["session_id"], "offline-fixture")
        self.assertEqual(result["recorded_cost_usd"], 0.25)
        workdir = self.root / session["workdir"]
        argv = json.loads((workdir / "argv.json").read_text(encoding="utf-8"))
        self.assertEqual(argv[0], "--print")
        self.assertIn("BRIEF.md", argv[1])
        self.assertEqual(argv[argv.index("--tools") + 1], "Read,Write,Edit")
        self.assertEqual(argv[argv.index("--permission-mode") + 1], "acceptEdits")
        self.assertEqual(argv[argv.index("--max-budget-usd") + 1], "0.5")
        self.assertEqual(argv[argv.index("--model") + 1], "sonnet")
        self.assertEqual(session["unexpected_files"], ["argv.json"])
        self.assertFalse((workdir / "inputs").exists())
        brief = (workdir / "BRIEF.md").read_text(encoding="utf-8")
        self.assertIn("Input images are not shared", brief)
        # A failed session still counts, and the limit then stops further spending.
        (self.cli / "scene_to_write.json").unlink()
        (self.cli / "exit_code.txt").write_text("1", encoding="utf-8")
        with self.assertRaisesRegex(RuntimeError, "no usable scene"):
            author(self.root, job_id)
        statuses = [s["status"] for s in rt.state(self.root)["authoring"]]
        self.assertEqual(statuses, ["COMPLETED", "FAILED"])
        with self.assertRaisesRegex(ValueError, "AUTHOR_SESSION_LIMIT_REACHED"):
            author(self.root, job_id)

    def test_shared_inputs_and_invalid_scenes_reach_the_next_brief(self):
        job_id, _ = self.code_project()
        probe_claude(self.root)
        self.allow(claude_code_session_limit=3, claude_code_share_inputs=True)
        self.writes({"schema": "hsd-scene/1", "layers": [{"type": "image", "asset": "OTHER"}]})
        result = author(self.root, job_id)
        self.assertEqual(result["status"], "INVALID_SCENE")
        self.assertTrue((self.root / result["session"]["workdir"] / "inputs/PLATE.png").is_file())
        _, text = write_brief(self.root, job_id)
        self.assertIn("wrote an invalid scene", text)
        self.assertIn("layers[0].asset", text)

    def test_probe_rejects_a_cli_without_tool_restriction(self):
        self.code_project()
        script = self.cli / "fake_claude.py"
        script.write_text(script.read_text(encoding="utf-8").replace("--tools", "--other"), "utf-8")
        observation = probe_claude(self.root)
        self.assertFalse(observation["available"])
        self.assertIn("--tools", observation["problems"][0])

    def test_unready_job_spends_no_session(self):
        job_id, _ = self.code_project(visual=False)
        probe_claude(self.root)
        self.allow(claude_code_session_limit=1)
        with self.assertRaisesRegex(ValueError, "G2_VISUAL"):
            author(self.root, job_id)
        self.assertNotIn("authoring", rt.state(self.root))


def test_shipped_example_scenes_validate_and_preview(tmp_path):
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "code_video_example", REPOSITORY / "examples/claude-code-video/create_demo.py"
    )
    example = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(example)
    project = example.create(tmp_path / "demo")
    assert main(["prepare", str(project)]) == 0
    jobs = rt.jobs(project)
    assert {job["provider"] for job in jobs.values()} == {"code"}
    from historical_shortfilm_director.providers.code.render import job_context, render_policy

    for job_id, program in (
        ("FLOW_U1", "programs/U1.scene.json"),
        ("FLOW_U2", "programs/U2.scene.json"),
    ):
        _, refs, _, settings = job_context(project, job_id)
        read_program(
            project, program, {r["asset_id"] for r in refs}, settings, render_policy(project)
        )
    result = preview(project, "FLOW_U1", "programs/U1.scene.json", [3.96])
    assert result["warnings"] == []
