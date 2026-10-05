"""Create an offline synthetic project. No historical claims, provider calls or gate approvals."""

from __future__ import annotations

import argparse
import json
import struct
import wave
import zlib
from pathlib import Path

from historical_shortfilm_director.cli import main
from historical_shortfilm_director.runtime.common import register, save


def png(path, color):
    """Original deterministic geometry, encoded using only the Python standard library."""
    width, height = 320, 180
    rows = []
    for y in range(height):
        row = bytearray([0])
        for x in range(width):
            edge = (
                (90 <= x <= 230 and y in range(35, 40))
                or (90 <= x <= 230 and y in range(140, 145))
                or (35 <= y <= 145 and x in range(90, 95))
                or (35 <= y <= 145 and x in range(225, 230))
            )
            row.extend((240, 240, 240) if edge else color)
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
    result = main(["init", "--title", "Synthetic threshold study", "--dir", str(root)])
    if result:
        raise ValueError("Initialization failed")
    for identifier, color in (("A", (16, 32, 70)), ("B", (12, 88, 80))):
        path = root / "materials" / (identifier + ".png")
        png(path, color)
        register(
            root,
            identifier,
            str(path),
            status="SOURCE_VERIFIED",
            origin="SYNTHETIC",
            historical_status="NO_HISTORICAL_CLAIM",
            provenance="Original deterministic geometric fixture; verified file, not archival evidence",
        )
    with wave.open(str(root / "materials/silence.wav"), "w") as output:
        output.setnchannels(1)
        output.setsampwidth(2)
        output.setframerate(24000)
        output.writeframes(b"\x00\x00" * 6000)
    (root / "01_evidence_ledger.md").write_text(
        "# Synthetic fixture ledger\n\n"
        "This example makes no historical claims. SOURCE_VERIFIED records verify local fixture files only.\n\n"
        "| ID | Claim | Source | Evidence class | Allowed wording |\n"
        "|---|---|---|---|---|\n"
        "| FIX_A | A blue geometric frame exists | materials/A.png, original code | SYNTHETIC | Geometric study |\n"
        "| FIX_B | A green geometric frame exists | materials/B.png, original code | SYNTHETIC | Geometric study |\n",
        encoding="utf-8",
    )
    graph = {
        "schema_version": "3.2",
        "title": "Synthetic threshold study",
        "external_refs": [],
        "frames": [
            {
                "id": fid,
                "route": "SOURCE_LOCKED",
                "task": "Synthetic geometry",
                "preview_path": "materials/" + fid + ".png",
            }
            for fid in ("A", "B")
        ],
        "units": [
            {
                "id": uid,
                "mode": "SKIP_FLOW",
                "start": fid,
                "end": fid,
                "duration_s": 2,
                "edit_s": 1.5,
                "in_s": 0,
                "preview_motion": "HOLD",
            }
            for uid, fid in (("U1", "A"), ("U2", "B"))
        ],
        "joins": [
            {
                "id": "J1",
                "from": "U1",
                "to": "U2",
                "type": "HARD_CUT",
                "fallback": "Keep the explicit hard cut",
                "handles": "0",
            }
        ],
        "preview": {"width": 320, "height": 180, "fps": 25, "audio": "materials/silence.wav"},
    }
    save(root / "03_production_graph.json", graph)
    print(
        json.dumps(
            {
                "status": "SYNTHETIC_PROJECT_CREATED",
                "cloud_calls": 0,
                "human_gates": "PENDING",
                "historical_claims": 0,
            }
        )
    )
    return root


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project_dir")
    create(parser.parse_args().project_dir)
