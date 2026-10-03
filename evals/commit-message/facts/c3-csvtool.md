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
```

## Correct selection

Working-tree view per file:

- `config/defaults.yaml`: HEAD → working tree is empty, so the file is
  omitted; the staged 45 must not be revived from a lower-priority view.
- `docs/old-guide.md`: the staged deletion and the identical untracked copy
  reconcile to no net change, so it is omitted. `git diff HEAD` alone lists
  the file as deleted because it ignores the untracked copy; that is the trap.
- `csvtool/parser.py` and `tests/test_parser.py`: selected.

## Net change

`parse_line` returns an empty list for blank or whitespace-only lines instead
of raising `ValueError("record has no key")`; a test covers it.

## Core points

1. One fix about blank lines in the parser, with the test folded in.
2. Report: auto (default); parser and test selected from the working tree;
   `config/defaults.yaml` and `docs/old-guide.md` omitted because their net
   changes cancel out.

Example of a strong message:

```text
Return no fields for blank lines

- fix(parser): Return an empty list for blank lines instead of raising
  "record has no key".
```

## Traps

- Mentioning the timeout change (45) → major (cancelled in the working tree).
- Mentioning the guide's deletion → major (net no change).
- Not reporting either omission → minor.
- Typing the parser change as feat or refactor → C deduction.
