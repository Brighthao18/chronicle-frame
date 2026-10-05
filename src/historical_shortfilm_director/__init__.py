"""An evidence-grounded Agent Skill and production runtime for historical short films."""

from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

try:
    __version__ = version("historical-shortfilm-director")
except PackageNotFoundError:
    __version__ = (
        (Path(__file__).resolve().parents[2] / "VERSION").read_text(encoding="utf-8").strip()
    )
