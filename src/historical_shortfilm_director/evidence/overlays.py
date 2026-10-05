"""Create lossless sealed derivatives and source-pixel verification receipts (never overwrite inputs)."""

import argparse
import csv
from pathlib import Path
from PIL import Image
import numpy as np
from historical_shortfilm_director.runtime.common import (
    local,
    relative,
    sha,
    load,
    save,
    digest,
    now,
)
from historical_shortfilm_director.evidence.apply_overlays import box, xy


def apply_plan(root, plan="03e_evidence_overlay_plan.csv"):
    with local(root, plan).open(encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    groups = {}
    for r in rows:
        if str(r.get("approval", "")).upper() not in {"APPROVED", "READY", "PASS"}:
            continue
        groups.setdefault(r["target_path"], []).append(r)
    report = load(
        Path(root) / "06s_overlay_receipts.json", {"schema_version": "3.1", "outputs": {}}
    )
    outputs = []
    for target, items in groups.items():
        srcbase = local(root, target)
        with Image.open(srcbase) as im:
            base = im.convert("RGBA")
        sources = [{"path": relative(root, srcbase), "sha256": sha(srcbase)}]
        checks = []
        for r in items:
            src = local(root, r["source_path"])
            with Image.open(src) as im:
                original = im.convert("RGBA")
            b = box(r.get("source_box", ""), original.size)
            pos = xy(r.get("target_xy", ""))
            if not (0 <= b[0] < b[2] <= original.width and 0 <= b[1] < b[3] <= original.height):
                raise ValueError("Source crop out of bounds")
            patch = original.crop(b)
            if (
                pos[0] < 0
                or pos[1] < 0
                or pos[0] + patch.width > base.width
                or pos[1] + patch.height > base.height
            ):
                raise ValueError("Overlay out of bounds")
            mask = None
            if r.get("alpha_mask_path"):
                mp = local(root, r["alpha_mask_path"])
                with Image.open(mp) as im:
                    mask = im.convert("L")
                if mask.size != patch.size or not set(np.unique(np.array(mask))).issubset({0, 255}):
                    raise ValueError(
                        "Exact evidence lock requires a matching binary mask; feather non-critical surroundings separately"
                    )
                sources.append({"path": relative(root, mp), "sha256": sha(mp)})
            base.paste(patch, pos, mask)
            active = (
                np.ones((patch.height, patch.width), dtype=bool)
                if mask is None
                else np.array(mask) > 0
            )
            checks.append((pos, np.array(patch), active))
            sources.append({"path": relative(root, src), "sha256": sha(src)})
        # Overlapping locks must all survive the completed composite.
        final = np.array(base)
        for (x, y), patch, mask in checks:
            if not np.array_equal(
                final[y : y + patch.shape[0], x : x + patch.shape[1]][mask], patch[mask]
            ):
                raise ValueError("Conflicting evidence overlays")
        outputs_requested = {r.get("output_path") for r in items if r.get("output_path")}
        if len(outputs_requested) > 1:
            raise ValueError("Multiple destinations for one sealed composite")
        out = (
            local(root, next(iter(outputs_requested)))
            if outputs_requested
            else local(root, "assets/sealed")
            / (srcbase.stem + "-" + digest({"sources": sources, "rows": items})[:12] + ".png")
        )
        if out == srcbase or out.suffix.lower() != ".png":
            raise ValueError("Use a separate PNG output for lossless evidence lock")
        out.parent.mkdir(parents=True, exist_ok=True)
        if out.exists():
            with Image.open(out) as im:
                if not np.array_equal(np.array(im.convert("RGBA")), final):
                    raise ValueError(
                        "Existing sealed destination differs; choose a new output_path"
                    )
        else:
            base.save(out, format="PNG")
        with Image.open(out) as im:
            if not np.array_equal(np.array(im.convert("RGBA")), final):
                raise ValueError("Lossless roundtrip failed")
        record = {
            "path": relative(root, out),
            "sha256": sha(out),
            "sources": sources,
            "regions": len(checks),
            "pixel_check": "PASS",
            "time": now(),
        }
        report["outputs"][record["sha256"]] = record
        outputs.append(record)
    save(Path(root) / "06s_overlay_receipts.json", report)
    return outputs


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("project_dir")
    p.add_argument("--plan", default="03e_evidence_overlay_plan.csv")
    a = p.parse_args()
    print(apply_plan(Path(a.project_dir).resolve(), a.plan))
