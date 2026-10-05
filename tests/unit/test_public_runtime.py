"""Behavior added by the public package, independent of a live provider."""

import subprocess
import sys
from pathlib import Path

import pytest

from historical_shortfilm_director.cli import main
from historical_shortfilm_director.profiles import load_profile, project_profile, profile_qc
from historical_shortfilm_director.production.generation_plan import infer_route
from historical_shortfilm_director.production.graph import compile_graph, validate
from historical_shortfilm_director.providers.capabilities import capability
from historical_shortfilm_director.runtime.common import load, now, save, sha
from tests.support.fixtures import FixtureCase


REPOSITORY = Path(__file__).resolve().parents[2]


def test_core_cli_has_no_site_or_media_dependency(tmp_path):
    code = "import sys,runpy; sys.path.insert(0,sys.argv.pop(1)); sys.argv=['hsd',*sys.argv[1:]]; runpy.run_module('historical_shortfilm_director',run_name='__main__')"
    result = subprocess.run(
        [
            sys.executable,
            "-S",
            "-X",
            "utf8",
            "-c",
            code,
            str(REPOSITORY / "src"),
            "init",
            "--title",
            "Core only",
            "--dir",
            str(tmp_path / "project"),
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert load(tmp_path / "project/project.json")["profile"] == "generic"
    assert "numpy" not in result.stdout


def test_generic_profile_does_not_read_builtin_resources(monkeypatch):
    monkeypatch.setattr(
        Path,
        "glob",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("Profile resource read")),
    )
    assert load_profile("generic").templates == {}


def test_custom_profile_snapshot_survives_missing_original(tmp_path):
    profile = tmp_path / "profile.json"
    save(
        profile,
        {
            "name": "museum",
            "templates": {"extra/notes.md": "Original museum notes"},
            "initialization_files": {"extra/rules.json": {"original": True}},
            "constraints": {"duration_ceiling_seconds": 90, "max_duration_seconds": 90},
            "routing": {"R-D": "OCCLUSION_2STEP"},
        },
    )
    project = tmp_path / "project"
    assert (
        main(["init", "--title", "Museum", "--profile", str(profile), "--dir", str(project)]) == 0
    )
    profile.unlink()
    frozen = project_profile(project)
    assert frozen.name == "museum"
    assert (project / "extra/notes.md").read_text() == "Original museum notes"
    assert load(project / "extra/rules.json")["original"] is True
    assert load(project / "project.json")["profile"] == "museum"
    assert str(tmp_path) not in (project / "project.json").read_text()
    assert infer_route("R-D", "HIGH", frozen) == "OCCLUSION_2STEP"
    errors, _ = profile_qc(project, frozen, {"duration_ceiling_seconds": 91})
    assert errors


@pytest.mark.parametrize("profile_name", ["jnu_gate", "jnu120"])
def test_historical_profile_aliases_and_qc(tmp_path, profile_name):
    project = tmp_path / "project"
    assert (
        main(
            [
                "init",
                "--title",
                "Historical example",
                "--profile",
                profile_name,
                "--dir",
                str(project),
            ]
        )
        == 0
    )
    profile = project_profile(project)
    assert profile.name == "jnu_gate"
    assert (project / "02b_gate_creative_lab.md").is_file()
    assert infer_route("R-D", "HIGH", profile) == "OCCLUSION_2STEP"
    assert not profile_qc(project, profile, load(project / "project.json"))[0]


@pytest.mark.parametrize("target", ["../escape.md", "extra/CON.md", "extra/file:stream.md"])
def test_profile_templates_cannot_escape_project(tmp_path, target):
    profile = tmp_path / "profile.json"
    save(profile, {"name": "unsafe", "templates": {target: "untrusted"}})
    assert (
        main(
            [
                "init",
                "--title",
                "Unsafe",
                "--profile",
                str(profile),
                "--dir",
                str(tmp_path / "project"),
            ]
        )
        == 2
    )
    assert not (tmp_path / "escape.md").exists()


def test_unknown_profile_fails_before_initialization(tmp_path):
    assert (
        main(
            [
                "init",
                "--title",
                "No profile",
                "--profile",
                "missing_profile",
                "--dir",
                str(tmp_path / "project"),
            ]
        )
        == 2
    )
    assert not (tmp_path / "project").exists()


def observed_video(root, **changes):
    mode = {
        "model": "SYNTHETIC_FIXTURE_NOT_REAL",
        "durations_s": [2, 4],
        "max_references": 2,
        "first_frame": True,
        "first_last_frames": True,
    }
    mode.update(changes)
    save(
        root / "00_capability_snapshot.json",
        {
            "video": {
                "available": True,
                "observed_at": now(),
                "evidence": "Deterministic fixture, not live provider evidence",
                "execution": "operator",
                "modes": {"FRAMES": mode},
            }
        },
    )
    return {
        "provider": "video",
        "mode": "FRAMES",
        "duration_s": 3,
        "start_frame_id": "A",
        "end_frame_id": "B",
    }


def test_neutral_video_selects_observed_duration(tmp_path):
    job = observed_video(tmp_path)
    selected, errors = capability(tmp_path, job)
    assert errors == []
    assert selected["duration_s"] == 4
    assert selected["execution"] == "operator"


def test_neutral_video_requires_observed_conditioning(tmp_path):
    job = observed_video(tmp_path, first_last_frames=None)
    assert capability(tmp_path, job)[1] == ["CONDITIONING_UNVERIFIED:first_last_frames"]
    observed_video(tmp_path, first_last_frames=False)
    assert capability(tmp_path, job)[1] == ["CONDITIONING_UNSUPPORTED:first_last_frames"]


def test_reference_and_duration_limits_block_neutral_video(tmp_path):
    job = observed_video(tmp_path, max_references=1)
    assert capability(tmp_path, job)[1] == ["REFERENCE_LIMIT"]
    job = observed_video(tmp_path)
    job["duration_s"] = 5
    assert capability(tmp_path, job)[1] == ["DURATION_UNSUPPORTED"]


def test_unavailable_provider_is_a_local_blocker(tmp_path):
    save(tmp_path / "00_capability_snapshot.json", {})
    assert capability(tmp_path, {"provider": "video"})[1] == ["CAPABILITY_UNAVAILABLE"]


class TestLegacyPlanOwnership(FixtureCase):
    def test_pristine_legacy_templates_are_adopted_without_losing_guard(self):
        graph = self.graph()
        save(self.root / "03_production_graph.json", graph)
        templates = load(
            REPOSITORY / "src/historical_shortfilm_director/data/legacy-templates.json"
        )
        for name in (
            "03d_frame_asset_plan.md",
            "05f_shot_endpoint_plan.md",
            "04c_flow_prompt_blueprints.md",
            "05h_join_contracts.md",
        ):
            (self.root / name).write_text(templates[name], encoding="utf-8")
        result = compile_graph(self.root)
        assert result["unit_count"] == 2
        plan = self.root / "03d_frame_asset_plan.md"
        plan.write_text(plan.read_text(encoding="utf-8") + "Authored note\n", encoding="utf-8")
        before = sha(plan)
        with pytest.raises(ValueError, match="manually edited"):
            compile_graph(self.root)
        assert sha(plan) == before

    def test_neutral_image_routes_validate_and_prepare(self):
        graph = self.graph()
        for frame in graph["frames"]:
            frame["route"] = "IMAGE_SYNTH"
        validate(self.root, graph)
        save(self.root / "03_production_graph.json", graph)
        assert main(["prepare", str(self.root)]) == 0
        assert all(
            job["model_preference"] is None
            for job in load(self.root / "06i_image25_job_queue.json")["jobs"]
        )


def test_all_legacy_migrations_are_dry_run_then_idempotent(tmp_path):
    project = tmp_path / "project"
    project.mkdir()
    save(project / "project.json", {"title": "Synthetic legacy project", "profile": "generic"})
    authored = project / "01_evidence_ledger.md"
    authored.write_text("Original synthetic ledger\n", encoding="utf-8")
    original = sha(authored)
    for revision in ("1.3", "1.4", "1.5", "1.6", "1.7", "1.8", "1.9", "1.10", "2.0", "3.0"):
        snapshot = {
            path.relative_to(project): sha(path) for path in project.rglob("*") if path.is_file()
        }
        assert main(["migrate", revision, str(project)]) == 0
        assert snapshot == {
            path.relative_to(project): sha(path) for path in project.rglob("*") if path.is_file()
        }
        assert main(["migrate", revision, str(project), "--apply"]) == 0
        assert main(["migrate", revision, str(project), "--apply"]) == 0
        assert sha(authored) == original
