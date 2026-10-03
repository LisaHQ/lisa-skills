"""Freeze a version of a suite's skill for an evaluation arm.

Usage: python snapshot_skill.py <suite> <label> [--ref <git-ref>]

Without --ref, copies the working tree (your candidate edit). With --ref,
extracts that commit's version (for example HEAD as the baseline). The result
lands in <work>/<suite>/skill-snapshots/<label>/<skill>; run_arms.py accepts
the label.
"""
import io
import shutil
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path

from evalenv import REPO, SESSION_ENV, force_rmtree, load_suite, positional, split_flag


def main() -> None:
    suite, args = load_suite(sys.argv[1:], __doc__)
    ref, args = split_flag(args, "--ref")
    label = positional(args, __doc__, exactly=1)[0]
    dest = suite.snapshot(label)
    force_rmtree(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    if ref is None:
        shutil.copytree(suite.skill_dir, dest)
    else:
        rel = suite.skill_dir.relative_to(REPO).as_posix()
        data = subprocess.run(["git", "-C", str(REPO), "archive", "--format=tar", ref, rel],
                              capture_output=True, check=True, env=SESSION_ENV).stdout
        with tempfile.TemporaryDirectory() as tmp, tarfile.open(fileobj=io.BytesIO(data)) as tar:
            try:
                tar.extractall(tmp, filter="data")
            except TypeError:  # Python without tarfile extraction filters
                tar.extractall(tmp)
            shutil.copytree(Path(tmp) / rel, dest)
    print(f"{label} ({ref or 'working tree'}): {dest}")
    for f in sorted(p.relative_to(dest).as_posix() for p in dest.rglob("*") if p.is_file()):
        print("  " + f)


if __name__ == "__main__":
    main()
