# Fact sheet: c14-pressline

Request: "Write a commit message for my changes." The project is an SVN
working copy at revision 2; default `auto` selects working-copy changes
against BASE.

## Repository state (`svn status`)

```text
M       src/report.py           adds export_csv(rows, path), imports write_rows from .csvout
?       src/csvout.py           unversioned: write_rows(path, header, rows) through csv.writer
 M      scripts/export.sh       property change only: svn:executable added
!       docs/press-codes.txt    missing: deleted from disk without `svn delete`
```

`press.log` is ignored by the `svn:ignore` property (`*.log`) on trunk.

## Correct selection

Working-copy changes against BASE: the text change in `src/report.py` and the
`svn:executable` property on `scripts/export.sh`.

Owner decision on the unversioned `src/csvout.py`; both readings are
acceptable:

- Include it as an addition and remind the user to `svn add` it before
  committing, or `report.py`'s import breaks.
- Exclude it, warning that `report.py` imports an unversioned module, so the
  commit would break without it.

Only silence about `src/csvout.py` is wrong. `docs/press-codes.txt` is
missing but not scheduled for deletion, so a commit would not delete it:
report it (`svn delete` it if intended, or restore it). `press.log` is
ignored.

## Net change

- `export_csv` writes the monthly report as CSV with a machine,parts header,
  using `csvout.write_rows`.
- `scripts/export.sh` becomes executable.

## Core points

1. A feat for the CSV export and a separate bullet (chore or build) for the
   executable bit.
2. The property change is a real change, though `svn diff` shows it only as
   "Property changes on: scripts/export.sh".
3. Report: auto (default), working copy against BASE; how `src/csvout.py` was
   treated and what to do about it; `docs/press-codes.txt` missing and
   unscheduled; `press.log` ignored.

Example of a strong message:

```text
Export the press report as CSV

- feat(report): Add `export_csv` to write the monthly report as CSV with a
  machine,parts header, using the new csvout module.
- chore(scripts): Mark scripts/export.sh executable.
```

## Traps

- Omitting the `svn:executable` change → major (tracked metadata).
- Silence about `src/csvout.py` (neither included with an `svn add` reminder
  nor excluded with a warning) → major.
- Including `src/csvout.py` without an `svn add` reminder → minor.
- `press.log` in the message → major (ignored file).
- Claiming, without comment, that the commit deletes `docs/press-codes.txt`
  → minor.
- Treating the project as Git, or saying SVN cannot select changes → major.
- Folding the executable bit into the CSV bullet → C deduction.

## Judge notes

- `svn status` shows all four states; `svn status --no-ignore` adds
  `I press.log`. `svn diff` shows `report.py` and the property change, but
  neither `csvout.py` nor the missing file. `svn proplist -v scripts/export.sh`
  shows `svn:executable`. All of these work offline in `scenario/`.
- The repository is read-only: a commit attempt fails without changing it.
- An attribution trailer such as `Co-Authored-By:` is neutral.
