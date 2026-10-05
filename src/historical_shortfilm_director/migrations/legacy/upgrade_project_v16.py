#!/usr/bin/env python3
"""Non-destructive v1.6 project upgrader.

Adds chain-prompt compilation support without replacing existing evidence,
creative, script, storyboard, or prompt content.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from historical_shortfilm_director import __version__

CHAIN_TEMPLATE = """# Shot Chaining / Reference Budget Plan

Hard production profile: max 3 reference images per generated shot; max 10 seconds per clip. Fill this table, then run `python scripts/compile_chain_prompts.py <project_dir>` to compile executable prompt blocks.

| Shot | Duration | Chain role | Prev shot / source | Start anchor | End anchor target | Ref1 | Ref2 | Ref3 | Inherit prev carry? | Export carry to next? | Extraction rule | Reset conditions | Subject motion | Environment / layer motion | Camera motion | Timing | End state | Continuity locks | Negative constraints |
|---|---:|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|

## Reference-slot convention

- `Ref1`: carry-forward continuity frame when chaining is used; otherwise reallocate deliberately.
- `Ref2`: authoritative identity / geometry reference.
- `Ref3`: shot-specific control reference or approved end/composite frame.

## Carry-frame naming

Use stable IDs such as `CF_S03_v2`.

## Composite-anchor needs

List shots that require pre-composited anchor frames because more than 3 conceptual source assets are needed.

## High-risk resets

List shots that must reset to an authoritative archival/keyframe reference instead of inheriting the prior shot tail frame.
"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("project_dir")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument(
        "--replace-empty-v15-chain-template",
        action="store_true",
        help="Replace only a near-empty v1.5 05c template; never replace a populated plan.",
    )
    args = ap.parse_args()

    root = Path(args.project_dir).resolve()
    if not root.exists():
        raise SystemExit(f"project directory does not exist: {root}")

    chain = root / "05c_shot_chaining_plan.md"
    create_chain = not chain.exists()
    replace_chain = False
    if chain.exists() and args.replace_empty_v15_chain_template:
        text = chain.read_text(encoding="utf-8", errors="replace")
        old_schema = "Reference budget (1/2/3)" in text and "| Ref1 |" not in text
        # Replace only if it looks like the untouched scaffold (no shot IDs beyond header).
        shot_like = [
            ln
            for ln in text.splitlines()
            if ln.strip().startswith("|") and any(c.isdigit() for c in ln.split("|")[1] if c)
        ]
        replace_chain = old_schema and not shot_like

    print(f"Project: {root}")
    print(f"Create new 05c template: {create_chain}")
    print(f"Replace untouched v1.5 05c template: {replace_chain}")
    print(
        "Will add compiler outputs only when compile_chain_prompts.py is run; no generated prompt files are invented during upgrade."
    )

    if not args.apply:
        print("Dry run only. Re-run with --apply to update metadata/create safe support files.")
        return 0

    if create_chain or replace_chain:
        chain.write_text(CHAIN_TEMPLATE, encoding="utf-8")

    meta_path = root / "project.json"
    if meta_path.exists():
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
        except Exception:
            meta = {}
        if isinstance(meta, dict):
            meta["skill_pipeline_version"] = __version__
            meta.setdefault(
                "ai_generation_constraints",
                {
                    "max_reference_images_per_shot": 3,
                    "max_clip_duration_seconds": 10,
                },
            )
            meta["chain_prompt_compiler"] = "scripts/compile_chain_prompts.py"
            meta_path.write_text(
                json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
            )

    notes = root / "V16_UPGRADE_NOTES.md"
    if not notes.exists():
        notes.write_text(
            "# v1.6 Upgrade Notes\n\n"
            "Added chain-prompt compilation support. Fill the v1.6 `05c_shot_chaining_plan.md` slot-level table, then run `python scripts/compile_chain_prompts.py <project_dir>` to generate `06b_chain_prompt_pack.md` and `06c_chain_generation_runbook.md`. Existing populated v1.5 plans are preserved unless you explicitly replace an untouched scaffold.\n",
            encoding="utf-8",
        )
    print("Applied.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
