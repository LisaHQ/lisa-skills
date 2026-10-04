"""Pool judged iterations by skill version and compare versions head to head.

Usage: python aggregate.py <suite> <judgments-name>:<arm>=<version>[,<arm>=<version>...] [...]
                           [--mapping <judgments-name>=<mapping-file>] [--pair <version>,<version>]
                           [--common] [--drop <dims>]

Example (two rounds that both ran the committed skill and a candidate):
  python aggregate.py commit-message r1:A=none,B=base,C=cand r2:A=none,B=base,C=cand

Each <judgments-name> reads <work>/<suite>/judgments/<name>/ and the mapping of
the blind set it judged (resolved from blind/<name>.json, judgments/<name>/
_set.json, or the name itself; --mapping overrides).

The per-version table (mean, standard error, error counts) is descriptive:
it pools scenarios of different difficulty. Decide from the paired section,
which compares two versions only where the same judge scored both in the same
scenario: a 95% interval that excludes 0 is evidence of a difference;
otherwise the result is inconclusive. One round of about 10 scenarios measures
a paired difference to roughly +/-0.35, two rounds to +/-0.22 (measured on
readme-md). --pair limits the paired section to the named versions; --common
keeps only scenarios that every listed set judged; --drop E also compares
without those rubric keys. Invalid or missing verdicts are skipped and listed.
"""
import json
import sys
from collections import defaultdict
from collections.abc import Callable

import stats
from evalenv import (load_suite, mapping_path, pop_switch, positional, read_json, set_info, split_flag, split_multi,
                     verdict_problems)


def paired_diffs(rows, a: str, b: str, score: Callable[[dict], float]) -> list[float]:
    """Per judged scenario: mean score of version b minus mean score of version a."""
    def mean_of(entries, version):
        values = [score(entry["scores"]) for v, entry in entries if v == version]
        return sum(values) / len(values)
    return [mean_of(entries, b) - mean_of(entries, a) for _, entries in rows]


