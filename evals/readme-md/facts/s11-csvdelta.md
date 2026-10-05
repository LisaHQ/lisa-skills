# Fact sheet: s11-csvdelta

Request (Vietnamese): "README của công cụ này đã lỗi thời từ khi bọn mình lên bản 2.0 và đổi tên mấy cờ dòng lệnh. Cập nhật lại giúp mình nhé." ("This tool's README has been out of date since we moved to 2.0 and renamed some command-line flags. Please update it.") (improve mode; stale English `README.md` and stale `README.vi.md` exist)
Role: project overview for a command-line tool.
Kind: CLI tool (Python). Reader: people who compare CSV exports, in English (`README.md`) and Vietnamese (`README.vi.md`).

## Ground truth (v2.0.0)

- Package `csvdelta` 2.0.0 (pyproject, `__init__`, tag v2.0.0); Python **>= 3.10**; no runtime dependencies; MIT (LICENSE + pyproject). Console command `csvdelta` (`csvdelta.cli:main`); `python -m csvdelta` also works. Remote https://github.com/example-org/csvdelta.git. Install from Git (`pipx install git+https://github.com/example-org/csvdelta`); no evidence of a PyPI release.
- Usage: `csvdelta [-h] -k KEY [-d DELIMITER] [-f {table,json,csv}] [-o FILE] [--version] old new`.
  - `-k`/`--key` (required): the column that identifies a row.
  - `-d`/`--delimiter` (default `,`).
  - `-f`/`--format`: `table` (default), `json`, or `csv`.
  - `-o`/`--output FILE`: write the report to a file instead of stdout.
  - `--version` prints `csvdelta 2.0.0`.
- Abbreviated flags are rejected (`allow_abbrev=False`), so the v1 flags **`--out` and `--sep` fail** with "unrecognized arguments" and exit 2. There are no aliases.
- Output: removed rows, then added, then changed (each sorted by key). Table lines: `removed  A2`, `added    A4`, `changed  A1 price` (changed column names, comma-separated). `json` is a list of `{change, key[, columns]}`; `csv` has the header `change,key,columns`.
- Example (verified): `csvdelta --key sku examples/products-v1.csv examples/products-v2.csv` prints the three table lines above and exits 1.
- Exit codes: **0** same rows, **1** at least one row added, removed, or changed, **2** usage error, a missing or unreadable input path (`OSError`), or a key column missing from a file with rows (the message is terse, for example `csvdelta: 'id'`).
- Unhandled failures exit **1** with a traceback, the same code as "differences found": an input file that is not UTF-8 (`UnicodeDecodeError`, for example an ANSI or cp1258 export from Excel) and an `--output` path in a missing folder. A missing key column goes unnoticed (exit 0) when the files have only a header row.
- No configuration file: `docs/configuration.md` says so and lists the flags. `docs/cookbook.md` is stale (`--sep ";"`).
- CHANGELOG 2.0.0 (2024-05-20): `--out` -> `--output`, `--sep` -> `--delimiter`, abbreviations rejected, `docs/config.md` moved to `docs/configuration.md`, `--format json` and `csv` added. 1.3.0 added `--sep`.
- Pristine `README.md` (English, v1-era): links `[Tiếng Việt](README.vi.md)`; shows `--out report.txt` and `--sep ";"`; links `docs/config.md` (missing) and `#exit-status` (the heading is "Exit codes", anchor `#exit-codes`); its exit-code table is correct for the handled cases. `README.vi.md` has the same stale flags and the same broken `docs/config.md` link, in Vietnamese.

## Core points a strong result delivers

1. `README.md` stays in English, with the v2 flags and a real example (output and exit code).
2. The broken link and anchor are fixed (`docs/configuration.md`, `#exit-codes`).
3. `README.vi.md` is updated the same way in Vietnamese, or reported as stale.
4. A short upgrade note for 1.x users (renamed flags, no abbreviations) linking the CHANGELOG.
5. The report is in Vietnamese and flags `docs/cookbook.md` as stale.

## Traps (judge explicitly)

- `python -m csvdelta` or `PYTHONPATH=src` documented as usage from a checkout without an install -> minor: it works only in the eval session, whose PYTHONPATH lists `src`. After `pip install .` it is correct.
- `README.md` converted to Vietnamese, leaving no English README for `README.vi.md` to translate -> major (F).
- `--out` or `--sep` left as current usage in `README.md` -> major each.
- Claiming the old flags still work (aliases or abbreviations) -> major.
- Invented configuration file or option -> major. Wrong exit codes or output format -> major.
- `docs/config.md` link or `#exit-status` anchor left broken -> minor each (D).
- `README.vi.md` neither updated nor reported -> F minor. `README.vi.md` updated with old or wrong flags -> major.
- Report not in Vietnamese -> F minor.
- Copying all of `docs/configuration.md` into the README -> C penalty only.

## Judge notes

- The request is in Vietnamese but names no README language. `README.vi.md` already exists, so `README.md` stays English under either reading of "the requested language"; judge the report language separately. A Vietnamese `README.md` with the English text moved to a new file is not the language trap, but judge the churn under C and F.
- Run commands from the sandbox root, where `scenario/src` is on the Python path: `python -m csvdelta -k sku scenario/examples/products-v1.csv scenario/examples/products-v2.csv`. Abbreviated flags fail by design.
- Fixing `docs/cookbook.md` as well is acceptable when the report says so.
- Optional deep catch (not required): the unhandled failures above. Stating that a non-UTF-8 file exits 1 is correct, not a wrong exit code.
- Writers cannot ask questions; unknowns belong in the report.
