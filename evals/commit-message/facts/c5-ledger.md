# Fact sheet: c5-ledger

Request: "Write a commit message for my changes." Default `auto`.

## Repository state

```text
R  ledger/export.py -> ledger/exporter.py       staged rename; option --out renamed --output (-o kept)
M  ledger/cli.py                                staged: imports exporter, uses args.output
R  tests/test_export.py -> tests/test_exporter.py   staged rename; imports ledger.exporter
 M README.md                                    unstaged: documents --output
```

## Correct selection

Working-tree view for all files; both renames keep their old/new pairing.

## Net change

- `ledger export --out FILE` no longer works; use `--output FILE` or `-o FILE`.
- The module `ledger.export` is now `ledger.exporter`; code importing the old
  module breaks.
- CSV output is unchanged.

## Core points

1. One bullet for the rename (refactor or feat are both defensible; fix is
   wrong), with README and tests folded in.
2. A `BREAKING CHANGE:` trailer with the migration: use `--output` or `-o`,
   and import from `ledger.exporter`.
3. Report: auto (default), working tree; renames recognized as renames.

Example of a strong message:

```text
Rename the export option to --output

- refactor(export): Rename the `--out` option to `--output` and the
  `ledger.export` module to `ledger.exporter`.

BREAKING CHANGE: `ledger export --out FILE` no longer works; use
`--output FILE` or `-o FILE`, and import from `ledger.exporter`.
```

## Traps

- No breaking-change note or migration → major.
- Claiming `--out` still works or is deprecated rather than removed → major.
- Describing the renames as unrelated deletions and additions → minor.
- Claiming the CSV format changed → major.
