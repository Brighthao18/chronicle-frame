"""Preserved local production invariants."""

from __future__ import annotations
from pathlib import Path
from .storage import local, load, relative, sha, now, save


def register(root, asset_id, path, **extra):
    p = local(root, str(path))
    regp = Path(root) / "06n_asset_registry.json"
    reg = load(regp, {"schema_version": "3.1", "assets": {}})
    item = {"path": relative(root, p), "sha256": sha(p), "registered_at": now(), **extra}
    old = reg["assets"].get(asset_id)
    if old and old != item:
        reg.setdefault("history", []).append({"asset_id": asset_id, **old})
    reg["assets"][asset_id] = item
    save(regp, reg)
    return item
