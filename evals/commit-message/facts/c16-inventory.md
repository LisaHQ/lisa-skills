# Fact sheet: c16-inventory

Request: "Write a commit message for my changes." Default `auto`, priority
working-tree → staged → unstaged. The repository has no commits yet.

## Repository state

```text
A  .gitignore                  staged: .venv/, __pycache__/, *.log
AM pyproject.toml              staged with requires-python ">=3.8"; unstaged on top: ">=3.10"
A  src/inventory/__init__.py   staged: docstring and __version__ = "0.1.0"
?? README.md                   untracked: says the package requires Python 3.10+
?? src/inventory/py.typed      untracked, empty marker file
?? tests/                      tests/test_version.py: checks __version__ == "0.1.0"
!! debug.log                   ignored (*.log)
```

HEAD does not exist: `git rev-parse HEAD` and `git diff HEAD` fail with
"ambiguous argument 'HEAD'", while `git status`, `git diff --cached`, and
`git diff` work.

## Correct selection

Every view compares against an empty baseline. The working-tree view selects
all six paths as additions; `pyproject.toml` appears once, at its final
`>=3.10`. The empty `py.typed` is still an addition. The ignored `debug.log`
is excluded.

## Net change

Initial scaffolding of a typed `inventory` package (version 0.1.0) for
Python 3.10+, with a README, a version test, and an ignore file.

## Core points

1. One `chore` bullet for the initial scaffolding; nothing claims features the
   files do not implement.
2. The final `>=3.10`, not the staged `>=3.8`.
3. Report: no commits yet, so the comparison starts from an empty tree; all
   six paths selected as additions. Naming the ignored `debug.log` in the
   report is neutral.

Example of a strong message:

```text
Scaffold the inventory package

- chore: Set up the typed inventory package for Python 3.10+ with a README
  and a version test.
```

## Traps

- Reporting no changes, or that the changes cannot be compared → major.
- Describing only the staged files → major (README, tests, and `py.typed`
  are additions too).
- Python 3.8 or `>=3.8` in the message → major (staged-only value).
- `debug.log` in the message → major (ignored file).
- Typing the scaffold as feat with invented capabilities → C deduction and
  an A error for each invented capability.
- Leaving `py.typed` out of both the report and the message → minor.

## Judge notes

- Use `git status`, `git diff --cached`, `git diff`, and
  `git ls-files -o --exclude-standard`; `git ls-files -o` lists untracked
  files, including the empty `py.typed`.
- An attribution trailer such as `Co-Authored-By:` is neutral.
