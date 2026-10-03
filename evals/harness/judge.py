"""Judge blinded outcomes with headless Claude Code, one judge per scenario.

Usage: python judge.py <suite> <name> [--only <scenario>,...] [--model opus] [--jobs 5]
                       [--out <judgments-name>] [--timeout 3600] [--retries 1] [--rejudge]
                       [--effort <level>] [--max-budget-usd <usd>] [--allow-baseline-change]
                       [--print-prompts]

<name> is the blind set from blind.py (<iter> or <iter>-<tag>). Each judge
runs in its own sandbox, <work>/<suite>/judge-sandbox/<out>/<scenario>/,
holding only the rubric, the fact sheet, the request, a copy of the pristine
scenario, and the blinded outcomes. File tools and shell reads are confined
to the sandbox; interpreter commands are not, so tool calls that reach toward
runs, mappings, or snapshots are flagged afterwards. A verdict must be valid
(every label scored 1-5 on every rubric key, a full ranking); a failed or
invalid judge is rerun up to --retries times.

Saved to <work>/<suite>/judgments/<out>/ (default <out> = <name>):
<scenario>.json (the verdict), .txt (the judge's last message), .meta.json
(status, tokens, cost, the hashes of the outcomes, rubric, prompt, and facts
it judged, and flagged tool calls), .tools.jsonl, every attempt's record in
<scenario>.attempts/, and _set.json naming the blind set. Reruns skip
scenarios whose verdict still matches the same outcomes, rubric, prompt, and
facts (--rejudge forces them); a replaced verdict is kept as .prev.json. A
scenario whose pristine copy differs from the one its round was prepared from
is skipped unless --allow-baseline-change. Exits 1 when any scenario has no
valid verdict.

--print-prompts builds the sandboxes and prints one prompt per scenario
instead of running judges, for judging with subagents in an interactive
session; such verdicts are not validated and their cost is not recorded.
"""
import json
import shutil
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor

import session
from blind import tree_hash
from evalenv import (DENIED_TOOLS, HARNESS, ISOLATION_FLAGS, blind_set_info, check_name, file_digest, force_rmtree,
                     load_suite, parse_only, pop_switch, positional, positive_int, reach_flags, read_json, split_flag,
                     tree_digest, verdict_problems)

TEMPLATE = (HARNESS / "judge_prompt.md").read_text(encoding="utf-8")


def provenance(suite, name: str, scen: str, opts: dict) -> dict:
    """What a verdict depends on; a verdict is current while all of it is unchanged."""
    return {"blind": name, "model": opts["model"], "effort": opts["effort"],
            "outcomes": tree_hash(suite.work / "blind" / name / scen),
            "rubric": file_digest(suite.dir / "rubric.md"),
            "judge_prompt": file_digest(HARNESS / "judge_prompt.md"),
            "facts": file_digest(suite.dir / "facts" / f"{scen}.md"),
            "request": suite.requests[scen]}


def build_sandbox(suite, name: str, out: str, scen: str):
    outcomes = suite.work / "blind" / name / scen
    labels = sorted(p.name for p in outcomes.iterdir() if p.is_dir())
    box = suite.work / "judge-sandbox" / out / scen
    force_rmtree(box)
    box.mkdir(parents=True)
    shutil.copy2(suite.dir / "rubric.md", box / "rubric.md")
    shutil.copy2(suite.dir / "facts" / f"{scen}.md", box / "facts.md")
    (box / "request.txt").write_text(suite.requests[scen] + "\n", encoding="utf-8")
    shutil.copytree(suite.work / "scenarios" / scen, box / "scenario", symlinks=True)
    shutil.copytree(outcomes, box / "outcomes")
    prompt = TEMPLATE.format(count=len(labels), labels=", ".join(labels), scenario=scen)
    return box, labels, prompt


def read_verdict(path):
    """Parse verdict.json, tolerating a UTF-8 byte-order mark or UTF-16 (PowerShell output)."""
    raw = path.read_bytes()
    encoding = "utf-16" if raw[:2] in (b"\xff\xfe", b"\xfe\xff") else "utf-8-sig"
    return json.loads(raw.decode(encoding))


