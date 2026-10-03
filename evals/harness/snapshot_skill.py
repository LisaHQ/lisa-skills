"""Freeze a version of a suite's skill for an evaluation arm.

Usage: python snapshot_skill.py <suite> <label> [--ref <git-ref>]

Without --ref, copies the working tree (your candidate edit). With --ref,
extracts that commit's version (for example HEAD as the baseline). The result
lands in <work>/<suite>/skill-snapshots/<label>/<skill>, read-only, with its
source and content hash in skill-snapshots/<label>.json; run_arms.py accepts
the label and checks the hash after a round. An existing snapshot is replaced
only after the new one was extracted successfully.
"""
import hashlib
import io
import json
import shutil
import subprocess
import sys
import tarfile
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from evalenv import (REPO, SESSION_ENV, check_name, force_rmtree, load_suite, make_read_only, positional,
                     split_flag)


def content_hash(path: Path) -> str:
    h = hashlib.sha256()
    for p in sorted(p for p in path.rglob("*") if p.is_file()):
        h.update(p.relative_to(path).as_posix().encode() + b"\0" + p.read_bytes() + b"\0")
    return h.hexdigest()


def git(*args: str) -> subprocess.CompletedProcess:
    proc = subprocess.run(["git", "-C", str(REPO), *args], capture_output=True, env=SESSION_ENV)
    if proc.returncode != 0:
        raise SystemExit(f"git {' '.join(args)} failed: {proc.stderr.decode('utf-8', 'replace').strip()}")
    return proc


def main() -> None:
    suite, args = load_suite(sys.argv[1:], __doc__)
    ref, args = split_flag(args, "--ref")
    label = check_name("snapshot label", positional(args, __doc__, exactly=1)[0], dashes=True)
    dest = suite.snapshot(label)
    dest.parent.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=dest.parent.parent) as tmp:
        staged = Path(tmp) / suite.skill
        rel = suite.skill_dir.relative_to(REPO).as_posix()
        if ref is None:
            shutil.copytree(suite.skill_dir, staged)
            commit = git("rev-parse", "HEAD").stdout.decode().strip()
        else:
            commit = git("rev-parse", "--verify", "--quiet", f"{ref}^{{commit}}").stdout.decode().strip()
            data = git("archive", "--format=tar", commit, rel).stdout
            with tarfile.open(fileobj=io.BytesIO(data)) as tar:
                try:
                    tar.extractall(tmp, filter="data")
                except TypeError:  # Python without tarfile extraction filters
                    tar.extractall(tmp)
            shutil.move(str(Path(tmp) / rel), str(staged))
        if not (staged / "SKILL.md").exists():
            raise SystemExit(f"{ref or 'working tree'} has no {rel}/SKILL.md; the existing snapshot is unchanged")
        force_rmtree(dest.parent)
        dest.parent.mkdir(parents=True)
        shutil.move(str(staged), str(dest))
    make_read_only(dest)
    info = {"label": label, "skill": suite.skill, "ref": ref or "working tree", "commit": commit,
            "sha256": content_hash(dest), "created": datetime.now(timezone.utc).isoformat(timespec="seconds")}
    (dest.parent.parent / f"{label}.json").write_text(json.dumps(info, indent=1), encoding="utf-8")
    print(f"{label} ({ref or 'working tree'} at {commit[:7]}, sha256 {info['sha256'][:12]}): {dest}")
    for f in sorted(p.relative_to(dest).as_posix() for p in dest.rglob("*") if p.is_file()):
        print("  " + f)


if __name__ == "__main__":
    main()
