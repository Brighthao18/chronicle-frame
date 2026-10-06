"""Headless Claude Code authoring: one `claude -p` session writes one scene for one code job.

This adapter is opt-in and budgeted. It observes the installed CLI before use, resolves the
executable from the environment rather than from project data, and runs each session in a
confined work directory with file tools only: no shell, no network tools, no settings from
the project. Sessions are reserved in the execution state before they start, so a crashed or
timed-out session still counts. The session only writes a scene; the local renderer, an
explicit review and acceptance decide what happens to it.
"""

from __future__ import annotations

import json
import math
import os
import re
import shutil
import subprocess
import uuid
from pathlib import Path

import historical_shortfilm_director.runtime.engine as runtime
from historical_shortfilm_director.providers.capabilities import observation_errors
from historical_shortfilm_director.providers.code import AUTHOR_EXECUTION, AUTHOR_SLOT
from historical_shortfilm_director.providers.code.brief import build_brief
from historical_shortfilm_director.providers.code.render import (
    job_context,
    read_program,
    render,
    render_policy,
)
from historical_shortfilm_director.providers.code.scene import SceneError
from historical_shortfilm_director.runtime.common import (
    load,
    local,
    mutation,
    now,
    relative,
    save,
    sha,
)

SESSIONS = "work/code_authoring"
PROGRAM = "scene.json"
PROMPT = (
    "Read BRIEF.md in the current directory and follow it exactly. Write the finished scene"
    " to scene.json in the current directory. Do not create or change any other file."
)
FLAG = re.compile(r"(?<![\w-])(--[a-z][a-z0-9-]*)")
REQUIRED_FLAGS = {"--print", "--output-format", "--permission-mode", "--tools"}
HARDENING_FLAGS = {"--restricted", "--permission-prompts", "--max-budget-usd", "--model"}
MODEL = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:/\[\]-]{0,99}")


def executable():
    """The CLI to run, from HSD_CLAUDE or PATH; never from project files."""
    found = os.environ.get("HSD_CLAUDE") or shutil.which("claude")
    if not found or not Path(found).is_file():
        raise RuntimeError("Claude Code CLI not found; install it or set HSD_CLAUDE")
    return str(Path(found))


def ask(command, *arguments):
    try:
        result = subprocess.run(
            [command, *arguments],
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=60,
        )
    except subprocess.TimeoutExpired:
        raise RuntimeError(f"`claude {' '.join(arguments)}` did not answer within 60 s")
    if result.returncode:
        raise RuntimeError(f"`claude {' '.join(arguments)}` failed: {result.stderr[-400:]}")
    return result.stdout


def probe_claude(root):
    """Observe the installed CLI's version and the flags this adapter relies on."""
    root = Path(root).resolve()
    problems = []
    version, flags = None, []
    try:
        command = executable()
        version = ask(command, "--version").strip().splitlines()[0]
        listed = set(FLAG.findall(ask(command, "--help")))
        flags = sorted((REQUIRED_FLAGS | HARDENING_FLAGS) & listed)
        missing = sorted(REQUIRED_FLAGS - listed)
        if missing:
            problems.append("CLI does not list required flags: " + ", ".join(missing))
    except (RuntimeError, OSError, IndexError) as error:
        command = None
        problems.append(str(error))
    observation = {
        "available": not problems,
        "observed_at": now(),
        "evidence": (
            f"`claude --version`: {version}; `claude --help` lists {', '.join(flags)}"
            if version
            else "; ".join(problems)
        ),
        "execution": AUTHOR_EXECUTION,
        "executable": Path(command).name if command else None,
        "version": version,
        "flags": flags,
        "problems": problems,
    }
    path = root / "00_capability_snapshot.json"
    snapshot = load(path, {})
    snapshot[AUTHOR_SLOT] = observation
    save(path, snapshot)
    return observation


