"""Declarative, portable project profiles; no executable configuration imports."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Profile:
    name: str = "generic"
    templates: dict = field(default_factory=dict)
    constraints: dict = field(default_factory=dict)
    metadata: dict = field(default_factory=dict)
    routing: dict = field(default_factory=dict)
    qc: dict = field(default_factory=dict)
    initialization_files: dict = field(default_factory=dict)
    base: Path | None = None


def load_profile(value="generic"):
    """Load a bundled name/alias or explicit JSON file without running profile code."""
    value = str(value)
    if value == "generic":
        return Profile()
    explicit = Path(value)
    candidates = (
        [explicit]
        if explicit.is_file()
        else sorted((Path(__file__).parent / "builtin").glob("*/profile.json"))
    )
    for path in candidates:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
        if explicit.is_file() or value in [data.get("name"), *data.get("aliases", [])]:
            allowed = {
                "name",
                "aliases",
                "description",
                "templates",
                "constraints",
                "metadata",
                "routing",
                "qc",
                "initialization_files",
            }
            if set(data) - allowed:
                raise ValueError("Unknown profile fields: " + str(sorted(set(data) - allowed)))
            result = Profile(
                **{k: data[k] for k in allowed - {"aliases", "description"} if k in data},
                base=path.parent,
            )
            if not re.fullmatch(r"[a-z0-9][a-z0-9_-]{0,63}", result.name):
                raise ValueError("Invalid profile name")
            for key in (
                "templates",
                "constraints",
                "metadata",
                "routing",
                "qc",
                "initialization_files",
            ):
                if not isinstance(getattr(result, key), dict):
                    raise ValueError("Profile field must be an object: " + key)
            return result
    raise ValueError("Unknown profile: " + value)


def apply_profile(root, profile):
    from historical_shortfilm_director.runtime.common import local, save

    for name, body in profile.templates.items():
        target = local(root, name)
        if not target.exists():
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(body, encoding="utf-8")
    for name, value in profile.initialization_files.items():
        target = local(root, name)
        if not target.exists():
            save(target, value)
    if profile.name != "generic":
        save(
            Path(root) / "00_profile.json",
            {
                k: getattr(profile, k)
                for k in (
                    "name",
                    "templates",
                    "constraints",
                    "metadata",
                    "routing",
                    "qc",
                    "initialization_files",
                )
            },
        )


def project_profile(root, meta=None):
    snapshot = Path(root) / "00_profile.json"
    if snapshot.is_file():
        return load_profile(snapshot)
    if meta is None:
        meta = json.loads((Path(root) / "project.json").read_text(encoding="utf-8-sig"))
    return load_profile(meta.get("profile", "generic"))


def legacy_templates(profile, revision):
    if not profile.base:
        return profile.templates
    path = profile.base / ("legacy-" + revision + "-templates.json")
    return json.loads(path.read_text(encoding="utf-8")) if path.is_file() else profile.templates


def profile_qc(root, profile, meta):
    """Generic checks driven entirely by a profile's constraints and protected assets."""
    from historical_shortfilm_director.runtime.common import local

    errors, warnings = [], []
    for name in [*profile.templates, *profile.initialization_files]:
        if not local(root, name).exists():
            warnings.append(f"Profile {profile.name} is missing initialization file: {name}")
    maximum = profile.constraints.get("max_duration_seconds")
    ceiling = meta.get("duration_ceiling_seconds")
    if maximum is not None and (ceiling is None or ceiling > maximum):
        errors.append(f"Profile {profile.name} requires a duration ceiling <= {maximum}s")
    preferred = profile.constraints.get("preferred_orientation")
    if preferred and meta.get("orientation") not in {preferred, "either"}:
        warnings.append(f"Profile {profile.name} suggests orientation {preferred}")
    ids = profile.qc.get("avoid_repeated_drift_ids", [])
    board = Path(root) / "05_storyboard.md"
    if ids and board.is_file():
        text = board.read_text(encoding="utf-8")
        if all(value in text for value in ids):
            matches = [
                line
                for line in text.splitlines()
                if any(value in line for value in ids)
                and re.search(r"慢推|横移|推近|叠化|slow push|pan", line, re.I)
            ]
            if len(matches) >= 3:
                warnings.append(
                    f"Profile {profile.name}: repeated isolated archival drift shots need review"
                )
    return errors, warnings
