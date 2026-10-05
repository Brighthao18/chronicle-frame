"""One local preparation command; real generation remains an explicit agent-tool action."""

import argparse
import json
import subprocess
from pathlib import Path
from historical_shortfilm_director.commands import module_command
from historical_shortfilm_director.runtime.common import save
from historical_shortfilm_director.production.graph import compile_graph
from historical_shortfilm_director.runtime.engine import sync, next_jobs, state


def prepare(root):
    root = Path(root).resolve()
    compilation = compile_graph(root)
    runs = []
    for script in ("compile_image25_jobs.py", "compile_flow_prompts.py", "compile_flow_jobs.py"):
        cp = subprocess.run(
            [*module_command(script), str(root)],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        item = {
            "script": script,
            "exit_code": cp.returncode,
            "output": cp.stdout[-4000:],
            "errors": cp.stderr[-2000:],
        }
        runs.append(item)
        if cp.returncode:
            save(root / "06u_agent_runboard.json", {"status": "COMPILE_FAILED", "runs": runs})
            raise ValueError("Preparation failed at " + script + ": " + cp.stdout + cp.stderr)
    sync(root)
    schedule = next_jobs(root)
    execution = state(root)
    ready = [j for j in schedule["jobs"] if j["ready"]]
    reviews = [j for j in schedule["jobs"] if j["status"] == "REVIEW"]
    active = []
    for j in schedule["jobs"]:
        if j["status"] == "ACTIVE":
            attempt = execution["jobs"][j["job_id"]]["attempts"][-1]
            active.append(
                {
                    "job_id": j["job_id"],
                    "token": attempt["token"],
                    "receipt": attempt.get("receipt"),
                    "next": "Observe the original tool/provider result; do not resubmit based on this local record.",
                }
            )
    result = {
        "schema_version": "3.2",
        "status": "READY_WORK"
        if ready
        else "REVIEW_WORK"
        if reviews
        else "OBSERVE_EXISTING"
        if active
        else "NO_DISPATCHABLE_JOB",
        "compilation": compilation,
        "runs": runs,
        "ready": ready,
        "review": reviews,
        "existing_attempts": active,
        "held": [
            j
            for j in schedule["jobs"]
            if not j["ready"] and j["status"] not in {"ACTIVE", "REVIEW", "ACCEPTED"}
        ],
        "note": "No claims, generation calls or approvals were performed. A non-dispatchable queue is not proof of film completion.",
    }
    save(root / "06u_agent_runboard.json", result)
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("project_dir")
    a = p.parse_args()
    print(json.dumps(prepare(a.project_dir), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
