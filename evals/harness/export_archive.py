"""Pack a suite's work directory into one zip for long-term storage.

Usage: python export_archive.py <suite> <output.zip> [--work <dir>] [--note <ARCHIVE.md>]

Keeps everything needed to audit or extend the results: snapshots, blinded
outcomes, judgments, mappings, run metadata and notes, and the scenarios.
Run folders are slimmed to notes.md, meta.json, changes.txt, and the files
the writer added or modified (under files/), because full copies are
regenerable with build_scenarios.py and prep_runs.py. Restore by unzipping
into <LISA_EVAL_WORK>/<suite>; collect.py, aggregate.py, and checks.py work
on the slim layout.
"""
import sys
import zipfile
from pathlib import Path

from evalenv import diff_tree, folder_of, load_suite, positional, split_flag, vcs_report

SKIP_DIRS = {"judge-sandbox", "trigger", "__pycache__"}


def changes_text(added, modified, deleted, extra=""):
    return ("added:\n" + "".join(f"  {f}\n" for f in added)
            + "modified:\n" + "".join(f"  {f}\n" for f in modified)
            + "deleted:\n" + "".join(f"  {f}\n" for f in deleted) + extra)


def main() -> None:
    suite, args = load_suite(sys.argv[1:], __doc__)
    work, args = split_flag(args, "--work")
    note, args = split_flag(args, "--note")
    out = Path(positional(args, __doc__, exactly=1)[0]).resolve()
    work = Path(work).resolve() if work else suite.work
    out.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        if note:
            zf.write(note, "ARCHIVE.md")
            count += 1
        for path in sorted(work.rglob("*")):
            rel = path.relative_to(work)
            if path.is_file() and rel.parts[0] not in SKIP_DIRS and rel.parts[0] != "runs":
                zf.write(path, rel.as_posix())
                count += 1
        runs = work / "runs"
        for it in sorted(p for p in runs.iterdir() if p.is_dir()) if runs.exists() else []:
            for extra in it.iterdir():
                if extra.is_file():  # mapping*.json, run.log, timing.jsonl
                    zf.write(extra, extra.relative_to(work).as_posix())
                    count += 1
            for scen in sorted(p for p in it.iterdir() if p.is_dir()):
                for arm in sorted(p for p in scen.iterdir() if p.is_dir()):
                    base = arm.relative_to(work).as_posix()
                    for name in ("notes.md", "meta.json"):
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
                        zf.writestr(f"{base}/changes.txt",
                                    changes_text(added, modified, deleted, vcs_report(pristine, folder)))
                        count += 1
                    else:  # already slim
                        for f in sorted(arm.rglob("*")):
                            if f.is_file() and f.name not in ("notes.md", "meta.json"):
                                zf.write(f, f"{base}/{f.relative_to(arm).as_posix()}")
                                count += 1
    with zipfile.ZipFile(out) as zf:
        bad = zf.testzip()
    print(f"wrote {out} ({out.stat().st_size / 1e6:.1f} MB, {count} files, "
          f"integrity {'ok' if bad is None else 'FAILED: ' + bad})")


if __name__ == "__main__":
    main()
