"""Local CLI. External generation remains an explicit agent/operator action."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import __version__
from .commands import legacy_main


def emit(value):
    print(json.dumps(value, ensure_ascii=False, indent=2))


def parser():
    command = argparse.ArgumentParser(prog="hsd", description=__doc__)
    command.add_argument("--version", action="version", version=__version__)
    sub = command.add_subparsers(dest="command", required=True)
    init = sub.add_parser("init", help="Initialize an empty local project")
    init.add_argument("--title", required=True)
    init.add_argument("--dir", required=True)
    init.add_argument("--profile", default="generic")
    init.add_argument("--generator", choices=["generic", "flow"], default="generic")
    init.add_argument("--duration", type=int)
    init.add_argument(
        "--orientation", choices=["either", "landscape", "portrait"], default="either"
    )
    for name, help_text in {
        "prepare": "Compile local plans and ready-work records; never generate media",
        "status": "Read stage, gates, jobs and completion limitations",
        "next": "Read runnable jobs and explicit blockers",
        "animatic": "Render a still-based timed preview (media extras and FFmpeg)",
    }.items():
        item = sub.add_parser(name, help=help_text)
        item.add_argument("project_dir")
    validate = sub.add_parser("validate", help="Validate a graph or Skill bundle")
    validate.add_argument("project_dir", nargs="?")
    validate.add_argument("--skill", metavar="SKILL_DIR")
    qc = sub.add_parser("qc", help="Check graph, profile constraints and asset hashes")
    qc.add_argument("project_dir")
    qc.add_argument(
        "--media", action="store_true", help="Also inspect and fully decode registered media"
    )
    qc.add_argument(
        "--readiness", action="store_true", help="Run the full planning/readiness audit"
    )
    assemble = sub.add_parser("assemble", help="Prepare or execute deterministic FFmpeg assembly")
    assemble.add_argument("project_dir")
    assemble.add_argument("--manifest", default="06k_direct_assembly_manifest.csv")
    assemble.add_argument("--output", default="exports/direct_picture_master.mp4")
    assemble.add_argument("--fps", type=float, default=25)
    assemble.add_argument("--width", type=int, default=1920)
    assemble.add_argument("--height", type=int, default=1080)
    assemble.add_argument("--execute", action="store_true")
    runtime = sub.add_parser(
        "runtime", help="Local claim/receipt/ingest/review/accept state commands"
    )
    runtime.add_argument("project_dir")
    runtime.add_argument("arguments", nargs=argparse.REMAINDER)
    migrate = sub.add_parser("migrate", help="Retained legacy migration; dry-run by default")
    migrate.add_argument(
        "revision", choices=["1.3", "1.4", "1.5", "1.6", "1.7", "1.8", "1.9", "1.10", "2.0", "3.0"]
    )
    migrate.add_argument("project_dir")
    migrate.add_argument("--apply", action="store_true")
    sub.add_parser("doctor", help="Read local dependency availability")
    return command


def main(argv=None):
    command = parser()
    args = command.parse_args(argv)
    try:
        if args.command == "init":
            values = [
                "--title",
                args.title,
                "--dir",
                args.dir,
                "--profile",
                args.profile,
                "--generator",
                args.generator,
                "--orientation",
                args.orientation,
            ]
            if args.duration is not None:
                values.extend(["--duration", str(args.duration)])
            return legacy_main("init_project", values)
        if args.command == "doctor":
            return legacy_main("check_dependencies", [])
        if args.command == "validate" and args.skill:
            from .validation import validate_bundle

            result = validate_bundle(Path(args.skill))
            emit(result)
            return 0 if result["status"] == "PASS" else 2
        if not getattr(args, "project_dir", None):
            command.error("a project directory or --skill directory is required")
        root = Path(args.project_dir).resolve()
        if not (root / "project.json").is_file():
            raise ValueError("Project metadata missing; initialize a project first")
        if args.command == "prepare":
            from .production.prepare import prepare

            emit(prepare(root))
        elif args.command == "validate":
            from .production.graph import validate
            from .runtime.common import load

            graph = validate(root, load(root / "03_production_graph.json"))
            emit(
                {
                    "status": "PASS",
                    "schema_version": graph["schema_version"],
                    "scope": "Graph structure, references, paths and timing; historical truth needs separate review",
                }
            )
        elif args.command in {"status", "next"}:
            from .runtime.engine import next_jobs

            result = next_jobs(root)
            if args.command == "status":
                from .runtime.controller import controller_state
                from .runtime.common import load

                result.update(controller_state(root, load(root / "00_pipeline_control.json", {})))
                result["completion"] = (
                    "LOCAL_STATE_ONLY; final delivery requires verified media and actual decisions"
                )
            emit(result)
        elif args.command == "qc":
            if args.readiness:
                return legacy_main("qc_project", [str(root)])
            from .qc.project import inspect_project

            result = inspect_project(root, inspect_media=args.media)
            emit(result)
            return 0 if result["status"] == "PASS" else 2
        elif args.command == "animatic":
            from .media.animatic import build

            emit(build(root))
        elif args.command == "assemble":
            values = [
                str(root),
                "--manifest",
                args.manifest,
                "--output",
                args.output,
                "--fps",
                str(args.fps),
                "--width",
                str(args.width),
                "--height",
                str(args.height),
            ]
            if args.execute:
                values.append("--execute")
            return legacy_main("assemble_direct", values)
        elif args.command == "runtime":
            return legacy_main("production_runtime", [str(root), *args.arguments])
        elif args.command == "migrate":
            key = "upgrade_project_v" + args.revision.replace(".", "")
            return legacy_main(key, [str(root), *(["--apply"] if args.apply else [])])
        return 0
    except (ValueError, RuntimeError, KeyError, TypeError, OSError, ImportError) as error:
        print("ERROR: " + str(error), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
