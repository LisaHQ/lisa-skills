"""Run a suite's tasks with headless Claude Code, one session per scenario and arm.

Usage:
  python run_arms.py <suite> <iter> <arm>=<snapshot-label|skill-dir|none> [<arm>=...]
                     [--only <scenario>,...] [--model sonnet] [--jobs 6] [--max-turns 80]
                     [--timeout 2400] [--effort <level>] [--max-budget-usd <usd>] [--retry-failed]
                     [--allow-mixed]

Each session starts in <work>/<suite>/runs/<iter>/<scenario>/<arm>/<folder>
(see prep_runs.py) with the isolation flags in evalenv.py, so neither this
repository's instructions nor your own Claude Code setup leaks into it. A
skill arm is told to read the snapshot's SKILL.md first; `none` is the
no-skill baseline. Beside the folder go notes.md (the final message),
meta.json (status, tokens, cost, CLI version, denials, and tool calls that
reached outside the folder), and tools.jsonl (every tool call).

Reruns resume: finished runs are skipped. A run that failed for reasons
outside the writer's control (API or usage-limit error, timeout, no result)
or was interrupted keeps failed-result.md instead of notes.md and is not
blinded; rerun the same command with --retry-failed, which resets its folder
from the pristine scenario first. Runs that stopped at --max-turns or
--max-budget-usd are genuine outcomes. runs/<iter>/round.json pins the model,
limits, effort, and each arm's skill snapshot for the whole round; a later
invocation with other values stops unless --allow-mixed. Ctrl+C cancels
queued runs and stops running sessions. The script prints a cost estimate
from earlier rounds before it starts and a usage summary at the end, and
exits 1 while any run is failed or missing.
"""
import hashlib
import json
import shutil
import statistics
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import session
from evalenv import (DENIED_TOOLS, HARNESS_VERSION, INFRA_FAILURES, ISOLATION_FLAGS, check_name, diff_tree,
                     folder_of, load_suite, outside_files, parse_only, pop_switch, positional, positive_int,
                     reach_flags, read_json, remove_path, run_status, split_flag, tree_digest, vcs_report)

NOTE = ("(You are running non-interactively, so you cannot ask me follow-up questions. "
        "If something is unclear, make the most reasonable choice and say so in your final message. "
        "Your current directory is the project root; run commands from it without cd. {writer_note}"
        "Do not mention instruction files you were given.)")
# Settings that must be the same for every run of a round; "note" fingerprints the suite's writer_note.
ROUND_KEYS = ("model", "max_turns", "effort", "budget", "harness", "note")


def note_for(suite) -> str:
    """The closing note of every writer prompt, with the suite's optional writer_note (suite.json)."""
    return NOTE.format(writer_note=suite.writer_note + " " if suite.writer_note else "")


def resolve_skill(suite, spec: str) -> Path | None:
    if spec == "none":
        return None
    snapshot = suite.snapshot(spec) if not any(c in spec for c in "/\\:") else Path(spec)
    path = snapshot if snapshot.exists() else Path(spec)
    if not (path / "SKILL.md").exists():
        raise SystemExit(f"no SKILL.md for arm spec {spec!r} (looked in {path})")
    return path.resolve()


def snapshot_hash(path: Path | None) -> str | None:
    if path is None:
        return None
    from snapshot_skill import content_hash
    return content_hash(path)


def estimate(suite, model: str, count: int) -> str:
    """Median and p90 cost of earlier writer sessions with the same model alias."""
    costs = []
    for meta_path in suite.work.glob("runs/*/*/*/meta.json"):
        meta = read_json(meta_path)
        if meta.get("model") == model and meta.get("total_cost_usd") is not None:
            costs.append(meta["total_cost_usd"])
    if len(costs) < 3:
        return f"no cost estimate: fewer than 3 earlier '{model}' writer sessions recorded for {suite.name}"
    costs.sort()
    median, p90 = statistics.median(costs), costs[min(len(costs) - 1, int(0.9 * len(costs)))]
    return (f"estimate: {count} sessions x ${median:.3f} median (p90 ${p90:.3f}, from {len(costs)} earlier "
            f"'{model}' sessions) = ${count * median:.2f}-{count * p90:.2f} at API list prices")