def main() -> None:
    suite, args = load_suite(sys.argv[1:], __doc__)
    overrides_raw, args = split_multi(args, "--mapping")
    pairs_raw, args = split_multi(args, "--pair")
    drop, args = split_flag(args, "--drop", "")
    common, args = pop_switch(args, "--common")
    positional(args, __doc__, at_least=1)
    drop = tuple(d.strip() for d in drop.split(",") if d.strip())
    if any(d not in suite.weights for d in drop):
        raise SystemExit(f"--drop: unknown rubric keys; known: {', '.join(suite.weights)}")
    overrides = {}
    for item in overrides_raw:
        name, sep, path = item.partition("=")
        if not sep:
            raise SystemExit("--mapping needs <judgments-name>=<mapping-file>")
        overrides[name] = path
    specs = []
    for spec in args:
        name, sep, arms = spec.partition(":")
        if not sep or not arms:
            raise SystemExit(f"bad spec {spec!r}\n\n{__doc__}")
        try:
            versions = dict(pair.split("=", 1) for pair in arms.split(","))
        except ValueError:
            raise SystemExit(f"bad arm list in {spec!r}: use A=version,B=version")
        specs.append((name, versions))
    names = [n for n, _ in specs]
    if len(set(names)) != len(names):
        raise SystemExit("a judgments set is listed twice; that would double-count it")

    scores, dims, errors = defaultdict(list), defaultdict(lambda: defaultdict(list)), defaultdict(lambda: [0, 0, 0])
    by_dim = defaultdict(lambda: defaultdict(int))
    writer_setup = defaultdict(lambda: defaultdict(set))
    cells: dict[tuple[str, str], list[tuple[str, dict]]] = {}
    skipped, provenance = [], defaultdict(set)
    for name, versions in specs:
        mapping = json.loads(open(overrides[name], encoding="utf-8").read()) if name in overrides \
            else json.loads(mapping_path(suite, name).read_text(encoding="utf-8"))
        known_arms = {arm for labels in mapping.values() for arm in labels.values()}
        try:
            it = set_info(suite, name)["iter"]
        except SystemExit:
            it = None
        unknown = sorted(set(versions) - known_arms)
        if unknown:
            raise SystemExit(f"{name}: arms {', '.join(unknown)} are not in its mapping "
                             f"({', '.join(sorted(known_arms))})")
        for scen, labels in sorted(mapping.items()):
            path = suite.work / "judgments" / name / f"{scen}.json"
            if not path.exists():
                skipped.append(f"{name}/{scen}: no judgment")
                continue
            verdict = read_json(path)
            wanted = [label for label, arm in labels.items() if arm in versions]
            problems = verdict_problems(verdict, wanted, suite.weights, ranking=False)
            if problems:
                skipped.append(f"{name}/{scen}: invalid ({'; '.join(problems[:2])})")
                continue
            meta = read_json(path.with_name(f"{scen}.meta.json"))
            prov = meta.get("provenance") or {}
            for key in ("rubric", "judge_prompt", "session"):
                provenance[key].add(prov.get(key) or "unrecorded")
            provenance[f"facts of {scen}"].add(prov.get("facts") or "unrecorded")
            provenance["judge models"].add(",".join(meta.get("models") or []) or "unrecorded")
            provenance["judge harness"].add(str(meta.get("harness") or "unrecorded"))
            for arm in labels.values():
                if arm in versions and it:
                    wmeta = read_json(suite.work / "runs" / it / scen / arm / "meta.json")
                    for key in ("skill_sha256", "models", "effort", "max_turns", "harness", "note"):
                        writer_setup[versions[arm]][key].add(json.dumps(wmeta.get(key)))
            cells[(name, scen)] = [(versions[arm], verdict[label]) for label, arm in sorted(labels.items())
                                   if arm in versions]
    if common:
        scen_sets = [{s for (n, s) in cells if n == name} for name in names]
        keep = set.intersection(*scen_sets) if scen_sets else set()
        dropped_cells = sorted(f"{n}/{s}" for (n, s) in cells if s not in keep)
        cells = {k: v for k, v in cells.items() if k[1] in keep}
        if dropped_cells:
            print(f"--common: left out {len(dropped_cells)} judged outcomes not present in every set")
    for (name, scen), entries in cells.items():
        for version, entry in entries:
            s = entry["scores"]
            scores[version].append(suite.weighted(s))
            for k in suite.weights:
                dims[version][k].append(s[k])
            for e in entry.get("errors", []):
                errors[version][{"major": 0, "minor": 1}.get(e.get("severity"), 2)] += 1
                by_dim[version][f"{e.get('dimension') or 'untagged'}:{e.get('severity')}"] += 1

    print(f"{'version':10} {'n':>3} {'mean':>5} {'se':>5} {'major':>5} {'minor/run':>9}  dimensions"
          "   (errors counted over all dimensions)")
    for version in sorted(scores):
        xs = scores[version]
        n, mean = len(xs), sum(xs) / len(xs)
        se = (sum((x - mean) ** 2 for x in xs) / (n - 1)) ** 0.5 / n ** 0.5 if n > 1 else float("nan")
        dim = " ".join(f"{k}{sum(v) / len(v):.2f}" for k, v in dims[version].items())
        print(f"{version:10} {n:>3} {mean:>5.2f} {se:>5.2f} {errors[version][0]:>5} "
              f"{errors[version][1] / n:>9.2f}  {dim}")

    # Versions in order of first appearance, so the default pairs read 'cand - base'.
    versions = list(dict.fromkeys(v for _, spec in specs for v in spec.values() if v in scores))
    wanted_pairs = [tuple(p.split(",", 1)) for p in pairs_raw] or \
        [(a, b) for i, a in enumerate(versions) for b in versions[i + 1:]]
    unknown = sorted({v for pair in wanted_pairs for v in pair} - set(scores))
    if unknown or any(len(pair) != 2 for pair in wanted_pairs):
        raise SystemExit(f"--pair needs two of: {', '.join(versions)}")
    print("\npaired differences (later minus earlier version; same judge, same scenario):")
    for a, b in wanted_pairs:
        rows = [(s, entries) for (_, s), entries in sorted(cells.items()) if {a, b} <= {v for v, _ in entries}]
        clusters = [s for s, _ in rows]
        print(stats.paired_line(f"{b} - {a}", paired_diffs(rows, a, b, suite.weighted), clusters))
        if drop and rows:
            print("  " + stats.paired_line(f"without {'+'.join(drop)}",
                                           paired_diffs(rows, a, b, lambda sc: suite.weighted(sc, drop)), clusters))
        if rows:
            per_dim = " ".join(f"{k}{sum(paired_diffs(rows, a, b, lambda sc, k=k: sc[k])) / len(rows):+.2f}"
                               for k in suite.weights)
            print(f"  per dimension: {per_dim}")
    if any(k.split(":")[0] != "untagged" for v in by_dim.values() for k in v):
        print("\nerrors by dimension:")
        for version in sorted(by_dim):
            print(f"  {version}: " + " ".join(f"{k}={n}" for k, n in sorted(by_dim[version].items())))
    for key, values in provenance.items():
        if len(values) > 1:
            print(f"warning: pooled verdicts differ in {key}: {', '.join(sorted(v[:12] for v in values))}")
    for version, setup in sorted(writer_setup.items()):
        for key, values in setup.items():
            if len(values) > 1:
                print(f"warning: version {version} pools writers with different {key}: {', '.join(sorted(values))}")
    if skipped:
        print(f"\nskipped {len(skipped)} scenario verdicts:\n  " + "\n  ".join(skipped))


if __name__ == "__main__":
    main()
