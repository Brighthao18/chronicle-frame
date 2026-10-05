#!/usr/bin/env python3
"""Record an actual user decision against concrete artifact hashes."""

import argparse
from pathlib import Path
from historical_shortfilm_director.runtime.common import (
    load,
    save,
    sha,
    local,
    relative,
    now,
    mutation,
)

GATES = ["G1_STORY", "G2_VISUAL", "G3_HERO_MOTION", "G4_PICTURE_LOCK"]


def update(root, gate, status, note, decision_ref="", artifacts=()):
    if status == "NOT_REQUIRED":
        if gate != "G3_HERO_MOTION":
            raise ValueError("Only G3 is conditionally optional")
        queue = load(Path(root) / "06o_flow_job_queue.json", None)
        if queue is None:
            raise ValueError("Compile motion queue before deciding G3 is unnecessary")
        if any(j.get("human_gate") == gate for j in queue["jobs"]):
            raise ValueError("Motion queue still has escalations")
        if not note:
            raise ValueError("Record why no G3 escalation is needed")
    if status == "APPROVED" and (not decision_ref or not artifacts):
        raise ValueError(
            "Record the existing user decision reference and reviewed artifacts; do not infer approval"
        )
    records = []
    for path in artifacts:
        p = local(root, path)
        if not p.is_file() or not p.stat().st_size:
            raise ValueError("Review artifact missing/empty: " + str(p))
        records.append({"path": relative(root, p), "sha256": sha(p)})
    with mutation(root):
        p = Path(root) / "00_pipeline_control.json"
        data = load(p, {"schema_version": "3.1", "gates": {}})
        old = data.setdefault("gates", {}).get(gate)
        if old:
            data.setdefault("gate_history", []).append({"gate": gate, "value": old})
        data["gates"][gate] = {
            "status": status,
            "note": note,
            "decision_ref": decision_ref,
            "artifacts": records,
            "updated_at": now(),
        }
        if status in {"REVISE", "BLOCKED"}:
            for later in GATES[GATES.index(gate) + 1 :]:
                prev = data["gates"].get(later)
                if prev:
                    data.setdefault("gate_history", []).append({"gate": later, "value": prev})
                data["gates"][later] = {"status": "PENDING", "note": "Upstream revision: " + gate}
        save(p, data)
    return data["gates"][gate]


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("project_dir")
    p.add_argument("gate", choices=GATES)
    p.add_argument("status", choices=["PENDING", "APPROVED", "REVISE", "BLOCKED", "NOT_REQUIRED"])
    p.add_argument("--note", default="")
    p.add_argument("--decision-ref", default="")
    p.add_argument("--artifact", action="append", default=[])
    a = p.parse_args()
    update(Path(a.project_dir).resolve(), a.gate, a.status, a.note, a.decision_ref, a.artifact)
    print(a.gate + " -> " + a.status)


if __name__ == "__main__":
    main()