def authorization(root, model):
    """The user's limits for headless sessions, checked before any session starts."""
    auth = load(Path(root) / "00_execution_policy.json", {}).get("authorization", {})
    if not auth.get("reference"):
        raise ValueError("EXECUTION_SCOPE_MISSING: record the request that authorizes this wave")
    limit = auth.get("claude_code_session_limit")
    if isinstance(limit, bool) or not isinstance(limit, int) or limit < 1:
        raise ValueError("Set authorization.claude_code_session_limit to a positive integer")
    budget = auth.get("claude_code_max_budget_usd")
    if budget is not None and (
        isinstance(budget, bool)
        or not isinstance(budget, (int, float))
        or not math.isfinite(budget)
        or budget <= 0
    ):
        raise ValueError("authorization.claude_code_max_budget_usd must be a positive number")
    if model is not None and not MODEL.fullmatch(model):
        raise ValueError("Model names may contain letters, digits and . _ : / [ ] - only")
    return {
        "limit": limit,
        "max_budget_usd": budget,
        "share_inputs": auth.get("claude_code_share_inputs") is True,
    }


def observed(root):
    caps = load(Path(root) / "00_capability_snapshot.json", {}).get(AUTHOR_SLOT, {})
    errors = observation_errors(caps)
    if not errors and caps.get("execution") != AUTHOR_EXECUTION:
        errors = ["EXECUTION_UNSUPPORTED"]
    if not errors and not REQUIRED_FLAGS <= set(caps.get("flags", [])):
        errors = ["CLI_FLAGS_UNVERIFIED"]
    if errors:
        raise ValueError(
            "Claude Code is not observed for headless authoring ("
            + ", ".join(errors)
            + "); run `hsd code probe <project> --claude`"
        )
    return caps


def arguments(command, caps, limits, model):
    flags = set(caps["flags"])
    argv = [
        command,
        "--print",
        PROMPT,
        "--output-format",
        "json",
        "--permission-mode",
        "acceptEdits",
        "--tools",
        "Read,Write,Edit",
    ]
    if "--restricted" in flags:
        argv.append("--restricted")
    if "--permission-prompts" in flags:
        argv += ["--permission-prompts", "none"]
    if limits["max_budget_usd"] is not None:
        if "--max-budget-usd" not in flags:
            raise ValueError("A USD cap is set but this CLI did not list --max-budget-usd")
        argv += ["--max-budget-usd", format(limits["max_budget_usd"], "g")]
    if model:
        argv += ["--model", model]
    return argv


def result_object(stdout):
    """The CLI's final JSON result, tolerating log lines printed before it."""
    for candidate in [stdout.strip(), *reversed(stdout.strip().splitlines())]:
        try:
            value = json.loads(candidate)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            return value
    return {}


def update_session(root, token, **changes):
    with mutation(root):
        state = runtime.state(root)
        session = next(s for s in state.get("authoring", []) if s["token"] == token)
        session.update(changes)
        runtime.event(state, "AUTHOR_" + changes.get("status", "UPDATE"), token=token)
        save(Path(root) / runtime.STATE, state)
    return session


