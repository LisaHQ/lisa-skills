# Fact sheet: c3-csvtool

Request: "Can you write the commit message for what I've got here?" Default
`auto`, priority working-tree → staged → unstaged.

## Repository state

```text
MM config/defaults.yaml    staged: timeout 30 → 45; the working tree changed it back to 30 (same as HEAD)
D  docs/old-guide.md       staged deletion ...
?? docs/                   ... and the same file recreated, identical to HEAD (untracked)
 M csvtool/parser.py       unstaged: blank lines return [] instead of raising ValueError("record has no key")
 M tests/test_parser.py    unstaged: new test for blank lines
M  scripts/lint.sh         staged mode change only: 100644 → 100755 (executable); content unchanged
```

The repository sets `core.filemode=false`, so the index alone decides the
executable bit and the working file's own mode is ignored.

## Correct selection

Working-tree view per file:

- `config/defaults.yaml`: HEAD → working tree is empty, so the file is
  omitted; the staged 45 must not be revived from a lower-priority view.
- `docs/old-guide.md`: the staged deletion and the identical untracked copy
  reconcile to no net change, so it is omitted. `git diff HEAD` alone lists
  the file as deleted because it ignores the untracked copy; that is the trap.
- `scripts/lint.sh`: selected. The comparison is not empty, because tracked
  metadata (the file mode) differs from HEAD although the content does not.
- `csvtool/parser.py` and `tests/test_parser.py`: selected.

## Net change

- `parse_line` returns an empty list for blank or whitespace-only lines
  instead of raising `ValueError("record has no key")`; a test covers it.
- `scripts/lint.sh` becomes executable; its content is unchanged.

## Core points

1. One bullet about blank lines in the parser, with the test folded in. Type
   `fix` or `feat`: both are acceptable (owner decision), because the old
   error may have been intended.
2. A separate bullet for the mode change, typed `chore` or `build`: it is an
   independent goal. A split recommendation is a plus.
3. Report: auto (default); parser, test, and `scripts/lint.sh` selected from
   the working tree; `config/defaults.yaml` and `docs/old-guide.md` omitted
   because their net changes cancel out.

Example of a strong message:

```text
Return no fields for blank lines

- fix(parser): Return an empty list for blank lines instead of raising
  "record has no key".
- chore: Make scripts/lint.sh executable.
```

## Traps

- Mentioning the timeout change (45) → major (cancelled in the working tree).
- Mentioning the guide's deletion → major (net no change).
- Omitting `scripts/lint.sh` as unchanged, or treating its comparison as
  empty → major (a mode change is a tracked-metadata difference).
- Claiming `scripts/lint.sh`'s content changed → minor.
- Not reporting the timeout or guide omission → minor.
- Folding the mode change into the parser bullet → C deduction.
- Typing the parser change as refactor → C deduction (fix and feat are both
  accepted).

## Judge notes

- `git diff HEAD --stat` shows `scripts/lint.sh | 0`, and
  `git diff HEAD -- scripts/lint.sh` shows only `old mode 100644` /
  `new mode 100755`. `git diff` (unstaged) does not list the file.
- An attribution trailer such as `Co-Authored-By:` is neutral.
