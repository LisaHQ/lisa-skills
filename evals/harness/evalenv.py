"""Shared paths, suite loading, and helpers for the skill evaluation harness.

Every script takes the suite name first (a folder under evals/, such as
readme-md or commit-message). Generated material for a suite lives in
<work root>/<suite>, where the work root is $LISA_EVAL_WORK or
<system temp>/lisa-evals. Keep it outside synced folders: a round writes
thousands of files and nested .git folders.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
from codecs import BOM_UTF16_BE as BOM_BE, BOM_UTF16_LE as BOM_LE
from pathlib import Path

HARNESS = Path(__file__).resolve().parent
EVALS = HARNESS.parent
REPO = EVALS.parent
WORK_ROOT = Path(os.environ.get("LISA_EVAL_WORK") or Path(tempfile.gettempdir()) / "lisa-evals").resolve()

# Bump when a change to the harness makes new rounds incomparable with older
# ones (session flags, prompts, blinding). Recorded in every session record.
HARNESS_VERSION = 2

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from fixture import git_config_env  # noqa: E402  (harness folder is on sys.path)

# Variables a launching Claude Code session exports to its children. Passing
# them on would couple eval sessions to that session (tools, messaging, effort).
SESSION_COUPLING = {
    "CLAUDECODE", "CLAUDE_AGENT_SDK_VERSION", "CLAUDE_CODE_CHILD_SESSION", "CLAUDE_CODE_DESKTOP_APP_VERSION",
    "CLAUDE_CODE_DISABLE_CRON", "CLAUDE_CODE_DISABLE_TERMINAL_TITLE", "CLAUDE_CODE_EAGER_FLUSH",
    "CLAUDE_CODE_EMIT_TOOL_USE_SUMMARIES", "CLAUDE_CODE_ENABLE_ASK_USER_QUESTION_TOOL",
    "CLAUDE_CODE_ENABLE_SDK_FILE_CHECKPOINTING", "CLAUDE_CODE_ENTRYPOINT", "CLAUDE_CODE_HOST_SESSION_ID",
    "CLAUDE_CODE_MESSAGING_SOCKET", "CLAUDE_CODE_MESSAGING_TOKEN", "CLAUDE_CODE_REPORT_FINDINGS",
    "CLAUDE_CODE_SDK_HAS_HOST_AUTH_REFRESH", "CLAUDE_CODE_SESSION_ATTENDED", "CLAUDE_CODE_SESSION_ID",
    "CLAUDE_CODE_TERMINAL_MCP_TOOLS", "CLAUDE_EFFORT", "CLAUDE_PID", "CLAUDE_PREVIEW_CLASSIFIER_FLOOR",
    "DISABLE_MICROCOMPACT", "MCP_CONNECTION_NONBLOCKING", "MCP_SERVER_CONNECTION_BATCH_SIZE",
    "GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "GIT_OBJECT_DIRECTORY", "GIT_COMMON_DIR",
}

# Environment for headless sessions and harness git calls. Git must work in
# work directories on drives without ownership records, must not reach the
# network (a scenario remote could expose answers), must not look for a
# repository above the work root, and shows no line-ending warnings.
SESSION_ENV = dict(
    git_config_env({k: v for k, v in os.environ.items() if k not in SESSION_COUPLING},
                   {"safe.directory": "*", "core.autocrlf": "false"}),
    GIT_ALLOW_PROTOCOL="file",
    GIT_TERMINAL_PROMPT="0",
    GCM_INTERACTIVE="never",
    GIT_CEILING_DIRECTORIES=str(WORK_ROOT),
)

# Commands a headless writer may run without approval: reading, counting,
# version-control inspection, and local interpreters. Commands outside the
# list are denied and recorded. Interpreters can still write files or reach
# the network, so the harness detects repository changes after each run
# instead of preventing them. Suites add read-only extras in suite.json.
WRITER_BASH = [
    "python", "python3", "node", "PYTHONPATH=src python", "PYTHONPATH=src python3",
    "cd", "echo", "printf", "sed -n", "tr", "od", "diff", "cmp",
    "powershell", "pwsh", "git log", "git status", "git remote", "git tag", "git describe",
    "git show", "git diff", "git ls-files", "ls", "cat", "head", "tail", "wc", "find", "grep",
    "file", "unzip -l", "awk", "sort", "uniq", "cut", "du", "stat",
]
# Skill is denied so installed copies of a skill (user or plugin level) cannot
# leak into the no-skill arm; skill arms read their snapshot directly.
DENIED_TOOLS = ["WebFetch", "WebSearch", "Skill"]

# Every writer and judge session starts in isolation: no user or project
# customizations (CLAUDE.md and AGENTS.md included), no MCP servers, no saved
# session, only the tools a task needs, and no commit attribution instruction.
# File tools and shell reads stay inside the working directories (the run
# folder and, for skill arms, the skill snapshot); interpreters are not
# confined, so reach_flags() audits tool calls afterwards.
SESSION_SETTINGS = {
    "attribution": {"commit": "", "pr": ""},
    "includeCoAuthoredBy": False,
    "permissions": {"blockReadsOutsideWorkingDirectories": True},
}
ISOLATION_FLAGS = ["--safe-mode", "--strict-mcp-config", "--no-session-persistence",
                   "--tools", "Read,Write,Edit,Glob,Grep,Bash", "--settings", json.dumps(SESSION_SETTINGS)]

NAME = re.compile(r"[A-Za-z0-9](?:[A-Za-z0-9_.]*[A-Za-z0-9_])?")


def check_name(kind: str, value: str, dashes: bool = False) -> str:
    """Reject names that could escape the work directory or confuse name parsing.

    Iteration and tag names may not contain '-', which separates them in blind
    set names (<iter>-<tag>); snapshot labels and arms may.
    """
    pattern = r"[A-Za-z0-9](?:[A-Za-z0-9_.-]*[A-Za-z0-9_])?" if dashes else NAME.pattern
    if not re.fullmatch(pattern, value or ""):
        allowed = "letters, digits, '_', '.'" + (", '-'" if dashes else "")
        raise SystemExit(f"invalid {kind} name {value!r}: use {allowed}, starting and ending with a letter or digit")
    return value


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
        return self.work / "skill-snapshots" / check_name("snapshot label", label, dashes=True) / self.skill

    def weighted(self, scores: dict, drop: tuple[str, ...] = ()) -> float:
        keys = [k for k in self.weights if k not in drop]
        return sum(self.weights[k] * scores[k] for k in keys) / sum(self.weights[k] for k in keys)


def suites() -> list[str]:
    return sorted(p.name for p in EVALS.iterdir() if (p / "suite.json").exists())


def guard_work_root() -> None:
    """Refuse a work root inside a checkout or below instruction files.

    Sessions would otherwise find the outer repository or load its CLAUDE.md
    or AGENTS.md (trigger tests run without safe mode).
    """
    for folder in [WORK_ROOT, *WORK_ROOT.parents]:
        for name in (".git", ".svn", "CLAUDE.md", "CLAUDE.local.md", "AGENTS.md"):
            if (folder / name).exists():
                raise SystemExit(f"work root {WORK_ROOT} is below {folder / name}; set LISA_EVAL_WORK to a "
                                 "folder outside any repository or project with instruction files")


def load_suite(args: list[str], usage: str) -> tuple[Suite, list[str]]:
    """Take the suite name from the first argument."""
    if not args or args[0] not in suites():
        raise SystemExit(f"{usage}\nSuites: {', '.join(suites())}")
    guard_work_root()
    return Suite(args[0]), args[1:]


def claude_cmd() -> list[str]:
    """Command that starts the Claude Code CLI; set CLAUDE_BIN to override.

    CLAUDE_BIN may point to a .py file (a fake CLI for offline tests), which
    runs with the current Python.
    """
    if os.environ.get("CLAUDE_BIN"):
        path = os.environ["CLAUDE_BIN"]
        return [sys.executable, path] if path.endswith(".py") else [path]
    if os.name == "nt":
        # npm's claude.cmd shim cannot be launched without a shell; call the exe it wraps.
        exe = Path(os.environ.get("APPDATA", "")) / "npm/node_modules/@anthropic-ai/claude-code/bin/claude.exe"
        if exe.exists():
            return [str(exe)]
        found = shutil.which("claude.exe")
        if found:
            return [found]
    found = shutil.which("claude")
    if not found:
        raise SystemExit("Claude Code CLI not found; install it or set CLAUDE_BIN.")
    return [found]


def folder_of(scenario: str) -> str:
    """Scenario s1-logslice is checked out in a folder named logslice."""
    return scenario.split("-", 1)[1]


def scenario_dirs(base: Path) -> list[Path]:
    """Scenario folders under base; names starting with _ or . hold helpers."""
    return sorted(p for p in base.iterdir() if p.is_dir() and not p.name.startswith(("_", ".")))


SKIP_DIRS = {".git", ".svn", "__pycache__", "node_modules", ".venv", ".pytest_cache"}
# Files the harness writes beside a run's project folder.
RUN_FILES = {"notes.md", "meta.json", "tools.jsonl", "failed-result.md", "changes.txt", "files"}


def walk(base: Path):
    for p in base.rglob("*"):
        if p.is_file() and not any(part in SKIP_DIRS for part in p.relative_to(base).parts):
            yield p.relative_to(base).as_posix()


def _digest(text: str) -> str:
    return hashlib.sha1(text.encode("utf-8", "replace")).hexdigest()


def vcs_state(path: Path) -> dict | None:
    """Fingerprint version-control state that working-file diffs cannot show.

    Git: HEAD, the current branch, every ref, the index and its flags, the
    stash, the repository config, the exclude file, and installed hooks. SVN:
    the working copy revision, scheduled changes, and the repository head.
    Returns None when path is not a checkout.
    """
    def run(*cmd):
        out = subprocess.run(cmd, cwd=path, env=SESSION_ENV, capture_output=True, text=True,
                             encoding="utf-8", errors="replace")
        return out.stdout.strip()

    def read(rel):
        p = path / rel
        return p.read_bytes().decode("utf-8", "replace") if p.is_file() else ""

    if (path / ".git").exists():
        git = ("git", "--no-optional-locks")
        hooks = path / ".git" / "hooks"
        return {
            "HEAD": run(*git, "rev-parse", "HEAD"),
            "branch": run(*git, "symbolic-ref", "-q", "HEAD"),
            "refs": _digest(run(*git, "for-each-ref", "--format=%(refname) %(objectname) %(symref)")),
            "index": _digest(run(*git, "ls-files", "-s")),
            "index_flags": _digest(run(*git, "ls-files", "-v")),
            "stash": run(*git, "stash", "list"),
            "config": _digest(read(".git/config")),
            "exclude": _digest(read(".git/info/exclude")),
            "hooks": ",".join(sorted(p.name for p in hooks.iterdir() if not p.name.endswith(".sample")))
            if hooks.is_dir() else "",
        }
    if (path / ".svn").exists():
        return {
            "revision": run("svn", "info", "--show-item", "revision"),
            "scheduled": run("svn", "status", "-q"),
            "repo_head": run("svn", "info", "-r", "HEAD", "--show-item", "revision"),
        }
    return None


def vcs_report(pristine: Path, out: Path) -> str:
    """One line per version-control fingerprint: unchanged or CHANGED.

    A checkout the writer removed or created is reported too, because working
    file diffs skip .git and .svn folders.
    """
    before, after = vcs_state(pristine), vcs_state(out)
    if before is None and after is None:
        return ""
    if after is None:
        return "vcs checkout: REMOVED\n"
    if before is None:
        return "vcs checkout: CREATED\n"
    return "".join(f"vcs {key}: {'unchanged' if before[key] == after.get(key) else 'CHANGED'}\n"
                   for key in before)


def diff_tree(pristine: Path, out: Path):
    """Return (added, modified, deleted) working files of out compared with pristine."""
    import filecmp
    before, after = set(walk(pristine)), set(walk(out)) if out.exists() else set()
    modified = sorted(f for f in before & after if not filecmp.cmp(pristine / f, out / f, shallow=False))
    return sorted(after - before), modified, sorted(before - after)


def changes_text(added, modified, deleted, extra: str = "") -> str:
    return ("added:\n" + "".join(f"  {f}\n" for f in added)
            + "modified:\n" + "".join(f"  {f}\n" for f in modified)
            + "deleted:\n" + "".join(f"  {f}\n" for f in deleted) + extra)


def outside_files(arm_dir: Path, folder: str) -> list[str]:
    """Entries a writer created beside its project folder (writes through '..')."""
    return sorted(p.name for p in arm_dir.iterdir() if p.name != folder and p.name not in RUN_FILES)


def tree_digest(path: Path) -> str:
    """Content fingerprint of a scenario: working files plus version-control state."""
    h = hashlib.sha256()
    for rel in sorted(walk(path)):
        h.update(rel.encode() + b"\0" + (path / rel).read_bytes() + b"\0")
    h.update(json.dumps(vcs_state(path), sort_keys=True).encode())
    return h.hexdigest()


def file_digest(path: Path) -> str | None:
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None


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


def make_read_only(path: Path) -> None:
    for p in path.rglob("*"):
        if p.is_file():
            p.chmod(stat.S_IREAD)


def split_flag(args: list[str], flag: str, default=None):
    """Remove `flag value` from args and return (value, remaining args)."""
    if flag in args:
        i = args.index(flag)
        if i + 1 >= len(args) or args[i + 1].startswith("--"):
            raise SystemExit(f"{flag} needs a value")
        return args[i + 1], args[:i] + args[i + 2:]
    return default, args


def split_multi(args: list[str], flag: str) -> tuple[list[str], list[str]]:
    """Remove every `flag value` pair and return (values, remaining args)."""
    values = []
    while flag in args:
        value, args = split_flag(args, flag)
        values.append(value)
    return values, args


def pop_switch(args: list[str], flag: str) -> tuple[bool, list[str]]:
    """Remove a boolean flag and return (present, remaining args)."""
    return flag in args, [a for a in args if a != flag]


def positional(args: list[str], usage: str, exactly: int | None = None, at_least: int = 0) -> list[str]:
    """Return the remaining arguments, or print usage on unknown flags or a wrong count."""
    if any(a.startswith("-") for a in args) or len(args) < at_least or (exactly is not None and len(args) != exactly):
        raise SystemExit(usage)
    return args


def parse_only(value: str | None, valid, what: str = "scenario") -> set[str] | None:
    """Parse --only: None means all; empty or unknown names are errors."""
    if value is None:
        return None
    names = {v.strip() for v in value.split(",") if v.strip()}
    unknown = sorted(names - set(valid))
    if not names or unknown:
        raise SystemExit(f"--only: {'no names given' if not names else 'unknown ' + what + ' ' + ', '.join(unknown)}"
                         f"\nknown: {', '.join(sorted(valid))}")
    return names


def positive_int(value: str, flag: str) -> int:
    try:
        n = int(value)
    except ValueError:
        n = 0
    if n < 1:
        raise SystemExit(f"{flag} must be a positive integer")
    return n


# ---------------------------------------------------------------- blind sets and mappings

def blind_set_info(suite: Suite, name: str) -> dict:
    """Iteration and tag of a blind set, from blind/<name>.json (written by blind.py).

    Older work falls back to a runs/<name> folder, then to <iter>-<tag> with an
    existing runs/<iter>/mapping-<tag>.json; anything else is an error rather
    than a guess, because a wrong mapping silently swaps arms.
    """
    data = read_json(suite.work / "blind" / f"{name}.json")
    if data.get("iter"):
        return {"iter": data["iter"], "tag": data.get("tag"), "blind": name}
    runs = suite.work / "runs"
    if (runs / name).is_dir():
        return {"iter": name, "tag": None, "blind": name}
    for i in [i for i, ch in enumerate(name) if ch == "-"]:
        it, rest = name[:i], name[i + 1:]
        if (runs / it / f"mapping-{rest}.json").exists():
            return {"iter": it, "tag": rest, "blind": name}
    raise SystemExit(f"cannot tell which round and blind set {name!r} belongs to; pass --mapping or check the name")


def set_info(suite: Suite, name: str) -> dict:
    """Iteration, tag, and blind set behind a judgments folder name.

    judge.py records the blind set a judgments folder holds in
    judgments/<name>/_set.json; without that record the name is the blind set.
    """
    owner = read_json(suite.work / "judgments" / name / "_set.json").get("blind") or name
    return blind_set_info(suite, owner)


def mapping_path(suite: Suite, name: str) -> Path:
    info = set_info(suite, name)
    path = suite.work / "runs" / info["iter"] / f"mapping{'-' + info['tag'] if info['tag'] else ''}.json"
    if not path.exists():
        raise SystemExit(f"{name}: mapping file {path} not found")
    return path


# ---------------------------------------------------------------- run status and verdicts

# Sessions that failed for reasons outside the writer's control. They are
# rerun with --retry-failed and never blinded. A session that stopped at its
# turn or budget limit is a genuine (if poor) outcome and is judged.
INFRA_FAILURES = {"error", "timeout", "no_result", "harness_error"}


def read_json(path: Path) -> dict:
    """Parse a JSON file ({} when missing or unreadable); tolerates a UTF-8 BOM or UTF-16."""
    try:
        raw = path.read_bytes()
        encoding = "utf-16" if raw[:2] in (BOM_LE, BOM_BE) else "utf-8-sig"
        return json.loads(raw.decode(encoding))
    except (OSError, ValueError):
        return {}


def remove_path(path: Path) -> None:
    """Delete a file or folder, including read-only ones (git objects on Windows)."""
    if path.is_dir() and not path.is_symlink():
        force_rmtree(path)
    else:
        path.chmod(stat.S_IWRITE)
        path.unlink()


def run_status(meta: dict) -> str:
    """A session's status, derived for records written before statuses existed."""
    if not meta:
        return "missing"
    if meta.get("status"):
        return meta["status"]
    subtype = meta.get("subtype") or ""
    if "stdout_tail" in meta and not subtype:
        return "no_result"
    if subtype == "success" and not meta.get("is_error"):
        return "ok"
    if "max_turns" in subtype:
        return "max_turns"
    return "error"


