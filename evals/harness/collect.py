"""Unblind one judged iteration and summarize it per scenario and per arm.

Usage: python collect.py <suite> <iter> [--tag NAME] [--judgments <name>] [--mapping <file>] [--drop <dims>]

Reads the round's label-to-arm mapping and the verdicts in judgments/<name>/
(default <iter> or <iter>-<tag>) under <work>/<suite>. Prints each scenario's
weighted score per arm with its dimension scores and error counts
(major/minor), marking arms whose session stopped early (A*max_turns), then
per-arm means, first places, rank points, paired differences between arms,
and the round's token use and cost. Weights come from the suite's suite.json;
--drop E also reports means without those rubric keys (useful when a key
encodes the skill's own format). It also prints each arm's turns and denied
tool calls, and warns about tool calls that reached outside a writer's folder
or a judge's sandbox and about rounds with mixed writer settings. Invalid
verdicts are skipped and reported; the script exits 1 when any scenario lacks
a usable verdict. --mapping overrides the label-to-arm mapping file.
"""
import json
import sys
from collections import defaultdict

import stats
import usage
from blind import settings_warnings
from evalenv import (load_suite, mapping_path, positional, read_json, run_status, split_flag, verdict_problems,
                     verdict_warnings)


def main() -> None:
    suite, args = load_suite(sys.argv[1:], __doc__)
    tag, args = split_flag(args, "--tag")
    jname, args = split_flag(args, "--judgments")
    drop, args = split_flag(args, "--drop", "")
    mapping_file, args = split_flag(args, "--mapping")
    it = positional(args, __doc__, exactly=1)[0]
    set_name = f"{it}-{tag}" if tag else it
    jname = jname or set_name
    drop = tuple(d.strip() for d in drop.split(",") if d.strip())
    if any(d not in suite.weights for d in drop):
        raise SystemExit(f"--drop: unknown rubric keys; known: {', '.join(suite.weights)}")
    recorded = read_json(suite.work / "judgments" / jname / "_set.json").get("blind")
    tagged = suite.work / "runs" / it / f"mapping-{tag}.json" if tag else None
    if mapping_file:
        path = mapping_file
    elif recorded:  # the blind set judge.py recorded decides the mapping
        if recorded != set_name:
            raise SystemExit(f"judgments/{jname} holds verdicts of blind set {recorded}, not {set_name}; "
                             "check --tag or --judgments")
        path = mapping_path(suite, jname)
    else:  # judgments from before harness v2
        path = tagged if tagged and tagged.exists() else mapping_path(suite, jname)
    mapping = json.loads(open(path, encoding="utf-8").read())
    keys = list(suite.weights)
    per_arm, dims = defaultdict(list), defaultdict(lambda: defaultdict(list))
    dropped = defaultdict(list)
    firsts, points = defaultdict(int), defaultdict(int)
    rows: dict[str, dict[str, float]] = {}
    missing, warnings = [], []
    sessions = defaultdict(list)
    for scen, labels in sorted(mapping.items()):
        path = suite.work / "judgments" / jname / f"{scen}.json"
        if not path.exists():
            print(f"{scen:24} (no judgment)")
            missing.append(scen)
            continue
        verdict = read_json(path)
        problems = verdict_problems(verdict, list(labels), suite.weights, ranking=False)
        if problems:
            print(f"{scen:24} (invalid judgment: {'; '.join(problems[:3])})")
            missing.append(scen)
            continue
        warnings += [f"{scen}: {w}" for w in verdict_warnings(verdict, list(labels), suite)]
        reach = read_json(path.with_name(f"{scen}.meta.json")).get("reach")
        if reach:
            warnings.append(f"{scen}: the judge reached outside its sandbox: {reach[:3]}")
        parts = [f"{scen:24}"]
        rows[scen] = {}
        for label, arm in sorted(labels.items(), key=lambda kv: kv[1]):
            scores = verdict[label]["scores"]
            w = suite.weighted(scores)
            per_arm[arm].append(w)
            rows[scen][arm] = w
            if drop:
                dropped[arm].append(suite.weighted(scores, drop))
            for k in keys:
                dims[arm][k].append(scores[k])
            errors = verdict[label].get("errors", [])
            major = sum(e.get("severity") == "major" for e in errors)
            minor = sum(e.get("severity") == "minor" for e in errors)
            meta = read_json(suite.work / "runs" / it / scen / arm / "meta.json")
            status = run_status(meta)
            mark = "" if status in ("ok", "missing") else f"*{status}"
            sessions[arm].append(meta)
            if meta.get("reach"):
                warnings.append(f"{scen}/{arm}: the writer reached outside its folder: {meta['reach'][:3]}")
            parts.append(f"{arm}{mark}={w:.2f}[{''.join(str(scores[k]) for k in keys)}]e{major}/{minor}")
        order = verdict.get("ranking")
        if verdict_problems(verdict, list(labels), suite.weights, ranking=True):
            warnings.append(f"{scen}: ranking {order!r} is incomplete; left out of firsts and rank points")
        else:
            ranking = [labels[label] for label in order]
            firsts[ranking[0]] += 1
            for pos, arm in enumerate(ranking):
                points[arm] += len(ranking) - 1 - pos
            parts.append("rank=" + ">".join(ranking) + f" ({verdict.get('confidence')})")
        print("  ".join(parts))
    print()
    for arm in sorted(per_arm):
        ws = per_arm[arm]
        dim = " ".join(f"{k}{sum(v) / len(v):.2f}" for k, v in dims[arm].items())
        extra = f"  without {'+'.join(drop)}: {sum(dropped[arm]) / len(dropped[arm]):.2f}" if drop else ""
        metas = [m for m in sessions[arm] if m]
        turns = sum(m.get("num_turns") or 0 for m in metas) / max(1, len(metas))
        denied = sum(len(m.get("denials") or []) for m in metas)
        print(f"{arm}: mean {sum(ws) / len(ws):.2f} (n={len(ws)})  firsts={firsts[arm]}  "
              f"rank_pts={points[arm]}  {dim}{extra}  turns/run {turns:.1f}  denied calls {denied}")
    arms = sorted(per_arm)
    for a in arms:
        for b in arms:
            if a < b:
                diffs = [rows[s][b] - rows[s][a] for s in rows if a in rows[s] and b in rows[s]]
                print(stats.paired_line(f"{b} - {a}", diffs))
    warnings += settings_warnings(suite.work / "runs" / it, sorted(rows), arms)
    for w in warnings:
        print("warning:", w)
    judged = len(mapping) - len(missing)
    print(f"\n{judged} of {len(mapping)} scenarios judged" + (f"; missing or invalid: {', '.join(missing)}"
                                                             if missing else ""))
    print()
    usage.report(suite, [it])
    if missing:
        sys.exit(1)


if __name__ == "__main__":
    main()
