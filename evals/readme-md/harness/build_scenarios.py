"""Build the nine evaluation scenarios into <work>/scenarios.

Usage: python build_scenarios.py [--s8-ref <git-ref>]

Builders are deterministic (fixed seeds, fixed commit dates), so every build
produces the same files. s8 is a clone of this repository trimmed to
--s8-ref (default 668ba4f, the README the recorded results used).
"""
import importlib
import subprocess
import sys

from evalenv import REPO, WORK, force_rmtree, positional, split_flag
from fixture import ENV  # evalenv puts the scenarios folder on sys.path

BUILDERS = ["s1_logslice", "s2_fetchkit", "s3_air", "s4_shopfloor",
            "s5_saoluu", "s6_grepl", "s7_tasklog", "s9_cnc"]
S8_REF = "668ba4f"


def build_s8(base, ref: str) -> None:
    """Clone this repository at `ref`, keeping only history up to it."""
    dest = base / "s8-lisa-skills"

    def git(*args):
        subprocess.run(["git", "-C", str(dest), *args], check=True, env=ENV,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    subprocess.run(["git", "clone", "-q", "--no-hardlinks", str(REPO), str(dest)],
                   check=True, env=ENV)
    git("checkout", "-q", "-B", "main", ref)
    tags = subprocess.run(["git", "-C", str(dest), "tag", "-l"], capture_output=True,
                          text=True, check=True, env=ENV).stdout.split()
    for tag in tags:
        git("tag", "-d", tag)
    git("remote", "remove", "origin")
    git("remote", "add", "origin", "https://github.com/LisaHQ/lisa-skills.git")
    git("reflog", "expire", "--expire=now", "--all")
    git("gc", "-q", "--prune=now")


def main() -> None:
    ref, args = split_flag(sys.argv[1:], "--s8-ref", S8_REF)
    positional(args, __doc__, exactly=0)
    base = WORK / "scenarios"
    force_rmtree(base)
    base.mkdir(parents=True)
    for name in BUILDERS:
        module = importlib.import_module(name)
        module.build(base)
        print("built", module.ROOT)
    build_s8(base, ref)
    print(f"built s8-lisa-skills at {ref}")
    print(f"scenarios: {base}")


if __name__ == "__main__":
    main()
