"""Run one headless Claude Code session and record what it did and used.

Writers, judges, and trigger queries all start through run(). It reads the
session's event stream (--output-format stream-json), so the record costs no
extra model calls: status, token use and cost per model, the CLI version, what
the session loaded, every tool call, and permission denials. Each attempt is
also written to <work>/<suite>/usage/<attempt>.json, so retried and failed
sessions still count toward a round's spend.
"""
from __future__ import annotations

import json
import os
import signal
import subprocess
import tempfile
import threading
import time
import uuid
from collections.abc import Iterable
from concurrent.futures import FIRST_COMPLETED, wait
from datetime import datetime, timezone
from pathlib import Path

from evalenv import HARNESS_VERSION, SESSION_ENV, claude_cmd

TOKENS = ("input", "cache_write", "cache_read", "output")


def parse_events(text: str) -> list[dict]:
    """JSON events from stream-json output; also accepts one JSON object or array."""
    text = text or ""
    stripped = text.strip()
    if stripped.startswith("["):
        try:
            data = json.loads(stripped)
            return [e for e in data if isinstance(e, dict)]
        except json.JSONDecodeError:
            pass
    events = []
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("{"):
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(event, dict):
                events.append(event)
    return events


def usage_of(result: dict | None, events: Iterable[dict] = ()) -> dict:
    """Token and cost totals for one session, overall and per model.

    Uses the result event's modelUsage, which covers every model the session
    called (subagents included); then its usage plus total_cost_usd. Without
    a result (a killed session) it sums the last usage seen per assistant
    message: input and cache tokens are right, output is a lower bound, and
    cost is unknown, so the record is marked partial.
    """
    by_model: dict[str, dict] = {}
    partial = False
    if result and result.get("modelUsage"):
        for model, u in result["modelUsage"].items():
            by_model[model] = {"input": u.get("inputTokens") or 0,
                               "cache_write": u.get("cacheCreationInputTokens") or 0,
                               "cache_read": u.get("cacheReadInputTokens") or 0,
                               "output": u.get("outputTokens") or 0,
                               "cost_usd": u.get("costUSD") if u.get("costBasis") != "unknown" else None}
    elif result and result.get("usage"):
        u = result["usage"]
        by_model["unknown"] = {"input": u.get("input_tokens") or 0,
                               "cache_write": u.get("cache_creation_input_tokens") or 0,
                               "cache_read": u.get("cache_read_input_tokens") or 0,
                               "output": u.get("output_tokens") or 0,
                               "cost_usd": result.get("total_cost_usd")}
    else:
        last: dict[str, tuple[str, dict]] = {}
        for e in events:
            message = e.get("message") or {}
            if e.get("type") == "assistant" and message.get("id") and message.get("usage"):
                last[message["id"]] = (message.get("model") or "unknown", message["usage"])
        for model, u in last.values():
            m = by_model.setdefault(model, {**dict.fromkeys(TOKENS, 0), "cost_usd": None})
            m["input"] += u.get("input_tokens") or 0
            m["cache_write"] += u.get("cache_creation_input_tokens") or 0
            m["cache_read"] += u.get("cache_read_input_tokens") or 0
            m["output"] += u.get("output_tokens") or 0
        partial = bool(last)
    total: dict = {k: sum(m[k] for m in by_model.values()) for k in TOKENS}
    costs = [m["cost_usd"] for m in by_model.values()]
    total["cost_usd"] = (result or {}).get("total_cost_usd")
    if total["cost_usd"] is None and costs and None not in costs:
        total["cost_usd"] = sum(costs)
    total["by_model"] = by_model
    if partial or (result is None and not by_model):
        total["partial"] = True
    return total


def status_of(result: dict | None, timed_out: bool) -> str:
    """ok, max_turns, budget (writer-caused endings) or error, timeout, no_result (infrastructure)."""
    if timed_out:
        return "timeout"
    if result is None:
        return "no_result"
    subtype = result.get("subtype") or ""
    if "max_turns" in subtype:
        return "max_turns"
    if "budget" in subtype:
        return "budget"
    if subtype == "success" and not result.get("is_error") and not result.get("api_error_status"):
        return "ok"
    return "error"


