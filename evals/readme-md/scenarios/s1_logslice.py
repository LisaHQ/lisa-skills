"""Scenario s1: Python CLI 'logslice' (create mode)."""
from fixture import w, git_init

ROOT = "s1-logslice"


def build(base):
    r = base / ROOT
    w(r / "pyproject.toml", '''\
[build-system]
requires = ["hatchling>=1.24"]
build-backend = "hatchling.build"

[project]
name = "logslice"
version = "0.4.1"
description = "Slice large, time-sorted log files by time range without reading them end to end."
readme = "README.md"
requires-python = ">=3.10"
license = "Apache-2.0"
authors = [{ name = "Example Labs", email = "dev@example.invalid" }]
classifiers = [
  "Programming Language :: Python :: 3",
  "Environment :: Console",
  "Topic :: System :: Logging",
]
dependencies = []

[project.optional-dependencies]
zstd = ["zstandard>=0.22"]
dev = ["pytest>=8", "ruff>=0.5"]

[project.scripts]
lslice = "logslice.cli:main"

[project.urls]
Source = "https://github.com/example-org/logslice"
Issues = "https://github.com/example-org/logslice/issues"

[tool.hatch.build.targets.wheel]
packages = ["src/logslice"]
''')
    w(r / "src/logslice/__init__.py", '''\
"""Slice time-sorted log files by time range."""

__version__ = "0.4.1"
''')
    w(r / "src/logslice/__main__.py", '''\
from .cli import main

raise SystemExit(main())
''')
    w(r / "src/logslice/cli.py", '''\
"""Command-line interface for logslice."""
from __future__ import annotations

import argparse
import os
import sys

from . import __version__
from .core import open_input, slice_lines
from .formats import FORMATS
from .timeparse import parse_bound


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="lslice",
        description="Print the lines of time-sorted log files that fall inside a time range.",
    )
    p.add_argument(
        "files", nargs="*", default=["-"], metavar="FILE",
        help="log files to read (.log, .gz, .zst); '-' or nothing reads standard input",
    )
    p.add_argument(
        "--from", dest="start", metavar="TIME",
        help="inclusive start: ISO 8601 (2024-05-01T10:00) or relative to now (-15m, -2h, -1d)",
    )
    p.add_argument(
        "--to", dest="end", metavar="TIME",
        help="exclusive end, same formats as --from",
    )
    p.add_argument(
        "--format", choices=sorted(FORMATS), default="auto",
        help="log line format (default: auto-detect)",
    )
    p.add_argument(
        "--tz", default=os.environ.get("LOGSLICE_TZ", "UTC"),
        help="time zone for timestamps without an offset (default: $LOGSLICE_TZ, else UTC)",
    )
    p.add_argument(
        "--count", action="store_true",
        help="print only the number of matching lines",
    )
    p.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    start = parse_bound(args.start, args.tz) if args.start else None
    end = parse_bound(args.end, args.tz) if args.end else None
    if start and end and start >= end:
        print("lslice: --from must be earlier than --to", file=sys.stderr)
        return 2
    total = 0
    for name in args.files:
        try:
            handle, seekable = open_input(name)
        except ModuleNotFoundError:
            print("lslice: reading .zst files needs the 'zstd' extra: pip install 'logslice[zstd]'",
                  file=sys.stderr)
            return 2
        except OSError as exc:
            print(f"lslice: {name}: {exc.strerror}", file=sys.stderr)
            return 2
        with handle:
            for line in slice_lines(handle, seekable, start, end, args.format, args.tz):
                total += 1
                if not args.count:
                    sys.stdout.write(line)
    if args.count:
        print(total)
    return 0 if total else 1
''')
    w(r / "src/logslice/core.py", '''\
"""Find the lines inside a time range.

Plain, seekable files are searched with a binary search over byte offsets, so
lslice reads only a few blocks before it reaches the first matching line, no
matter how large the file is. Compressed files (.gz, .zst) and standard input
cannot seek, so they are scanned line by line from the start.

Both strategies assume the input is sorted by time. Lines without a
recognizable timestamp (for example, stack-trace continuation lines) belong to
the closest preceding timestamped line.
"""
from __future__ import annotations

import gzip
import io
import sys
from datetime import datetime
from typing import IO, Iterator

from .formats import detect_format, extract_time

BLOCK = 64 * 1024


def open_input(name: str) -> tuple[IO[str], bool]:
    """Return a text handle and whether it supports binary search."""
    if name == "-":
        return sys.stdin, False
    if name.endswith(".gz"):
        return io.TextIOWrapper(gzip.open(name, "rb"), encoding="utf-8", errors="replace"), False
    if name.endswith(".zst"):
        import zstandard  # optional dependency: pip install 'logslice[zstd]'

        raw = open(name, "rb")
        reader = zstandard.ZstdDecompressor().stream_reader(raw)
        return io.TextIOWrapper(reader, encoding="utf-8", errors="replace"), False
    return open(name, "r", encoding="utf-8", errors="replace"), True


def slice_lines(handle, seekable: bool, start: datetime | None, end: datetime | None,
                fmt: str, tz: str) -> Iterator[str]:
    if seekable and start is not None:
        _seek_to(handle, start, fmt, tz)
    in_range = start is None
    for line in handle:
        ts = extract_time(line, fmt, tz)
        if ts is not None:
            if end is not None and ts >= end:
                return
            in_range = start is None or ts >= start
        if in_range:
            yield line


def _seek_to(handle, start: datetime, fmt: str, tz: str) -> None:
    """Binary-search byte offsets for the first block at or after start."""
    handle.seek(0, io.SEEK_END)
    lo, hi = 0, handle.tell()
    while hi - lo > BLOCK:
        mid = (lo + hi) // 2
        handle.seek(mid)
        handle.readline()  # skip the partial line
        ts = None
        while ts is None:
            line = handle.readline()
            if not line:
                break
            ts = extract_time(line, fmt, tz)
        if ts is None or ts >= start:
            hi = mid
        else:
            lo = mid
    handle.seek(lo)
    if lo:
        handle.readline()
''')
    w(r / "src/logslice/formats.py", '''\
"""Timestamp extraction for supported log formats."""
from __future__ import annotations

import json
import re
from datetime import datetime

from .timeparse import get_zone

FORMATS = {"auto", "iso", "nginx", "jsonl", "syslog"}

_ISO = re.compile(r"^(\\d{4}-\\d{2}-\\d{2}[T ]\\d{2}:\\d{2}:\\d{2}(?:\\.\\d+)?(?:Z|[+-]\\d{2}:?\\d{2})?)")
_NGINX = re.compile(r"\\[(\\d{2}/[A-Z][a-z]{2}/\\d{4}:\\d{2}:\\d{2}:\\d{2} [+-]\\d{4})\\]")
_SYSLOG = re.compile(r"^([A-Z][a-z]{2} [ \\d]\\d \\d{2}:\\d{2}:\\d{2})")
_JSON_KEYS = ("ts", "time", "timestamp")

_detected: dict[int, str] = {}


def detect_format(sample: list[str]) -> str:
    for name, rx in (("nginx", _NGINX), ("iso", _ISO), ("syslog", _SYSLOG)):
        hits = sum(bool(rx.search(s)) for s in sample)
        if hits and hits * 2 >= len(sample):
            return name
    if all(s.lstrip().startswith("{") for s in sample if s.strip()):
        return "jsonl"
    return "iso"


def _localize(dt: datetime, tz: str) -> datetime:
    return dt if dt.tzinfo else dt.replace(tzinfo=get_zone(tz))


def extract_time(line: str, fmt: str, tz: str) -> datetime | None:
    if fmt == "auto":
        fmt = _detected.setdefault(0, detect_format([line]))
    if fmt == "iso":
        m = _ISO.match(line)
        return _localize(datetime.fromisoformat(m.group(1).replace("Z", "+00:00")), tz) if m else None
    if fmt == "nginx":
        m = _NGINX.search(line)
        return datetime.strptime(m.group(1), "%d/%b/%Y:%H:%M:%S %z") if m else None
    if fmt == "syslog":
        m = _SYSLOG.match(line)
        if not m:
            return None
        # RFC 3164 timestamps carry no year; assume the current year.
        now = datetime.now(get_zone(tz))
        return datetime.strptime(f"{now.year} {m.group(1)}", "%Y %b %d %H:%M:%S").replace(tzinfo=get_zone(tz))
    if fmt == "jsonl":
        try:
            obj = json.loads(line)
        except ValueError:
            return None
        for key in _JSON_KEYS:
            if key in obj:
                return _localize(datetime.fromisoformat(str(obj[key]).replace("Z", "+00:00")), tz)
        return None
    raise ValueError(f"unknown format: {fmt}")
''')
    w(r / "src/logslice/timeparse.py", '''\
"""Parse --from/--to bounds."""
from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

_RELATIVE = re.compile(r"^-(\\d+)([smhd])$")
_UNITS = {"s": "seconds", "m": "minutes", "h": "hours", "d": "days"}


def get_zone(name: str):
    """Return the tzinfo for an IANA name; UTC needs no tz database."""
    return timezone.utc if name.upper() == "UTC" else ZoneInfo(name)


def parse_bound(text: str, tz: str) -> datetime:
    """Accept ISO 8601 timestamps or relative offsets such as -15m, -2h, -1d."""
    m = _RELATIVE.match(text.strip())
    if m:
        amount, unit = int(m.group(1)), _UNITS[m.group(2)]
        return datetime.now(get_zone(tz)) - timedelta(**{unit: amount})
    dt = datetime.fromisoformat(text.replace("Z", "+00:00"))
    return dt if dt.tzinfo else dt.replace(tzinfo=get_zone(tz))
''')
    w(r / "tests/test_timeparse.py", '''\
from datetime import datetime, timezone

from logslice.timeparse import parse_bound


def test_iso_with_offset():
    assert parse_bound("2024-05-01T10:00:00+00:00", "UTC") == datetime(2024, 5, 1, 10, tzinfo=timezone.utc)


def test_relative_hours_is_in_the_past():
    assert parse_bound("-2h", "UTC") < datetime.now(timezone.utc)
''')
    w(r / "tests/test_cli.py", '''\
from pathlib import Path

from logslice.cli import main

SAMPLE = Path(__file__).parent.parent / "examples" / "nginx-access.log"


def test_count_inside_window(capsys):
    code = main(["--from", "2024-05-01T10:00:00+00:00", "--to", "2024-05-01T10:05:00+00:00",
                 "--count", str(SAMPLE)])
    assert code == 0
    assert capsys.readouterr().out.strip() == "4"
''')
    w(r / "examples/nginx-access.log", '''\
203.0.113.10 - - [01/May/2024:09:58:12 +0000] "GET /health HTTP/1.1" 200 2 "-" "kube-probe/1.29"
203.0.113.24 - - [01/May/2024:09:59:47 +0000] "GET /api/orders HTTP/1.1" 200 5123 "-" "Mozilla/5.0"
198.51.100.7 - - [01/May/2024:10:00:03 +0000] "POST /api/orders HTTP/1.1" 201 87 "-" "curl/8.5.0"
203.0.113.24 - - [01/May/2024:10:01:15 +0000] "GET /api/orders/981 HTTP/1.1" 200 811 "-" "Mozilla/5.0"
203.0.113.10 - - [01/May/2024:10:02:12 +0000] "GET /health HTTP/1.1" 200 2 "-" "kube-probe/1.29"
198.51.100.7 - - [01/May/2024:10:04:59 +0000] "DELETE /api/orders/981 HTTP/1.1" 500 64 "-" "curl/8.5.0"
203.0.113.10 - - [01/May/2024:10:05:00 +0000] "GET /health HTTP/1.1" 200 2 "-" "kube-probe/1.29"
203.0.113.24 - - [01/May/2024:10:07:33 +0000] "GET /api/orders HTTP/1.1" 200 5119 "-" "Mozilla/5.0"
''')
    w(r / "Makefile", '''\
.PHONY: test lint

test:
\tpython -m pytest -q

lint:
\truff check src tests
''')
    w(r / ".github/workflows/ci.yml", '''\
name: CI

on:
  push:
    branches: [main]
  pull_request:

jobs:
  test:
    strategy:
      matrix:
        os: [ubuntu-latest, macos-latest]
        python: ["3.10", "3.11", "3.12"]
    runs-on: ${{ matrix.os }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python }}
      - run: pip install -e ".[dev,zstd]"
      - run: ruff check src tests
      - run: python -m pytest -q
''')
    w(r / "CHANGELOG.md", '''\
# Changelog

## 0.4.1 - 2024-06-12

- Fix relative times such as `-2h` so they respect `--tz`.

## 0.4.0 - 2024-05-20

- Add `--count` to print only the number of matching lines.
- Read `.zst` files through the optional `zstd` extra.

## 0.3.0 - 2024-03-02

- Add the `jsonl` format (keys `ts`, `time`, or `timestamp`).

## 0.2.0 - 2024-01-15

- Add binary search for plain files.
''')
    w(r / "LICENSE", '''\

                                 Apache License
                           Version 2.0, January 2004
                        http://www.apache.org/licenses/

   TERMS AND CONDITIONS FOR USE, REPRODUCTION, AND DISTRIBUTION

   1. Definitions.

      "License" shall mean the terms and conditions for use, reproduction,
      and distribution as defined by Sections 1 through 9 of this document.

   [Remaining sections of the Apache License 2.0 omitted in this fixture.]

   Copyright 2024 Example Labs

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
''')
    w(r / ".gitignore", "__pycache__/\n*.egg-info/\n.venv/\ndist/\n")
    git_init(r, remote="https://github.com/example-org/logslice.git", tag="v0.4.1")