def judge_once(suite, name, out, scen, opts):
    box, labels, prompt = build_sandbox(suite, name, out, scen)
    args = [*ISOLATION_FLAGS, "--model", opts["model"], "--max-turns", "120",
            "--allowedTools", *suite.judge_tools, "--disallowedTools", *DENIED_TOOLS]
    if opts["effort"]:
        args += ["--effort", opts["effort"]]
    if opts["budget"]:
        args += ["--max-budget-usd", opts["budget"]]
    attempts = suite.work / "judgments" / out / f"{scen}.attempts"
    attempts.mkdir(parents=True, exist_ok=True)
    context = {"suite": suite.name, "round": opts["round"], "scenario": scen, "label": out, "blind": name,
               "model": opts["model"], "effort": opts["effort"]}
    log = attempts / "last.tools.jsonl"
    text, record = session.run(args, prompt, box, opts["timeout"], kind="judge", tools_log=log,
                               record_dir=suite.work / "usage", context=context)
    verdict, problems = None, []
    verdict_file = box / "verdict.json"
    if not verdict_file.exists():
        problems = ["no verdict.json in the sandbox"]
    else:
        try:
            verdict = read_verdict(verdict_file)
            problems = verdict_problems(verdict, labels, suite.weights)
        except ValueError as exc:  # undecodable bytes or invalid JSON
            problems = [f"verdict.json is unreadable ({exc})"]
    calls = [json.loads(line) for line in log.read_text(encoding="utf-8").splitlines()]
    record["reach"] = reach_flags(calls, [box])
    record["labels"] = labels
    record["verdict_problems"] = problems
    record["provenance"] = provenance(suite, name, scen, opts)
    session.write_json(attempts / f"{record['attempt']}.json", record)
    (attempts / f"{record['attempt']}.txt").write_text(text or record.get("stdout_tail", ""), encoding="utf-8")
    log.replace(attempts / f"{record['attempt']}.tools.jsonl")
    return text, record, verdict


def run_judge(suite, name: str, out: str, scen: str, opts) -> str:
    dest = suite.work / "judgments" / out
    attempts = []
    while True:
        _, record, verdict = judge_once(suite, name, out, scen, opts)
        attempts.append(record["attempt"])
        # A valid verdict counts even if the session ended badly; Ctrl+C stops the retries.
        if not record["verdict_problems"] or session.STOP.is_set() or len(attempts) > opts["retries"]:
            break
    record["attempts"] = attempts
    warn = f" WARNING reached outside the sandbox: {record['reach']}" if record["reach"] else ""
    folder = dest / f"{scen}.attempts"
    if record["verdict_problems"]:
        session.write_json(dest / f"{scen}.failed.meta.json", record)
        old = " (an earlier verdict was kept)" if (dest / f"{scen}.json").exists() else ""
        return (f"{scen}: FAILED after {len(attempts)} attempt(s): {record['status']}, "
                f"{'; '.join(record['verdict_problems'][:3])}{old} [{session.short(record)}]{warn}")
    if (dest / f"{scen}.json").exists():
        shutil.copy2(dest / f"{scen}.json", dest / f"{scen}.prev.json")
    session.write_json(dest / f"{scen}.json", verdict)
    session.write_json(dest / f"{scen}.meta.json", record)
    shutil.copy2(folder / f"{record['attempt']}.txt", dest / f"{scen}.txt")
    shutil.copy2(folder / f"{record['attempt']}.tools.jsonl", dest / f"{scen}.tools.jsonl")
    (dest / f"{scen}.failed.meta.json").unlink(missing_ok=True)
    order = ",".join(verdict.get("ranking") or [])
    return f"{scen}: ranking={order} [{session.short(record)}]{warn}"


def current(suite, name: str, out: str, scen: str, opts: dict) -> bool:
    """Whether judgments/<out>/<scen>.json is a valid verdict of exactly the current inputs and judge."""
    dest = suite.work / "judgments" / out
    verdict, meta = read_json(dest / f"{scen}.json"), read_json(dest / f"{scen}.meta.json")
    labels = sorted(p.name for p in (suite.work / "blind" / name / scen).iterdir() if p.is_dir())
    return bool(verdict) and not verdict_problems(verdict, labels, suite.weights) \
        and meta.get("provenance") == provenance(suite, name, scen, opts)


