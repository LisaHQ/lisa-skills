"""Hide which arm produced which outcome before judging.

Usage: python blind.py <suite> <iter> <arm> <arm> [<arm> ...] [--only <scenario>,...] [--tag NAME]
                       [--allow-failed] [--allow-baseline-change] [--redact] [--force]

Writes <work>/<suite>/blind/<name>/<scenario>/<label>/ for labels X, Y, Z, W:
the files the writer added or modified (files/, with uniform timestamps),
changes.txt, and notes.md with run paths scrubbed. <name> is <iter> or
<iter>-<tag>. Labels are assigned once per scenario and kept: a scenario
blinded before keeps its labels, and new scenarios cycle through the arm
orders so each arm holds each label, and each pair each order, about equally
often (seeded by the set name and the sorted arms). The label-to-arm mapping
goes to runs/<iter>/mapping[-<tag>].json, which judges must never read, and
blind/<name>.json records which round the set belongs to.

changes.txt also lists version-control changes, files written outside the
project folder, denied commands that would have changed the repository (when
the suite's suite_checks.py defines mutates()), and a session that stopped at
its turn or budget limit.

A scenario is skipped (and the script exits 1) when any arm's run failed
(--allow-failed overrides) or when the pristine scenario differs from the one
prep_runs.py recorded (--allow-baseline-change overrides); an arm without a
run folder stops the script. Re-blinding a judged scenario with a different
set of arms needs --force. When a judged scenario's content changes, its
verdicts in every judgments folder of this set are renamed *.stale.*.
Notes that mention the writer's instruction files or still contain run paths
are listed in blind/<name>.leaks.txt; --redact removes the instruction-file
sentences. Runs whose writers reached outside their folder, and rounds run
with mixed settings, are reported as warnings.
"""
import hashlib
import itertools
import json
import os
import random
import re
import shutil
import sys

from evalenv import (INFRA_FAILURES, WORK_ROOT, changes_text, check_name, diff_tree, folder_of, force_rmtree,
                     load_suite, outside_files, parse_only, pop_switch, positional, read_json, run_status,
                     split_flag, tree_digest, vcs_report, walk)

LABELS = "XYZW"
FIXED_TIME = 1718186400  # 2024-06-12T10:00Z, the fixtures' commit time
# Paths that name the arm or the skill version would unblind the judge.
RUN_PATH = re.compile(r"(?:[A-Za-z]:|/[a-zA-Z])?[\\/]?[^\s`'\"()\[\]<>]*?[\\/]runs[\\/][^\\/\s]+[\\/][^\\/\s]+"
                      r"[\\/][^\\/\s]+")
SKILL_PATH = re.compile(r"(?:[A-Za-z]:|/[a-zA-Z])?[\\/]?[^\s`'\"()\[\]<>]*?skill-snapshots[\\/][^\\/\s]+")
# Sentences that tell the judge an outcome followed instruction files.
LEAK = re.compile(r"SKILL\.md|<instructions-dir>|\bskills?\b", re.I)
VERDICT_FILES = (".json", ".txt", ".meta.json", ".tools.jsonl", ".invalid.json", ".prev.json", ".failed.meta.json")


def keep_urls(replacement):
    def sub(match):
        before = match.string[max(0, match.start() - 3):match.start()]
        return match.group(0) if before.endswith("://") or match.group(0).lower().startswith("http") else replacement
    return sub


def scrub(text: str, it: str = "", scen: str = "", arm: str = "") -> str:
    text = RUN_PATH.sub(keep_urls("<run-dir>"), text)
    text = SKILL_PATH.sub(keep_urls("<instructions-dir>"), text)
    if scen and arm:  # relative forms such as runs/r1/c1-x/B, c1-x\B, or ../B/<folder>
        tail = rf"(?:\.\.[\\/]+)*(?:runs[\\/]+{re.escape(it)}[\\/]+)?{re.escape(scen)}[\\/]+{re.escape(arm)}"
        text = re.sub(tail + r"(?=[\\/]|[\s`'\")\]>.,:;]|$)", "<run-dir>", text)
        text = re.sub(rf"(?:\.\.[\\/]+)+{re.escape(arm)}[\\/]+{re.escape(folder_of(scen))}\b",
                      "<run-dir>/" + folder_of(scen), text)
    return text


