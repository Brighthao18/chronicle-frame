"""Create an offline code-video project. No historical claims, provider calls or gate approvals."""

from __future__ import annotations

import argparse
import json
import shutil
import struct
import zlib
from pathlib import Path

from historical_shortfilm_director.cli import main
from historical_shortfilm_director.runtime.common import register, save

HERE = Path(__file__).resolve().parent


def png(path, width=640, height=360):
    """Original document-like geometry, encoded with only the Python standard library."""
    rows = []
    for y in range(height):
        row = bytearray([0])
        for x in range(width):
            color = (236, 228, 210)
            if 30 <= y < 60 and 60 <= x < 580:
                color = (52, 58, 70)
            elif y > 80 and y % 24 == 0 and 60 <= x < 580:
                color = (150, 140, 128)
            elif 52 <= x < 55 and y > 70:
                color = (190, 90, 80)
            if 230 <= y < 310 and 470 <= x < 550:
                color = (176, 42, 38)
            row.extend(color)
        rows.append(bytes(row))

    def chunk(kind, data):
        return (
            struct.pack("!I", len(data)) + kind + data + struct.pack("!I", zlib.crc32(kind + data))
        )

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack("!2I5B", width, height, 8, 2, 0, 0, 0))
        + chunk(b"IDAT", zlib.compress(b"".join(rows)))
        + chunk(b"IEND", b"")
    )


def create(root):
    root = Path(root).resolve()
    if main(["init", "--title", "Synthetic code video study", "--dir", str(root)]):
        raise ValueError("Initialization failed")
    plate = root / "materials/plate.png"
    png(plate)
    register(
        root,
        "PLATE",
        str(plate),
        status="SOURCE_VERIFIED",
        origin="SYNTHETIC",
        historical_status="NO_HISTORICAL_CLAIM",
        provenance="Original document-like geometry; verified file, not archival evidence",
    )
    (root / "01_evidence_ledger.md").write_text(
        "# Synthetic fixture ledger\n\n"
        "This example makes no historical claims. SOURCE_VERIFIED verifies the local file only.\n\n"
        "| ID | Claim | Source | Evidence class | Allowed wording |\n"
        "|---|---|---|---|---|\n"
        "| FIX_PLATE | A synthetic ruled sheet with a red square exists | materials/plate.png,"
        " original code | SYNTHETIC | Synthetic study |\n"
        "| FIX_SCOPE | This study makes no historical claim | examples/claude-code-video |"
        " SYNTHETIC | no historical claim |\n",
        encoding="utf-8",
    )
    graph = {
        "schema_version": "3.2",
        "title": "Synthetic code video study",
        "external_refs": ["PLATE"],
        "frames": [
            {"id": "SHEET", "route": "SOURCE_LOCKED", "preview_path": "materials/plate.png"}
        ],
        "units": [
            {
                "id": "U1",
                "mode": "CODE",
                "ingredients": ["PLATE"],
                "duration_s": 4,
                "edit_s": 3.2,
                "in_s": 0.4,
                "action": "Push slowly toward the red square and outline it once the move settles.",
                "camera": "One eased push-in; no rotation.",
                "keep": "Sheet geometry and colours",
                "change": "Framing only",
                "story_beat": "Find the mark",
                "preview_frame": "SHEET",
                "preview_motion": "PUSH_IN",
            },
            {
                "id": "U2",
                "mode": "CODE",
                "ingredients": ["PLATE"],
                "duration_s": 3,
                "edit_s": 2.6,
                "in_s": 0.2,
                "action": "A dark panel wipes across the sheet and a caption appears on it.",
                "camera": "Locked frame.",
                "keep": "Sheet geometry under the panel",
                "change": "Panel and caption only",
                "story_beat": "Close the study",
                "preview_frame": "SHEET",
                "preview_motion": "FADE_TO_BLACK",
            },
        ],
        "joins": [
            {
                "id": "J1",
                "from": "U1",
                "to": "U2",
                "type": "GRAPHIC_RESET",
                "fallback": "Hard cut on the settled outline",
                "handles": "0.2 s",
            }
        ],
        "preview": {"width": 320, "height": 180, "fps": 25},
        "render": {"width": 640, "height": 360, "fps": 25},
    }
    save(root / "03_production_graph.json", graph)
    # Scenes as Claude Code might write them from `hsd code brief`.
    for name in ("U1.scene.json", "U2.scene.json"):
        target = root / "programs" / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(HERE / "programs" / name, target)
    print(
        json.dumps(
            {
                "status": "SYNTHETIC_PROJECT_CREATED",
                "cloud_calls": 0,
                "human_gates": "PENDING",
                "historical_claims": 0,
                "programs": ["programs/U1.scene.json", "programs/U2.scene.json"],
            }
        )
    )
    return root


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project_dir")
    create(parser.parse_args().project_dir)