def verdict_problems(verdict, labels: list[str], weights: dict, ranking: bool = True) -> list[str]:
    """Problems that make a verdict unusable; empty when it is valid.

    Scores must be integers 1-5 for every label and rubric key, and error
    severities 'major' or 'minor'. With ranking=True the ranking must also be
    a permutation of the labels (older pairwise verdicts have no ranking).
    """
    if not isinstance(verdict, dict):
        return ["not a JSON object"]
    problems = []
    for label in labels:
        entry = verdict.get(label)
        scores = entry.get("scores") if isinstance(entry, dict) else None
        if not isinstance(scores, dict):
            problems.append(f"{label}: no scores")
            continue
        problems += [f"{label}.{k}={scores.get(k)!r}" for k in weights
                     if type(scores.get(k)) is not int or not 1 <= scores[k] <= 5]
        errors = entry.get("errors", [])
        if not isinstance(errors, list) or any(not isinstance(e, dict) or e.get("severity") not in ("major", "minor")
                                               for e in errors):
            problems.append(f"{label}: malformed errors")
    if ranking:
        order = verdict.get("ranking")
        if not (isinstance(order, list) and len(order) == len(labels) and set(map(str, order)) == set(labels)):
            problems.append(f"ranking {order!r} is not a permutation of {labels}")
    return problems


