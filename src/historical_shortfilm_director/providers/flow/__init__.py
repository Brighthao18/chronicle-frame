"""Google Flow browser/operator handoff. This adapter makes no network calls."""

import json
from pathlib import Path


def configuration():
    return json.loads((Path(__file__).parent / "config.json").read_text(encoding="utf-8"))