def tool_calls(events: list[dict]) -> list[dict]:
    """Every tool call in order: {"tool": name, "input": input} (long values truncated)."""
    calls, seen = [], set()
    for e in events:
        if e.get("type") != "assistant":
            continue
        for block in (e.get("message") or {}).get("content") or []:
            if not isinstance(block, dict) or block.get("type") != "tool_use" or block.get("id") in seen:
                continue
            seen.add(block.get("id"))
            data = block.get("input") if isinstance(block.get("input"), dict) else {}
            calls.append({"tool": block.get("name"),
                          "input": {k: (v[:2000] if isinstance(v, str) else v) for k, v in data.items()}})
    return calls


def denial_text(d: dict) -> str:
    """'Tool: detail' for a permission denial, so Bash and other tools stay distinguishable."""
    data = d.get("tool_input") or {}
    detail = (data.get("command") or data.get("file_path") or data.get("pattern") or data.get("skill")
              or json.dumps(data))
    return f"{d.get('tool_name')}: {detail}"


# Sessions that are running now, so an interrupted round can stop them all;
# once STOP is set (Ctrl+C), no new session starts.
_LIVE: set[subprocess.Popen] = set()
_LIVE_LOCK = threading.Lock()
STOP = threading.Event()


def kill_tree(proc: subprocess.Popen) -> None:
    """Kill a session and the commands it started."""
    if os.name == "nt":
        subprocess.run(["taskkill", "/T", "/F", "/PID", str(proc.pid)], capture_output=True)
    else:
        try:
            os.killpg(proc.pid, signal.SIGKILL)
        except OSError:
            pass
    try:
        proc.kill()
    except OSError:
        pass


def as_finished(futures):
    """Yield futures as they finish, waking often so Ctrl+C is handled promptly on Windows."""
    pending = set(futures)
    while pending:
        done, pending = wait(pending, timeout=0.5, return_when=FIRST_COMPLETED)
        yield from done


def kill_all() -> int:
    """Kill every running session and start no new ones (after Ctrl+C); return how many were running."""
    with _LIVE_LOCK:
        STOP.set()
        live = list(_LIVE)
    for proc in live:
        kill_tree(proc)
    return len(live)


def write_json(path: Path, data) -> None:
    """Write JSON atomically, so an interrupted write never leaves a truncated file."""
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(data, indent=1, ensure_ascii=False), encoding="utf-8")
    os.replace(tmp, path)