def verdict_warnings(verdict: dict, labels: list[str], suite: Suite) -> list[str]:
    """Inconsistencies worth a look that do not invalidate a verdict."""
    notes = []
    for label in labels:
        entry = verdict[label]
        reported = entry.get("weighted")
        if isinstance(reported, (int, float)) and abs(reported - suite.weighted(entry["scores"])) > 0.011:
            notes.append(f"{label}: judge's weighted {reported} differs from {suite.weighted(entry['scores']):.2f}")
        tagged = [e for e in entry.get("errors", []) if e.get("dimension") == "A"]
        if any("dimension" in e for e in entry.get("errors", [])):
            major = sum(e["severity"] == "major" for e in tagged)
            minor = len(tagged) - major
            expected = (5 if not tagged else 4 if (major, minor) == (0, 1) else 3 if (major == 0 and minor >= 2)
                        or (major == 1 and minor <= 3) else 2 if major == 1 or major == 2 else 1)
            if entry["scores"]["A"] != expected:
                notes.append(f"{label}: A={entry['scores']['A']} but its A errors ({major} major, {minor} minor) "
                             f"suggest {expected}")
    order = verdict.get("ranking") or []
    computed = [suite.weighted(verdict[x]["scores"]) for x in order if x in labels]
    if any(b - a > 0.011 for a, b in zip(computed, computed[1:])):
        notes.append(f"ranking {order} contradicts the weighted scores")
    return notes


