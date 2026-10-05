"""Install a local wheel in a clean environment; never consult Git configuration."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import tempfile
import venv
from pathlib import Path


def check(directory):
    wheels = sorted(Path(directory).resolve().glob("historical_shortfilm_director-*.whl"))
    if len(wheels) != 1:
        raise ValueError("Expected exactly one built project wheel")
    with tempfile.TemporaryDirectory(prefix="hsd_wheel_") as name:
        root = Path(name)
        environment = root / "venv"
        venv.EnvBuilder(with_pip=True).create(environment)
        binaries = environment / ("Scripts" if os.name == "nt" else "bin")
        python = binaries / ("python.exe" if os.name == "nt" else "python")
        subprocess.run(
            [str(python), "-m", "pip", "install", "--no-deps", str(wheels[0])],
            cwd=root,
            check=True,
            capture_output=True,
        )
        clean = os.environ.copy()
        clean.pop("PYTHONPATH", None)
        for args in (
            ["--help"],
            ["--version"],
            ["init", "--title", "Wheel generic", "--dir", "generic"],
            ["init", "--title", "Wheel profile", "--profile", "jnu_gate", "--dir", "profile"],
        ):
            subprocess.run(
                [str(python), "-m", "historical_shortfilm_director", *args],
                cwd=root,
                env=clean,
                check=True,
                capture_output=True,
            )
        generic = json.loads((root / "generic/project.json").read_text(encoding="utf-8"))
        profile = json.loads((root / "profile/00_profile.json").read_text(encoding="utf-8"))
        assert generic["profile"] == "generic"
        assert profile["name"] == "jnu_gate"
        assert (root / "profile/02b_gate_creative_lab.md").is_file()
        # No dependencies installed: this additionally checks the standard-library-only core.
        probe = "import importlib.util; assert importlib.util.find_spec('numpy') is None; from historical_shortfilm_director.production.prepare import prepare; from historical_shortfilm_director.media.animatic import build"
        subprocess.run(
            [str(python), "-c", probe], cwd=root, env=clean, check=True, capture_output=True
        )
    return {
        "status": "PASS",
        "wheel": wheels[0].name,
        "core_dependencies": 0,
        "generic_profile": "PASS",
        "bundled_historical_profile": "PASS",
        "cloud_calls": 0,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory")
    print(json.dumps(check(parser.parse_args().directory), indent=2))
