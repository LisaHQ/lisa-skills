"""Build the readme-md scenarios (called by evals/harness/build_scenarios.py)."""
import importlib
import subprocess

from evalenv import REPO, force_rmtree
from fixture import ENV

BUILDERS = ["s1_logslice", "s2_fetchkit", "s3_air", "s4_shopfloor", "s5_saoluu", "s6_grepl",
            "s7_tasklog", "s9_cnc", "s10_acme", "s11_csvdelta", "s12_slugkit", "s13_plantware",
            "s14_hookshelf", "s15_wattlog", "s16_linegate"]

# Paths that must not exist anywhere in the s8 clone's history: the eval suite
# (rubric, fact sheets, results) and the skill under test.
S8_FORBIDDEN = ("evals", "skills/readme-md")


def _git(cwd, *args: str) -> str:
    """Run git in cwd; on failure exit with the command and git's own message."""
    out = subprocess.run(["git", "-C", str(cwd), *args], env=ENV, capture_output=True, text=True)
    if out.returncode:
        raise SystemExit(f"s8: git {' '.join(args)} failed in {cwd}: {out.stderr.strip()}")
    return out.stdout


def build_s8(base, ref: str) -> str:
    """Clone this repository at `ref`, keeping only refs/heads/main and its history."""
    dest = base / "s8-lisa-skills"
    sha = subprocess.run(["git", "-C", str(REPO), "rev-parse", "--verify", "--quiet", f"{ref}^{{commit}}"],
                         env=ENV, capture_output=True, text=True).stdout.strip()
    if not sha:
        raise SystemExit(f"s8: {ref!r} is not a commit in {REPO}; in a shallow clone, run git fetch --unshallow")
    if _git(REPO, "log", "-1", "--full-history", "--format=%h", sha, "--", *S8_FORBIDDEN).strip():
        raise SystemExit(f"s8: {ref} or its history contains {' or '.join(S8_FORBIDDEN)}; "
                         "pick a commit that predates the eval harness (before 314060f)")
    try:
        subprocess.run(["git", "clone", "-q", "--no-hardlinks", "--no-checkout", str(REPO), str(dest)],
                       env=ENV, check=True, capture_output=True, text=True)
        _git(dest, "checkout", "-q", "-B", "main", sha)
        _git(dest, "remote", "remove", "origin")
        # The clone also holds the source's checked-out branch and its tags.
        for name in _git(dest, "for-each-ref", "--format=%(refname)").split():
            if name != "refs/heads/main":
                _git(dest, "update-ref", "--no-deref", "-d", name)
        _git(dest, "remote", "add", "origin", "https://github.com/LisaHQ/lisa-skills.git")
        _git(dest, "reflog", "expire", "--expire=now", "--all")
        _git(dest, "gc", "-q", "--prune=now")
        refs = _git(dest, "for-each-ref", "--format=%(refname)").split()
        if refs != ["refs/heads/main"] or _git(dest, "rev-parse", "HEAD").strip() != sha:
            raise SystemExit(f"s8: unexpected refs after the clone: {refs}")
        if _git(dest, "rev-list", "--all", "--count") != _git(dest, "rev-list", "main", "--count"):
            raise SystemExit("s8: the clone holds commits outside main")
        unreachable = [line for line in _git(dest, "fsck", "--unreachable", "--no-dangling", "--no-reflogs",
                                             "--no-progress").splitlines() if line.startswith("unreachable")]
        if unreachable:
            raise SystemExit(f"s8: the clone keeps {len(unreachable)} unreachable objects")
    except subprocess.CalledProcessError as exc:
        force_rmtree(dest)
        raise SystemExit(f"s8: git clone failed: {exc.stderr.strip()}") from None
    except BaseException:
        force_rmtree(dest)
        raise
    return f"s8-lisa-skills at {sha[:7]}"


def build_all(base, ref):
    # s8 first, so a refused ref fails before anything is built; any failure removes every
    # scenario, so prep_runs.py never prepares a round with a scenario missing.
    try:
        built = [build_s8(base, ref)]
        for name in BUILDERS:
            module = importlib.import_module(name)
            module.build(base)
            built.append(module.ROOT)
    except BaseException:
        for child in base.iterdir():
            force_rmtree(child)
        raise
    return built
