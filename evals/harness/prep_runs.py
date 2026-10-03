"""Copy pristine scenarios into fresh run folders.

Usage: python prep_runs.py <suite> <iter> <arm> [<arm> ...] [--only <scenario>,...]

Creates <work>/<suite>/runs/<iter>/<scenario>/<arm>/<folder> for every
scenario and arm. Run build_scenarios.py first.
"""
import shutil
import sys

from evalenv import folder_of, load_suite, positional, scenario_dirs, split_flag


def main() -> None:
    suite, args = load_suite(sys.argv[1:], __doc__)
    only, args = split_flag(args, "--only")
    positional(args, __doc__, at_least=2)
    it, arms = args[0], args[1:]
    only = set(only.split(",")) if only else None
    base = suite.work / "scenarios"
    if not base.exists() or not scenario_dirs(base):
        raise SystemExit("No scenarios; run build_scenarios.py first.")
    count = 0
    for scen in scenario_dirs(base):
        if only and scen.name not in only:
            continue
        for arm in arms:
            dest = suite.work / "runs" / it / scen.name / arm / folder_of(scen.name)
            if dest.exists():
                raise SystemExit(f"exists: {dest}")
            shutil.copytree(scen, dest, symlinks=True)
            count += 1
    print(f"prepared {count} run folders under {suite.work / 'runs' / it}")


if __name__ == "__main__":
    main()
