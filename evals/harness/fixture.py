"""Helpers for building scenario fixtures."""
from __future__ import annotations

import os
import subprocess
from pathlib import Path


def git_trust_env(base: dict) -> dict:
    """Trust every repository for git processes started with this environment.

    Work directories on drives that do not record file ownership (FAT, exFAT,
    some RAM disks) otherwise fail git's dubious-ownership check. This adds
    safe.directory=* in command scope, so the user's git config stays untouched.
    """
    return git_config_env(base, {"safe.directory": "*"})


def git_config_env(base: dict, settings: dict[str, str]) -> dict:
    """Add command-scope git config entries (GIT_CONFIG_KEY_n/VALUE_n) to an environment."""
    env = dict(base)
    n = int(env.get("GIT_CONFIG_COUNT", "0"))
    for key, value in settings.items():
        env[f"GIT_CONFIG_KEY_{n}"] = key
        env[f"GIT_CONFIG_VALUE_{n}"] = value
        n += 1
    env["GIT_CONFIG_COUNT"] = str(n)
    return env


# Variables that would point git at another repository or index.
GIT_REDIRECTS = ("GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "GIT_OBJECT_DIRECTORY", "GIT_COMMON_DIR",
                 "GIT_ALTERNATE_OBJECT_DIRECTORIES", "GIT_NAMESPACE")

# Fixed identity and dates make every build produce the same commits. Global
# and system git config are ignored, so hooks, templates, or status settings
# on the building machine cannot change the fixtures.
ENV = dict(
    git_trust_env({k: v for k, v in os.environ.items() if k not in GIT_REDIRECTS}),
    GIT_CONFIG_GLOBAL=os.devnull,
    GIT_CONFIG_NOSYSTEM="1",
    GIT_AUTHOR_NAME="Example Dev",
    GIT_AUTHOR_EMAIL="dev@example.invalid",
    GIT_COMMITTER_NAME="Example Dev",
    GIT_COMMITTER_EMAIL="dev@example.invalid",
    GIT_AUTHOR_DATE="2024-06-12T10:00:00+00:00",
    GIT_COMMITTER_DATE="2024-06-12T10:00:00+00:00",
)


def w(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def wb(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def _run_git(cwd: Path, args: tuple[str, ...]) -> subprocess.CompletedProcess:
    proc = subprocess.run(["git", *args], cwd=cwd, env=ENV, capture_output=True, text=True,
                          encoding="utf-8", errors="replace")
    if proc.returncode != 0:
        raise SystemExit(f"git {' '.join(args)} failed in {cwd} (exit {proc.returncode}):\n{proc.stderr.strip()}")
    return proc


def git(cwd: Path, *args: str) -> None:
    _run_git(cwd, args)


def git_out(cwd: Path, *args: str) -> str:
    return _run_git(cwd, args).stdout


def commit_all(cwd: Path, message: str) -> None:
    git(cwd, "add", "-A")
    git(cwd, "-c", "commit.gpgsign=false", "commit", "-q", "-m", message)


def expect_status(cwd: Path, expected: list[str]) -> None:
    """Fail the build unless `git status --porcelain` lists exactly the expected entries."""
    actual = sorted(line for line in git_out(cwd, "status", "--porcelain", "--untracked-files=normal",
                                             "--renames").splitlines() if line)
    if actual != sorted(expected):
        raise SystemExit(f"{cwd.name}: unexpected git status\n  expected {sorted(expected)}\n  actual   {actual}")


def git_init(path: Path, remote: str | None = None, tag: str | None = None,
             message: str = "Initial import") -> None:
    git(path, "init", "-q", "-b", "main")
    git(path, "add", "-A")
    git(path, "-c", "commit.gpgsign=false", "commit", "-q", "-m", message)
    if remote:
        git(path, "remote", "add", "origin", remote)
    if tag:
        git(path, "-c", "tag.gpgsign=false", "tag", tag)


def minimal_pdf(lines: list[str]) -> bytes:
    """Return a one-page PDF that shows the given text lines."""
    def esc(s: str) -> str:
        return s.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")

    y = 760
    ops = ["BT", "/F1 11 Tf", "14 TL", f"50 {y} Td"]
    for line in lines:
        ops.append(f"({esc(line)}) Tj T*")
    ops.append("ET")
    stream = "\n".join(ops).encode("latin-1")
    objs = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
        b"/Resources << /Font << /F1 5 0 R >> >> /Contents 4 0 R >>",
        b"<< /Length " + str(len(stream)).encode() + b" >>\nstream\n" + stream + b"\nendstream",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]
    out = bytearray(b"%PDF-1.4\n")
    offsets = []
    for i, body in enumerate(objs, start=1):
        offsets.append(len(out))
        out += f"{i} 0 obj\n".encode() + body + b"\nendobj\n"
    xref = len(out)
    out += f"xref\n0 {len(objs) + 1}\n0000000000 65535 f \n".encode()
    for off in offsets:
        out += f"{off:010d} 00000 n \n".encode()
    out += f"trailer\n<< /Size {len(objs) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode()
    return bytes(out)