def leaks(text: str, pristine_text: str) -> list[str]:
    """Sentences that mention instruction files, unless the scenario itself uses the term."""
    found = []
    for sentence in re.split(r"(?<=[.!?])\s+|\n", text):
        terms = {m.group(0).lower() for m in LEAK.finditer(sentence)}
        if terms and any(t not in pristine_text for t in terms):
            found.append(sentence.strip())
    return found


def path_hints(text: str, it: str, scen: str, arms: list[str]) -> list[str]:
    """Run paths that survived scrubbing (warn only; files/ are never rewritten)."""
    norm = text.replace("\\", "/").lower()
    marks = [f"runs/{it}/".lower(), "skill-snapshots", str(WORK_ROOT).replace("\\", "/").lower()]
    marks += [f"/{a}/{folder_of(scen)}/".lower() for a in arms]
    return [m for m in marks if m in norm]


def text_of(base) -> str:
    parts = []
    for rel in walk(base):
        p = base / rel
        if p.stat().st_size < 1_000_000:
            parts.append(rel.lower() + "\n" + p.read_bytes().decode("utf-8", "ignore").lower())
    return "\n".join(parts)


def tree_hash(path) -> str:
    h = hashlib.sha1()
    if path.exists():
        for p in sorted(path.rglob("*")):
            if p.is_file():
                h.update(p.relative_to(path).as_posix().encode() + b"\0" + p.read_bytes())
    return h.hexdigest()


def copy_flat_time(src, dst) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, dst)
    os.utime(dst, (FIXED_TIME, FIXED_TIME))


def mutation_lines(meta: dict, mutates, it, scen, arm) -> str:
    if mutates is None:
        return ""
    denied = []
    for d in meta.get("denials", []):
        tool, sep, detail = d.partition(": ")
        command = detail if sep and tool in ("Bash", "PowerShell") else d
        if mutates(command):
            denied.append(scrub(command, it, scen, arm))
    return "denied attempts:\n" + "".join(f"  {c}\n" for c in denied) if denied else ""


def session_line(status: str) -> str:
    return {"max_turns": "writer session: stopped at the turn limit before finishing\n",
            "budget": "writer session: stopped at the cost limit before finishing\n"}.get(status, "")


def judgment_folders(suite, name: str) -> list:
    """Every judgments folder that holds verdicts of this blind set (including --out re-judges)."""
    root = suite.work / "judgments"
    if not root.is_dir():
        return []
    return [d for d in root.iterdir() if d.is_dir()
            and (read_json(d / "_set.json").get("blind") or d.name) == name]


def mark_stale(folders, scen: str, old_labels: dict | None) -> list[str]:
    """Rename a scenario's verdict files to *.stale[N].*, keeping the labels they used; return the folders."""
    touched = []
    for folder in folders:
        if not (folder / f"{scen}.json").exists():
            continue
        n = ""
        while any((folder / f"{scen}.stale{n}{s}").exists() for s in VERDICT_FILES):
            n = str(int(n or 1) + 1)
        for suffix in VERDICT_FILES:
            f = folder / f"{scen}{suffix}"
            if f.exists():
                f.replace(folder / f"{scen}.stale{n}{suffix}")
        if old_labels:
            (folder / f"{scen}.stale{n}.mapping.json").write_text(json.dumps(old_labels), encoding="utf-8")
        touched.append(folder.name)
    return touched


def check_arm(runs, scen: str, arm: str) -> tuple[str, str | None]:
    """('ok' | 'failed' | 'missing', detail) for one arm's run of a scenario."""
    arm_dir = runs / scen / arm
    full = (arm_dir / folder_of(scen)).exists()
    slim = not full and (arm_dir / "changes.txt").exists()
    if not (full or slim):
        return "missing", f"{arm}: no run folder"
    status = run_status(read_json(arm_dir / "meta.json"))
    if status in INFRA_FAILURES or status == "missing":
        return "failed", f"{arm}: {status}"
    return "ok", None


