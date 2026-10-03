"""Selection-report length and exclusion recall for commit-message rounds; spends no model usage.

Usage (from evals/harness/):
  python ../commit-message/report_metrics.py <iter>[:<arm>=<version>,...] [...] [--pair <version>,<version>]

The report is the writer's final message without the commit-message block.
Per version (an arm letter when a round has no mapping), it prints the mean
and median report words and sentences, how many outcomes state test status,
the mean number of distinct file names, the outcomes whose message has a main
bullet of four or more lines, and the recall of the exclusions that each fact
sheet's report core point requires. It also counts outcomes without a message
(their whole notes count as the report) and runs skipped for infrastructure
failures. --pair X,Y prints the paired difference Y - X in report words over
outcomes of the same round and scenario. The patterns are heuristic: compare
versions within one version of this script, and read judged scores first.
"""
import re
import statistics
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "harness"))
import stats  # noqa: E402
from evalenv import INFRA_FAILURES, load_suite, read_json, run_status, split_flag  # noqa: E402

LABEL = re.compile(r"^\s*\**Commit description:\**\s*$", re.M)
SENTENCE = re.compile(r"(?<=[.!?])\s+|\n\s*\n|\n(?=\s*[-*] )")
TEST_STATUS = re.compile(r"\btests?\b[^.\n]*\b(?:run|ran|pass)|\b(?:run|ran)\b[^.\n]*\btests?\b|untested"
                         r"|chạy (?:test|kiểm thử)", re.I)
FILE_NAME = re.compile(r"[\w.-]+\.(?:py|js|ts|md|toml|ya?ml|json|csv|sh|txt|ini|http|log|typed|cfg|tmp)\b")
# A selected file's own left-out edits: "<path>'s unstaged edits", "<path> also
# has unstaged edits", or "unstaged edits ... <path>".
_CLAUSE = r"(?:(?![.;]\s)[^\n])"
_EDITS = r"(?:(?:unstaged|further|extra|later) (?:edit|change)s?|on top)"


def _own_edits(path: str) -> str:
    return rf"{path}[^,;\n]{{0,30}}?(?:{_EDITS}|unstaged)|{_EDITS}{_CLAUSE}{{0,80}}?{path}"


# The exclusions each facts/<scenario>.md report core point requires; ignored
# files are neutral there and left out. Update this table with the fact sheets.
EXCLUDED = {
    "c2-notes-api": [r"store\.js", r"scratch\.http",
                     r"findNote|removeNote|(?-i:DELETE)|store\.remove|" + _own_edits(r"notes\.js")],
    "c3-csvtool": [r"defaults\.ya?ml", r"old-guide"],
    "c8-invoices": [r"models\.py|uncommitted|\bdebug|working[- ]tree (?:change|edit)|local (?:change|edit)"],
    "c11-meter": [r"ATTEMPTS = 5|\b(?:5|five) attempts|\bdebug\b|" + _own_edits(r"serial_read")],
    "c12-labelgen": [r"cli\.py", r"width|độ rộng"],
    "c13-shopapp": [r"outside|session\.py|README|test_invoice|boundary"],
    "c14-pressline": [r"press-codes", r"csvout"],
}
USAGE = __doc__


def parse_spec(spec: str) -> tuple[str, dict[str, str]]:
    it, _, arms = spec.partition(":")
    mapping = {}
    for part in filter(None, arms.split(",")):
        arm, eq, version = part.partition("=")
        if not eq or not arm or not version:
            raise SystemExit(f"bad round spec {spec!r}\n{USAGE}")
        mapping[arm] = version
    return it, mapping


def measure(scenario: str, notes: str) -> dict:
    import suite_checks as sc  # importable once the suite is loaded
    found = sc.message(notes, any_label=True)
    report = LABEL.sub("", found.report).strip()
    sentences = [s for s in SENTENCE.split(report) if s and re.search(r"\w", s)]
    groups = sc.bullets(found.lines) if found.lines else []
    wanted = EXCLUDED.get(scenario, [])
    return {
        "words": len(report.split()),
        "sentences": len(sentences),
        "tests": any(TEST_STATUS.search(s) for s in sentences),
        "names": len({Path(n).name.lower() for n in FILE_NAME.findall(report)}),
        "long_bullet": any(len(g) >= 4 for g in groups),
        "no_message": found.lines is None,
        "excluded": (sum(bool(re.search(p, report, re.I)) for p in wanted), len(wanted)),
    }


def main() -> None:
    suite, args = load_suite(["commit-message", *sys.argv[1:]], USAGE)
    pair, args = split_flag(args, "--pair")
    if not args:
        raise SystemExit(USAGE)
    rows = defaultdict(list)          # version -> measures
    by_key = defaultdict(dict)        # (round, scenario) -> {version: words}
    skipped = defaultdict(int)
    for spec in args:
        it, mapping = parse_spec(spec)
        base = suite.work / "runs" / it
        if not base.is_dir():
            raise SystemExit(f"no runs for round {it!r} under {base}")
        for scen_dir in sorted(p for p in base.iterdir() if p.is_dir()):
            for arm_dir in sorted(p for p in scen_dir.iterdir() if p.is_dir()):
                version = mapping.get(arm_dir.name, arm_dir.name if not mapping else None)
                if version is None:
                    continue
                notes = arm_dir / "notes.md"
                if run_status(read_json(arm_dir / "meta.json")) in INFRA_FAILURES or not notes.exists():
                    skipped[version] += 1
                    continue
                m = measure(scen_dir.name, notes.read_text(encoding="utf-8-sig").replace("\r\n", "\n"))
                rows[version].append(m)
                by_key[(it, scen_dir.name)][version] = m["words"]
    if not rows:
        raise SystemExit("no outcomes found")
    print(f"{'version':<10} {'n':>3} {'words':>6} {'median':>6} {'sent.':>5} {'tests':>5} {'names':>5} "
          f"{'long':>4} {'no msg':>6} {'excluded':>9} {'skipped':>7}")
    for version, ms in sorted(rows.items()):
        got = sum(m["excluded"][0] for m in ms)
        need = sum(m["excluded"][1] for m in ms)
        print(f"{version:<10} {len(ms):>3} {statistics.fmean(m['words'] for m in ms):>6.1f} "
              f"{statistics.median(m['words'] for m in ms):>6.0f} {statistics.fmean(m['sentences'] for m in ms):>5.2f} "
              f"{sum(m['tests'] for m in ms):>5} {statistics.fmean(m['names'] for m in ms):>5.2f} "
              f"{sum(m['long_bullet'] for m in ms):>4} {sum(m['no_message'] for m in ms):>6} "
              f"{got:>4}/{need:<4} {skipped[version]:>7}")
    if pair:
        x, _, y = pair.partition(",")
        if x not in rows or y not in rows:
            raise SystemExit(f"--pair: unknown version; known: {', '.join(sorted(rows))}")
        keys = [k for k, v in sorted(by_key.items()) if x in v and y in v]
        diffs = [by_key[k][y] - by_key[k][x] for k in keys]
        print(stats.paired_line(f"report words {y} - {x}", diffs, [k[1] for k in keys]))


if __name__ == "__main__":
    main()
