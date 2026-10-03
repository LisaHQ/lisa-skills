# Fact sheet: c11-meter

Request: "Write a commit message for my changes. Use auto scope with
auto-priority staged,unstaged,working-tree." Scope `auto` with a custom
priority: for each file, staged first, then unstaged, then working-tree.

## Repository state

```text
MM meter/serial_read.py   staged: ATTEMPTS = 3, a read loop that tries port.query up to 3 times before IOError;
                          unstaged on top: ATTEMPTS = 5 and a print("DEBUG reply", ...) inside the loop
MM config/meter.ini       staged: baud 9600 → 19200; unstaged: baud back to 9600 (same as HEAD)
M  docs/meter.md          staged only: "A register read is attempted up to three times before it fails."
 M meter/units.py         unstaged only: new kwh_to_mwh(kwh) = kwh / 1000
?? tests/                 tests/test_units.py: asserts kwh_to_mwh(2500) == 2.5
```

## Correct selection

Walk staged → unstaged → working-tree per file:

- `meter/serial_read.py`: staged view changed → select it (3 attempts). Its
  unstaged edits (5 attempts, the DEBUG print) are excluded.
- `config/meter.ini`: staged view changed → select it (baud 19200), even
  though the working tree reverts it. Owner decision: this is the literal
  reading of the walk; a non-empty higher-priority view wins.
- `docs/meter.md`: staged view changed → select it.
- `meter/units.py`: staged view empty → continue; unstaged view changed →
  select it.
- `tests/test_units.py`: not in the index, so the staged view is empty →
  continue; the unstaged view includes it as an untracked addition.

## Net change

- `read_register` tries the query up to 3 times (`ATTEMPTS = 3`) before
  raising `IOError`; the docs say so.
- The serial baud rate is 19200 instead of 9600.
- `kwh_to_mwh` converts kWh to MWh; a test covers it.

## Core points

1. Three independent goals: attempts on register reads (feat, docs folded
   in), the kWh-to-MWh conversion (feat, test folded in), and the baud rate
   (chore: a value-only change). A split recommendation is a plus.
2. Values from the selected views: 3 attempts and 19200 baud.
3. Report: auto with the custom priority; files grouped by view (staged:
   `serial_read.py`, `meter.ini`, `meter.md`; unstaged: `units.py` and the
   untracked test); `serial_read.py`'s unstaged edits excluded. The report
   need not say whether the mix was tested.

Example of a strong message:

```text
Add meter read attempts and a kWh-to-MWh conversion

- feat(meter): Attempt each register read up to 3 times before raising
  IOError.
- feat(units): Add a kWh-to-MWh conversion.
- chore(config): Raise the serial baud rate to 19200.
```

## Traps

- 5 attempts or the DEBUG print in the message → major (excluded unstaged
  view of `serial_read.py`).
- Omitting the 19200 baud rate, or calling it unchanged or reverted → major
  (the staged view is selected for `config/meter.ini`).
- Omitting `kwh_to_mwh` → major (`units.py` is selected from the unstaged view).
- Treating HEAD → working tree as the selection for every file → major.
- Claiming tests pass or that the selected mix was tested → major (invented).
- Leaving the untracked test out of the report, or calling it excluded → minor.
- Typing the attempts change as fix → C minor (no defect is established).
- Separate `docs:` or `test:` bullets → C deduction.

## Judge notes

- `git diff --cached` is the staged view (3 attempts, baud 19200, the docs
  line); `git diff` is the unstaged view (5 attempts, the DEBUG print, baud
  back to 9600, `kwh_to_mwh`). `git diff HEAD` is the working-tree view: it
  shows 5 attempts and omits `config/meter.ini`, so it is the wrong view for
  both files.
- An attribution trailer such as `Co-Authored-By:` is neutral.
