# Fact sheet: s1-logslice

Request: "Write a README for this project." (create mode; no README exists)
Role: project overview for a command-line tool.
Kind: CLI tool (Python). Reader: developers/operators who need to cut log files by time.

## Ground truth

- Package `logslice` 0.4.1; console command is **`lslice`** (not `logslice`). `python -m logslice` also works.
- Python **>= 3.10**; **no runtime dependencies**. Optional extra **`zstd`** (zstandard) needed only for `.zst` input, installed from a checkout or Git (for example `pip install '.[zstd]'` or `pip install 'logslice[zstd] @ git+https://github.com/example-org/logslice'`); `dev` extra = pytest + ruff. The code's own hint (`cli.py`, `core.py`) says `pip install 'logslice[zstd]'`, which assumes a PyPI release.
- Inputs: files (`.log`/plain, `.gz`, `.zst`) or stdin (`-` or no file).
- Flags: `--from TIME` (inclusive), `--to TIME` (exclusive); TIME = ISO 8601 or relative to now (`-15m`, `-2h`, `-1d`, also `s`); `--format {auto,iso,jsonl,nginx,syslog}` (default auto); `--tz` (default `$LOGSLICE_TZ`, else UTC; applies to timestamps without offset); `--count`; `--version`.
- Exit codes: 0 when lines matched, 1 when none matched, 2 on errors (bad range, unreadable file, missing zstd extra).
- Core mechanism: plain seekable files use **binary search over byte offsets** (reads only a few blocks before the first match); **compressed files and stdin are scanned linearly**. Input must be **sorted by time**. Lines without timestamps (e.g., stack-trace continuation lines) stay with the preceding timestamped line.
- jsonl looks for keys `ts`, `time`, or `timestamp`. syslog (RFC 3164) has no year: current year assumed.
- Example file `examples/nginx-access.log` exists; `lslice --from 2024-05-01T10:00 --to 2024-05-01T10:05 examples/nginx-access.log` prints 4 lines (`--count` prints 4).
- Dev: `make test` (= `python -m pytest -q`), `make lint` (`ruff check src tests`); CI tests Python 3.10/3.11/3.12 on ubuntu-latest and macos-latest (GitHub Actions workflow `ci.yml`).
- License **Apache-2.0** (LICENSE + pyproject). Repo URL https://github.com/example-org/logslice (from pyproject and git remote). Latest tag v0.4.1. CHANGELOG.md exists.
- No evidence the package is published on PyPI (no publish workflow, no badge, no docs). Installing from source/Git (`pip install .`, `pipx install git+https://github.com/example-org/logslice`, or similar) is supported by evidence.

## Core points a strong README highlights

1. What: cut/slice log lines between two times (absolute or relative).
2. Why: fast on huge files without reading them end to end (binary search) - with the honest caveat that compressed input/stdin is scanned linearly and input must be time-sorted.
3. Formats supported + auto-detect; gz/zst/stdin; `--count`.
4. Quick start with the real command `lslice` and the bundled example.

## Traps (judge explicitly)

- `python -m logslice` or `PYTHONPATH=src` documented as usage from a checkout without an install -> minor: it works only in the eval session, whose PYTHONPATH lists `src`. After `pip install .` it is correct.
- Calling the command `logslice` instead of `lslice` -> major.
- A PyPI install of the package with no clear caveat in the README that it is not published, such as `pip install logslice`, `python -m pip install logslice`, `pipx install logslice`, `uv tool install logslice`, or `pip install 'logslice[zstd]'` -> major when it is the install path (not evidenced; the name may belong to someone else on PyPI). Count minor instead when only the notes flag it as unverified, or when it appears only for the optional `zstd` extra. A local `pip install '.[zstd]'` or a Git URL install is correct.
- Claiming binary search / speed applies to `.gz`/`.zst`/stdin -> major.
- Wrong Python minimum, wrong license, invented flags/options, invented badges (PyPI version/downloads/coverage) -> major each.
- Claiming `--to` is inclusive or `--from` exclusive -> minor.
- Invented performance numbers ("10 GB in 2 seconds") -> major.
- Windows support claims: CI covers only Ubuntu and macOS (not Windows) -> minor if stated as tested.

## Judge notes

- Run the documented commands from the sandbox root, where `scenario/src` is on the Python path: `python -m logslice ... scenario/examples/nginx-access.log` stands in for `lslice`.
- Relative times written with a space (`--from -15m`) fail on at least Python 3.9-3.12 argparse ("expected one argument"); Python 3.14 accepts them, and `--from=-15m` works everywhere. Judge against the 3.10 minimum: count the space form as one minor error per outcome, and do not accept a writer's successful local run on 3.14 as proof.
- A malformed time or unknown `--tz` crashes with a traceback and exit code 1, not 2.
- On Windows without the `tzdata` package, any `--tz` or `LOGSLICE_TZ` other than UTC raises `ZoneInfoNotFoundError`, because the package declares no dependencies. This is an environment limit, not a README error; a README that notes it is an optional deep catch. Judging on Windows, skip such commands: a session cannot set environment variables such as `PYTHONTZPATH`.
