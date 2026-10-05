"""Local integrity QC; no automatic historical or aesthetic judgment."""

from pathlib import Path

from historical_shortfilm_director.production.graph import validate
from historical_shortfilm_director.profiles import profile_qc, project_profile
from historical_shortfilm_director.runtime.common import gate_status, load, local, media_check, sha


def inspect_project(root, inspect_media=False):
    root = Path(root).resolve()
    meta = load(root / "project.json")
    errors, warnings = profile_qc(root, project_profile(root, meta), meta)
    graph = load(root / "03_production_graph.json")
    if graph is None:
        errors.append("Production graph is missing")
    else:
        try:
            validate(root, graph)
        except (ValueError, KeyError, TypeError) as error:
            errors.append(str(error))
    ledger = root / "01_evidence_ledger.md"
    if not ledger.is_file():
        errors.append("Evidence ledger is missing")
    assets = {}
    for name, item in load(root / "06n_asset_registry.json", {"assets": {}})["assets"].items():
        try:
            path = local(root, item["path"])
            if not path.is_file() or sha(path) != item.get("sha256"):
                raise ValueError("Missing or modified asset: " + name)
            assets[name] = media_check(path, root) if inspect_media else {"sha256": item["sha256"]}
        except (ValueError, OSError, KeyError) as error:
            errors.append(str(error))
    gates = {
        gate: gate_status(root, gate)
        for gate in ("G1_STORY", "G2_VISUAL", "G3_HERO_MOTION", "G4_PICTURE_LOCK")
    }
    errors.extend(
        "Stale human decision: " + gate for gate, status in gates.items() if status == "STALE"
    )
    return {
        "status": "FAIL" if errors else "PASS",
        "errors": errors,
        "warnings": warnings,
        "assets": assets,
        "gates": gates,
        "scope": "Local graph/profile/file integrity; semantic and historical review remain explicit",
        "provider_tests": "NOT_RUN",
    }
