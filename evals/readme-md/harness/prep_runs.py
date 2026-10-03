"""Copy pristine scenarios into fresh run folders.

Usage: python prep_runs.py <iter> <arm> [<arm> ...] [--only s1-logslice,s2-fetchkit]

Creates <work>/runs/<iter>/<scenario>/<arm>/<folder> for every scenario and
arm. Run build_scenarios.py first.
"""
import shutil
import sys

from evalenv import WORK, folder_of, positional, split_flag


def main() -> None:
    only, args = split_flag(sys.argv[1:], "--only")
    positional(args, __doc__, at_least=2)
    it, arms = args[0], args[1:]
    only = set(only.split(",")) if only else None
    scenarios = sorted(p for p in (WORK / "scenarios").iterdir() if p.is_dir())
    if not scenarios:
        raise SystemExit("No scenarios; run build_scenarios.py first.")
    count = 0
    for scen in scenarios:
        if only and scen.name not in only:
            continue
        for arm in arms:
            dest = WORK / "runs" / it / scen.name / arm / folder_of(scen.name)
            if dest.exists():
                raise SystemExit(f"exists: {dest}")
            shutil.copytree(scen, dest, symlinks=True)
            count += 1
    print(f"prepared {count} run folders under {WORK / 'runs' / it}")


if __name__ == "__main__":
    main()
