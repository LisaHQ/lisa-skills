"""Scenario s11: Python CLI 'csvdelta' with a stale English README and a stale README.vi.md;
the request is in Vietnamese (improve mode, language precedence, translations, broken links)."""
from fixture import w, git_init

ROOT = "s11-csvdelta"


def build(base):
    r = base / ROOT
    w(r / "pyproject.toml", '''\
[build-system]
requires = ["hatchling>=1.24"]
build-backend = "hatchling.build"

[project]
name = "csvdelta"
version = "2.0.0"
description = "Compare two CSV files by a key column and report added, removed, and changed rows."
readme = "README.md"
requires-python = ">=3.10"
license = "MIT"
dependencies = []

[project.scripts]
csvdelta = "csvdelta.cli:main"

[project.urls]
Source = "https://github.com/example-org/csvdelta"

[tool.hatch.build.targets.wheel]
packages = ["src/csvdelta"]
''')
    w(r / "src/csvdelta/__init__.py", '"""Compare CSV files by key."""\n\n__version__ = "2.0.0"\n')
    w(r / "src/csvdelta/__main__.py", "from .cli import main\n\nraise SystemExit(main())\n")
    w(r / "src/csvdelta/cli.py", '''\
"""Command-line interface for csvdelta."""
from __future__ import annotations

import argparse
import csv
import json
import sys

from . import __version__


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="csvdelta", allow_abbrev=False,
        description="Compare two CSV files by a key column.")
    p.add_argument("old", help="the earlier CSV file")
    p.add_argument("new", help="the later CSV file")
    p.add_argument("-k", "--key", required=True, help="column that identifies a row")
    p.add_argument("-d", "--delimiter", default=",", help="field delimiter (default: ,)")
    p.add_argument("-f", "--format", choices=["table", "json", "csv"], default="table",
                   help="output format (default: table)")
    p.add_argument("-o", "--output", metavar="FILE", help="write the report to FILE instead of stdout")
    p.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    return p


def load(path: str, key: str, delimiter: str) -> dict[str, dict[str, str]]:
    with open(path, newline="", encoding="utf-8-sig") as f:
        return {row[key]: row for row in csv.DictReader(f, delimiter=delimiter)}


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        old, new = load(args.old, args.key, args.delimiter), load(args.new, args.key, args.delimiter)
    except (OSError, KeyError) as exc:
        print(f"csvdelta: {exc}", file=sys.stderr)
        return 2
    report = []
    for k in sorted(old.keys() - new.keys()):
        report.append({"change": "removed", "key": k})
    for k in sorted(new.keys() - old.keys()):
        report.append({"change": "added", "key": k})
    for k in sorted(old.keys() & new.keys()):
        cols = sorted(c for c in new[k] if old[k].get(c) != new[k][c])
        if cols:
            report.append({"change": "changed", "key": k, "columns": ",".join(cols)})
    out = open(args.output, "w", encoding="utf-8", newline="") if args.output else sys.stdout
    try:
        if args.format == "json":
            json.dump(report, out, indent=2)
            out.write("\\n")
        elif args.format == "csv":
            writer = csv.DictWriter(out, fieldnames=["change", "key", "columns"])
            writer.writeheader()
            writer.writerows(report)
        else:
            for item in report:
                out.write(f"{item['change']:8} {item['key']} {item.get('columns', '')}".rstrip() + "\\n")
    finally:
        if out is not sys.stdout:
            out.close()
    return 1 if report else 0
''')
    w(r / "examples/products-v1.csv", "sku,name,price\nA1,Pen,1.20\nA2,Notebook,3.50\nA3,Stapler,7.00\n")
    w(r / "examples/products-v2.csv", "sku,name,price\nA1,Pen,1.25\nA3,Stapler,7.00\nA4,Ruler,0.90\n")
    w(r / "docs/configuration.md", '''\
# Configuration

`csvdelta` reads no configuration file. Every option is a command-line flag;
run `csvdelta --help` for the full list.

| Flag | Default | Meaning |
| --- | --- | --- |
| `-k`, `--key` | required | Column that identifies a row |
| `-d`, `--delimiter` | `,` | Field delimiter |
| `-f`, `--format` | `table` | `table`, `json`, or `csv` |
| `-o`, `--output` | stdout | Write the report to a file |
''')
    w(r / "docs/cookbook.md", '''\
# Cookbook

Compare semicolon-separated exports from the ERP:

```bash
csvdelta --key sku --sep ";" old.csv new.csv
```
''')
    w(r / "CHANGELOG.md", '''\
# Changelog

## 2.0.0 - 2024-05-20

### Breaking changes

- Rename `--out` to `--output` and `--sep` to `--delimiter`. Abbreviated flags are no longer accepted.
- Move `docs/config.md` to `docs/configuration.md`.

### Added

- `--format json` and `--format csv`.

## 1.3.0 - 2024-01-08

- Add `--sep` for semicolon-separated files.
''')
    w(r / "LICENSE", "MIT License\n\nCopyright (c) 2024 Example Org\n\n[Full MIT text omitted in this fixture.]\n")
    w(r / "README.md", '''\
# csvdelta

Compare two CSV files by a key column and see which rows were added, removed,
or changed.

[Tiếng Việt](README.vi.md)

## Install

Requires Python 3.10 or later.

```bash
pipx install git+https://github.com/example-org/csvdelta
```

## Usage

```bash
csvdelta --key sku --out report.txt old.csv new.csv
```

Use `--sep ";"` for semicolon-separated files. See the
[configuration guide](docs/config.md) for every option and the
[exit codes](#exit-status) for scripting.

## Exit codes

| Code | Meaning |
| --- | --- |
| `0` | The files have the same rows |
| `1` | At least one row was added, removed, or changed |
| `2` | A file could not be read or the key column is missing |

## License

MIT. See [LICENSE](LICENSE).
''')
    w(r / "README.vi.md", '''\
# csvdelta

So sánh hai tệp CSV theo một cột khóa và xem dòng nào được thêm, bị xóa hoặc
bị thay đổi.

[English](README.md)

## Cài đặt

Cần Python 3.10 trở lên.

```bash
pipx install git+https://github.com/example-org/csvdelta
```

## Cách dùng

```bash
csvdelta --key sku --out report.txt old.csv new.csv
```

Dùng `--sep ";"` cho tệp phân tách bằng dấu chấm phẩy. Xem
[hướng dẫn cấu hình](docs/config.md) để biết mọi tùy chọn.

## Mã thoát

| Mã | Ý nghĩa |
| --- | --- |
| `0` | Hai tệp có cùng các dòng |
| `1` | Có ít nhất một dòng được thêm, bị xóa hoặc bị thay đổi |
| `2` | Không đọc được tệp hoặc thiếu cột khóa |

## Giấy phép

MIT. Xem [LICENSE](LICENSE).
''')
    w(r / ".gitignore", "__pycache__/\n*.egg-info/\n.venv/\ndist/\n")
    git_init(r, remote="https://github.com/example-org/csvdelta.git", tag="v2.0.0")
