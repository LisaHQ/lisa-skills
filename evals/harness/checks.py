"""Fast mechanical checks on run outputs: cheap regression signals, not a substitute for judges.

Usage: python checks.py <suite> <iter> [--only <scenario>,...] [<arm> ...]

Runs the suite's suite_checks.CHECKS functions, one per scenario, on every
run of an iteration and prints pass/fail per check (`-` marks a check that
needs data the run does not have, such as a slim archived run). Works on full
run folders and on the slim layout that export_archive.py writes.
"""
import json
import re
import sys
from pathlib import Path

from evalenv import diff_tree, folder_of, load_suite, positional, split_flag, vcs_state


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace").replace("\r\n", "\n") if path.exists() else ""


class RunContext:
    """What a check may inspect about one run."""

    def __init__(self, suite, scenario: str, arm_dir: Path):
        self.scenario = scenario
        self.arm_dir = arm_dir
        self.pristine = suite.work / "scenarios" / scenario
        full = arm_dir / folder_of(scenario)
        self.full = full if full.exists() else None
        self.notes = _read(arm_dir / "notes.md")
        meta = arm_dir / "meta.json"
        self.meta = json.loads(meta.read_text(encoding="utf-8")) if meta.exists() else {}

    def file(self, rel: str) -> str:
        """The file as the run left it (falls back to the pristine copy)."""
        if self.full:
            return _read(self.full / rel)
        slim = self.arm_dir / "files" / rel
        return _read(slim) if slim.exists() else self.original(rel)

    def original(self, rel: str) -> str:
        return _read(self.pristine / rel)

    def changes(self) -> tuple[list[str], list[str], list[str]]:
        """Working files the run added, modified, and deleted."""
        if self.full:
            return diff_tree(self.pristine, self.full)
        groups, current = {"added": [], "modified": [], "deleted": []}, None
        for line in _read(self.arm_dir / "changes.txt").splitlines():
            if line.rstrip(":") in groups:
                current = line.rstrip(":")
            elif line.startswith("  ") and current:
                groups[current].append(line.strip())
        return groups["added"], groups["modified"], groups["deleted"]

    def vcs_unchanged(self) -> bool | None:
        """True when HEAD, index, and stash (or SVN schedule) match the pristine scenario."""
        if not self.full:
            return None
        before, after = vcs_state(self.pristine), vcs_state(self.full)
        return None if before is None else before == after

    def denied(self, pattern: str) -> bool:
        """Whether the session tried a tool call matching pattern and was denied."""
        return any(re.search(pattern, d) for d in self.meta.get("denials", []))


def main() -> None:
    suite, args = load_suite(sys.argv[1:], __doc__)
    only, args = split_flag(args, "--only")
    args = positional(args, __doc__, at_least=1)
    it, wanted = args[0], set(args[1:])
    only = set(only.split(",")) if only else None
    from suite_checks import CHECKS  # from evals/<suite>
    for scen_dir in sorted(p for p in (suite.work / "runs" / it).iterdir() if p.is_dir()):
        scen = scen_dir.name
        if scen not in CHECKS or (only and scen not in only):
            continue
        for arm_dir in sorted(p for p in scen_dir.iterdir() if p.is_dir()):
            if wanted and arm_dir.name not in wanted:
                continue
            results = CHECKS[scen](RunContext(suite, scen, arm_dir))
            ran = {k: v for k, v in results.items() if v is not None}
            failed = [k for k, ok in ran.items() if not ok]
            skipped = [k for k, v in results.items() if v is None]
            print(f"{scen:24} {arm_dir.name:4} {sum(ran.values())}/{len(ran)} pass"
                  + (f"  failed: {', '.join(failed)}" if failed else "")
                  + (f"  -: {', '.join(skipped)}" if skipped else ""))


if __name__ == "__main__":
    main()
