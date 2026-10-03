"""Run a suite's tasks with headless Claude Code, one session per scenario and arm.

Usage:
  python run_arms.py <suite> <iter> <arm>=<snapshot-label|skill-dir|none> [<arm>=...]
                     [--only <scenario>,...] [--model sonnet] [--jobs 6] [--max-turns 80]

Each session starts in <work>/<suite>/runs/<iter>/<scenario>/<arm>/<folder>
(see prep_runs.py), so no repository instructions leak into it. A skill arm is
told to read the snapshot's SKILL.md first; `none` is the no-skill baseline.
The final message goes to notes.md and run metadata, including any denied
tool calls, to meta.json beside the folder.
"""
import json
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from evalenv import DENIED_TOOLS, SESSION_ENV, claude_bin, folder_of, load_suite, positional, split_flag

NOTE = ("(You are running non-interactively, so you cannot ask me follow-up questions. "
        "If something is unclear, make the most reasonable choice and say so in your final message.)")


def resolve_skill(suite, spec: str) -> Path | None:
    if spec == "none":
        return None
    snapshot = suite.snapshot(spec)
    path = snapshot if snapshot.exists() else Path(spec)
    if not (path / "SKILL.md").exists():
        raise SystemExit(f"no SKILL.md for arm spec {spec!r} (looked in {path})")
    return path.resolve()


def run_one(suite, it, scen, arm, skill, model, max_turns) -> str:
    run_dir = suite.work / "runs" / it / scen / arm
    cwd = run_dir / folder_of(scen)
    if not cwd.exists():
        return f"{scen}/{arm}: missing {cwd} (run prep_runs.py)"
    prompt = suite.requests[scen] + "\n\n" + NOTE
    cmd = [claude_bin(), "-p", "--model", model, "--output-format", "json", "--max-turns", max_turns,
           "--allowedTools", *suite.writer_tools, "--disallowedTools", *DENIED_TOOLS]
    if skill:
        prompt = (f"Before you start, read the skill file {skill.as_posix()}/SKILL.md and follow it. "
                  "Open the reference files it points to when it tells you to.\n\n" + prompt)
        cmd += ["--add-dir", str(skill)]
    started = time.time()
    proc = subprocess.run(cmd, input=prompt, cwd=cwd, env=SESSION_ENV, capture_output=True, text=True,
                          encoding="utf-8", errors="replace", timeout=2400)
    elapsed = time.time() - started
    try:
        data = json.loads(proc.stdout)
    except json.JSONDecodeError:
        data = {"result": None}
    (run_dir / "notes.md").write_text(data.get("result") or "", encoding="utf-8")
    meta = {k: data.get(k) for k in ("total_cost_usd", "num_turns", "duration_ms", "is_error", "subtype")}
    meta["model"] = model
    meta["skill"] = str(skill) if skill else None
    meta["denials"] = [str((d.get("tool_input") or {}).get("command") or d.get("tool_name"))
                       for d in (data.get("permission_denials") or [])]
    meta["wall_s"] = round(elapsed, 1)
    meta["returncode"] = proc.returncode
    if data.get("result") is None:
        meta["stdout_tail"] = proc.stdout[-2000:]
        meta["stderr_tail"] = proc.stderr[-2000:]
    (run_dir / "meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    return (f"{scen}/{arm}: rc={proc.returncode} turns={meta['num_turns']} "
            f"cost={meta['total_cost_usd']} {elapsed:.0f}s")


def main() -> None:
    suite, args = load_suite(sys.argv[1:], __doc__)
    only, args = split_flag(args, "--only")
    model, args = split_flag(args, "--model", "sonnet")
    jobs, args = split_flag(args, "--jobs", "6")
    max_turns, args = split_flag(args, "--max-turns", "80")
    positional(args, __doc__, at_least=2)
    it = args[0]
    arms = {}
    for spec in args[1:]:
        arm, skill = spec.split("=", 1)
        arms[arm] = resolve_skill(suite, skill)
    only = set(only.split(",")) if only else None
    tasks = [(suite, it, scen, arm, skill, model, max_turns)
             for scen in sorted(suite.requests) if not only or scen in only
             for arm, skill in arms.items()]
    with ThreadPoolExecutor(max_workers=int(jobs)) as pool:
        for line in pool.map(lambda t: run_one(*t), tasks):
            print(line, flush=True)


if __name__ == "__main__":
    main()
