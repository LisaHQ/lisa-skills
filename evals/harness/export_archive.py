"""Pack a suite's work directory into one zip for long-term storage.

Usage: python export_archive.py <suite> <output.zip> [--work <dir>] [--note <ARCHIVE.md>]

Keeps everything needed to audit or extend the results: snapshots, blinded
outcomes, judgments with their session records, mappings, scenario
fingerprints, the usage ledger, run metadata, tool-call logs and notes, and
the scenarios. Run folders are slimmed to notes.md, meta.json, tools.jsonl,
failed-result.md, changes.txt, and the files the writer added or modified
(under files/), because full copies are regenerable with build_scenarios.py
and prep_runs.py. Restore by unzipping into <LISA_EVAL_WORK>/<suite>;
collect.py, aggregate.py, checks.py, usage.py, and blind.py work on the slim
layout. Empty folders are kept, because Git checkouts need them. SVN working
copies point at their repository by absolute path, recorded in
_export.json: restore to the same work root, or relocate them with
`svn relocate` before running svn commands that contact the repository. Run
it from evals/harness/ with paths such as ../<suite>/archive/<name>.zip; the
zip is written to a temporary name and renamed only when it is complete.
"""
import json
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path

from evalenv import (changes_text, diff_tree, folder_of, load_suite, outside_files, positional, split_flag,
                     vcs_report)

SKIP_DIRS = {"judge-sandbox", "trigger", "__pycache__"}
KEEP = ("notes.md", "meta.json", "tools.jsonl", "failed-result.md")


def main() -> None:
    suite, args = load_suite(sys.argv[1:], __doc__)
    work, args = split_flag(args, "--work")
    note, args = split_flag(args, "--note")
    out = Path(positional(args, __doc__, exactly=1)[0]).resolve()
    work = Path(work).resolve() if work else suite.work
    if note and not Path(note).is_file():
        raise SystemExit(f"--note file not found: {note}")
    if not work.is_dir():
        raise SystemExit(f"no work directory {work}")
    if out.is_relative_to(work):
        raise SystemExit("write the archive outside the work directory it packs")
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = out.with_name(out.name + ".tmp")
    count = 0
    with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        if note:
            zf.write(note, "ARCHIVE.md")
            count += 1
        zf.writestr("_export.json", json.dumps({"work_root": str(work), "suite": suite.name, "exported":
                                                datetime.now(timezone.utc).isoformat(timespec="seconds")}))
        for path in sorted(work.rglob("*")):
            rel = path.relative_to(work)
            if rel.parts[0] in SKIP_DIRS or rel.parts[0] == "runs" or rel.as_posix() == "_export.json":
                continue
            if note and rel.as_posix() == "ARCHIVE.md":
                continue  # the new note replaces the one restored with an earlier archive
            if path.is_file() or (path.is_dir() and not any(path.iterdir())):
                zf.write(path, rel.as_posix())
                count += 1
        runs = work / "runs"
        for it in sorted(p for p in runs.iterdir() if p.is_dir()) if runs.exists() else []:
            for extra in it.iterdir():
                if extra.is_file():  # mapping*.json, scenarios.json, run.log
                    zf.write(extra, extra.relative_to(work).as_posix())
                    count += 1
            for scen in sorted(p for p in it.iterdir() if p.is_dir()):
                for arm in sorted(p for p in scen.iterdir() if p.is_dir()):
                    base = arm.relative_to(work).as_posix()
                    for name in KEEP:
                        if (arm / name).exists():
                            zf.write(arm / name, f"{base}/{name}")
                            count += 1
                    folder = arm / folder_of(scen.name)
                    if folder.exists():
                        pristine = work / "scenarios" / scen.name
                        added, modified, deleted = diff_tree(pristine, folder)
                        for rel in added + modified:
                            zf.write(folder / rel, f"{base}/files/{rel}")
                            count += 1
                        outside = outside_files(arm, folder_of(scen.name))
                        extra = vcs_report(pristine, folder) + (
                            "outside the project folder:\n" + "".join(f"  {f}\n" for f in outside) if outside else "")
                        zf.writestr(f"{base}/changes.txt", changes_text(added, modified, deleted, extra))
                        count += 1
                    else:  # already slim
                        for f in sorted(arm.rglob("*")):
                            rel = f.relative_to(arm).as_posix()
                            if f.is_file() and rel not in KEEP:
                                zf.write(f, f"{base}/{rel}")
                                count += 1
    with zipfile.ZipFile(tmp) as zf:
        bad = zf.testzip()
    if bad is not None:
        raise SystemExit(f"integrity check FAILED on {bad}; kept {tmp} for inspection")
    tmp.replace(out)
    print(f"wrote {out} ({out.stat().st_size / 1e6:.1f} MB, {count} files, integrity ok)")


if __name__ == "__main__":
    main()