def author(root, k, then_render=False, model=None, timeout=900):
    """Run one budgeted headless session that writes a scene for job `k`."""
    root = Path(root).resolve()
    if os.environ.get("CLAUDECODE"):
        raise RuntimeError(
            "Already inside a Claude Code session: author the scene directly from"
            " `hsd code brief` instead of starting a nested headless session"
        )
    job, refs, assets, settings = job_context(root, k)
    blockers = runtime.readiness(root, k, job, runtime.state(root))
    if blockers and blockers != ["ACTIVE"]:
        raise ValueError(f"{k} is not ready: " + "; ".join(blockers))
    caps = observed(root)
    limits = authorization(root, model)
    command = executable()
    version = ask(command, "--version").strip().splitlines()[0]
    if version != caps.get("version"):
        raise ValueError(
            f"Claude Code is now {version!r}, observed {caps.get('version')!r};"
            " run `hsd code probe <project> --claude` again"
        )
    argv = arguments(command, caps, limits, model)
    token = uuid.uuid4().hex
    workdir = local(root, SESSIONS) / token
    with mutation(root):
        state = runtime.state(root)
        sessions = state.setdefault("authoring", [])
        if len(sessions) >= limits["limit"]:
            raise ValueError(
                f"AUTHOR_SESSION_LIMIT_REACHED: {len(sessions)} of {limits['limit']} sessions used"
            )
        sessions.append(
            {
                "token": token,
                "job_id": k,
                "status": "STARTED",
                "started_at": now(),
                "workdir": relative(root, workdir),
                "cli_version": version,
                "model": model,
                "max_budget_usd": limits["max_budget_usd"],
                "share_inputs": limits["share_inputs"],
                "arguments": argv[1:2] + ["<prompt>"] + argv[3:],
            }
        )
        runtime.event(state, "AUTHOR_START", job_id=k, token=token)
        save(root / runtime.STATE, state)
    workdir.mkdir(parents=True)
    files = None
    if limits["share_inputs"]:
        (workdir / "inputs").mkdir()
        files = {}
        for ref in refs:
            name = f"inputs/{ref['asset_id']}{assets[ref['asset_id']].suffix.lower()}"
            shutil.copy2(assets[ref["asset_id"]], workdir / name)
            files[ref["asset_id"]] = name
    text = build_brief(root, k, program_path=PROGRAM, input_files=files)
    (workdir / "BRIEF.md").write_text(text, encoding="utf-8", newline="\n")
    try:
        completed = subprocess.run(
            argv,
            cwd=workdir,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        update_session(root, token, status="TIMEOUT", finished_at=now())
        raise RuntimeError(f"Claude Code session exceeded {timeout} s; it still counts")
    allowed = {"BRIEF.md", PROGRAM, *(files or {}).values()}
    unexpected = sorted(
        path.relative_to(workdir).as_posix()
        for path in workdir.rglob("*")
        if path.is_file() and path.relative_to(workdir).as_posix() not in allowed
    )
    (workdir / "session.json").write_text(completed.stdout, encoding="utf-8")
    (workdir / "stderr.txt").write_text(completed.stderr, encoding="utf-8")
    result = result_object(completed.stdout)
    program = workdir / PROGRAM
    problems = []
    if program.is_file():
        try:
            read_program(
                root,
                relative(root, program),
                {r["asset_id"] for r in refs},
                settings,
                render_policy(root),
            )
        except SceneError as error:
            problems = error.problems
        except ValueError as error:
            problems = [str(error)]
    failed = completed.returncode or result.get("is_error") or not program.is_file()
    session = update_session(
        root,
        token,
        status="FAILED" if failed else "COMPLETED",
        finished_at=now(),
        exit_code=completed.returncode,
        brief_sha256=sha(workdir / "BRIEF.md"),
        program=relative(root, program) if program.is_file() else None,
        program_sha256=sha(program) if program.is_file() else None,
        program_problems=problems,
        unexpected_files=unexpected,
        **{
            key: result.get(key)
            for key in ("session_id", "subtype", "is_error", "num_turns", "total_cost_usd")
        },
    )
    if failed:
        raise RuntimeError(
            f"Claude Code session {token} wrote no usable scene (exit {completed.returncode});"
            f" see {relative(root, workdir)}"
        )
    used = [s for s in runtime.state(root).get("authoring", [])]
    outcome = {
        "session": session,
        "sessions_used": len(used),
        "session_limit": limits["limit"],
        "recorded_cost_usd": round(sum(float(s.get("total_cost_usd") or 0) for s in used), 6),
    }
    if problems:
        return {
            **outcome,
            "status": "INVALID_SCENE",
            "next": "The next session's brief lists these problems; author again or fix the scene.",
        }
    if not then_render:
        return {
            **outcome,
            "status": "SCENE_WRITTEN",
            "next": f"Preview or render it: `hsd code render <project> {k} --program {session['program']}`",
        }
    rendered = render(
        root,
        k,
        session["program"],
        author={
            "kind": "claude-code-headless",
            "session_token": token,
            "session_id": session.get("session_id"),
            "cli_version": version,
            "model": model,
            "brief_sha256": session["brief_sha256"],
        },
    )
    return {**outcome, "status": rendered["status"], "render": rendered}
