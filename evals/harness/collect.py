"""Unblind one judged iteration and summarize it per scenario and per arm.

Usage: python collect.py <suite> <iter> [--tag NAME] [--judgments <name>]

Reads runs/<iter>/mapping[-<tag>].json and the verdicts in judgments/<name>/
(default <iter> or <iter>-<tag>) under <work>/<suite>. Prints each
scenario's weighted score per arm with its dimension scores and error counts
(major/minor), then per-arm means, first places, and rank points. Weights
come from the suite's suite.json.
"""
import json
import sys
from collections import defaultdict

from evalenv import load_suite, positional, split_flag


def main() -> None:
    suite, args = load_suite(sys.argv[1:], __doc__)
    tag, args = split_flag(args, "--tag")
    jname, args = split_flag(args, "--judgments")
    it = positional(args, __doc__, exactly=1)[0]
    jname = jname or (f"{it}-{tag}" if tag else it)
    mapping_path = suite.work / "runs" / it / f"mapping{'-' + tag if tag else ''}.json"
    mapping = json.loads(mapping_path.read_text(encoding="utf-8"))
    keys = list(suite.weights)
    per_arm, dims = defaultdict(list), defaultdict(lambda: defaultdict(list))
    firsts, points = defaultdict(int), defaultdict(int)
    for scen, labels in sorted(mapping.items()):
        path = suite.work / "judgments" / jname / f"{scen}.json"
        if not path.exists():
            print(f"{scen:24} (no judgment)")
            continue
        verdict = json.loads(path.read_text(encoding="utf-8"))
        parts = [f"{scen:24}"]
        for label, arm in sorted(labels.items(), key=lambda kv: kv[1]):
            scores = verdict[label]["scores"]
            w = suite.weighted(scores)
            per_arm[arm].append(w)
            for k, v in scores.items():
                dims[arm][k].append(v)
            errors = verdict[label].get("errors", [])
            major = sum(e.get("severity") == "major" for e in errors)
            minor = sum(e.get("severity") == "minor" for e in errors)
            parts.append(f"{arm}={w:.2f}[{''.join(str(scores[k]) for k in keys)}]e{major}/{minor}")
        ranking = [labels[label] for label in verdict.get("ranking", [])]
        if ranking:
            firsts[ranking[0]] += 1
            for pos, arm in enumerate(ranking):
                points[arm] += len(ranking) - 1 - pos
        parts.append("rank=" + ">".join(ranking) + f" ({verdict.get('confidence')})")
        print("  ".join(parts))
    print()
    for arm in sorted(per_arm):
        ws = per_arm[arm]
        dim = " ".join(f"{k}{sum(v) / len(v):.2f}" for k, v in sorted(dims[arm].items()))
        print(f"{arm}: mean {sum(ws) / len(ws):.2f} (n={len(ws)})  firsts={firsts[arm]}  "
              f"rank_pts={points[arm]}  {dim}")


if __name__ == "__main__":
    main()
