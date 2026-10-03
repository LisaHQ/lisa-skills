"""Shared paths, suite loading, and helpers for the skill evaluation harness.

Every script takes the suite name first (a folder under evals/, such as
readme-md or commit-message). Generated material for a suite lives in
<work root>/<suite>, where the work root is $LISA_EVAL_WORK or
<system temp>/lisa-evals. Keep it outside synced folders: a round writes
thousands of files and nested .git folders.
"""
from __future__ import annotations

import json
import os
import shutil
import stat
import sys
import tempfile
from pathlib import Path

HARNESS = Path(__file__).resolve().parent
EVALS = HARNESS.parent
REPO = EVALS.parent
WORK_ROOT = Path(os.environ.get("LISA_EVAL_WORK") or Path(tempfile.gettempdir()) / "lisa-evals")

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from fixture import git_trust_env  # noqa: E402  (harness folder is on sys.path)

# Environment for headless sessions and harness git calls: git must work in
# work directories on drives without ownership records.
SESSION_ENV = git_trust_env(os.environ)

# Commands a headless writer may run without approval: reading, counting,
# version-control inspection, and local interpreters. Installs, network
# access, and repository mutations stay denied. Suites add read-only extras.
WRITER_BASH = [
    "python", "python3", "node", "PYTHONPATH=src python", "PYTHONPATH=src python3",
    "PYTHONDONTWRITEBYTECODE=1", "cd", "echo", "printf", "sed -n", "tr", "od", "diff", "cmp",
    "powershell", "pwsh", "git log", "git status", "git remote", "git tag", "git describe",
    "git show", "git diff", "git ls-files", "ls", "cat", "head", "tail", "wc", "find", "grep",
    "file", "unzip -l", "awk", "sort", "uniq", "cut", "du", "stat",
]
# Skill is denied so installed copies of a skill (user or plugin level) cannot
# leak into the no-skill arm; skill arms read their snapshot directly.
DENIED_TOOLS = ["WebFetch", "WebSearch", "Skill"]


class Suite:
    """One evaluation suite: evals/<name>/ plus its work directory."""

    def __init__(self, name: str):
        self.name = name
        self.dir = EVALS / name
        config = json.loads((self.dir / "suite.json").read_text(encoding="utf-8"))
        self.skill = config["skill"]
        self.weights: dict[str, float] = config["weights"]
        self.extra_bash: list[str] = config.get("extra_bash", [])
        self.repo_ref: str | None = config.get("repo_ref")
        self.skill_dir = REPO / "skills" / self.skill
        self.work = WORK_ROOT / name
        self.requests: dict[str, str] = json.loads((self.dir / "requests.json").read_text(encoding="utf-8"))
        sys.path.insert(0, str(self.dir / "scenarios"))
        sys.path.insert(0, str(self.dir))

    @property
    def writer_tools(self) -> list[str]:
        return ["Read", "Write", "Edit", "Glob", "Grep",
                *(f"Bash({c}:*)" for c in WRITER_BASH + self.extra_bash)]

    @property
    def judge_tools(self) -> list[str]:
        return self.writer_tools + ["Bash(mkdir:*)", "Bash(cp:*)"]

    def snapshot(self, label: str) -> Path:
        return self.work / "skill-snapshots" / label / self.skill

    def weighted(self, scores: dict) -> float:
        return sum(self.weights[k] * scores[k] for k in self.weights) / sum(self.weights.values())


def suites() -> list[str]:
    return sorted(p.name for p in EVALS.iterdir() if (p / "suite.json").exists())


def load_suite(args: list[str], usage: str) -> tuple[Suite, list[str]]:
    """Take the suite name from the first argument."""
    if not args or args[0] not in suites():
        raise SystemExit(f"{usage}\nSuites: {', '.join(suites())}")
    return Suite(args[0]), args[1:]


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


def scenario_dirs(base: Path) -> list[Path]:
    """Scenario folders under base; names starting with _ or . hold helpers."""
    return sorted(p for p in base.iterdir() if p.is_dir() and not p.name.startswith(("_", ".")))


SKIP_DIRS = {".git", ".svn", "__pycache__", "node_modules", ".venv", ".pytest_cache"}


def walk(base: Path):
    for p in base.rglob("*"):
        if p.is_file() and not any(part in SKIP_DIRS for part in p.relative_to(base).parts):
            yield p.relative_to(base).as_posix()


def vcs_state(path: Path) -> dict | None:
    """Fingerprint version-control state that working-file diffs cannot show.

    Git: the HEAD commit, the index entries, and the stash. SVN: the working
    copy revision and scheduled changes (svn status without unversioned files).
    Returns None when path is not a checkout.
    """
    import hashlib
    import subprocess

    def run(*cmd):
        out = subprocess.run(cmd, cwd=path, env=SESSION_ENV, capture_output=True, text=True,
                             encoding="utf-8", errors="replace")
        return out.stdout.strip()

    if (path / ".git").exists():
        return {
            "HEAD": run("git", "rev-parse", "HEAD"),
            "index": hashlib.sha1(run("git", "ls-files", "-s").encode()).hexdigest(),
            "stash": run("git", "stash", "list"),
        }
    if (path / ".svn").exists():
        return {
            "revision": run("svn", "info", "--show-item", "revision"),
            "scheduled": run("svn", "status", "-q"),
        }
    return None


def vcs_report(pristine: Path, out: Path) -> str:
    """One line per version-control fingerprint: unchanged or CHANGED."""
    before, after = vcs_state(pristine), vcs_state(out)
    if before is None or after is None:
        return ""
    return "".join(f"vcs {key}: {'unchanged' if before[key] == after.get(key) else 'CHANGED'}\n"
                   for key in before)


def diff_tree(pristine: Path, out: Path):
    """Return (added, modified, deleted) working files of out compared with pristine."""
    import filecmp
    before, after = set(walk(pristine)), set(walk(out))
    modified = sorted(f for f in before & after if not filecmp.cmp(pristine / f, out / f, shallow=False))
    return sorted(after - before), modified, sorted(before - after)


def force_rmtree(path: Path) -> None:
    """Delete a tree, clearing read-only bits that git and svn files carry on Windows."""
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
