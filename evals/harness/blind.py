"""Hide which arm produced which outcome before judging.

Usage: python blind.py <suite> <iter> <arm> <arm> [<arm> ...] [--only <scenario>,...] [--tag NAME]

For each scenario, shuffles the arms into labels X, Y, Z, W (seeded by the
iteration, scenario, and arms, so reruns give the same labels) and writes
<work>/<suite>/blind/<name>/<scenario>/<label>/ with the files the writer
added or modified (files/), changes.txt, and notes.md with run paths scrubbed.
The label-to-arm mapping goes to runs/<iter>/mapping[-<tag>].json, which
judges must never read. <name> is <iter> or <iter>-<tag>.
"""
import hashlib
import json
import random
import re
import shutil
import sys

from evalenv import diff_tree, folder_of, force_rmtree, load_suite, positional, split_flag, vcs_report

LABELS = "XYZW"
# Paths that name the arm or the skill version would unblind the judge.
RUN_PATH = re.compile(r"(?:[A-Za-z]:|/[a-zA-Z])?[\\/]?[^\s`'\"()\[\]<>]*?[\\/]runs[\\/][^\\/\s]+[\\/][^\\/\s]+[\\/][^\\/\s]+")
SKILL_PATH = re.compile(r"(?:[A-Za-z]:|/[a-zA-Z])?[\\/]?[^\s`'\"()\[\]<>]*?skill-snapshots[\\/][^\\/\s]+")


def scrub(text: str) -> str:
    return SKILL_PATH.sub("<instructions-dir>", RUN_PATH.sub("<run-dir>", text))


def main() -> None:
    suite, args = load_suite(sys.argv[1:], __doc__)
    only, args = split_flag(args, "--only")
    tag, args = split_flag(args, "--tag")
    positional(args, __doc__, at_least=3)
    it, arms = args[0], args[1:]
    if len(arms) > len(LABELS):
        raise SystemExit(f"at most {len(LABELS)} arms per judge")
    only = set(only.split(",")) if only else None
    name = f"{it}-{tag}" if tag else it
    mapping_file = suite.work / "runs" / it / f"mapping{'-' + tag if tag else ''}.json"
    mapping = json.loads(mapping_file.read_text(encoding="utf-8")) if mapping_file.exists() else {}
    for scen in sorted(p for p in (suite.work / "runs" / it).iterdir() if p.is_dir()):
        if only and scen.name not in only:
            continue
        order = list(arms)
        seed = int(hashlib.sha1(f"{name}{scen.name}{''.join(arms)}".encode()).hexdigest()[:8], 16)
        random.Random(seed).shuffle(order)
        mapping[scen.name] = {LABELS[i]: arm for i, arm in enumerate(order)}
        for i, arm in enumerate(order):
            src = scen / arm / folder_of(scen.name)
            dst = suite.work / "blind" / name / scen.name / LABELS[i]
            force_rmtree(dst)
            dst.mkdir(parents=True)
            pristine = suite.work / "scenarios" / scen.name
            added, modified, deleted = diff_tree(pristine, src)
            for rel in added + modified:
                (dst / "files" / rel).parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src / rel, dst / "files" / rel)
            notes = scen / arm / "notes.md"
            if notes.exists():
                text = notes.read_text(encoding="utf-8", errors="replace")
                (dst / "notes.md").write_text(scrub(text), encoding="utf-8")
            (dst / "changes.txt").write_text(
                "added:\n" + "".join(f"  {f}\n" for f in added)
                + "modified:\n" + "".join(f"  {f}\n" for f in modified)
                + "deleted:\n" + "".join(f"  {f}\n" for f in deleted)
                + vcs_report(pristine, src),
                encoding="utf-8")
    mapping_file.write_text(json.dumps(mapping, indent=2), encoding="utf-8")
    print("blinded:", ", ".join(sorted(k for k in mapping if not only or k in only)))
    print(f"outcomes: {suite.work / 'blind' / name}")


if __name__ == "__main__":
    main()
