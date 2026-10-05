#!/usr/bin/env python3
"""Non-destructive v1.4 project upgrader.

Adds short-form creative-system and profile support files without replacing
existing evidence, script, storyboard, prompts, or project assets.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from historical_shortfilm_director import __version__
from historical_shortfilm_director.profiles import load_profile, legacy_templates

GENERIC_NEW = {
    "05a_anchor_frame_plan.md": """# Anchor Frame Plan\n\n## First-frame variants\n\n| Variant | Visual proposition | Single focal point | Question / tension | Reference IDs | Evidence/reconstruction status | Production method | Risk | Decision |\n|---|---|---|---|---|---|---|---|---|\n\n## Selected first-frame contract\n\n## Final-frame variants\n\n| Variant | Payoff function | Relationship to opening | Reference IDs | Production method | Risk | Decision |\n|---|---|---|---|---|---|---|\n\n## Selected anchor pair\n\n## Silent side-by-side test\n\n""",
    "05b_attention_map.md": """# Attention / State-Change Map\n\n| Time | Viewer question | New information | Visual state change | Emotional state | Sound state | Unresolved gap | Payoff/next question |\n|---|---|---|---|---|---|---|---|\n\n## Likely attention valleys\n\n## Compression / redesign decisions\n""",
}

GATE_NEW = {}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("project_dir")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument(
        "--gate-mode", action="store_true", help="Add Door Outside, Four Seas specific files"
    )
    args = ap.parse_args()

    root = Path(args.project_dir).resolve()
    if not root.exists():
        raise SystemExit(f"project directory does not exist: {root}")

    meta_path = root / "project.json"
    meta = {}
    if meta_path.exists():
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
        except Exception:
            pass

    selected_profile = load_profile(meta.get("profile", "generic"))
    gate = args.gate_mode or bool(selected_profile.templates)
    if args.gate_mode and not selected_profile.templates:
        selected_profile = load_profile("jnu_gate")
    wanted = dict(GENERIC_NEW)
    if gate:
        wanted.update(legacy_templates(selected_profile, "v14"))

    missing = [name for name in wanted if not (root / name).exists()]
    print(f"Project: {root}")
    print(f"Gate mode: {gate}")
    print("Missing support files:")
    for name in missing:
        print(f"  + {name}")

    if not args.apply:
        print("Dry run only. Re-run with --apply to create missing files.")
        return 0

    for name in missing:
        (root / name).write_text(wanted[name], encoding="utf-8")

    if meta_path.exists() and isinstance(meta, dict):
        meta["skill_pipeline_version"] = __version__
        if gate:
            for name, value in selected_profile.metadata.items():
                meta.setdefault(name, value)
        meta_path.write_text(
            json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )

    notes = root / "V14_UPGRADE_NOTES.md"
    if not notes.exists():
        notes.write_text(
            "# v1.4 Upgrade Notes\n\n"
            "Added non-destructive creative-system support: anchor-frame planning, attention/state-change mapping"
            + (
                ", and the selected profile creative lab / motif graph / director review."
                if gate
                else "."
            )
            + "\nExisting evidence, script, storyboard, prompts, and assets were not overwritten.\n",
            encoding="utf-8",
        )
    print("Applied.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
