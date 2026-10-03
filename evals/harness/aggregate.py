"""Pool judged iterations by skill version to compare versions with more samples.

Usage: python aggregate.py <suite> <judgments-name>:<arm>=<version>[,<arm>=<version>...] [...]
                           [--mapping <judgments-name>=<mapping-file>]

Example (two rounds that both ran the committed skill and a candidate):
  python aggregate.py commit-message r1:A=none,B=base,C=cand r2:A=none,B=base,C=cand

Each <judgments-name> reads <work>/<suite>/judgments/<name>/ and, unless
overridden, runs/<iter>/mapping.json where <iter> is the part before any "-".
Single-run scores vary by about ±0.3, so trust differences larger than about
twice the reported standard error.
"""
import json
import sys
from collections import defaultdict

from evalenv import load_suite, positional


def main() -> None:
    suite, args = load_suite(sys.argv[1:], __doc__)
    overrides = {}
    while "--mapping" in args:
        i = args.index("--mapping")
        name, path = args[i + 1].split("=", 1)
        overrides[name] = path
        args = args[:i] + args[i + 2:]
    positional(args, __doc__, at_least=1)
    scores, dims, errors = defaultdict(list), defaultdict(lambda: defaultdict(list)), defaultdict(lambda: [0, 0])
    for spec in args:
        name, arms = spec.split(":", 1)
        versions = dict(pair.split("=", 1) for pair in arms.split(","))
        it = name.split("-", 1)[0]
        mapping_path = overrides.get(name) or suite.work / "runs" / it / "mapping.json"
        mapping = json.loads(open(mapping_path, encoding="utf-8").read())
        for scen, labels in mapping.items():
            path = suite.work / "judgments" / name / f"{scen}.json"
            if not path.exists():
                continue
            verdict = json.loads(path.read_text(encoding="utf-8"))
            for label, arm in labels.items():
                if arm not in versions or label not in verdict:
                    continue
                version = versions[arm]
                s = verdict[label]["scores"]
                scores[version].append(suite.weighted(s))
                for k in suite.weights:
                    dims[version][k].append(s[k])
                for e in verdict[label].get("errors", []):
                    errors[version][0 if e.get("severity") == "major" else 1] += 1
    print(f"{'version':10} {'n':>3} {'mean':>5} {'se':>5} {'major':>5} {'minor/run':>9}  dimensions")
    for version in sorted(scores):
        xs = scores[version]
        n, mean = len(xs), sum(xs) / len(xs)
        se = (sum((x - mean) ** 2 for x in xs) / (n - 1)) ** 0.5 / n ** 0.5 if n > 1 else float("nan")
        dim = " ".join(f"{k}{sum(v) / len(v):.2f}" for k, v in dims[version].items())
        print(f"{version:10} {n:>3} {mean:>5.2f} {se:>5.2f} {errors[version][0]:>5} "
              f"{errors[version][1] / n:>9.2f}  {dim}")


if __name__ == "__main__":
    main()
