"""Build a suite's scenarios into <work>/<suite>/scenarios.

Usage: python build_scenarios.py <suite> [--ref <git-ref>] [--force]

Each suite's scenarios/suite_build.py creates deterministic fixtures (fixed
seeds, identities, and commit dates, with the machine's git config ignored),
so every build produces the same files and commits, and checks that each
scenario reached its intended state. --ref overrides the commit of this
repository that cloning scenarios use (default: the suite's repo_ref).
The new build goes to scenarios.new/ first and replaces scenarios/ only when
no scenario differs from the build an earlier round was prepared from
(runs/<iter>/scenarios.json), because blind.py, judge.py, and checks.py
compare runs against the current build; --force replaces it anyway. Builders
keep external repositories (SVN) in <work>/<suite>/svn-repos, which run
copies point at; a refused build restores them as they were.
"""
import shutil
import sys

from evalenv import force_rmtree, load_suite, pop_switch, positional, read_json, split_flag, tree_digest


def stdlib_shadows(base) -> list[str]:
    """Top-level names under each scenario's src/ that a session's PYTHONPATH would put ahead of the stdlib."""
    return sorted(f"{src.parent.name}/src/{entry.name}" for src in base.glob("*/src") for entry in src.iterdir()
                  if (entry.stem if entry.suffix == ".py" else entry.name) in sys.stdlib_module_names)


def main() -> None:
    suite, args = load_suite(sys.argv[1:], __doc__)
    ref, args = split_flag(args, "--ref", suite.repo_ref)
    force, args = pop_switch(args, "--force")
    positional(args, __doc__, exactly=0)
    import suite_build  # from evals/<suite>/scenarios
    base, staging = suite.work / "scenarios", suite.work / "scenarios.new"
    repos, backup = suite.work / "svn-repos", suite.work / "svn-repos.bak"
    force_rmtree(staging)
    force_rmtree(backup)
    if repos.exists():
        shutil.copytree(repos, backup)
    staging.mkdir(parents=True)
    try:
        for name in suite_build.build_all(staging, ref):
            print("built", name)
        shadows = stdlib_shadows(staging)
        if shadows:  # sessions put src/ ahead of the standard library (evalenv.SESSION_ENV)
            raise SystemExit(f"scenario src/ entries shadow standard-library modules: {', '.join(shadows)}")
        conflicts = []
        for prints in sorted((suite.work / "runs").glob("*/scenarios.json")):
            changed = [scen for scen, info in read_json(prints).items()
                       if not scen.startswith("_") and (staging / scen).exists()
                       and tree_digest(staging / scen) != info["tree"]]
            if changed:
                conflicts.append(f"round {prints.parent.name}: {', '.join(changed)}")
        if conflicts and not force:
            lines = "\n  ".join(conflicts)
            raise SystemExit(f"the new build differs from the one these rounds were prepared from:\n  {lines}\n"
                             "scenarios/ is unchanged; finish or archive those rounds, or rebuild with --force")
    except BaseException:
        force_rmtree(staging)
        if backup.exists():  # put back the repositories that existing run copies point at
            force_rmtree(repos)
            backup.rename(repos)
        raise
    for line in conflicts:
        print(f"warning: replaced the build that {line} was prepared from")
    force_rmtree(backup)
    force_rmtree(base)
    staging.rename(base)
    print(f"scenarios: {base}")


if __name__ == "__main__":
    main()
