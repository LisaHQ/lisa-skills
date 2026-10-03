# Fact sheet: c1-shipcalc

Request: "Write a commit message for my changes." No scope given, so the
default applies: `auto`, priority working-tree → staged → unstaged.

## Repository state

```text
MM shipcalc/rates.py        staged: express pricing with minimum surcharge 4.95; unstaged on top: minimum changed to 6.25
 M shipcalc/cli.py          unstaged only: new --express flag passed to quote()
 M README.md                unstaged only: documents `shipcalc 2.5 --express`
?? tests/test_express.py    untracked, not ignored: express tests expecting 11.95 and 42.75
```

## Correct selection

Working-tree view (HEAD → working tree) for all four files. `rates.py` appears
once with its staged and unstaged edits combined; the untracked test is an
addition. Nothing is excluded.

## Net change

- `quote(weight_kg, express=False)`: express delivery costs 1.5 × the standard
  price, and at least the standard price + 6.25 (`EXPRESS_MINIMUM_SURCHARGE`).
- `shipcalc --express` quotes express delivery; the README shows it.
- New tests cover the minimum-surcharge case and the multiplier case.

## Core points

1. One feat about express shipping, naming the 1.5× multiplier and the 6.25
   minimum surcharge (or describing them accurately) and the `--express` flag.
2. Tests and README folded into that bullet, not listed as separate changes.
3. Report: auto (default) with the priority; all four files from the working
   tree; `rates.py` combines staged and unstaged edits once.

Example of a strong message:

```text
Add express shipping option

- feat: Quote express delivery at 1.5x the standard price with a minimum
  surcharge of 6.25, and expose it as `shipcalc --express`.
```

## Traps

- The staged-only value 4.95 anywhere in the message → major (wrong view).
- Describing only the staged change (omitting the CLI flag, README, or tests
  as if excluded) → major.
- Claiming tests pass or were run without running them → major (invented).
- Separate `test:` or `docs:` bullets for the supporting files → C deduction.

## Judge notes

- `git diff --cached shipcalc/rates.py` shows 4.95; `git diff HEAD` shows 6.25.
  The untracked test appears only in `git status`; read it directly.
- An attribution trailer such as `Co-Authored-By:` is neutral.
