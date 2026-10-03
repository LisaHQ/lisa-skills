"""Build a suite's scenarios into <work>/<suite>/scenarios.

Usage: python build_scenarios.py <suite> [--ref <git-ref>]

Each suite's scenarios/suite_build.py creates deterministic fixtures (fixed
seeds, identities, and commit dates), so every build produces the same files
and commits, and checks that each scenario reached its intended state.
--ref overrides the commit of this repository that cloning scenarios use
(default: the suite's repo_ref).
"""
import sys

from evalenv import force_rmtree, load_suite, positional, split_flag


def main() -> None:
    suite, args = load_suite(sys.argv[1:], __doc__)
    ref, args = split_flag(args, "--ref", suite.repo_ref)
    positional(args, __doc__, exactly=0)
    import suite_build  # from evals/<suite>/scenarios
    base = suite.work / "scenarios"
    force_rmtree(base)
    base.mkdir(parents=True)
    for name in suite_build.build_all(base, ref):
        print("built", name)
    print(f"scenarios: {base}")


if __name__ == "__main__":
    main()
