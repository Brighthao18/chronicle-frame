"""Run package commands in child processes, including an uninstalled complete Skill checkout."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from historical_shortfilm_director.commands import legacy_main

if __name__ == "__main__":
    raise SystemExit(legacy_main(sys.argv[1], sys.argv[2:]))
