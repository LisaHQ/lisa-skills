"""Pack an evaluation work directory into one zip for long-term storage.

Usage: python export_archive.py <output.zip> [--work <dir>] [--note <ARCHIVE.md>]

Keeps everything needed to audit or extend the results: snapshots, blinded
outcomes, judgments, mappings, metadata, notes, and the scenarios. Run folders
are slimmed to notes.md, meta.json, changes.txt, and the files the writer
added or modified (under files/), because full copies are regenerable with
build_scenarios.py + prep_runs.py. Restore by unzipping into a folder and
pointing README_EVAL_WORK at it; collect.py, aggregate.py, and checks.py work
on the slim layout.
"""
import sys
import zipfile
from pathlib import Path

from blind import diff_tree
from evalenv import WORK, folder_of, positional, split_flag

SKIP_DIRS = {"judge-sandbox", "trigger", "__pycache__"}


def main() -> None:
    args = sys.argv[1:]
    work, args = split_flag(args, "--work")
    note, args = split_flag(args, "--note")
    positional(args, __doc__, exactly=1)
    work = Path(work).resolve() if work else WORK
    out = Path(args[0]).resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        if note:
            zf.write(note, "ARCHIVE.md")
        for path in sorted(work.rglob("*")):
            rel = path.relative_to(work)
            if not path.is_file() or rel.parts[0] in SKIP_DIRS or rel.parts[0] == "runs":
                continue
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
                        added, modified, deleted = diff_tree(work / "scenarios" / scen.name, folder)
                    else:  # already slim
                        added, modified, deleted = [], [], []
                        for f in sorted((arm / "files").rglob("*")) if (arm / "files").exists() else []:
                            if f.is_file():
                                zf.write(f, f"{base}/files/{f.relative_to(arm / 'files').as_posix()}")
                                count += 1
                        if (arm / "changes.txt").exists():
                            zf.write(arm / "changes.txt", f"{base}/changes.txt")
                            count += 1
                        continue
                    for rel in added + modified:
                        zf.write(folder / rel, f"{base}/files/{rel}")
                        count += 1
                    zf.writestr(f"{base}/changes.txt",
                                "added:\n" + "".join(f"  {f}\n" for f in added)
                                + "modified:\n" + "".join(f"  {f}\n" for f in modified)
                                + "deleted:\n" + "".join(f"  {f}\n" for f in deleted))
                    count += 1
    with zipfile.ZipFile(out) as zf:
        bad = zf.testzip()
    print(f"wrote {out} ({out.stat().st_size / 1e6:.1f} MB, {count} files, integrity {'ok' if bad is None else 'FAILED: ' + bad})")


if __name__ == "__main__":
    main()