def main() -> None:
    suite, args = load_suite(sys.argv[1:], __doc__)
    only, args = split_flag(args, "--only")
    model, args = split_flag(args, "--model", "opus")
    jobs, args = split_flag(args, "--jobs", "5")
    out, args = split_flag(args, "--out")
    timeout, args = split_flag(args, "--timeout", "3600")
    retries, args = split_flag(args, "--retries", "1")
    effort, args = split_flag(args, "--effort")
    budget, args = split_flag(args, "--max-budget-usd")
    rejudge, args = pop_switch(args, "--rejudge")
    allow_change, args = pop_switch(args, "--allow-baseline-change")
    print_prompts, args = pop_switch(args, "--print-prompts")
    name = positional(args, __doc__, exactly=1)[0]
    out = check_name("judgments", out, dashes=True) if out else name
    if not retries.isdigit():
        raise SystemExit("--retries must be a whole number (0 or more)")
    blind = suite.work / "blind" / name
    if not blind.is_dir():
        raise SystemExit(f"no blind set {blind}; run blind.py first")
    dest = suite.work / "judgments" / out
    owner = read_json(dest / "_set.json").get("blind")
    if owner and owner != name and any(dest.glob("*.json")):
        raise SystemExit(f"judgments/{out} holds verdicts of blind set {owner}; choose another --out")
    if out != name and (suite.work / "blind" / f"{out}.json").exists():
        raise SystemExit(f"--out {out} is the name of another blind set; choose another name")
    available = sorted(p.name for p in blind.iterdir() if p.is_dir())
    only = parse_only(only, available)
    info = blind_set_info(suite, name)
    opts = {"model": model, "timeout": positive_int(timeout, "--timeout"), "effort": effort, "budget": budget,
            "retries": int(retries), "round": info["iter"]}
    prints = read_json(suite.work / "runs" / info["iter"] / "scenarios.json")
    scenarios, skipped = [], []
    for scen in available:
        if only and scen not in only:
            continue
        recorded = prints.get(scen, {}).get("tree")
        if recorded and tree_digest(suite.work / "scenarios" / scen) != recorded and not allow_change:
            skipped.append(f"{scen}: scenarios/{scen} differs from the one the round was prepared from")
        elif not print_prompts and not rejudge and current(suite, name, out, scen, opts):
            print(f"skip {scen}: already judged (use --rejudge to judge it again)")
        else:
            scenarios.append(scen)
    dest.mkdir(parents=True, exist_ok=True)
    session.write_json(dest / "_set.json", {"blind": name, "round": info["iter"], "tag": info["tag"],
                                            "mode": "subagent" if print_prompts else "headless"})
    if print_prompts:
        for scen in scenarios:
            box, _, prompt = build_sandbox(suite, name, out, scen)
            print(f"===== {scen}\nWorking directory: {box}\n----- prompt -----\n{prompt}\n----- end prompt -----\n"
                  f"Dispatcher (not part of the prompt): when the subagent finishes, copy "
                  f"{box / 'verdict.json'} to {dest / (scen + '.json')}\n")
        for line in skipped:
            print("skipped", line)
        sys.exit(1 if skipped else 0)
    failed = []
    pool = ThreadPoolExecutor(max_workers=positive_int(jobs, "--jobs"))
    futures = {pool.submit(run_judge, suite, name, out, scen, opts): scen for scen in scenarios}
    try:
        for future in session.as_finished(futures):
            try:
                line = future.result()
            except Exception as exc:  # one broken judge must not stop the others
                line = f"{futures[future]}: FAILED: {type(exc).__name__}: {exc}"
            if ": FAILED" in line:
                failed.append(futures[future])
            print(line, flush=True)
    except KeyboardInterrupt:
        cancelled = sum(f.cancel() for f in futures)
        stopped = session.kill_all()
        pool.shutdown(wait=True)
        print(f"\ninterrupted: {cancelled} queued judges cancelled, {stopped} running judges stopped; "
              "rerun the same command to judge the rest", flush=True)
        sys.exit(130)
    pool.shutdown(wait=True)
    records = [read_json(dest / f"{s}.meta.json") for s in scenarios if s not in failed]
    cost = sum(r.get("total_cost_usd") or 0 for r in records)
    tokens = sum(sum((r.get("usage") or {}).get(k) or 0 for k in session.TOKENS) for r in records)
    print(f"\n{len(scenarios) - len(failed)} of {len(scenarios)} scenarios judged in this run; accepted attempts "
          f"used {tokens / 1e6:.2f}M tokens, ${cost:.2f} at API list prices (usage.py counts every attempt)")
    for line in skipped:
        print("skipped", line)
    if failed:
        argv = sys.argv[1:]
        kept = [a for i, a in enumerate(argv) if a != "--only" and (i == 0 or argv[i - 1] != "--only")]
        rerun = subprocess.list2cmdline(kept + ["--only", ",".join(sorted(failed))])
        print(f"rerun the failed scenarios with `python judge.py {rerun}`")
    if failed or skipped:
        sys.exit(1)


if __name__ == "__main__":
    main()
