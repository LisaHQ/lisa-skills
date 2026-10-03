"""Shared paths and helpers for the readme-md evaluation harness.

Generated material (scenarios, runs, blind copies, judgments, snapshots) lives
in the work directory: $README_EVAL_WORK, or <system temp>/readme-md-eval.
Keep it outside synced folders; it holds thousands of files and nested .git
directories.
"""
from __future__ import annotations

import json
import os
import shutil
import stat
import sys
import tempfile
from pathlib import Path

EVAL = Path(__file__).resolve().parents[1]
REPO = EVAL.parents[1]
SKILL = REPO / "skills" / "readme-md"
WORK = Path(os.environ.get("README_EVAL_WORK") or Path(tempfile.gettempdir()) / "readme-md-eval")
REQUESTS: dict[str, str] = json.loads((EVAL / "requests.json").read_text(encoding="utf-8"))

# Bash commands a headless writer may run without approval: reading, counting,
# git inspection, and local interpreters. Installs and network access stay denied.
WRITER_BASH = [
    "python", "python3", "node", "PYTHONPATH=src python", "PYTHONPATH=src python3",
    "PYTHONDONTWRITEBYTECODE=1", "cd", "echo", "printf", "sed -n", "tr", "od", "diff", "cmp",
    "powershell", "pwsh", "git log", "git status", "git remote", "git tag", "git describe",
    "git show", "git diff", "git ls-files", "ls", "cat", "head", "tail", "wc", "find", "grep",
    "file", "unzip -l", "awk", "sort", "uniq", "cut", "du", "stat",
]
WRITER_TOOLS = ["Read", "Write", "Edit", "Glob", "Grep", *(f"Bash({c}:*)" for c in WRITER_BASH)]
JUDGE_TOOLS = WRITER_TOOLS + ["Bash(mkdir:*)", "Bash(cp:*)"]
DENIED_TOOLS = ["WebFetch", "WebSearch"]

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, str(EVAL / "scenarios"))
from fixture import git_trust_env  # noqa: E402

# Environment for headless sessions: their git commands must work in work
# directories on drives without ownership records.
SESSION_ENV = git_trust_env(os.environ)


def claude_bin() -> str:
    """Locate the Claude Code CLI; set CLAUDE_BIN to override."""
    if os.environ.get("CLAUDE_BIN"):
        return os.environ["CLAUDE_BIN"]
    if os.name == "nt":
        # npm's claude.cmd shim cannot be launched without a shell; call the exe it wraps.
        exe = Path(os.environ.get("APPDATA", "")) / "npm/node_modules/@anthropic-ai/claude-code/bin/claude.exe"
        if exe.exists():
            return str(exe)
        found = shutil.which("claude.exe")
        if found:
            return found
    found = shutil.which("claude")
    if not found:
        raise SystemExit("Claude Code CLI not found; install it or set CLAUDE_BIN.")
    return found


def folder_of(scenario: str) -> str:
    """Scenario s1-logslice is checked out in a folder named logslice."""
    return scenario.split("-", 1)[1]


def force_rmtree(path: Path) -> None:
    """Delete a tree, clearing read-only bits that git object files carry on Windows."""
    def retry(func, p, _exc):
        Path(p).chmod(stat.S_IWRITE)
        func(p)
    if not path.exists():
        return
    if sys.version_info >= (3, 12):
        shutil.rmtree(path, onexc=retry)
    else:
        shutil.rmtree(path, onerror=retry)


def split_flag(args: list[str], flag: str, default=None):
    """Remove `flag value` from args and return (value, remaining args)."""
    if flag in args:
        i = args.index(flag)
        if i + 1 >= len(args):
            raise SystemExit(f"{flag} needs a value")
        return args[i + 1], args[:i] + args[i + 2:]
    return default, args


def positional(args: list[str], usage: str, exactly: int | None = None, at_least: int = 0) -> list[str]:
    """Return the remaining arguments, or print usage on unknown flags or a wrong count."""
    if any(a.startswith("-") for a in args) or len(args) < at_least or (exactly is not None and len(args) != exactly):
        raise SystemExit(usage)
    return args
