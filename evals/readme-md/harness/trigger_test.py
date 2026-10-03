"""Check that the skill's description makes Claude Code load it at the right times.

Usage: python trigger_test.py <snapshot-label|skill-dir> [--model sonnet] [--jobs 5]

Installs the skill into a throwaway project (<work>/trigger/q<N>/.claude/skills/),
sends each query through headless Claude Code, and records whether the session
invoked the skill (a Skill tool call or a read of its SKILL.md). Results go to
<work>/trigger-results.json. Edit QUERIES to probe new near-misses.
"""
import json
import shutil
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from evalenv import SESSION_ENV, WORK, claude_bin, force_rmtree, positional, split_flag

QUERIES = [
    ("write a README for this repo", True),
    ("Viết README cho project này giúp mình nhé", True),
    ("can you review my readme and tell me what's wrong with it? don't change anything", True),
    ("our README.md is outdated since we renamed the CLI flags, please update it", True),
    ("document this folder so new people know what the files are and how to use them", True),
    ("make the readme look more professional, maybe add some badges", True),
    ("write a CONTRIBUTING.md that explains how to send pull requests", False),
    ("add doc comments to every function in main.go", False),
    ("write a commit message for my staged changes", False),
    ("explain in two sentences what this repo does", False),
]


def run_query(project: Path, query: str, model: str) -> dict:
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
            if (block.get("name") == "Skill" and "readme-md" in text) or ("readme-md" in text and "SKILL.md" in text):
                triggered, evidence = True, f"{block.get('name')} {text[:120]}"
    return {"query": query, "triggered": triggered, "evidence": evidence}


def main() -> None:
    args = sys.argv[1:]
    model, args = split_flag(args, "--model", "sonnet")
    jobs, args = split_flag(args, "--jobs", "5")
    positional(args, __doc__, exactly=1)
    snapshot = WORK / "skill-snapshots" / args[0] / "readme-md"
    skill = snapshot if snapshot.exists() else Path(args[0]).resolve()
    if not (skill / "SKILL.md").exists():
        raise SystemExit(f"no SKILL.md in {skill}")
    project_template = WORK / "scenarios" / "s6-grepl"
    if not project_template.exists():
        raise SystemExit("run build_scenarios.py first (the test project copies s6-grepl)")
    work = WORK / "trigger"
    force_rmtree(work)

    def one(item):
        idx, (query, expected) = item
        project = work / f"q{idx}"
        shutil.copytree(project_template, project)
        shutil.copytree(skill, project / ".claude" / "skills" / "readme-md")
        result = run_query(project, query, model)
        result["expected"] = expected
        return result

    with ThreadPoolExecutor(max_workers=int(jobs)) as pool:
        results = list(pool.map(one, enumerate(QUERIES)))
    (WORK / "trigger-results.json").write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
    ok = 0
    for r in results:
        hit = r["triggered"] == r["expected"]
        ok += hit
        print(f"{'OK ' if hit else 'BAD'} expected={r['expected']!s:5} got={r['triggered']!s:5} {r['query']}")
    print(f"{ok}/{len(results)} as expected")


if __name__ == "__main__":
    main()
