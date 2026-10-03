"""Check that a skill's description makes Claude Code load it at the right times.

Usage: python trigger_test.py <suite> <snapshot-label|skill-dir> [--model sonnet] [--jobs 5] [--repeat 1]

Reads evals/<suite>/trigger.json: {"project": <scenario to copy>, "queries":
[[query, should_trigger], ...]}. For each query, installs the skill into a
throwaway copy of the project (<work>/<suite>/trigger/q<N>/.claude/skills/),
sends the query through headless Claude Code, and records whether the session
invoked the skill (a Skill call naming it, or a Read of its installed
SKILL.md), every Skill call it made, and the skills it could see. Tool-call
logs go to <work>/<suite>/trigger-logs-<label>/. Skills must stay enabled here, so these sessions run without safe
mode: other skills installed on the machine compete for the query, as they
would in real use, and the results depend on them. MCP servers are still left
out, and the test stops if another skill with the same name is installed.

A session that fails before deciding (API or usage-limit error, no result)
counts as ERR, neither right nor wrong. --repeat N asks each query N times
and reports hits per query. Results, with each session's tokens and cost, go
to <work>/<suite>/trigger-results-<label>.json (and trigger-results.json).
Exits 1 on any wrong or errored query.
"""
import json
import os
import shutil
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import session
from evalenv import force_rmtree, load_suite, positional, positive_int, split_flag

TRIGGER_FLAGS = ["--strict-mcp-config", "--no-session-persistence", "--max-turns", "4",
                 "--allowedTools", "Read", "Glob", "Grep", "Skill",
                 "--disallowedTools", "Write", "Edit", "Bash", "PowerShell", "WebFetch", "WebSearch"]
ABNORMAL = {"no_result", "timeout", "harness_error"}


def same_named_installs(skill_name: str, project: Path) -> list[str]:
    """Other copies Claude Code could load under the same name."""
    config = Path(os.environ.get("CLAUDE_CONFIG_DIR") or Path.home() / ".claude")
    found = [config / "skills" / skill_name]
    found += [folder / ".claude" / "skills" / skill_name for folder in project.parents]
    return [str(p) for p in found if (p / "SKILL.md").exists()]


def triggered_by(calls: list[dict], project: Path, skill_name: str) -> str:
    """Evidence that the session loaded this project's copy of the skill, or ''."""
    target = (project / ".claude" / "skills" / skill_name / "SKILL.md").resolve()
    for call in calls:
        data = call["input"]
        if call["tool"] == "Skill" and (data.get("skill") or data.get("command")) == skill_name:
            return f"Skill {json.dumps(data)[:120]}"
        if call["tool"] == "Read" and data.get("file_path"):
            path = Path(data["file_path"])
            path = path if path.is_absolute() else project / path
            if os.path.normcase(str(path.resolve())) == os.path.normcase(str(target)):
                return f"Read {data['file_path']}"
    return ""


def run_query(suite, label, project: Path, log: Path, query: str, model: str, index: int) -> dict:
    _, record = session.run([*TRIGGER_FLAGS, "--model", model], query, project, 600, kind="trigger",
                            tools_log=log, record_dir=suite.work / "usage", skill_names=True,
                            context={"suite": suite.name, "round": "trigger", "label": label, "model": model,
                                     "query_index": index})
    calls = [json.loads(line) for line in log.read_text(encoding="utf-8").splitlines() if line.strip()]
    evidence = triggered_by(calls, project, suite.skill)
    names = (record.get("loaded") or {}).get("skill_names") or []
    return {"query": query, "triggered": bool(evidence), "evidence": evidence, "status": record["status"],
            "calls": [c["tool"] for c in calls],
            "skill_calls": [c["input"] for c in calls if c["tool"] == "Skill"],
            "same_name_skills": names.count(suite.skill), "meta": record}


