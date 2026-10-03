# Fact sheet: c5-ledger

Request: "Write a commit message for my changes." Default `auto`.

## Repository state

```text
R  ledger/export.py -> ledger/exporter.py       staged rename; option --out renamed --output (-o kept)
M  ledger/cli.py                                staged: imports exporter, uses args.output
R  tests/test_export.py -> tests/test_exporter.py   staged rename; imports ledger.exporter
 M README.md                                    unstaged: documents --output
```

History (`git log --oneline`), in Conventional Commits style:

```text
882a951 docs(readme): document ledger export
8b40430 feat(export): add the CSV export command
```

The `export` subcommand's parser sets `allow_abbrev=False` in both HEAD and
the working tree, so argparse accepts no abbreviated long options.

## Correct selection

Working-tree view for all files; both renames keep their old/new pairing.

## Net change

- `ledger export --out FILE` no longer works; use `--output FILE` or `-o FILE`.
- The module `ledger.export` is now `ledger.exporter`; code importing the old
  module breaks.
- CSV output is unchanged.

## Core points

1. The rename in one bullet, or two (the option and the module); both are
   fine. `refactor`, `feat`, and `chore` are all acceptable types; `fix` is
   wrong. README and tests are folded in.
2. A `BREAKING CHANGE:` trailer with the migration: use `--output` or `-o`,
   and import from `ledger.exporter`.
3. A plain summary line, as for any other repository: the Conventional
   Commits history is not a format requirement. Noting the convention outside
   the message block is fine.
4. Report: auto (default), working tree; renames recognized as renames.

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
- Claiming the CSV format changed → major.
- Describing the renames as unrelated deletions and additions → minor.
- A typed summary copied from the history's style (for example
  `refactor(export)!: rename ...`) → E deduction; the message keeps its
  format unless the user states a requirement.
- A separate `docs:` or `test:` bullet for the README or the tests → C
  deduction.
- Typing the rename as fix → C deduction.

## Judge notes

- Verify on a copy: `python -c "from ledger import cli;
  cli.main(['export','--out','x.csv'])"` exits 2 ("the following arguments
  are required: -o/--output"), while `--output x.csv` and `-o x.csv` work. In
  HEAD, `--out x.csv` works.
- An attribution trailer such as `Co-Authored-By:` is neutral.
