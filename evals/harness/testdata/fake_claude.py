"""A stand-in for `claude -p --output-format stream-json` used by selftest.py.

It spends no model usage. The mode comes from FAKE_CLAUDE_MODES, a
comma-separated list of <substring>=<mode> matched against the working
directory (first match wins), else FAKE_CLAUDE_MODE, else 'ok':

ok         writer: answer with a short note (and a README.md when the folder has
           no README); judge: write a valid verdict.json; trigger: call Skill
           when the query mentions a commit or a README
error      an API error result (is_error, api_error_status 529), for any role
max_turns  stops at the turn limit with no result text, for any role
nonjson    prints a plain-text error and exits 1
sleep      sleeps 30 seconds (for timeout tests)
bad_verdict / no_verdict   judge writes an invalid verdict / none at all
tamper     judge writes a valid verdict but adds a file to scenario/
script     judge writes a valid verdict after running a script that reads the round's mapping
denial     like ok, plus a denied `git add -A`
"""
import json
import os
import re
import sys
import time
from pathlib import Path

MODEL = "claude-fake-1"


def emit(event):
    print(json.dumps(event), flush=True)


def mode_for(cwd: str) -> str:
    norm = cwd.replace("\\", "/")
    for item in filter(None, os.environ.get("FAKE_CLAUDE_MODES", "").split(",")):
        key, _, mode = item.partition("=")
        if key and key in norm:
            return mode
    return os.environ.get("FAKE_CLAUDE_MODE", "ok")


def result(text, subtype="success", is_error=False, denials=(), api_error=None):
    usage = {"input_tokens": 12, "cache_creation_input_tokens": 1000, "cache_read_input_tokens": 3000,
             "output_tokens": 50}
    emit({"type": "result", "subtype": subtype, "is_error": is_error, "result": text, "num_turns": 3,
          "duration_ms": 1200, "duration_api_ms": 900, "session_id": "fake", "total_cost_usd": 0.01,
          "api_error_status": api_error, "terminal_reason": "completed", "usage": usage,
          "modelUsage": {MODEL: {"inputTokens": 12, "outputTokens": 50, "cacheReadInputTokens": 3000,
                                 "cacheCreationInputTokens": 1000, "costUSD": 0.01, "costBasis": "list"}},
          "permission_denials": [{"tool_name": "Bash", "tool_input": {"command": c}} for c in denials],
          "subagent_stats": {"spawned": 0}})


def tool(name, data, n=[0]):
    n[0] += 1
    emit({"type": "assistant", "message": {"id": f"msg_{n[0]}", "model": MODEL, "content": [
        {"type": "tool_use", "id": f"tool_{n[0]}", "name": name, "input": data}],
        "usage": {"input_tokens": 4, "cache_creation_input_tokens": 100, "cache_read_input_tokens": 0,
                  "output_tokens": 2}}})


def judge(cwd: Path, mode: str):
    labels = sorted(p.name for p in (cwd / "outcomes").iterdir() if p.is_dir())
    rubric = (cwd / "rubric.md").read_text(encoding="utf-8")
    keys = sorted(set(re.findall(r"^\| ([A-F]) \|", rubric, re.M)))
    if mode == "no_verdict":
        return result("done without a verdict")
    verdict = {"scenario": cwd.name, "ranking": labels, "confidence": "medium", "decisive_reasons": []}
    for i, label in enumerate(labels):
        verdict[label] = {"scores": {k: max(1, 5 - i) for k in keys}, "errors": [], "strengths": [], "weaknesses": []}
    if mode == "bad_verdict":
        del verdict[labels[-1]]
    tool("Read", {"file_path": "rubric.md"})
    if mode == "tamper":
        (cwd / "scenario" / "judge-note.txt").write_text("changed evidence\n", encoding="utf-8")
    if mode == "script":
        code = "print(open('../../../runs/r1/mapping.json').read())\n"
        (cwd / "check.py").write_text(code, encoding="utf-8")
        tool("Write", {"file_path": str(cwd / "check.py"), "content": code})
        tool("Bash", {"command": "python check.py"})
    (cwd / "verdict.json").write_text(json.dumps(verdict), encoding="utf-8")
    result(f"{cwd.name}: ranking={','.join(labels)}")


def main():
    prompt = sys.stdin.read()
    cwd = Path.cwd()
    mode = mode_for(str(cwd))
    if mode == "nonjson":
        print("Error: not logged in")
        sys.exit(1)
    if mode == "sleep":
        time.sleep(30)
    emit({"type": "system", "subtype": "init", "claude_code_version": "0.0.0-fake", "apiKeySource": "none",
          "tools": ["Read", "Bash"], "mcp_servers": [], "plugins": [], "skills": [], "permissionMode": "default",
          "model": MODEL})
    emit({"type": "rate_limit_event", "rate_limit_info": {"status": "allowed", "isUsingOverage": False,
                                                          "unifiedWindows": {"five_hour": {"utilization": 0.25}}}})
    if mode == "error":
        return result("API Error: 529 overloaded", subtype="success", is_error=True, api_error=529)
    if mode == "max_turns":
        tool("Bash", {"command": "git status"})
        return result(None, subtype="error_max_turns", is_error=True)
    if (cwd / "rubric.md").exists() and (cwd / "outcomes").is_dir():
        return judge(cwd, mode)
    if "--max-turns" in sys.argv and sys.argv[sys.argv.index("--max-turns") + 1] == "4":  # trigger test
        if re.search(r"commit|readme", prompt, re.I) and not re.search(r"release notes|explain", prompt, re.I):
            name = "readme-md" if re.search(r"readme", prompt, re.I) else "commit-message"
            tool("Skill", {"skill": name})
        return result("ok")
    tool("Bash", {"command": "git status --short"})
    if not (cwd / "README.md").exists() and not (cwd / ".git").exists() and not (cwd / ".svn").exists():
        (cwd / "README.md").write_text("# Fake\n\nWritten by the fake CLI.\n", encoding="utf-8")
    denials = ["git add -A"] if mode == "denial" else []
    result("Commit description:\n\n```text\nDo the thing\n\n- fix: Do the thing.\n```\n", denials=denials)


if __name__ == "__main__":
    main()