# ---------------------------------------------------------------- reach audit

# Tool inputs that name places where arm identities or other outcomes live.
REACH = re.compile(r"mapping[^\s/]*\.json|skill-snapshots|judge-sandbox|/blind/|/usage/[0-9a-f]{8}|/runs/"
                   r"|\.\./\.\.", re.I)
PATH_FIELDS = ("file_path", "path", "command", "notebook_path")


def _norm_path_text(text: str) -> str:
    text = text.replace("\\\\", "/").replace("\\", "/").lower()
    return re.sub(r"(?<![\w:])/(?:cygdrive/|mnt/)?([a-z])/", r"\1:/", text)  # /b/x (Git Bash) -> b:/x


def reach_flags(calls: list[dict], allowed: list[Path]) -> list[str]:
    """Tool calls that reach outside the session's own folders toward other runs, mappings, or snapshots.

    allowed are the session's working directories; paths inside them are fine.
    Only path-carrying inputs are checked, so search patterns do not count.
    """
    root = _norm_path_text(str(WORK_ROOT))
    roots = sorted((_norm_path_text(str(p)) for p in allowed), key=len, reverse=True)
    flagged = []
    for call in calls:
        for key in PATH_FIELDS:
            value = (call.get("input") or {}).get(key)
            if not isinstance(value, str):
                continue
            text = _norm_path_text(value)
            for r in roots:
                text = text.replace(r, "<own>")
            if REACH.search(text) or root in text:
                flagged.append(f"{call.get('tool')}: {value[:300]}")
                break
    return flagged
