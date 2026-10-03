"""Judge blinded outcomes with headless Claude Code, one judge per scenario.

Usage: python judge.py <name> [--only s1-logslice,...] [--model opus] [--jobs 5]
                       [--out <judgments-name>] [--print-prompts]

<name> is the blind set from blind.py (<iter> or <iter>-<tag>). Each judge
runs in its own sandbox, <work>/judge-sandbox/<name>/<scenario>/, holding only
the rubric, the fact sheet, the request, a copy of the pristine scenario, and
the blinded outcomes, so it never sees which arm wrote what. Verdicts are
saved to <work>/judgments/<out>/<scenario>.json (default <out> = <name>).

--print-prompts builds the sandboxes and prints one prompt per scenario
instead of running judges, for judging with subagents in an interactive
session; point each subagent at its sandbox directory.
"""
import json
import shutil
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor

from evalenv import (DENIED_TOOLS, EVAL, JUDGE_TOOLS, REQUESTS, SESSION_ENV, WORK, claude_bin, force_rmtree,
                     positional, split_flag)

TEMPLATE = (EVAL / "harness" / "judge_prompt.md").read_text(encoding="utf-8")


def build_sandbox(name: str, scen: str):
    outcomes = WORK / "blind" / name / scen
    labels = sorted(p.name for p in outcomes.iterdir() if p.is_dir())
    box = WORK / "judge-sandbox" / name / scen
    force_rmtree(box)
    box.mkdir(parents=True)
    shutil.copy2(EVAL / "rubric.md", box / "rubric.md")
    shutil.copy2(EVAL / "facts" / f"{scen}.md", box / "facts.md")
    (box / "request.txt").write_text(REQUESTS[scen] + "\n", encoding="utf-8")
    shutil.copytree(WORK / "scenarios" / scen, box / "scenario", symlinks=True)
    shutil.copytree(outcomes, box / "outcomes")
    prompt = TEMPLATE.format(count=len(labels), labels=", ".join(labels), scenario=scen)
    return box, prompt


def run_judge(name: str, scen: str, out: str, model: str) -> str:
    box, prompt = build_sandbox(name, scen)
    cmd = [claude_bin(), "-p", "--model", model, "--output-format", "json", "--max-turns", "120",
           "--allowedTools", *JUDGE_TOOLS, "--disallowedTools", *DENIED_TOOLS]
    started = time.time()
    proc = subprocess.run(cmd, input=prompt, cwd=box, env=SESSION_ENV, capture_output=True, text=True,
                          encoding="utf-8", errors="replace", timeout=3600)
    try:
        data = json.loads(proc.stdout)
    except json.JSONDecodeError:
        data = {}
    dest = WORK / "judgments" / out
    dest.mkdir(parents=True, exist_ok=True)
    (dest / f"{scen}.txt").write_text(data.get("result") or proc.stdout[-4000:], encoding="utf-8")
    verdict = box / "verdict.json"
    if not verdict.exists():
        return f"{scen}: no verdict.json (rc={proc.returncode}); see {dest / (scen + '.txt')}"
    try:
        json.loads(verdict.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return f"{scen}: verdict.json is not valid JSON ({exc})"
    shutil.copy2(verdict, dest / f"{scen}.json")
    return f"{scen}: {(data.get('result') or '').strip()[:120]} ({time.time() - started:.0f}s, cost={data.get('total_cost_usd')})"


def main() -> None:
    args = sys.argv[1:]
    only, args = split_flag(args, "--only")
    model, args = split_flag(args, "--model", "opus")
    jobs, args = split_flag(args, "--jobs", "5")
    out, args = split_flag(args, "--out")
    print_prompts = "--print-prompts" in args
    args = [a for a in args if a != "--print-prompts"]
    name = positional(args, __doc__, exactly=1)[0]
    only = set(only.split(",")) if only else None
    scenarios = sorted(p.name for p in (WORK / "blind" / name).iterdir() if p.is_dir()
                       and (not only or p.name in only))
    if print_prompts:
        for scen in scenarios:
            box, prompt = build_sandbox(name, scen)
            print(f"===== {scen}\nWorking directory: {box}\n\n{prompt}\n"
                  f"(Save the verdict as {WORK / 'judgments' / (out or name) / (scen + '.json')})\n")
        return
    with ThreadPoolExecutor(max_workers=int(jobs)) as pool:
        for line in pool.map(lambda s: run_judge(name, s, out or name, model), scenarios):
            print(line, flush=True)


if __name__ == "__main__":
    main()
