#!/usr/bin/env python3
from __future__ import annotations
import argparse
import json
from pathlib import Path
from historical_shortfilm_director import __version__

TEMPLATE = """# Flow Cinematic Prompt Blueprints

| Unit | Prompt mode | Story beat | Visual premise | Anchor facts | Start state | ONE primary action | Environment response | Camera grammar | Focus / depth | Light / atmosphere | Temporal choreography | End composition | Audio intent | Continuity locks | Post-only | Density target | Approval |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|

Prompt mode: `T2V_RICH / I2V_BALANCED / FRAMES_PATH / EXTEND_CONTINUITY / OMNI_EDIT_LOCAL`.
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("project_dir")
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    r = Path(a.project_dir).resolve()
    p = r / "04c_flow_prompt_blueprints.md"
    print(f"Project: {r}")
    print(("+ " if not p.exists() else "= ") + p.name)
    if not a.apply:
        print("Dry run only. Re-run with --apply.")
        return 0
    if not p.exists():
        p.write_text(TEMPLATE, encoding="utf-8")
    mp = r / "project.json"
    if mp.exists():
        try:
            m = json.loads(mp.read_text(encoding="utf-8"))
            m["skill_pipeline_version"] = __version__
            m.setdefault("flow", {})["prompt_blueprints"] = "04c_flow_prompt_blueprints.md"
            m["flow"]["prompt_style"] = "balanced-cinematic-v1.9"
            mp.write_text(json.dumps(m, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        except Exception:
            pass
    n = r / "V19_UPGRADE_NOTES.md"
    if not n.exists():
        n.write_text(
            "# v1.9 Upgrade Notes\n\nAdds Flow cinematic prompt blueprints and replaces v1.8 skeletal motion-only compilation. Existing scripts, evidence, storyboards and prompts are preserved. Rebuild Flow prompts only after approving 04c.\n",
            encoding="utf-8",
        )
    print("Applied.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
