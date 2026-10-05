# Fact sheet: s15-wattlog

Request: "Before I replace our README, I want to compare it with a fresh take. Write a new README for this project from scratch and save it as drafts/README.new.md. Leave README.md alone." (create mode beside an existing README; target: the README of the repository root, saved as `drafts/README.new.md`)
Role: project overview and entry point for a small public command-line tool. The draft is saved in drafts/ for comparison, but it is the README of the repository root and will be moved there.
Kind: CLI tool (Python). Reader: people with a smart-meter CSV export who want daily or monthly totals and peak demand; the owner, who will compare the draft with the current README.

## Ground truth

- Package `wattlog` 0.3.0 (pyproject, `__init__`, tag **v0.3.0**; one commit on `main`; remote https://github.com/example-org/wattlog.git). Python **>= 3.10** (`requires-python`; the code uses `X | None` annotations, which need 3.10). **No dependencies**. MIT (`LICENSE`, "Example Org", and pyproject). Console command `wattlog` (`wattlog.cli:main`); `python -m wattlog` works once the package is installed.
- **No CI** (no `.github/`) and **no evidence of a PyPI release**. Install from Git (`pip install git+https://github.com/example-org/wattlog`, as the current README says, or `pipx install git+...`) or from a checkout (`pip install .`).
- What it does: reads a meter export (CSV, one row per 15-minute interval, columns `timestamp` and `kwh`) and prints one row per day or per month: total kWh, peak demand in kW (the highest reading times 4), and when the peak occurred.
- Usage: `wattlog [-h] [--by {day,month}] [--format {table,csv}] [--version] FILE`. `--by` defaults to `day` and `--format` to `table`; `FILE` is a path or `-` for standard input; `--version` prints `wattlog 0.3.0`. There are no other options.
- Recorded output (`tests/test_cli.py`) of `wattlog examples/meter.csv`, exit 0:

  ```text
  day              kwh  peak_kw  peak_at
  2024-01-30      4.32     3.40  18:45
  2024-01-31      4.23     3.72  19:00
  2024-02-01      3.94     2.64  18:45
  ```

  Standard error also gets `wattlog: skipped 1 row with an empty kwh value`. `--by month --format csv` prints `month,kwh,peak_kw,peak_at`, `2024-01,8.55,3.72,2024-01-31 19:00`, and `2024-02,3.94,2.64,2024-02-01 18:45`. Values have two decimals; `peak_at` is `HH:MM` by day and `YYYY-MM-DD HH:MM` by month; rows are in date order.
- `examples/meter.csv`: a header and 24 rows, 18:00 to 19:45 on 2024-01-30, 2024-01-31, and 2024-02-01 (an excerpt, so the totals cover two hours a day). The 2024-01-31T18:15 row has an empty `kwh`. On 2024-02-01 the 18:45 and 19:00 readings tie at 0.66, so the peak is reported at 18:45.
- Input (`docs/csv-format.md`, verified): comma-separated, with a header that names `timestamp` and `kwh` in lowercase; other columns are ignored. Timestamps are local time, `YYYY-MM-DDTHH:MM[:SS]` (a space may replace the `T`), and are never converted; a UTC offset or `Z` is rejected. The peak assumes 15-minute intervals and the spacing is not checked (30-minute data doubles the peak). Rows with an empty `kwh` are skipped and counted on standard error; missing rows are not estimated; on a tie the first row in the file is the peak.
- Exit codes: **0** on success, also when rows were skipped; **2** on usage errors (argparse) and input errors: an unreadable file, a missing column, a malformed timestamp or `kwh` (the message names the line: `wattlog: FILE: line 3: bad timestamp '30/01/2024 18:15'`), no readings, or text that is not UTF-8.
- `CHANGELOG.md`: 0.3.0 (2024-06-10) replaced `--daily` and `--monthly` with `--by day` and `--by month` (the old flags are removed and fail with exit 2) and raised the minimum Python from 3.8 to 3.10. 0.2.0 added `--monthly`, `--format csv`, and the skipping of empty rows; 0.1.0 was the first release.
- `CONTRIBUTING.md`: `python -m pip install -e .`; tests with `python tests/test_cli.py` (plain asserts, prints `2 tests passed`); code style (standard library only, PEP 8 with 100-character lines, type hints, a changelog line for every visible change).
- Current `README.md` (28 lines): right about the purpose, the Git install, `-` for standard input, the two columns, MIT, and its links (`docs/csv-format.md`, `LICENSE`). **Stale**: `wattlog --daily meter.csv` and "Python 3.8 or later". It has no example output, options, exit codes, or links to `CONTRIBUTING.md` and `CHANGELOG.md`.
- Links: from the repository root the files are `LICENSE`, `docs/csv-format.md`, `CONTRIBUTING.md`, `CHANGELOG.md`, and `examples/meter.csv`. No `drafts/` folder exists yet. Written from `drafts/` they would be `../LICENSE` and so on, and those targets break once the file is moved to the root.

## Core points a strong result delivers

1. The draft is at `drafts/README.new.md`, `README.md` is unchanged, and nothing else is added or changed.
2. The draft reads as the root README: what wattlog does and for whom, the install from Git or a checkout with Python 3.10, and a first run on `examples/meter.csv` with the recorded output.
3. The options (`--by`, `--format`, `-` for standard input), the input format in brief with a link to `docs/csv-format.md`, and exit codes 0 and 2.
4. Links to `CONTRIBUTING.md` and `CHANGELOG.md`; MIT with a link to `LICENSE`.
5. Every relative link is written for the repository root, so it works once the file is moved.
6. Strengths, not required: the notes point out the two stale statements in the current README; a short upgrade note for 0.2 users.

## Traps (judge explicitly)

- Links or image paths written relative to `drafts/` (`../LICENSE`, `../docs/csv-format.md`), which break when the file is moved to the root -> major (D), counted once however many links there are.
- `README.md` modified, replaced, or deleted -> major (F).
- The draft saved somewhere else, or not written -> major (F).
- `--daily` or `--monthly` shown as current usage -> major. Python 3.8 stated as the minimum -> major.
- A PyPI install (`pip install wattlog`, `pipx install wattlog`) without a caveat that the package is not published -> major (not evidenced).
- Invented badges (CI, coverage, PyPI) -> major. A static license badge or Python-version badge is acceptable.
- Example output that differs from the recorded output -> major.
- `python -m wattlog` or a `PYTHONPATH=src` prefix presented as the way to use an uninstalled checkout -> minor: it works only where `src` is on the Python path, as in the eval session. After an install it is correct.
- Files created besides the draft -> F minor.

## Judge notes

- The draft is `outcomes/<label>/files/drafts/README.new.md`. Judge its links as if it were `scenario/README.md`: every relative target must exist under `scenario/` (`scenario/LICENSE`, `scenario/docs/csv-format.md`), and none may start with `../`. That the links do not resolve while the file sits in `drafts/` is expected, not an error, and a sentence in the notes saying so is neutral: neither a strength nor an error. Absolute `https://github.com/example-org/wattlog/blob/main/...` links work in both places and are acceptable.
- `changes.txt` should list `drafts/README.new.md` as added and nothing else.
- Run from the sandbox root, where `scenario/src` is on the Python path: `python -m wattlog scenario/examples/meter.csv` stands in for `wattlog examples/meter.csv`, and `python scenario/tests/test_cli.py` prints `2 tests passed`. Do not install anything, not through `python -m pip` either: `pip`, `pipx`, and the installed `wattlog` command are out of reach in the sandbox, so judge install commands against `pyproject.toml`.
- Acceptable either way: the example by day or by month, with or without the standard-error line, as long as the rows match; `pip` or `pipx` for the Git install; an upgrade note that names `--daily`, `--monthly`, or Python 3.8 as removed (correct, not the stale trap); one line or an HTML comment that marks the file as a draft (longer commentary on the comparison belongs in the notes: C).
- The fixture was verified on Python 3.14 only. The output, exit codes, and `wattlog:` messages do not depend on the version; the wording of argparse's own errors may, so judge those by their exit code.
- Writers cannot ask questions; unknowns belong in the notes.
