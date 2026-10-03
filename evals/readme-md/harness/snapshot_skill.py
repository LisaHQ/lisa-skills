"""Freeze a version of skills/readme-md for an evaluation arm.

Usage: python snapshot_skill.py <label> [--ref <git-ref>]

Without --ref, copies the working tree (your candidate edit). With --ref,
extracts that commit's version (for example HEAD as the baseline). The result
lands in <work>/skill-snapshots/<label>/readme-md; run_arms.py accepts the label.
"""
import io
import shutil
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path

from evalenv import REPO, SESSION_ENV, SKILL, WORK, force_rmtree, positional, split_flag


def main() -> None:
    ref, args = split_flag(sys.argv[1:], "--ref")
    positional(args, __doc__, exactly=1)
    dest = WORK / "skill-snapshots" / args[0] / "readme-md"
    force_rmtree(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    if ref is None:
        shutil.copytree(SKILL, dest)
    else:
        rel = SKILL.relative_to(REPO).as_posix()
        data = subprocess.run(["git", "-C", str(REPO), "archive", "--format=tar", ref, rel],
                              capture_output=True, check=True, env=SESSION_ENV).stdout
        with tempfile.TemporaryDirectory() as tmp, tarfile.open(fileobj=io.BytesIO(data)) as tar:
            try:
                tar.extractall(tmp, filter="data")
            except TypeError:  # Python without tarfile extraction filters
                tar.extractall(tmp)
            shutil.copytree(Path(tmp) / rel, dest)
    files = sorted(p.relative_to(dest).as_posix() for p in dest.rglob("*") if p.is_file())
    print(f"{args[0]} ({ref or 'working tree'}): {dest}")
    for f in files:
        print("  " + f)


if __name__ == "__main__":
    main()
