#!/usr/bin/env python3
"""Compatibility entry point; implementation lives in historical_shortfilm_director.qc.readiness."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from historical_shortfilm_director.commands import legacy_main

if __name__ == "__main__":
    raise SystemExit(legacy_main("qc_project", sys.argv[1:]))
else:
    from importlib import import_module

    sys.modules[__name__] = import_module("historical_shortfilm_director.qc.readiness")
