"""Skill frontmatter, dependency scope and original coverage preservation."""

import ast
import json
from pathlib import Path

import yaml

from historical_shortfilm_director import __version__
from historical_shortfilm_director.validation import validate_bundle

ROOT = Path(__file__).resolve().parents[2]


def test_skill_structure_and_yaml_metadata():
    assert validate_bundle(ROOT)["status"] == "PASS"
    front = yaml.safe_load((ROOT / "SKILL.md").read_text(encoding="utf-8").split("---", 2)[1])
    assert front["metadata"]["version"] == __version__ == (ROOT / "VERSION").read_text().strip()
    assert front["metadata"]["author"] == "historical-shortfilm-director contributors"


def test_all_original_test_methods_have_replacement_assertions():
    catalog = json.loads((ROOT / "docs/test-coverage-mapping.json").read_text())
    assert len(catalog) == 41
    for item in catalog:
        tree = ast.parse((ROOT / item["new_file"]).read_text(encoding="utf-8"))
        methods = [
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.FunctionDef) and node.name == item["method"]
        ]
        assert len(methods) == 1
        assert any(
            isinstance(node, (ast.Assert, ast.With))
            or (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and node.func.attr.startswith("assert")
            )
            for node in ast.walk(methods[0])
        )


def test_manifest_core_dependencies_are_empty():
    text = (ROOT / "pyproject.toml").read_text()
    project = text.split("[project.optional-dependencies]", 1)[0]
    assert "dependencies = []" in project
