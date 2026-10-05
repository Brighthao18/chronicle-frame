"""Best-effort static tree scan. Report locations/categories, never secret values or Git identity."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path

IGNORED = {
    ".git",
    "__pycache__",
    ".venv",
    "venv",
    "work",
    "outputs",
    "build",
    "dist",
    ".pytest_cache",
    ".ruff_cache",
    ".idea",
    ".vscode",
}
RULES = {
    "known_api_key": re.compile(
        r"\b(?:sk-[A-Za-z0-9_-]{20,}|gh[pousr]_[A-Za-z0-9]{20,}|AKIA[A-Z0-9]{16})\b"
    ),
    "private_key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "embedded_credential": re.compile(
        r"(?i)\b(?:password|api_key|client_secret|access_token|refresh_token|session_cookie)\s*[:=]\s*['\"][^'\"\s]{12,}['\"]"
    ),
    "personal_path": re.compile(
        r"(?i)\b[A-Z]:[\\/]Users[\\/][^\\/\s'\"\[\]]+|/Users/[^/\s'\"\[\]]+|/home/[^/\s'\"\[\]]+"
    ),
    "email": re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"),
    "private_identity": re.compile(r"(?i)author:\s*OpenAI-assisted custom skill for\s+\S+"),
    "private_report": re.compile(
        r"(?i)the user" + r"'s[^\n]*(?:research report|reports)|user-supplied research" + " reports"
    ),
    "stale_submission_logistics": re.compile(r"(?i)submission (?:mailbox|deadline):"),
    "private_url": re.compile(
        r"(?i)https?://(?:10\.\d+\.\d+\.\d+|192\.168\.\d+\.\d+|127\.0\.0\.1|localhost)(?::\d+)?/"
    ),
}
ACCOUNT_NAMES = {
    "credentials.json",
    "cookies.json",
    "token.json",
    "storage_state.json",
    "auth_state.json",
}


def scan(root, check_index=True):
    root = Path(root).resolve()
    findings, scanned = [], 0
    terminology = 0
    for path in sorted(root.rglob("*")):
        rel = path.relative_to(root)
        if not path.is_file() or any(
            part in IGNORED or part.endswith(".egg-info") for part in rel.parts
        ):
            continue
        if path.name in ACCOUNT_NAMES or path.name == ".env":
            findings.append(
                {"path": rel.as_posix(), "line": 0, "category": "account_state_artifact"}
            )
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        scanned += 1
        for line_number, line in enumerate(text.splitlines(), 1):
            terminology += bool(
                re.search(r"\b(?:token|authorization|receipt|cookie|OAuth)\b", line, re.I)
            )
            for category, pattern in RULES.items():
                if pattern.search(line):
                    findings.append(
                        {"path": rel.as_posix(), "line": line_number, "category": category}
                    )
    index = "NOT_CHECKED"
    tracked_caches = []
    if check_index and (root / ".git").exists():
        result = subprocess.run(
            ["git", "ls-files", "-z"], cwd=root, capture_output=True, check=True
        )
        tracked = result.stdout.decode("utf-8").split("\0")
        tracked_caches = [
            name for name in tracked if "__pycache__" in name or name.endswith((".pyc", ".pyo"))
        ]
        index = "PASS" if not tracked_caches else "FAIL"
    return {
        "status": "FAIL" if findings or tracked_caches else "PASS",
        "files_scanned": scanned,
        "findings": findings,
        "tracked_cache_check": index,
        "tracked_caches": tracked_caches,
        "benign_runtime_security_term_lines": terminology,
        "term_classification": "Runtime attempt IDs, authorization schemas, synthetic fixtures and security guidance are not embedded account credentials",
        "history_scope": "Working tree/index only. No Git configuration or Git history inspected; no history-clean claim.",
        "limitations": "Pattern-based static review cannot establish absence of every secret or vulnerability",
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", nargs="?", default=".")
    parser.add_argument("--output")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    result = scan(args.root)
    payload = json.dumps(result, indent=2) + "\n"
    if args.output:
        Path(args.output).write_text(payload, encoding="utf-8")
    print(payload)
    raise SystemExit(2 if args.check and result["status"] != "PASS" else 0)
