"""Fast mechanical checks on run outputs: cheap regression signals, not a substitute for judges.

Usage: python checks.py <suite> <iter> [--only <scenario>,...] [--json <file>] [<arm> ...]

Runs the suite's suite_checks.CHECKS functions, one per scenario, on every
run of an iteration and prints pass/fail per check (`-` marks a check that
does not apply, such as a format check when there is no message), then a
summary per arm. A run whose session failed or stopped early is marked with
its status. Works on full run folders and on the slim layout that
export_archive.py writes, with the same results. --json writes
{scenario: {arm: {"status": ..., "checks": {name: true|false|null}}}}.
"""
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

from evalenv import (diff_tree, folder_of, load_suite, parse_only, positional, read_json, run_status,
                     split_flag, tree_digest, vcs_state)


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig", errors="replace").replace("\r\n", "\n") if path.exists() else ""


class RunContext:
    """What a check may inspect about one run."""

    def __init__(self, suite, scenario: str, arm_dir: Path):
        self.suite = suite
        self.scenario = scenario
        self.arm_dir = arm_dir
        self.pristine = suite.work / "scenarios" / scenario
        full = arm_dir / folder_of(scenario)
        self.full = full if full.exists() else None
        self.notes = _read(arm_dir / "notes.md")
        self.meta = read_json(arm_dir / "meta.json")
        self.status = run_status(self.meta)
        # Bash commands the writer ran (recorded since harness v2; empty for older runs).
        self.commands: list[str] = self.meta.get("commands") or []
        self._changes = None

    def file(self, rel: str) -> str:
        """The file as the run left it ('' if the run deleted it)."""
        if self.full:
            return _read(self.full / rel)
        slim = self.arm_dir / "files" / rel
        if slim.exists():
            return _read(slim)
        return "" if rel in self.changes()[2] else self.original(rel)

    def original(self, rel: str) -> str:
        return _read(self.pristine / rel)

    def changes(self) -> tuple[list[str], list[str], list[str]]:
        """Working files the run added, modified, and deleted."""
        if self._changes is None:
            if self.full:
                self._changes = diff_tree(self.pristine, self.full)
            else:
                groups, current = {"added": [], "modified": [], "deleted": []}, None
                for line in _read(self.arm_dir / "changes.txt").splitlines():
                    if line.rstrip(":") in groups:
                        current = line.rstrip(":")
                    elif line.startswith("  ") and current:
                        groups[current].append(line.strip())
                    elif line and not line.startswith(" "):
                        current = None
                self._changes = (groups["added"], groups["modified"], groups["deleted"])
        return self._changes

    def vcs_unchanged(self) -> bool | None:
        """True when the version-control fingerprint matches the pristine scenario."""
        if self.full:
            before, after = vcs_state(self.pristine), vcs_state(self.full)
            if before is None and after is None:
                return None
            return before == after
        lines = [line for line in _read(self.arm_dir / "changes.txt").splitlines() if line.startswith("vcs ")]
        if not lines:
            return None
        return all(line.endswith(": unchanged") for line in lines)

    def denied(self, pattern: str) -> bool:
        """Whether the session tried a tool call matching pattern and was denied."""
        return any(re.search(pattern, d) for d in self.meta.get("denials", []))


def main() -> None:
    suite, args = load_suite(sys.argv[1:], __doc__)
    only, args = split_flag(args, "--only")
    json_out, args = split_flag(args, "--json")
    args = positional(args, __doc__, at_least=1)
    it, wanted = args[0], set(args[1:])
    runs = suite.work / "runs" / it
    if not runs.is_dir():
        raise SystemExit(f"no round {runs}")
    only = parse_only(only, [p.name for p in runs.iterdir() if p.is_dir()])
    from suite_checks import CHECKS  # from evals/<suite>
    prints = read_json(runs / "scenarios.json")
    results, totals = {}, defaultdict(lambda: [0, 0, 0, defaultdict(int)])
    layout = set()
    for scen_dir in sorted(p for p in runs.iterdir() if p.is_dir()):
        scen = scen_dir.name
        if scen not in CHECKS or (only and scen not in only):
            continue
        pristine = suite.work / "scenarios" / scen
        if prints.get(scen, {}).get("tree") and pristine.exists() and tree_digest(pristine) != prints[scen]["tree"]:
            print(f"warning: scenarios/{scen} differs from the one {it} was prepared from; results may be wrong")
        for arm_dir in sorted(p for p in scen_dir.iterdir() if p.is_dir()):
            if wanted and arm_dir.name not in wanted:
                continue
            ctx = RunContext(suite, scen, arm_dir)
            layout.add("full" if ctx.full else "slim")
            res = CHECKS[scen](ctx)
            results.setdefault(scen, {})[arm_dir.name] = {"status": ctx.status, "checks": res}
            ran = {k: v for k, v in res.items() if v is not None}
            failed = [k for k, ok in ran.items() if not ok]
            skipped = [k for k, v in res.items() if v is None]
            t = totals[arm_dir.name]
            t[0] += sum(ran.values())
            t[1] += len(ran)
            t[2] += len(skipped)
            for k in failed:
                t[3][f"{scen}:{k}"] += 1
            mark = "" if ctx.status == "ok" else f" [{ctx.status}]"
            print(f"{scen:24} {arm_dir.name:4} {sum(ran.values())}/{len(ran)} pass{mark}"
                  + (f"  failed: {', '.join(failed)}" if failed else "")
                  + (f"  -: {', '.join(skipped)}" if skipped else ""))
    print(f"\nsummary ({'/'.join(sorted(layout))} layout):")
    for arm, (passed, ran, skipped, failed) in sorted(totals.items()):
        print(f"{arm}: {passed}/{ran} pass, {skipped} not applicable"
              + (f"; failed: {', '.join(sorted(failed))}" if failed else ""))
    if json_out:
        Path(json_out).write_text(json.dumps(results, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