def settings_warnings(runs, scens: list[str], arms: list[str]) -> list[str]:
    """Rounds that mix writer settings or skill snapshots, which make arms incomparable."""
    notes = []
    round_info = read_json(runs / "round.json")
    if round_info.get("mixed"):
        notes += [f"round.json records mixed settings: {m}" for m in round_info["mixed"]]
    for arm in arms:
        seen = {}
        for scen in scens:
            meta = read_json(runs / scen / arm / "meta.json")
            for key in ("model", "max_turns", "effort", "skill_sha256"):
                if key in meta:
                    seen.setdefault(key, set()).add(json.dumps(meta[key]))
        notes += [f"arm {arm} mixes {key}: {', '.join(sorted(v))}" for key, v in seen.items() if len(v) > 1]
    return notes


def main() -> None:
    suite, args = load_suite(sys.argv[1:], __doc__)
    only, args = split_flag(args, "--only")
    tag, args = split_flag(args, "--tag")
    allow_failed, args = pop_switch(args, "--allow-failed")
    allow_change, args = pop_switch(args, "--allow-baseline-change")
    redact, args = pop_switch(args, "--redact")
    force, args = pop_switch(args, "--force")
    positional(args, __doc__, at_least=3)
    it, arms = check_name("iteration", args[0]), args[1:]
    if tag:
        check_name("tag", tag)
    if len(arms) > len(LABELS):
        raise SystemExit(f"at most {len(LABELS)} arms per judge")
    if len({a.casefold() for a in arms}) != len(arms):
        raise SystemExit("duplicate arms (arm names must differ in more than letter case)")
    runs = suite.work / "runs" / it
    if not runs.is_dir():
        raise SystemExit(f"no round {runs}")
    all_scens = sorted(p.name for p in runs.iterdir() if p.is_dir())
    only = parse_only(only, all_scens)
    selected = [s for s in all_scens if not only or s in only]
    name = f"{it}-{tag}" if tag else it
    if (runs.parent / name).is_dir() and tag:
        raise SystemExit(f"blind set name {name} collides with the iteration {name}; choose another tag")
    owner = read_json(suite.work / "judgments" / name / "_set.json").get("blind")
    if owner and owner != name:
        raise SystemExit(f"judgments/{name} holds verdicts of blind set {owner}; choose another tag")
    try:
        from suite_checks import mutates
    except ImportError:  # the suite has no mutation detector
        mutates = None
    mapping_file = runs / f"mapping{'-' + tag if tag else ''}.json"
    mapping = json.loads(mapping_file.read_text(encoding="utf-8")) if mapping_file.exists() else {}
    prints = read_json(runs / "scenarios.json")
    folders = judgment_folders(suite, name)

    # Check everything before touching any blinded folder.
    missing = [detail for s in selected for a in arms for state, detail in [check_arm(runs, s, a)]
               if state == "missing"]
    if missing:
        raise SystemExit("no run for:\n  " + "\n  ".join(f"{s}" for s in missing)
                         + "\ncheck the arm names or prepare and run them first")
    skipped, todo = [], []
    for scen in selected:
        pristine = suite.work / "scenarios" / scen
        if prints.get(scen, {}).get("tree") and tree_digest(pristine) != prints[scen]["tree"] and not allow_change:
            skipped.append(f"{scen}: scenarios/{scen} differs from the one this round was prepared from")
            continue
        failed = [detail for state, detail in (check_arm(runs, scen, a) for a in arms) if state == "failed"]
        if failed and not allow_failed:
            skipped.append(f"{scen}: " + ", ".join(failed))
            continue
        old = mapping.get(scen)
        if old and sorted(old.values()) != sorted(arms) and any((f / f"{scen}.json").exists() for f in folders) \
                and not force:
            skipped.append(f"{scen}: judged with arms {', '.join(sorted(old.values()))}; use --force to re-blind")
            continue
        todo.append(scen)

    seed = int(hashlib.sha1(f"{name}{''.join(sorted(arms))}".encode()).hexdigest()[:8], 16)
    rng = random.Random(seed)
    position = list(all_scens)
    rng.shuffle(position)
    orders = list(itertools.permutations(sorted(arms)))
    rng.shuffle(orders)
    leak_lines, blinded, warnings = [], [], settings_warnings(runs, todo, arms)
    for scen in todo:
        old = mapping.get(scen)
        if old and sorted(old.values()) == sorted(arms):
            new = dict(old)  # labels stick once assigned
        else:
            order = orders[position.index(scen) % len(orders)]
            new = {LABELS[i]: arm for i, arm in enumerate(order)}
        out_dir = suite.work / "blind" / name / scen
        old_hash = tree_hash(out_dir)
        force_rmtree(out_dir)
        pristine = suite.work / "scenarios" / scen
        pristine_text = text_of(pristine)
        for label, arm in sorted(new.items()):
            arm_dir = runs / scen / arm
            src, dst = arm_dir / folder_of(scen), out_dir / label
            dst.mkdir(parents=True)
            meta = read_json(arm_dir / "meta.json")
            if meta.get("reach"):
                warnings.append(f"{scen}/{arm}: the writer reached outside its folder: {meta['reach'][:3]}")
            if src.exists():
                added, modified, deleted = diff_tree(pristine, src)
                for rel in added + modified:
                    copy_flat_time(src / rel, dst / "files" / rel)
                outside = outside_files(arm_dir, folder_of(scen))
                changes = changes_text(added, modified, deleted, vcs_report(pristine, src)
                                       + ("outside the project folder:\n" + "".join(f"  {f}\n" for f in outside)
                                          if outside else ""))
            else:  # slim archived run: files/ and changes.txt were saved by export_archive.py
                for f in sorted((arm_dir / "files").rglob("*")) if (arm_dir / "files").exists() else []:
                    if f.is_file():
                        copy_flat_time(f, dst / "files" / f.relative_to(arm_dir / "files"))
                changes = (arm_dir / "changes.txt").read_text(encoding="utf-8")
            changes += mutation_lines(meta, mutates, it, scen, arm) + session_line(run_status(meta))
            (dst / "changes.txt").write_text(changes, encoding="utf-8")
            notes = arm_dir / "notes.md"
            if notes.exists():
                text = scrub(notes.read_text(encoding="utf-8", errors="replace"), it, scen, arm)
                found = leaks(text, pristine_text)
                leak_lines += [f"{scen}/{label}: {s}" for s in found]
                if redact:
                    for sentence in found:
                        text = text.replace(sentence, "")
                (dst / "notes.md").write_text(text, encoding="utf-8")
            for p in dst.rglob("*"):
                if p.is_file():
                    hints = path_hints(p.read_bytes().decode("utf-8", "ignore"), it, scen, arms)
                    leak_lines += [f"{scen}/{label}: path {h!r} in {p.relative_to(dst).as_posix()}" for h in hints]
                    os.utime(p, (FIXED_TIME, FIXED_TIME))
        mapping[scen] = new
        blinded.append(scen)
        if old_hash != tree_hash(out_dir) or (old and old != new):
            touched = mark_stale(folders, scen, old)
            if touched:
                print(f"notice: {scen} changed since it was judged; verdicts in {', '.join(touched)} are now *.stale.*")
    if blinded:
        mapping_file.write_text(json.dumps(mapping, indent=2), encoding="utf-8")
        (suite.work / "blind" / f"{name}.json").write_text(json.dumps({"iter": it, "tag": tag}), encoding="utf-8")
    leak_file = suite.work / "blind" / f"{name}.leaks.txt"
    kept = [line for line in (leak_file.read_text(encoding="utf-8").splitlines() if leak_file.exists() else [])
            if line.split("/", 1)[0] not in blinded]
    merged = sorted(kept + leak_lines)
    if merged:
        leak_file.write_text("\n".join(merged) + "\n", encoding="utf-8")
        print(f"WARNING: {len(merged)} notes mention instruction files or run paths"
              f"{' (instruction-file sentences removed)' if redact else '; review them or rerun with --redact'}: "
              f"{leak_file}")
    else:
        leak_file.unlink(missing_ok=True)
    for w in warnings:
        print("WARNING:", w)
    print("blinded:", ", ".join(blinded) or "nothing")
    print(f"outcomes: {suite.work / 'blind' / name}")
    if skipped:
        print("skipped:\n  " + "\n  ".join(skipped))
        sys.exit(1)


if __name__ == "__main__":
    main()
