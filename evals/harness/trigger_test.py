"""Check that a skill's description makes Claude Code load it at the right times.

Usage: python trigger_test.py <suite> <snapshot-label|skill-dir> [--model sonnet] [--jobs 5]

Reads evals/<suite>/trigger.json: {"project": <scenario to copy>, "queries":
[[query, should_trigger], ...]}. For each query, installs the skill into a
throwaway copy of the project (<work>/<suite>/trigger/q<N>/.claude/skills/),
sends the query through headless Claude Code, and records whether the session
invoked the skill (a Skill tool call or a read of its SKILL.md). Results go to
<work>/<suite>/trigger-results.json.
"""
import json
import shutil
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from evalenv import SESSION_ENV, claude_bin, force_rmtree, load_suite, positional, split_flag


def run_query(project: Path, skill_name: str, query: str, model: str) -> dict:
    cmd = [claude_bin(), "-p", "--model", model, "--output-format", "stream-json", "--verbose",
           "--max-turns", "4", "--allowedTools", "Read", "Glob", "Grep", "Skill",
           "--disallowedTools", "Write", "Edit", "Bash", "WebFetch", "WebSearch"]
    proc = subprocess.run(cmd, input=query, cwd=project, env=SESSION_ENV, capture_output=True, text=True,
                          encoding="utf-8", errors="replace", timeout=600)
    triggered, evidence = False, ""
    for line in proc.stdout.splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        for block in (event.get("message") or {}).get("content") or []:
            if not isinstance(block, dict) or block.get("type") != "tool_use":
                continue
            text = json.dumps(block.get("input") or {})
            # Only this skill counts: an installed copy under another name (for example a
            # plugin's "anthropic-skills:commit-message") is a different skill.
            name = (block.get("input") or {}).get("skill", "")
            if (block.get("name") == "Skill" and name == skill_name) or f"skills/{skill_name}/SKILL.md" in text.replace("\\\\", "/"):
                triggered, evidence = True, f"{block.get('name')} {text[:120]}"
    return {"query": query, "triggered": triggered, "evidence": evidence}


def main() -> None:
    suite, args = load_suite(sys.argv[1:], __doc__)
    model, args = split_flag(args, "--model", "sonnet")
    jobs, args = split_flag(args, "--jobs", "5")
    spec = positional(args, __doc__, exactly=1)[0]
    skill = suite.snapshot(spec) if suite.snapshot(spec).exists() else Path(spec).resolve()
    if not (skill / "SKILL.md").exists():
        raise SystemExit(f"no SKILL.md in {skill}")
    config = json.loads((suite.dir / "trigger.json").read_text(encoding="utf-8"))
    template = suite.work / "scenarios" / config["project"]
    if not template.exists():
        raise SystemExit(f"run build_scenarios.py {suite.name} first (the test copies {config['project']})")
    work = suite.work / "trigger"
    force_rmtree(work)

    def one(item):
        idx, (query, expected) = item
        project = work / f"q{idx}"
        shutil.copytree(template, project, symlinks=True)
        shutil.copytree(skill, project / ".claude" / "skills" / suite.skill)
        result = run_query(project, suite.skill, query, model)
        result["expected"] = expected
        return result

    with ThreadPoolExecutor(max_workers=int(jobs)) as pool:
        results = list(pool.map(one, enumerate(config["queries"])))
    (suite.work / "trigger-results.json").write_text(json.dumps(results, indent=2, ensure_ascii=False),
                                                      encoding="utf-8")
    ok = 0
    for r in results:
        hit = r["triggered"] == r["expected"]
        ok += hit
        print(f"{'OK ' if hit else 'BAD'} expected={r['expected']!s:5} got={r['triggered']!s:5} {r['query']}")
    print(f"{ok}/{len(results)} as expected")


if __name__ == "__main__":
    main()