def run(args: list[str], prompt: str, cwd: Path, timeout: int, *, kind: str, tools_log: Path | None = None,
        record_dir: Path | None = None, context: dict | None = None,
        skill_names: bool = False) -> tuple[str | None, dict]:
    """Run one session; return (final message or None, session record).

    The record goes to record_dir/<attempt>.json when record_dir is given, and
    the tool calls to tools_log as JSON lines. Output goes through temporary
    files rather than pipes, so a command the session left running cannot
    hold the harness up or swallow the result.
    """
    attempt = uuid.uuid4().hex
    started_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    cmd = [*claude_cmd(), "-p", "--output-format", "stream-json", "--verbose", *args]
    started, timed_out, rc = time.time(), False, None
    # A new process group keeps a console Ctrl+C away from the sessions: the
    # harness catches it and decides what to stop.
    group = ({"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP} if os.name == "nt"
             else {"start_new_session": True})
    started_proc = False
    # A command the session left running may still hold the output files; leave them for later cleanup.
    with tempfile.TemporaryDirectory(prefix="lisa-session-", ignore_cleanup_errors=True) as tmp:
        out_path, err_path = Path(tmp) / "stdout", Path(tmp) / "stderr"
        with open(out_path, "wb") as out_file, open(err_path, "wb") as err_file:
            with _LIVE_LOCK:
                proc = None
                if STOP.is_set():
                    err_file.write(b"not started: the round was interrupted")
                else:
                    try:
                        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=out_file, stderr=err_file,
                                                cwd=cwd, env=SESSION_ENV, **group)
                        _LIVE.add(proc)
                        started_proc = True
                    except OSError as exc:
                        err_file.write(f"could not start the CLI: {exc}".encode())
            if proc is not None:
                try:
                    try:
                        proc.stdin.write(prompt.encode("utf-8"))
                        proc.stdin.close()
                    except OSError:
                        pass
                    rc = proc.wait(timeout=timeout)
                except subprocess.TimeoutExpired:
                    timed_out = True
                    kill_tree(proc)
                    try:
                        proc.wait(timeout=60)
                    except subprocess.TimeoutExpired:
                        pass
                finally:
                    with _LIVE_LOCK:
                        _LIVE.discard(proc)
        out = out_path.read_bytes().decode("utf-8", "replace")
        err = err_path.read_bytes().decode("utf-8", "replace")
    events = parse_events(out)
    init = next((e for e in events if e.get("type") == "system" and e.get("subtype") == "init"), {})
    result = next((e for e in reversed(events) if e.get("type") == "result"), None)
    windows = [e["rate_limit_info"] for e in events if e.get("type") == "rate_limit_event" and e.get("rate_limit_info")]
    calls = tool_calls(events)
    usage = usage_of(result, events)
    loaded = None
    if init:
        loaded = {"tools": init.get("tools"), "mcp_servers": [m.get("name") for m in init.get("mcp_servers") or []],
                  "plugins": [p.get("name") for p in init.get("plugins") or []],
                  "skills": len(init.get("skills") or []), "memory": bool(init.get("memory_paths")),
                  "permission_mode": init.get("permissionMode")}
        if skill_names:
            loaded["skill_names"] = init.get("skills")
    record = {
        "schema": 2,
        "harness": HARNESS_VERSION,
        "attempt": attempt,
        "kind": kind,
        **(context or {}),
        # A session that produced its result counts by that result, even if a
        # command it started kept running past the timeout.
        "status": status_of(result, timed_out and result is None),
        "exit_hang": timed_out and result is not None,
        "started_at": started_at,
        "wall_s": round(time.time() - started, 1),
        "returncode": rc,
        **{k: (result or {}).get(k) for k in ("subtype", "is_error", "terminal_reason", "api_error_status",
                                              "num_turns", "duration_ms", "duration_api_ms", "session_id",
                                              "errors", "startup_failure_reason")},
        "total_cost_usd": usage["cost_usd"],
        "usage": usage,
        "models": sorted(usage["by_model"]),
        "cli_version": init.get("claude_code_version"),
        "auth": None if not init else "subscription" if init.get("apiKeySource") in (None, "none") else "api-key",
        "loaded": loaded,
        "plan_window": {k: (v or {}).get("utilization") for k, v in (windows[-1].get("unifiedWindows") or {}).items()}
        if windows else None,
        "using_overage": any(w.get("isUsingOverage") for w in windows),
        "subagents": ((result or {}).get("subagent_stats") or {}).get("spawned"),
        "denials": [denial_text(d) for d in ((result or {}).get("permission_denials") or [])],
        "commands": [c["input"].get("command") for c in calls if c["tool"] == "Bash" and c["input"].get("command")],
    }
    if record["status"] != "ok":
        record["stdout_tail"] = out[-2000:]
        record["stderr_tail"] = err[-2000:]
    if tools_log is not None:
        tools_log.write_text("".join(json.dumps(c, ensure_ascii=False) + "\n" for c in calls), encoding="utf-8")
    if record_dir is not None and started_proc:  # a session that never started spent nothing
        record_dir.mkdir(parents=True, exist_ok=True)
        write_json(record_dir / f"{attempt}.json", record)
    text = (result or {}).get("result")
    if text is None and record.get("errors"):
        text = "\n".join(map(str, record["errors"]))
    return text, record


def short(record: dict) -> str:
    """One progress-line summary: status, turns, tokens, cost, time."""
    u = record.get("usage") or {}
    tokens = sum(u.get(k) or 0 for k in TOKENS)
    cost = record.get("total_cost_usd")
    return (f"{record['status']} turns={record.get('num_turns')} tokens={tokens / 1000:.0f}k "
            f"cost={'?' if cost is None else f'${cost:.3f}'} {record.get('wall_s', 0):.0f}s")
