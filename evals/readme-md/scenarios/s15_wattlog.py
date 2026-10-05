"""Scenario s15: Python CLI 'wattlog'; a fresh README drafted in drafts/ beside the existing one (create mode)."""
from fixture import w, git_init

ROOT = "s15-wattlog"


def build(base):
    r = base / ROOT
    w(r / "pyproject.toml", '''\
[build-system]
requires = ["hatchling>=1.24"]
build-backend = "hatchling.build"

[project]
name = "wattlog"
version = "0.3.0"
description = "Summarise energy-meter CSV exports: total kWh and peak demand per day or per month."
readme = "README.md"
requires-python = ">=3.10"
license = "MIT"
dependencies = []

[project.scripts]
wattlog = "wattlog.cli:main"

[project.urls]
Source = "https://github.com/example-org/wattlog"

[tool.hatch.build.targets.wheel]
packages = ["src/wattlog"]
''')
    w(r / "src/wattlog/__init__.py", '"""Summarise energy-meter CSV exports."""\n\n__version__ = "0.3.0"\n')
    w(r / "src/wattlog/__main__.py", "from .cli import main\n\nraise SystemExit(main())\n")
    w(r / "src/wattlog/core.py", '''\
"""Read interval readings from a meter export and summarise them per day or per month."""
import csv
import math
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Iterable

# Meter exports give local time without a UTC offset: 2024-01-30T18:00:00 (seconds optional).
TIMESTAMP = re.compile(r"(\\d{4})-(\\d{2})-(\\d{2})[T ](\\d{2}):(\\d{2})(?::(\\d{2}))?")
# Every reading is assumed to cover 15 minutes, so kWh x 4 is the average power in kW.
INTERVALS_PER_HOUR = 4


class InputError(Exception):
    """The export cannot be summarised."""


@dataclass
class Summary:
    period: str  # 2024-01-30 for a day, 2024-01 for a month
    kwh: float  # total energy in the period
    peak_kw: float  # highest reading of the period, as average power
    peak_at: datetime  # start of that reading


def parse_timestamp(text: str) -> datetime | None:
    m = TIMESTAMP.fullmatch(text.strip())
    if not m:
        return None
    try:
        return datetime(*(int(part) for part in m.groups(default="0")))
    except ValueError:  # 2024-02-30 or 25:00
        return None


def read_readings(lines: Iterable[str]) -> tuple[list[tuple[datetime, float]], int]:
    """Return the readings and the number of rows skipped because their kwh was empty."""
    reader = csv.DictReader(lines)
    readings, skipped = [], 0
    try:
        missing = {"timestamp", "kwh"} - set(reader.fieldnames or [])
        if missing:
            raise InputError("missing column: " + ", ".join(sorted(missing)))
        for row in reader:
            when = parse_timestamp(row["timestamp"] or "")
            if when is None:
                raise InputError(f"line {reader.line_num}: bad timestamp {row['timestamp']!r}")
            raw = (row["kwh"] or "").strip()
            if not raw:
                skipped += 1
                continue
            try:
                kwh = float(raw)
            except ValueError:
                kwh = math.nan
            if not math.isfinite(kwh) or kwh < 0:
                raise InputError(f"line {reader.line_num}: bad kwh value {raw!r}")
            readings.append((when, kwh))
    except csv.Error as exc:
        raise InputError(f"line {reader.line_num}: {exc}") from None
    if not readings:
        raise InputError("no readings")
    return readings, skipped


def summarise(readings: list[tuple[datetime, float]], by: str) -> list[Summary]:
    """One Summary per day or per month, in date order."""
    width = 10 if by == "day" else 7  # 2024-01-30 or 2024-01
    periods: dict[str, Summary] = {}
    for when, kwh in readings:
        key = when.isoformat()[:width]
        kw = kwh * INTERVALS_PER_HOUR
        found = periods.get(key)
        if found is None:
            periods[key] = Summary(key, kwh, kw, when)
            continue
        found.kwh += kwh
        if kw > found.peak_kw:  # on a tie, the reading that comes first in the file stays
            found.peak_kw, found.peak_at = kw, when
    return [periods[key] for key in sorted(periods)]
''')
    w(r / "src/wattlog/cli.py", '''\
"""Command-line interface for wattlog."""
import argparse
import csv
import sys

from . import __version__
from .core import InputError, read_readings, summarise


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="wattlog",
        description="Summarise an energy-meter CSV export: total kWh, peak demand in kW, "
                    "and when the peak occurred, per day or per month.")
    p.add_argument("file", metavar="FILE",
                   help="CSV export with timestamp and kwh columns; - reads standard input")
    p.add_argument("--by", choices=["day", "month"], default="day",
                   help="summarise per day or per month (default: day)")
    p.add_argument("--format", choices=["table", "csv"], default="table",
                   help="output format (default: table)")
    p.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    name = "standard input" if args.file == "-" else args.file
    try:
        if args.file == "-":
            readings, skipped = read_readings(sys.stdin)
        else:
            with open(args.file, newline="", encoding="utf-8-sig") as f:
                readings, skipped = read_readings(f)
    except OSError as exc:
        print(f"wattlog: {name}: {exc.strerror}", file=sys.stderr)
        return 2
    except UnicodeDecodeError:
        print(f"wattlog: {name}: not UTF-8 text", file=sys.stderr)
        return 2
    except InputError as exc:
        print(f"wattlog: {name}: {exc}", file=sys.stderr)
        return 2
    # The peak of a day needs only the time; the peak of a month needs the date too.
    peak_format = "%H:%M" if args.by == "day" else "%Y-%m-%d %H:%M"
    rows = [(s.period, f"{s.kwh:.2f}", f"{s.peak_kw:.2f}", s.peak_at.strftime(peak_format))
            for s in summarise(readings, args.by)]
    if args.format == "csv":
        out = csv.writer(sys.stdout, lineterminator="\\n")
        out.writerow([args.by, "kwh", "peak_kw", "peak_at"])
        out.writerows(rows)
    else:
        print(f"{args.by:<10}  {'kwh':>8}  {'peak_kw':>7}  peak_at")
        for period, kwh, peak_kw, peak_at in rows:
            print(f"{period:<10}  {kwh:>8}  {peak_kw:>7}  {peak_at}")
    if skipped:
        rows_word = "row" if skipped == 1 else "rows"
        print(f"wattlog: skipped {skipped} {rows_word} with an empty kwh value", file=sys.stderr)
    return 0
''')
    w(r / "examples/meter.csv", '''\
timestamp,kwh
2024-01-30T18:00:00,0.31
2024-01-30T18:15:00,0.42
2024-01-30T18:30:00,0.58
2024-01-30T18:45:00,0.85
2024-01-30T19:00:00,0.77
2024-01-30T19:15:00,0.64
2024-01-30T19:30:00,0.40
2024-01-30T19:45:00,0.35
2024-01-31T18:00:00,0.29
2024-01-31T18:15:00,
2024-01-31T18:30:00,0.61
2024-01-31T18:45:00,0.72
2024-01-31T19:00:00,0.93
2024-01-31T19:15:00,0.88
2024-01-31T19:30:00,0.47
2024-01-31T19:45:00,0.33
2024-02-01T18:00:00,0.36
2024-02-01T18:15:00,0.44
2024-02-01T18:30:00,0.52
2024-02-01T18:45:00,0.66
2024-02-01T19:00:00,0.66
2024-02-01T19:15:00,0.59
2024-02-01T19:30:00,0.41
2024-02-01T19:45:00,0.30
''')
    w(r / "tests/test_cli.py", '''\
"""The output for examples/meter.csv, recorded character by character.

Run with: python tests/test_cli.py
"""
import contextlib
import io
from pathlib import Path

from wattlog.cli import main

SAMPLE = str(Path(__file__).resolve().parent.parent / "examples" / "meter.csv")

BY_DAY = """\\
day              kwh  peak_kw  peak_at
2024-01-30      4.32     3.40  18:45
2024-01-31      4.23     3.72  19:00
2024-02-01      3.94     2.64  18:45
"""

BY_MONTH_CSV = """\\
month,kwh,peak_kw,peak_at
2024-01,8.55,3.72,2024-01-31 19:00
2024-02,3.94,2.64,2024-02-01 18:45
"""

SKIPPED = "wattlog: skipped 1 row with an empty kwh value\\n"


def run(*options):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = main([*options, SAMPLE])
    return code, out.getvalue(), err.getvalue()


def test_table_by_day():
    assert run() == (0, BY_DAY, SKIPPED)


def test_csv_by_month():
    assert run("--by", "month", "--format", "csv") == (0, BY_MONTH_CSV, SKIPPED)


if __name__ == "__main__":
    test_table_by_day()
    test_csv_by_month()
    print("2 tests passed")
''')
    w(r / "docs/csv-format.md", '''\
# CSV input format

wattlog reads the interval export that smart-meter portals offer: one row per
15-minute interval.

## Columns

| Column | Content |
| --- | --- |
| `timestamp` | Start of the interval in ISO 8601 local time, such as `2024-01-30T18:00:00` |
| `kwh` | Energy used during the interval, in kWh, with a decimal point |

The first row must be a header that names both columns in lowercase. Their
order does not matter, and other columns are ignored. Fields are separated by
commas; a semicolon-separated export is rejected because its header does not
name the columns.

Seconds are optional, and a space may replace the `T`: `2024-01-30 18:00` is
the same interval.

## Local time

Timestamps are used as written. wattlog does not convert time zones, so a day
is a calendar day on the meter's clock. A timestamp with a UTC offset or a
trailing `Z` is rejected. On the days the clocks change, the export has 92 or
100 intervals; wattlog adds up whatever the file contains.

## The 15-minute assumption

Peak demand is the highest `kwh` value of the period multiplied by 4, which
is the average power in kW during a 15-minute interval. wattlog does not check
the spacing of the rows. With 30-minute or hourly data the totals are still
correct, but the peak is 2 or 4 times too high.

When two intervals share the highest value, the one that comes first in the
file is reported.

## Gaps

- A row with an empty `kwh` is skipped. wattlog counts these rows and reports
  the count on standard error, for example
  `wattlog: skipped 1 row with an empty kwh value`.
- Missing rows are not estimated. A total is the sum of the rows that are
  present, so a day with gaps has a lower total.
- A timestamp that cannot be read, or a `kwh` that is not a number of zero or
  more, stops the run with an error that names the line (exit code 2).

`examples/meter.csv` is an excerpt: it holds only 18:00 to 19:45 on three
days, with one empty reading, so its totals cover two hours a day.
''')
    w(r / "CONTRIBUTING.md", '''\
# Contributing

Bug reports and pull requests are welcome at
https://github.com/example-org/wattlog.

## Set up

```bash
git clone https://github.com/example-org/wattlog
cd wattlog
python -m pip install -e .
```

## Run the tests

```bash
python tests/test_cli.py
```

The tests are plain `assert` statements and need no test runner. They compare
the output for `examples/meter.csv` character by character: update the
recorded output when you change the format on purpose.

## Code style

- Standard library only. wattlog has no dependencies, and that is a feature.
- Follow PEP 8, with lines up to 100 characters.
- Add type hints to new functions.
- Add a line to `CHANGELOG.md` for every change a user can see.
''')
    w(r / "CHANGELOG.md", '''\
# Changelog

## 0.3.0 - 2024-06-10

- Replace `--daily` and `--monthly` with `--by day` and `--by month`. The old
  flags are removed; `--by day` is the default.
- Raise the minimum Python version from 3.8 to 3.10.

## 0.2.0 - 2024-03-18

- Add `--monthly` and `--format csv`.
- Skip rows with an empty `kwh` value and report how many were skipped.

## 0.1.0 - 2024-01-22

- First release: `--daily` totals and peak demand.
''')
    w(r / "LICENSE", "MIT License\n\nCopyright (c) 2024 Example Org\n\n[Full MIT text omitted in this fixture.]\n")
    # The README the owner wants to compare against: mostly right, with a removed flag and an old Python minimum.
    w(r / "README.md", '''\
# wattlog

Summarise an energy-meter CSV export: total kWh and peak demand per day or
per month.

## Install

Python 3.8 or later.

```
pip install git+https://github.com/example-org/wattlog
```

## Usage

```
wattlog --daily meter.csv
```

Prints one row per day with the total kWh, the peak demand in kW, and the
time of the peak. Pass `-` instead of a file to read standard input.

The input is a CSV file with `timestamp` and `kwh` columns. See
[docs/csv-format.md](docs/csv-format.md) for the details.

## License

MIT. See [LICENSE](LICENSE).
''')
    w(r / ".gitignore", "__pycache__/\n*.egg-info/\n.venv/\ndist/\n")
    git_init(r, remote="https://github.com/example-org/wattlog.git", tag="v0.3.0")