def check_round(suite, it: str, opts: dict, allow_mixed: bool) -> None:
    """Keep every run of a round on the same settings and skill snapshots (runs/<iter>/round.json)."""
    path = suite.work / "runs" / it / "round.json"
    current = {**{k: opts[k] for k in ROUND_KEYS}, "arms": dict(opts["hashes"])}
    if not path.exists():
        session.write_json(path, current)
        return
    recorded = read_json(path)
    diffs = [f"{k}: the round has {recorded.get(k)!r}, this run {current[k]!r}" for k in ROUND_KEYS
             if recorded.get(k) != current[k]]
    diffs += [f"arm {arm}: its skill snapshot changed since the round started"
              for arm, sha in current["arms"].items()
              if arm in recorded.get("arms", {}) and recorded["arms"][arm] != sha]
    if diffs and not allow_mixed:
        raise SystemExit(f"settings differ from the round's earlier runs (runs/{it}/round.json):\n  "
                         + "\n  ".join(diffs)
                         + "\nrerun with the same flags and snapshots, start a new round, or pass --allow-mixed")
    arms = recorded.setdefault("arms", {})
    arms.update({a: sha for a, sha in current["arms"].items() if a not in arms})
    if diffs:
        recorded["mixed"] = sorted(set(recorded.get("mixed", [])) | set(diffs))
    session.write_json(path, recorded)


def reset(suite, it, scen, arm) -> None:
    """Restore a run folder to the pristine scenario the round was prepared from."""
    run_dir = suite.work / "runs" / it / scen / arm
    prints = read_json(suite.work / "runs" / it / "scenarios.json").get(scen, {})
    pristine = suite.work / "scenarios" / scen
    if prints.get("tree") and tree_digest(pristine) != prints["tree"]:
        raise RuntimeError(f"scenarios/{scen} changed since prep_runs; rebuild it as it was, or start a new round")
    for extra in run_dir.iterdir():  # outputs, the folder, and anything a writer left beside it
        remove_path(extra)
    shutil.copytree(pristine, run_dir / folder_of(scen), symlinks=True)


def plan(suite, it, scen, arm, retry_failed) -> str:
    """'run', 'reset' (failed or interrupted earlier, run again), or the reason to skip."""
    run_dir = suite.work / "runs" / it / scen / arm
    folder = run_dir / folder_of(scen)
    if not folder.exists():
        return "missing"
    status = None
    if (run_dir / "meta.json").exists():
        meta = read_json(run_dir / "meta.json")
        status = run_status(meta) if meta else "interrupted"  # an empty or truncated record
    if status is None:
        pristine = suite.work / "scenarios" / scen
        report = vcs_report(pristine, folder)
        dirty = (any(diff_tree(pristine, folder)) or any(w in report for w in ("CHANGED", "REMOVED", "CREATED"))
                 or bool(outside_files(run_dir, folder_of(scen))))
        if not dirty:
            return "run"
        status = "interrupted"
    if status in INFRA_FAILURES or status == "interrupted":
        return "reset" if retry_failed else f"failed earlier ({status}); use --retry-failed"
    return f"done ({status})"


def run_one(suite, it, scen, arm, skill, opts, action) -> dict:
    run_dir = suite.work / "runs" / it / scen / arm
    if action == "reset":
        reset(suite, it, scen, arm)
    prompt = suite.requests[scen] + "\n\n" + note_for(suite)
    args = [*ISOLATION_FLAGS, "--model", opts["model"], "--max-turns", str(opts["max_turns"]),
            "--allowedTools", *suite.writer_tools, "--disallowedTools", *DENIED_TOOLS]
    if skill:
        prompt = (f"Before you start, read the skill file {skill.as_posix()}/SKILL.md and follow it. "
                  "Open the reference files it points to when it tells you to.\n\n" + prompt)
        args += ["--add-dir", str(skill)]
    if opts["effort"]:
        args += ["--effort", opts["effort"]]
    if opts["budget"]:
        args += ["--max-budget-usd", opts["budget"]]
    context = {"suite": suite.name, "round": it, "scenario": scen, "arm": arm,
               **{k: opts[k] for k in ROUND_KEYS if k != "harness"}, "timeout": opts["timeout"],
               "skill": str(skill) if skill else None, "skill_sha256": opts["hashes"].get(arm)}
    folder = run_dir / folder_of(scen)
    text, record = session.run(args, prompt, folder, opts["timeout"], kind="writer",
                               tools_log=run_dir / "tools.jsonl", record_dir=suite.work / "usage", context=context)
    calls = [json.loads(line) for line in (run_dir / "tools.jsonl").read_text(encoding="utf-8").splitlines()]
    record["reach"] = reach_flags(calls, [folder] + ([skill] if skill else []))
    session.write_json(run_dir / "meta.json", record)
    if record["status"] in INFRA_FAILURES:
        (run_dir / "failed-result.md").write_text(text or "", encoding="utf-8")
        (run_dir / "notes.md").unlink(missing_ok=True)
    else:
        (run_dir / "notes.md").write_text(text or "", encoding="utf-8")
    return record


