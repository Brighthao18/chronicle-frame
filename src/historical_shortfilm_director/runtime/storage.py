"""Preserved local production invariants."""

from __future__ import annotations
import hashlib
import json
import os
import re
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path


def now():
    return datetime.now(timezone.utc).isoformat()


def load(path, default=None):
    p = Path(path)
    return json.loads(p.read_text(encoding="utf-8-sig")) if p.exists() else default


def save(path, value):
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_name(p.name + "." + uuid.uuid4().hex + ".tmp")
    try:
        with tmp.open("w", encoding="utf-8", newline="\n") as f:
            json.dump(value, f, ensure_ascii=False, indent=2, allow_nan=False)
            f.write("\n")
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, p)
    finally:
        if tmp.exists():
            tmp.unlink()


def digest(value):
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False).encode("utf-8")
    ).hexdigest()


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def identifier(value):
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,95}", value):
        raise ValueError(f"Invalid portable ID: {value!r}")
    if value.upper() in {
        "CON",
        "PRN",
        "AUX",
        "NUL",
        *[f"COM{i}" for i in range(1, 10)],
        *[f"LPT{i}" for i in range(1, 10)],
    }:
        raise ValueError(f"Windows reserved ID: {value}")
    return value


def local(root, value):
    if not value:
        raise ValueError("Empty path")
    root = Path(root).resolve()
    p = (root / value).resolve()
    if not p.is_relative_to(root):
        raise ValueError(f"Path outside project: {value}")
    for part in p.relative_to(root).parts:
        if part.endswith((" ", ".")) or re.search(r'[<>:"|?*]', part):
            raise ValueError(f"Invalid Windows path: {value}")
        if part.split(".")[0].upper() in {
            "CON",
            "PRN",
            "AUX",
            "NUL",
            *[f"COM{i}" for i in range(1, 10)],
            *[f"LPT{i}" for i in range(1, 10)],
        }:
            raise ValueError(f"Windows reserved path: {value}")
    return p


def relative(root, path):
    return Path(path).resolve().relative_to(Path(root).resolve()).as_posix()


@contextmanager
def mutation(root):
    """Short-lived single-writer lock. Never held during generation or media rendering."""
    p = local(root, "work/runtime.lock")
    p.parent.mkdir(parents=True, exist_ok=True)
    try:
        fd = os.open(p, os.O_WRONLY | os.O_CREAT | os.O_EXCL)
    except FileExistsError:
        raise RuntimeError(
            "Runtime writer locked. Inspect owner/process before removing a stale lock."
        )
    try:
        os.write(fd, json.dumps({"pid": os.getpid(), "time": now()}).encode())
        os.close(fd)
        yield
    finally:
        p.unlink(missing_ok=True)
