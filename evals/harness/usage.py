"""Report token use and cost per round and in total, from recorded sessions.

Usage: python usage.py <suite> [<iter> ...] [--by-scenario] [--markdown]
       python usage.py <suite> --estimate
       python usage.py --all [--markdown]

Every writer, judge, and trigger session since harness v2 leaves a record in
<work>/<suite>/usage/ (retries and failed attempts included). Older rounds
fall back to the cost stored in each writer's meta.json; their token counts
and judge costs were not recorded and show as '?' or 'unrecorded'.

Columns: sessions, failed (API or usage-limit error, timeout, no result; a
session that stopped at its turn limit is not a failure), turns, input, cache-write,
cache-read, and output tokens, cost in USD, and session minutes (summed, not
elapsed). '*' marks a total that misses some sessions' values. Costs are what
Claude Code computes at API list prices: an API-key user is billed about that
amount, while a subscription (Pro, Max, Team) counts the usage against the
plan's limits instead. The plan line shows the last reported use of the
five-hour and weekly windows, which other activity on the account shares.

--estimate prints the median and 90th-percentile cost per session by role and
model, to quote before approving a round. --all reports every suite.
"""
from __future__ import annotations

import statistics
import sys
from collections import defaultdict

from evalenv import (INFRA_FAILURES, Suite, guard_work_root, load_suite, pop_switch, positional, read_json,
                     run_status, set_info, suites)

TOKENS = ("input", "cache_write", "cache_read", "output")
HEADER = ("round", "role", "group", "sessions", "failed", "turns", "input", "cache-w", "cache-r", "output",
          "cost $", "minutes")
LABEL = ("Costs are API list-price equivalents: billed at about this amount with an API key; "
         "counted against plan limits on a subscription.")


class Tally:
    """Totals for a group of sessions; a total missing some sessions' values is marked '*'."""

    def __init__(self):
        self.runs = self.failed = self.turns = self.no_tokens = self.no_cost = 0
        self.tokens = dict.fromkeys(TOKENS, 0)
        self.cost = 0.0
        self.seconds = 0.0
        self.models: set[str] = set()
        self.aliases: set[str] = set()

    def add(self, rec: dict) -> None:
        self.runs += 1
        self.failed += run_status(rec) in INFRA_FAILURES
        self.turns += rec.get("num_turns") or 0
        self.seconds += rec.get("wall_s") or (rec.get("duration_ms") or 0) / 1000
        usage = rec.get("usage")
        if usage and not usage.get("partial"):
            for k in TOKENS:
                self.tokens[k] += usage.get(k) or 0
            self.models.update(m for m in usage.get("by_model") or {} if m != "unknown")
        else:
            self.no_tokens += 1
            if rec.get("model"):
                self.aliases.add(rec["model"])
        cost = rec.get("total_cost_usd")
        if cost is None:
            self.no_cost += 1
        else:
            self.cost += cost

    def unrecorded(self, n: int) -> None:
        self.runs += n
        self.no_tokens += n
        self.no_cost += n

    def merge(self, other: "Tally") -> None:
        for name in ("runs", "failed", "turns", "no_tokens", "no_cost", "cost", "seconds"):
            setattr(self, name, getattr(self, name) + getattr(other, name))
        for k in TOKENS:
            self.tokens[k] += other.tokens[k]
        self.models |= other.models
        self.aliases |= other.aliases


def human(n: float) -> str:
    return f"{n / 1e6:.2f}M" if n >= 1e6 else f"{n / 1e3:.1f}k" if n >= 1e3 else str(int(n))


def row(round_name: str, role: str, group: str, t: Tally) -> tuple:
    known = t.runs - t.no_tokens
    tokens = [(human(t.tokens[k]) + ("*" if t.no_tokens else "")) if known else "?" for k in TOKENS]
    cost = (f"{t.cost:.2f}" + ("*" if t.no_cost else "")) if t.runs > t.no_cost else "?"
    return (round_name, role, group, t.runs, t.failed, t.turns, *tokens, cost, f"{t.seconds / 60:.1f}")


def ledger(suite: Suite) -> list[dict]:
    folder = suite.work / "usage"
    return [r for r in (read_json(p) for p in sorted(folder.glob("*.json"))) if r] if folder.is_dir() else []


def rounds_of(suite: Suite) -> list[str]:
    runs = suite.work / "runs"
    names = {p.name for p in runs.iterdir() if p.is_dir()} if runs.exists() else set()
    names |= {r["round"] for r in ledger(suite) if r.get("round") and r.get("kind") != "trigger"}
    return sorted(names)


def round_groups(suite: Suite, it: str, records: list[dict], by_scenario: bool = False) -> dict:
    """{(role, group): Tally} for one round: ledger records, else legacy metas."""
    groups: dict[tuple[str, str], Tally] = defaultdict(Tally)
    mine = [r for r in records if r.get("round") == it and r.get("kind") in ("writer", "judge")]
    for r in mine:
        group = r.get("scenario") if by_scenario else (r.get("arm") if r["kind"] == "writer" else r.get("label"))
        groups[(r["kind"], group or "-")].add(r)
    if not any(r["kind"] == "writer" for r in mine):
        for arm_dir in sorted((suite.work / "runs" / it).glob("*/*")):
            if not arm_dir.is_dir():
                continue
            scen, arm = arm_dir.parent.name, arm_dir.name
            if (arm_dir / "meta.json").exists():
                groups[("writer", scen if by_scenario else arm)].add(read_json(arm_dir / "meta.json"))
            elif (arm_dir / "notes.md").exists() or (arm_dir / "changes.txt").exists():
                # subagent writers of early rounds left outputs but recorded nothing
                groups[("writer", f"{scen if by_scenario else arm} (unrecorded)")].unrecorded(1)
    judged = {r.get("label") for r in mine if r["kind"] == "judge"}
    jroot = suite.work / "judgments"
    for jdir in sorted(p for p in jroot.iterdir() if p.is_dir()) if jroot.exists() else []:
        if jdir.name in judged:
            continue
        try:
            if set_info(suite, jdir.name)["iter"] != it:
                continue
        except SystemExit:
            continue
        verdicts = [p for p in jdir.glob("*.json") if p.stem.count(".") == 0 and not p.name.startswith("_")]
        if verdicts:
            mode = read_json(jdir / "_set.json").get("mode")
            groups[("judge", f"{jdir.name} ({'subagent, ' if mode == 'subagent' else ''}unrecorded)")] \
                .unrecorded(len(verdicts))
    return groups