def main() -> None:
    suite, args = load_suite(sys.argv[1:], __doc__)
    only, args = split_flag(args, "--only")
    model, args = split_flag(args, "--model", "sonnet")
    jobs, args = split_flag(args, "--jobs", "6")
    max_turns, args = split_flag(args, "--max-turns", "80")
    timeout, args = split_flag(args, "--timeout", "2400")
    effort, args = split_flag(args, "--effort")
    budget, args = split_flag(args, "--max-budget-usd")
    retry_failed, args = pop_switch(args, "--retry-failed")
    allow_mixed, args = pop_switch(args, "--allow-mixed")
    positional(args, __doc__, at_least=2)
    it = check_name("iteration", args[0])
    arms = {}
    for spec in args[1:]:
        arm, sep, skill = spec.partition("=")
        if not sep or not skill:
            raise SystemExit(f"arm spec {spec!r} must look like A=none or B=<snapshot label>\n\n{__doc__}")
        if arm.casefold() in {a.casefold() for a in arms}:
            raise SystemExit(f"arm {arm} given twice (arm names must differ in more than letter case)")
        arms[check_name("arm", arm, dashes=True)] = resolve_skill(suite, skill)
    only = parse_only(only, suite.requests)
    opts = {"model": model, "max_turns": positive_int(max_turns, "--max-turns"),
            "timeout": positive_int(timeout, "--timeout"), "effort": effort, "budget": budget,
            "harness": HARNESS_VERSION,
            "note": hashlib.sha256(suite.writer_note.encode()).hexdigest()[:12] if suite.writer_note else None,
            "hashes": {arm: snapshot_hash(path) for arm, path in arms.items()}}
    if not (suite.work / "runs" / it).is_dir():
        raise SystemExit(f"no round {it}; run prep_runs.py first")
    check_round(suite, it, opts, allow_mixed)
    tasks, skipped = [], []
    for scen in sorted(suite.requests):
        if only and scen not in only:
            continue
        for arm, skill in arms.items():
            action = plan(suite, it, scen, arm, retry_failed)
            if action in ("run", "reset"):
                tasks.append((scen, arm, skill, action))
            else:
                skipped.append(f"{scen}/{arm}: {action}")
    for line in skipped:
        print("skip", line)
    if not tasks:
        print("nothing to run")
    else:
        print(estimate(suite, model, len(tasks)), flush=True)
    records = []
    pool = ThreadPoolExecutor(max_workers=positive_int(jobs, "--jobs"))
    futures = {pool.submit(run_one, suite, it, scen, arm, skill, opts, action): (scen, arm)
               for scen, arm, skill, action in tasks}
    try:
        for future in session.as_finished(futures):
            scen, arm = futures[future]
            try:
                record = future.result()
            except Exception as exc:  # one broken run must not stop the round
                record = {"status": "harness_error", "error": f"{type(exc).__name__}: {exc}", "wall_s": 0}
                run_dir = suite.work / "runs" / it / scen / arm
                if run_dir.exists():
                    session.write_json(run_dir / "meta.json", record)
            records.append(record)
            summary = session.short(record) if "usage" in record else f"{record['status']} {record.get('error', '')}"
            reach = f"  WARNING reached outside its folder: {record['reach']}" if record.get("reach") else ""
            print(f"{scen}/{arm}: {summary}{reach}", flush=True)
    except KeyboardInterrupt:
        cancelled = sum(f.cancel() for f in futures)
        stopped = session.kill_all()
        pool.shutdown(wait=True)
        print(f"\ninterrupted: {cancelled} queued runs cancelled, {stopped} running sessions stopped; "
              "finish the round by rerunning the same command with --retry-failed", flush=True)
        sys.exit(130)
    pool.shutdown(wait=True)
    for arm, path in arms.items():
        if path and opts["hashes"][arm] != snapshot_hash(path):
            print(f"WARNING: skill snapshot for arm {arm} changed during the round ({path})")
    statuses = {}
    for r in records:
        statuses[r["status"]] = statuses.get(r["status"], 0) + 1
    cost = sum(r.get("total_cost_usd") or 0 for r in records)
    tokens = sum(sum((r.get("usage") or {}).get(k) or 0 for k in session.TOKENS) for r in records)
    print(f"\n{len(records)} sessions: " + ", ".join(f"{n} {s}" for s, n in sorted(statuses.items()))
          + f"; {tokens / 1e6:.2f}M tokens, ${cost:.2f} at API list prices"
          + ("" if all(r.get("total_cost_usd") is not None for r in records) else " (some costs unknown)"))
    pending = [s for s in skipped if "failed earlier" in s or "missing" in s]
    failed = [r for r in records if r["status"] in INFRA_FAILURES]
    if failed or pending:
        rerun = subprocess.list2cmdline([a for a in sys.argv[1:] if a != "--retry-failed"] + ["--retry-failed"])
        print(f"{len(failed) + len(pending)} runs failed or missing; rerun with `python run_arms.py {rerun}`"
              + (" after prep_runs.py for missing folders" if any("missing" in s for s in pending) else ""))
        sys.exit(1)


if __name__ == "__main__":
    main()
