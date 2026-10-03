"""Copy pristine scenarios into fresh run folders.

Usage: python prep_runs.py <suite> <iter> <arm> [<arm> ...] [--only <scenario>,...]

Creates <work>/<suite>/runs/<iter>/<scenario>/<arm>/<folder> for every
scenario and arm, and records a fingerprint of each pristine scenario in
runs/<iter>/scenarios.json, so later steps can tell when scenarios were
rebuilt differently in between. Run build_scenarios.py first. Nothing is
copied when any destination already exists, or when arms are added to a round
whose scenarios have been rebuilt differently since.
"""
import json
import shutil
import sys

from evalenv import (check_name, file_digest, folder_of, load_suite, parse_only, positional, scenario_dirs,
                     split_flag, tree_digest)


def main() -> None:
    suite, args = load_suite(sys.argv[1:], __doc__)
    only, args = split_flag(args, "--only")
    positional(args, __doc__, at_least=2)
    it, arms = check_name("iteration", args[0]), [check_name("arm", a, dashes=True) for a in args[1:]]
    if len({a.casefold() for a in arms}) != len(arms):
        raise SystemExit("duplicate arm names (they must differ in more than letter case)")
    base = suite.work / "scenarios"
    if not base.exists() or not scenario_dirs(base):
        raise SystemExit("No scenarios; run build_scenarios.py first.")
    scenarios = [s for s in scenario_dirs(base)]
    only = parse_only(only, [s.name for s in scenarios])
    scenarios = [s for s in scenarios if not only or s.name in only]
    missing = sorted(set(suite.requests) - {s.name for s in scenario_dirs(base)})
    if missing and not only:
        raise SystemExit(f"scenarios not built: {', '.join(missing)}; rerun build_scenarios.py")
    jobs = [(scen, suite.work / "runs" / it / scen.name / arm / folder_of(scen.name))
            for scen in scenarios for arm in arms]
    existing = [str(dest) for _, dest in jobs if dest.exists()]
    if existing:
        raise SystemExit("already prepared (delete them or use another iteration name):\n  " + "\n  ".join(existing))
    prints_file = suite.work / "runs" / it / "scenarios.json"
    prints = json.loads(prints_file.read_text(encoding="utf-8")) if prints_file.exists() else {}
    trees = {scen.name: tree_digest(scen) for scen in scenarios}
    changed = [name for name, tree in trees.items() if name in prints and prints[name]["tree"] != tree]
    if changed:
        raise SystemExit(f"round {it} was prepared from a different build of: {', '.join(changed)}; "
                         "rebuild those scenarios as they were, or start a new round")
    for scen, dest in jobs:
        shutil.copytree(scen, dest, symlinks=True)
    for scen in scenarios:
        prints.setdefault(scen.name, {"tree": trees[scen.name], "request": suite.requests.get(scen.name),
                                      "facts": file_digest(suite.dir / "facts" / f"{scen.name}.md")})
    prints.setdefault("_suite", {"rubric": file_digest(suite.dir / "rubric.md"),
                                 "checks": file_digest(suite.dir / "suite_checks.py")})
    prints_file.write_text(json.dumps(prints, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"prepared {len(jobs)} run folders under {suite.work / 'runs' / it}")


if __name__ == "__main__":
    main()