def plan_line(records: list[dict]) -> str:
    latest = max((r for r in records if r.get("plan_window")), key=lambda r: r.get("started_at") or "", default=None)
    if not latest:
        return ""
    parts = [f"{name.replace('_', '-')} {value:.0%}" for name, value in latest["plan_window"].items()
             if isinstance(value, (int, float))]
    overage = " (usage credits were used)" if any(r.get("using_overage") for r in records) else ""
    return f"plan limits at the last session: {', '.join(parts)}{overage}" if parts else ""


def print_table(rows: list[tuple], markdown: bool) -> None:
    if markdown:
        print("| " + " | ".join(HEADER) + " |")
        print("| " + " | ".join("---" if i < 3 else "---:" for i in range(len(HEADER))) + " |")
        for r in rows:
            print("| " + " | ".join(str(v) for v in r) + " |")
        return
    widths = [max(len(str(r[i])) for r in [HEADER, *rows]) for i in range(len(HEADER))]
    for r in [HEADER, *rows]:
        print("  ".join(str(v).rjust(w) if i >= 3 else str(v).ljust(w) for i, (v, w) in enumerate(zip(r, widths))))


def report(suite: Suite, rounds: list[str], by_scenario: bool = False, markdown: bool = False,
           trigger: bool = False) -> Tally:
    records = ledger(suite)
    rows, grand = [], Tally()
    for it in rounds:
        total = Tally()
        for (role, group), t in sorted(round_groups(suite, it, records, by_scenario).items()):
            rows.append(row(it, role, group, t))
            total.merge(t)
        if total.runs:
            rows.append(row(it, "total", "", total))
            grand.merge(total)
    if trigger:
        by_label: dict[str, Tally] = defaultdict(Tally)
        for r in records:
            if r.get("kind") == "trigger":
                by_label[r.get("label") or "-"].add(r)
        for label, t in sorted(by_label.items()):
            rows.append(row("trigger", "query", label, t))
            grand.merge(t)
    print(f"{suite.name}: token use and cost by round")
    if rows:
        print_table(rows, markdown)
    print(f"{suite.name} total: ${grand.cost:.2f}{'*' if grand.no_cost else ''} over {grand.runs} sessions, "
          f"{human(sum(grand.tokens.values()))} tokens recorded"
          + (f"; {grand.no_tokens} sessions without token data" if grand.no_tokens else "")
          + (f", {grand.no_cost} without cost" if grand.no_cost else ""))
    if grand.models:
        print("models: " + ", ".join(sorted(grand.models)))
    if grand.aliases:
        print("requested aliases of sessions without per-model data: " + ", ".join(sorted(grand.aliases)))
    line = plan_line([r for r in records if r.get("round") in rounds or (trigger and r.get("kind") == "trigger")])
    if line:
        print(line)
    print(LABEL)
    return grand


def estimate(suite: Suite) -> None:
    costs: dict[tuple[str, str], list[float]] = defaultdict(list)
    for r in ledger(suite):
        if r.get("total_cost_usd") is not None:
            costs[(r.get("kind"), r.get("model") or ",".join(r.get("models") or []))].append(r["total_cost_usd"])
    if not any(k == "writer" for k, _ in costs):
        for meta_path in suite.work.glob("runs/*/*/*/meta.json"):
            meta = read_json(meta_path)
            if meta.get("total_cost_usd") is not None:
                model = meta.get("model") or f"unrecorded model, {meta_path.parents[2].name}"
                costs[("writer", model)].append(meta["total_cost_usd"])
    print(f"{suite.name}: cost per session from recorded history")
    for (kind, model), xs in sorted(costs.items()):
        xs.sort()
        p90 = xs[min(len(xs) - 1, int(0.9 * len(xs)))]
        print(f"  {kind:8} {model:24} n={len(xs):<4} median ${statistics.median(xs):.3f}  p90 ${p90:.3f}")
    if not costs:
        print("  nothing recorded yet")
    if not any(kind == "judge" for kind, _ in costs):
        print("  judges: none recorded yet; evals/README.md lists the measured ranges")
    print(LABEL)


def main() -> None:
    args = sys.argv[1:]
    markdown, args = pop_switch(args, "--markdown")
    if args == ["--all"]:
        guard_work_root()
        grand = Tally()
        for name in suites():
            suite = Suite(name)
            if suite.work.exists():
                grand.merge(report(suite, rounds_of(suite), markdown=markdown, trigger=True))
                print()
        print(f"all suites: ${grand.cost:.2f}{'*' if grand.no_cost else ''} over {grand.runs} sessions")
        return
    suite, args = load_suite(args, __doc__)
    if args == ["--estimate"]:
        estimate(suite)
        return
    by_scenario, args = pop_switch(args, "--by-scenario")
    rounds = positional(args, __doc__)
    report(suite, rounds or rounds_of(suite), by_scenario, markdown, trigger=not rounds)


if __name__ == "__main__":
    main()
