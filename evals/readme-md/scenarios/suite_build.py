"""Build the nine readme-md scenarios (called by evals/harness/build_scenarios.py)."""
import importlib
import subprocess

from evalenv import REPO
from fixture import ENV

BUILDERS = ["s1_logslice", "s2_fetchkit", "s3_air", "s4_shopfloor",
            "s5_saoluu", "s6_grepl", "s7_tasklog", "s9_cnc"]


def build_s8(base, ref: str) -> str:
    """Clone this repository at `ref`, keeping only history up to it."""
    dest = base / "s8-lisa-skills"

    def git(*args, capture=False):
        out = subprocess.run(["git", "-C", str(dest), *args], check=True, env=ENV,
                             capture_output=True, text=True)
        return out.stdout if capture else None

    subprocess.run(["git", "clone", "-q", "--no-hardlinks", str(REPO), str(dest)], check=True, env=ENV)
    git("checkout", "-q", "-B", "main", ref)
    for tag in git("tag", "-l", capture=True).split():
        git("tag", "-d", tag)
    git("remote", "remove", "origin")
    git("remote", "add", "origin", "https://github.com/LisaHQ/lisa-skills.git")
    git("reflog", "expire", "--expire=now", "--all")
    git("gc", "-q", "--prune=now")
    return f"s8-lisa-skills at {ref}"


def build_all(base, ref):
    built = []
    for name in BUILDERS:
        module = importlib.import_module(name)
        module.build(base)
        built.append(module.ROOT)
    built.append(build_s8(base, ref))
    return built