def main() -> None:
    suite, args = load_suite(sys.argv[1:], __doc__)
    model, args = split_flag(args, "--model", "sonnet")
    jobs, args = split_flag(args, "--jobs", "5")
    repeat, args = split_flag(args, "--repeat", "1")
    spec = positional(args, __doc__, exactly=1)[0]
    repeat = positive_int(repeat, "--repeat")
    is_label = not any(c in spec for c in "/\\:") and suite.snapshot(spec).exists()
    skill = suite.snapshot(spec) if is_label else Path(spec).resolve()
    if not (skill / "SKILL.md").exists():
        raise SystemExit(f"no SKILL.md in {skill}")
    label = spec if is_label else "dir"
    config = json.loads((suite.dir / "trigger.json").read_text(encoding="utf-8"))
    template = suite.work / "scenarios" / config["project"]
    if not template.exists():
        raise SystemExit(f"run build_scenarios.py {suite.name} first (the test copies {config['project']})")
    work = suite.work / "trigger"
    logs = suite.work / f"trigger-logs-{label}"
    clashes = same_named_installs(suite.skill, work / "q0")
    if clashes:
        raise SystemExit(f"another '{suite.skill}' skill is installed and would compete: {', '.join(clashes)}; "
                         "move it away for the test")
    force_rmtree(work)
    force_rmtree(logs)
    logs.mkdir(parents=True)
    items = [(i * repeat + r, i, q, expected)
             for i, (q, expected) in enumerate(config["queries"]) for r in range(repeat)]

    def one(item):
        n, index, query, expected = item
        project = work / f"q{n}"
        shutil.copytree(template, project, symlinks=True)
        shutil.copytree(skill, project / ".claude" / "skills" / suite.skill)
        try:
            result = run_query(suite, label, project, logs / f"q{n}.tools.jsonl", query, model, index)
        except Exception as exc:  # one broken query must not lose the others
            result = {"query": query, "triggered": False, "evidence": "", "status": "harness_error",
                      "meta": {"status": "harness_error", "error": f"{type(exc).__name__}: {exc}"}}
        result["expected"] = expected
        meta = result["meta"]
        if not result["triggered"] and (result["status"] in ABNORMAL or result["status"] == "error"):
            result["error"] = meta.get("api_error_status") or meta.get("terminal_reason") or result["status"]
        return result

    with ThreadPoolExecutor(max_workers=positive_int(jobs, "--jobs")) as pool:
        results = list(pool.map(one, items))
    text = json.dumps(results, indent=2, ensure_ascii=False)
    for name in (f"trigger-results-{label}.json", "trigger-results.json"):
        (suite.work / name).write_text(text, encoding="utf-8")
    ok = err = 0
    by_query: dict[int, list[dict]] = {}
    for (n, index, _, _), r in zip(items, results):
        by_query.setdefault(index, []).append(r)
    for index, rs in sorted(by_query.items()):
        expected = rs[0]["expected"]
        valid = [r for r in rs if "error" not in r]
        hits = sum(r["triggered"] for r in valid)
        errors = len(rs) - len(valid)
        good = sum(r["triggered"] == expected for r in valid)
        ok += good
        err += errors
        tag = "ERR" if errors and not valid else "OK " if good == len(valid) else "BAD"
        print(f"{tag} expected={expected!s:5} triggered {hits}/{len(valid)}"
              + (f" ({errors} errored)" if errors else "") + f"  {rs[0]['query']}")
    if any((r.get("same_name_skills") or 0) > 1 for r in results):
        print(f"WARNING: sessions listed more than one skill named '{suite.skill}'; see loaded skill names")
    total = len(results) - err
    cost = sum(r["meta"].get("total_cost_usd") or 0 for r in results)
    print(f"{ok}/{total} as expected" + (f", {err} errored (not counted)" if err else "")
          + f"; {len(results)} sessions, ${cost:.2f} at API list prices")
    if ok != total or err:
        sys.exit(1)


if __name__ == "__main__":
    main()
