"""Git scenarios for the commit-message suite (c1-c9, c11-c13, c15, c16).

Each builder commits a small project (c16 commits nothing), then leaves a
precise mix of staged, unstaged, untracked, and ignored changes, and checks
the resulting `git status --porcelain` so a build fails loudly if the state
drifts.
"""
from fixture import commit_all, expect_status, git, w


def init(path, files: dict[str, str], message: str = "Initial import", remote: str | None = None):
    for rel, text in files.items():
        w(path / rel, text)
    git(path, "init", "-q", "-b", "main")
    commit_all(path, message)
    if remote:
        git(path, "remote", "add", "origin", remote)


# --------------------------------------------------------------------------- c1
RATES_BASE = '''\
"""Shipping rate calculation."""
from decimal import ROUND_HALF_UP, Decimal

BASE_RATE = Decimal("4.50")
PER_KG = Decimal("1.20")


def quote(weight_kg: float) -> Decimal:
    """Return the shipping price for a parcel, rounded to cents."""
    if weight_kg <= 0:
        raise ValueError("weight must be positive")
    price = BASE_RATE + PER_KG * Decimal(str(weight_kg))
    return price.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
'''

RATES_EXPRESS = '''\
"""Shipping rate calculation."""
from decimal import ROUND_HALF_UP, Decimal

BASE_RATE = Decimal("4.50")
PER_KG = Decimal("1.20")
EXPRESS_MULTIPLIER = Decimal("1.5")
EXPRESS_MINIMUM_SURCHARGE = Decimal("{minimum}")


def quote(weight_kg: float, express: bool = False) -> Decimal:
    """Return the shipping price for a parcel, rounded to cents.

    Express delivery multiplies the price, adding at least the minimum surcharge.
    """
    if weight_kg <= 0:
        raise ValueError("weight must be positive")
    price = BASE_RATE + PER_KG * Decimal(str(weight_kg))
    if express:
        price = max(price * EXPRESS_MULTIPLIER, price + EXPRESS_MINIMUM_SURCHARGE)
    return price.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
'''

CLI_BASE = '''\
"""Command-line entry point: shipcalc WEIGHT_KG"""
import argparse

from .rates import quote


def main(argv=None) -> None:
    parser = argparse.ArgumentParser(prog="shipcalc", description="Quote a parcel's shipping price.")
    parser.add_argument("weight", type=float, help="parcel weight in kilograms")
    args = parser.parse_args(argv)
    print(quote(args.weight))
'''

CLI_EXPRESS = '''\
"""Command-line entry point: shipcalc WEIGHT_KG [--express]"""
import argparse

from .rates import quote


def main(argv=None) -> None:
    parser = argparse.ArgumentParser(prog="shipcalc", description="Quote a parcel's shipping price.")
    parser.add_argument("weight", type=float, help="parcel weight in kilograms")
    parser.add_argument("--express", action="store_true", help="quote express delivery")
    args = parser.parse_args(argv)
    print(quote(args.weight, express=args.express))
'''


def build_c1(base):
    path = base / "c1-shipcalc"
    init(path, {
        "pyproject.toml": '[project]\nname = "shipcalc"\nversion = "1.2.0"\nrequires-python = ">=3.10"\n\n'
                          '[project.scripts]\nshipcalc = "shipcalc.cli:main"\n',
        "shipcalc/__init__.py": '__version__ = "1.2.0"\n',
        "shipcalc/rates.py": RATES_BASE,
        "shipcalc/cli.py": CLI_BASE,
        "tests/test_rates.py": 'from decimal import Decimal\n\nfrom shipcalc.rates import quote\n\n\n'
                               'def test_quote_two_kg():\n    assert quote(2) == Decimal("6.90")\n',
        "README.md": "# shipcalc\n\nQuote parcel shipping prices.\n\n```bash\nshipcalc 2.5\n```\n",
    })
    w(path / "shipcalc/rates.py", RATES_EXPRESS.format(minimum="4.95"))
    git(path, "add", "shipcalc/rates.py")
    w(path / "shipcalc/rates.py", RATES_EXPRESS.format(minimum="6.25"))
    w(path / "shipcalc/cli.py", CLI_EXPRESS)
    w(path / "README.md", "# shipcalc\n\nQuote parcel shipping prices.\n\n```bash\nshipcalc 2.5\n"
                          "shipcalc 2.5 --express   # express delivery\n```\n")
    w(path / "tests/test_express.py", 'from decimal import Decimal\n\nfrom shipcalc.rates import quote\n\n\n'
                                      'def test_express_small_parcel_pays_minimum_surcharge():\n'
                                      '    assert quote(1, express=True) == Decimal("11.95")\n\n\n'
                                      'def test_express_large_parcel_pays_multiplier():\n'
                                      '    assert quote(20, express=True) == Decimal("42.75")\n')
    expect_status(path, ["MM shipcalc/rates.py", " M shipcalc/cli.py", " M README.md",
                         "?? tests/test_express.py"])
    return path.name


# --------------------------------------------------------------------------- c2
NOTES_BASE = '''\
const express = require("express");
const store = require("../store");

const router = express.Router();

router.get("/notes", (req, res) => {
  res.json(store.all());
});

router.post("/notes", (req, res) => {
  const note = store.add(req.body.text);
  res.status(201).json(note);
});

module.exports = router;
'''

NOTES_STAGED = NOTES_BASE.replace('''module.exports = router;''', '''function getNoteById(req, res) {
  const note = store.get(Number(req.params.id));
  if (!note) return res.status(404).json({ error: "note not found" });
  res.json(note);
}

router.get("/notes/:id", getNoteById);

module.exports = router;''')

NOTES_UNSTAGED = NOTES_STAGED.replace("getNoteById", "findNote").replace('''module.exports = router;''', '''function removeNote(req, res) {
  const removed = store.remove(Number(req.params.id));
  res.status(removed ? 204 : 404).end();
}

router.delete("/notes/:id", removeNote);

module.exports = router;''')

STORE_BASE = '''\
const notes = [];
let nextId = 1;

function all() {
  return notes;
}

function add(text) {
  const note = { id: nextId++, text };
  notes.push(note);
  return note;
}

function get(id) {
  return notes.find((note) => note.id === id);
}

module.exports = { all, add, get };
'''


def build_c2(base):
    path = base / "c2-notes-api"
    init(path, {
        "package.json": '{\n  "name": "notes-api",\n  "version": "0.4.0",\n  "private": true,\n'
                        '  "scripts": { "start": "node src/server.js", "test": "node --test" },\n'
                        '  "dependencies": { "express": "^4.19.2" }\n}\n',
        "src/server.js": 'const express = require("express");\nconst notes = require("./routes/notes");\n\n'
                         'const app = express();\napp.use(express.json());\napp.use(notes);\n'
                         'app.listen(3000);\n',
        "src/routes/notes.js": NOTES_BASE,
        "src/store.js": STORE_BASE,
        "test/notes.test.js": 'const test = require("node:test");\nconst assert = require("node:assert");\n'
                              'const store = require("../src/store");\n\n'
                              'test("add assigns ids", () => {\n  assert.equal(store.add("a").id, 1);\n});\n',
    })
    w(path / "src/routes/notes.js", NOTES_STAGED)
    w(path / "test/notes.test.js", 'const test = require("node:test");\nconst assert = require("node:assert");\n'
                                   'const store = require("../src/store");\n\n'
                                   'test("add assigns ids", () => {\n  assert.equal(store.add("a").id, 1);\n});\n\n'
                                   'test("get finds a note by id", () => {\n'
                                   '  const note = store.add("b");\n  assert.deepEqual(store.get(note.id), note);\n});\n')
    git(path, "add", "src/routes/notes.js", "test/notes.test.js")
    w(path / "src/routes/notes.js", NOTES_UNSTAGED)
    w(path / "src/store.js", STORE_BASE.replace("module.exports = { all, add, get };", '''function remove(id) {
  const index = notes.findIndex((note) => note.id === id);
  if (index === -1) return false;
  notes.splice(index, 1);
  return true;
}

module.exports = { all, add, get, remove };'''))
    w(path / "scratch.http", "GET http://localhost:3000/notes/1\n\nDELETE http://localhost:3000/notes/1\n")
    expect_status(path, ["MM src/routes/notes.js", "M  test/notes.test.js", " M src/store.js",
                         "?? scratch.http"])
    return path.name


# --------------------------------------------------------------------------- c3
PARSER_BASE = '''\
"""Parse simple comma-separated records."""


def parse_line(line: str) -> list[str]:
    """Split one record into trimmed fields."""
    fields = [field.strip() for field in line.split(",")]
    if fields[0] == "":
        raise ValueError("record has no key")
    return fields
'''

PARSER_FIXED = '''\
"""Parse simple comma-separated records."""


def parse_line(line: str) -> list[str]:
    """Split one record into trimmed fields; a blank line has no fields."""
    if not line.strip():
        return []
    fields = [field.strip() for field in line.split(",")]
    if fields[0] == "":
        raise ValueError("record has no key")
    return fields
'''

GUIDE = "# Migrating from csvtool 1.x\n\nRename `--sep` to `--delimiter` in your scripts.\n"


def build_c3(base):
    path = base / "c3-csvtool"
    init(path, {
        "csvtool/__init__.py": "",
        "csvtool/parser.py": PARSER_BASE,
        "config/defaults.yaml": "delimiter: \",\"\ntimeout: 30\n",
        "docs/old-guide.md": GUIDE,
        "scripts/lint.sh": "#!/bin/sh\npython -m pyflakes csvtool tests\n",
        "tests/test_parser.py": 'import pytest\n\nfrom csvtool.parser import parse_line\n\n\n'
                                'def test_fields_are_trimmed():\n    assert parse_line(" a , b ") == ["a", "b"]\n\n\n'
                                'def test_missing_key_is_rejected():\n    with pytest.raises(ValueError):\n'
                                '        parse_line(",b")\n',
    })
    # A staged mode-only change. core.filemode=false pins the semantics on every
    # platform: the index decides the executable bit, the working file's mode is ignored.
    git(path, "config", "core.filemode", "false")
    git(path, "update-index", "--chmod=+x", "scripts/lint.sh")
    w(path / "config/defaults.yaml", "delimiter: \",\"\ntimeout: 45\n")
    git(path, "add", "config/defaults.yaml")
    w(path / "config/defaults.yaml", "delimiter: \",\"\ntimeout: 30\n")
    git(path, "rm", "-q", "docs/old-guide.md")
    w(path / "docs/old-guide.md", GUIDE)
    w(path / "csvtool/parser.py", PARSER_FIXED)
    w(path / "tests/test_parser.py", 'import pytest\n\nfrom csvtool.parser import parse_line\n\n\n'
                                     'def test_fields_are_trimmed():\n    assert parse_line(" a , b ") == ["a", "b"]\n\n\n'
                                     'def test_missing_key_is_rejected():\n    with pytest.raises(ValueError):\n'
                                     '        parse_line(",b")\n\n\n'
                                     'def test_blank_line_has_no_fields():\n    assert parse_line("   ") == []\n')
    expect_status(path, ["MM config/defaults.yaml", "D  docs/old-guide.md", "?? docs/",
                         " M csvtool/parser.py", " M tests/test_parser.py", "M  scripts/lint.sh"])
    return path.name


# --------------------------------------------------------------------------- c4
WEATHER = '''\
"""Weather forecast client for the dashboard."""
import httpx

FORECAST_URL = "https://api.example.invalid/v1/forecast"


def fetch_forecast(city: str, client: httpx.Client | None = None) -> dict:
    """Return tomorrow's forecast for a city as {"high": int, "low": int, "summary": str}."""
    client = client or httpx.Client(timeout=5.0)
    response = client.get(FORECAST_URL, params={"city": city, "days": 1})
    response.raise_for_status()
    day = response.json()["days"][0]
    return {"high": day["max_c"], "low": day["min_c"], "summary": day["text"]}
'''


def build_c4(base):
    path = base / "c4-dashboard"
    init(path, {
        "requirements.txt": "flask==3.0.2\n",
        "app/__init__.py": "",
        "app/main.py": '"""Office dashboard: clock and news tiles."""\nfrom flask import Flask, render_template\n\n'
                       'from .tiles import clock_tile, news_tile\n\napp = Flask(__name__)\n\n\n'
                       '@app.route("/")\ndef index():\n    return render_template("index.html", '
                       'tiles=[clock_tile(), news_tile()])\n',
        "app/tiles.py": 'from datetime import datetime\n\n\ndef clock_tile():\n    return {"title": "Time", '
                        '"body": datetime.now().strftime("%H:%M")}\n\n\ndef news_tile():\n    return {"title": "News", '
                        '"body": "No news yet."}\n',
        "config/settings.toml": '[dashboard]\ntitle = "Plant 2 office"\nrefresh_seconds = 60\n',
        "README.md": "# dashboard\n\nOffice dashboard with clock and news tiles.\n",
    })
    # Two purposes in one file: the new httpx dependency and a routine Flask patch upgrade.
    w(path / "requirements.txt", "flask==3.0.3\nhttpx==0.27.0\n")
    w(path / "app/weather.py", WEATHER)
    w(path / "config/settings.toml", '[dashboard]\ntitle = "Plant 2 office"\nrefresh_seconds = 60\n\n'
                                     '[weather]\ncity = "Hanoi"\nforecast_timeout = 10\n')
    w(path / "tests/test_weather.py", 'from app.weather import fetch_forecast\n\n\nclass FakeResponse:\n'
                                      '    def raise_for_status(self):\n        pass\n\n    def json(self):\n'
                                      '        return {"days": [{"max_c": 31, "min_c": 24, "text": "Showers"}]}\n\n\n'
                                      'class FakeClient:\n    def get(self, url, params):\n'
                                      '        assert params == {"city": "Hanoi", "days": 1}\n        return FakeResponse()\n\n\n'
                                      'def test_fetch_forecast_maps_fields():\n'
                                      '    assert fetch_forecast("Hanoi", FakeClient()) == {"high": 31, "low": 24, '
                                      '"summary": "Showers"}\n')
    expect_status(path, [" M requirements.txt", " M config/settings.toml", "?? app/weather.py",
                         "?? tests/"])
    return path.name


# --------------------------------------------------------------------------- c5
EXPORT_BASE = '''\
"""ledger export: write ledger entries to CSV."""
import argparse
import csv


def export_csv(entries, path):
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["date", "account", "amount"])
        for entry in entries:
            writer.writerow([entry["date"], entry["account"], entry["amount"]])


def add_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("-o", "--out", required=True, help="CSV file to write")
'''


def build_c5(base):
    path = base / "c5-ledger"
    # The history uses Conventional Commits subjects; the skill keeps its own
    # summary format unless the user states a format requirement.
    # allow_abbrev=False makes argparse reject `--out` once the option is
    # `--output`; by default it would accept `--out` as an unambiguous prefix.
    init(path, {
        "ledger/__init__.py": "",
        "ledger/export.py": EXPORT_BASE,
        "ledger/cli.py": '"""ledger CLI."""\nimport argparse\n\nfrom . import export\n\n\n'
                         'def main(argv=None):\n    parser = argparse.ArgumentParser(prog="ledger")\n'
                         '    sub = parser.add_subparsers(dest="command", required=True)\n'
                         '    export.add_arguments(sub.add_parser("export", help="export entries to CSV", '
                         'allow_abbrev=False))\n'
                         '    args = parser.parse_args(argv)\n    export.export_csv([], args.out)\n',
        "tests/test_export.py": 'from ledger.export import export_csv\n\n\ndef test_header_only(tmp_path):\n'
                                '    out = tmp_path / "a.csv"\n    export_csv([], out)\n'
                                '    assert out.read_text().splitlines() == ["date,account,amount"]\n',
    }, message="feat(export): add the CSV export command")
    w(path / "README.md", "# ledger\n\nExport ledger entries:\n\n```bash\nledger export --out report.csv\n```\n")
    commit_all(path, "docs(readme): document ledger export")
    git(path, "mv", "ledger/export.py", "ledger/exporter.py")
    w(path / "ledger/exporter.py", EXPORT_BASE.replace("ledger export: write", "ledger exporter: write").replace(
        'parser.add_argument("-o", "--out", required=True, help="CSV file to write")',
        'parser.add_argument("-o", "--output", required=True, help="CSV file to write")'))
    w(path / "ledger/cli.py", '"""ledger CLI."""\nimport argparse\n\nfrom . import exporter\n\n\n'
                              'def main(argv=None):\n    parser = argparse.ArgumentParser(prog="ledger")\n'
                              '    sub = parser.add_subparsers(dest="command", required=True)\n'
                              '    exporter.add_arguments(sub.add_parser("export", help="export entries to CSV", '
                              'allow_abbrev=False))\n'
                              '    args = parser.parse_args(argv)\n    exporter.export_csv([], args.output)\n')
    git(path, "mv", "tests/test_export.py", "tests/test_exporter.py")
    w(path / "tests/test_exporter.py", 'from ledger.exporter import export_csv\n\n\ndef test_header_only(tmp_path):\n'
                                       '    out = tmp_path / "a.csv"\n    export_csv([], out)\n'
                                       '    assert out.read_text().splitlines() == ["date,account,amount"]\n')
    git(path, "add", "-A")
    w(path / "README.md", "# ledger\n\nExport ledger entries:\n\n```bash\nledger export --output report.csv\n```\n")
    expect_status(path, ["R  ledger/export.py -> ledger/exporter.py", "M  ledger/cli.py",
                         "R  tests/test_export.py -> tests/test_exporter.py", " M README.md"])
    return path.name


# --------------------------------------------------------------------------- c6
def build_c6(base):
    path = base / "c6-todo-cli"
    init(path, {
        "package.json": '{\n  "name": "todo-cli",\n  "version": "2.3.1",\n  "bin": { "todo": "src/cli.js" }\n}\n',
        "src/format.js": 'function formatDue(date) {\n  return date.toISOString().slice(0, 10);\n}\n\n'
                         'module.exports = { formatDue };\n',
        "src/cli.js": '#!/usr/bin/env node\nconst { formatDue } = require("./format");\n\n'
                      'console.log(formatDue(new Date()));\n',
    })
    w(path / "src/format.js", 'function formatDue(date) {\n  // Use the local calendar date, not the UTC one.\n'
                              '  const pad = (n) => String(n).padStart(2, "0");\n'
                              '  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`;\n'
                              '}\n\nmodule.exports = { formatDue };\n')
    w(path / "TODO.txt", "- handle time zones in reminders\n")
    expect_status(path, [" M src/format.js", "?? TODO.txt"])
    return path.name


# --------------------------------------------------------------------------- c7
def build_c7(base):
    path = base / "c7-catalog-api"
    init(path, {
        "package.json": '{\n  "name": "catalog-api",\n  "version": "1.8.0",\n  "scripts": { "test": "node --test" }\n}\n',
        "src/paginate.js": '/**\n * Slice items for a 1-based page number.\n */\nfunction paginate(items, page, size) {\n'
                           '  const offset = page * size;\n  return items.slice(offset, offset + size);\n}\n\n'
                           'module.exports = { paginate };\n',
        "test/paginate.test.js": 'const test = require("node:test");\nconst assert = require("node:assert");\n'
                                 'const { paginate } = require("../src/paginate");\n\n'
                                 'test("second page", () => {\n'
                                 '  assert.deepEqual(paginate([1, 2, 3, 4, 5], 1, 2), [3, 4]);\n});\n',
    })
    w(path / "src/paginate.js", '/**\n * Slice items for a 1-based page number.\n */\nfunction paginate(items, page, size) {\n'
                                '  const offset = (page - 1) * size;\n  return items.slice(offset, offset + size);\n}\n\n'
                                'module.exports = { paginate };\n')
    w(path / "test/paginate.test.js", 'const test = require("node:test");\nconst assert = require("node:assert");\n'
                                      'const { paginate } = require("../src/paginate");\n\n'
                                      'test("first page starts at the first item", () => {\n'
                                      '  assert.deepEqual(paginate([1, 2, 3, 4, 5], 1, 2), [1, 2]);\n});\n\n'
                                      'test("second page", () => {\n'
                                      '  assert.deepEqual(paginate([1, 2, 3, 4, 5], 2, 2), [3, 4]);\n});\n')
    expect_status(path, [" M src/paginate.js", " M test/paginate.test.js"])
    return path.name


# --------------------------------------------------------------------------- c8
def build_c8(base):
    path = base / "c8-invoices"
    init(path, {
        "invoices/__init__.py": "",
        "invoices/models.py": '"""Invoice records."""\nfrom dataclasses import dataclass\n\n\n@dataclass\nclass Invoice:\n'
                              '    number: str\n    customer: str\n    total: float\n\n\n'
                              'def load(rows):\n    return [Invoice(**row) for row in rows]\n',
        "README.md": "# invoices\n\nInvoice records for the billing team.\n",
    })
    w(path / "invoices/export.py", '"""Export invoices."""\nimport csv\n\nCOLUMNS = ["Number", "Customer", "Total (VND)"]\n\n\n'
                                   'def export_csv(invoices, fh):\n    fh.write(",".join(COLUMNS) + "\\n")\n'
                                   '    writer = csv.writer(fh)\n    for inv in invoices:\n'
                                   '        writer.writerow([inv.number, inv.customer, f"{inv.total:.0f}"])\n')
    commit_all(path, "Add CSV export")
    w(path / "invoices/export.py", '"""Export invoices."""\nimport csv\n\nCOLUMNS = ["Number", "Customer", "Total (VND)"]\n\n\n'
                                   'def export_csv(invoices, fh):\n    writer = csv.writer(fh)\n    writer.writerow(COLUMNS)\n'
                                   '    for inv in invoices:\n        writer.writerow([inv.number, inv.customer, f"{inv.total:.0f}"])\n')
    commit_all(path, "Fix header escaping")
    w(path / "tests/test_export.py", 'import io\n\nfrom invoices.export import export_csv\nfrom invoices.models import Invoice\n\n\n'
                                     'def test_rows_follow_header():\n    out = io.StringIO()\n'
                                     '    export_csv([Invoice("A-1", "Lan, Co.", 1500000)], out)\n'
                                     '    assert out.getvalue().splitlines() == [\n'
                                     '        "Number,Customer,Total (VND)",\n        \'A-1,"Lan, Co.",1500000\',\n    ]\n')
    commit_all(path, "Add export tests")
    w(path / "invoices/models.py", '"""Invoice records."""\nfrom dataclasses import dataclass\n\n\n@dataclass\nclass Invoice:\n'
                                   '    number: str\n    customer: str\n    total: float\n\n\n'
                                   'def load(rows):\n    print("DEBUG load", len(rows))\n'
                                   '    return [Invoice(**row) for row in rows]\n')
    expect_status(path, [" M invoices/models.py"])
    return path.name


# --------------------------------------------------------------------------- c9
TOKEN = "tok_live_8f3K2pQx7Lm9Zr4T"
SMTP_SECRET = "hunter2-example"


def build_c9(base):
    path = base / "c9-notifier"
    init(path, {
        ".gitignore": ".env\n__pycache__/\n",
        "notifier/__init__.py": "",
        "notifier/client.py": '"""Send shift notifications."""\n\n\ndef send(message: str) -> None:\n'
                              '    """Print the message until a delivery channel exists."""\n    print(message)\n',
        "README.md": "# notifier\n\nShift-change notifications for the plant floor.\n",
    })
    w(path / "notifier/client.py", '"""Send shift notifications to the plant webhook."""\nimport json\n'
                                   'import urllib.request\nfrom pathlib import Path\n\n'
                                   'CONFIG = Path(__file__).resolve().parent.parent / "config" / "service.json"\n\n\n'
                                   'def send(message: str) -> None:\n'
                                   '    """POST the message to the webhook configured in config/service.json."""\n'
                                   '    config = json.loads(CONFIG.read_text(encoding="utf-8"))\n'
                                   '    request = urllib.request.Request(\n        config["endpoint"],\n'
                                   '        data=json.dumps({"text": message}).encode(),\n'
                                   '        headers={"Authorization": f"Bearer {config[\'api_token\']}", '
                                   '"Content-Type": "application/json"},\n    )\n'
                                   '    urllib.request.urlopen(request, timeout=10)\n')
    w(path / "config/service.json", '{\n  "endpoint": "https://hooks.example.invalid/plant-2/notify",\n'
                                    f'  "api_token": "{TOKEN}"\n}}\n')
    w(path / ".env", f"SMTP_PASSWORD={SMTP_SECRET}\n")
    expect_status(path, [" M notifier/client.py", "?? config/"])
    return path.name


# --------------------------------------------------------------------------- c11
READ_BASE = '''\
"""Read registers from the plant energy meter."""


def read_register(port, address: int) -> int:
    """Return the raw register value; raise IOError when the meter does not answer."""
    reply = port.query(address)
    if reply is None:
        raise IOError(f"meter did not answer for register {address}")
    return reply
'''

READ_ATTEMPTS = '''\
"""Read registers from the plant energy meter."""

ATTEMPTS = {attempts}


def read_register(port, address: int) -> int:
    """Return the raw register value, trying up to ATTEMPTS times before raising IOError."""
    for _ in range(ATTEMPTS):
        reply = port.query(address){debug}
        if reply is not None:
            return reply
    raise IOError(f"meter did not answer for register {{address}} after {{ATTEMPTS}} attempts")
'''

UNITS_BASE = '"""Energy unit conversions."""\n\n\ndef wh_to_kwh(wh: float) -> float:\n    return wh / 1000\n'
METER_DOC = "# Meter reader\n\nReads registers from the press-line energy meter over RS-485.\n"


def build_c11(base):
    """Custom auto-priority staged,unstaged,working-tree: a non-empty staged view wins."""
    path = base / "c11-meter"
    init(path, {
        "meter/__init__.py": "",
        "meter/serial_read.py": READ_BASE,
        "meter/units.py": UNITS_BASE,
        "config/meter.ini": "[serial]\nport = COM3\nbaud = 9600\n",
        "docs/meter.md": METER_DOC,
    })
    w(path / "meter/serial_read.py", READ_ATTEMPTS.format(attempts=3, debug=""))
    w(path / "config/meter.ini", "[serial]\nport = COM3\nbaud = 19200\n")
    w(path / "docs/meter.md", METER_DOC + "A register read is attempted up to three times before it fails.\n")
    git(path, "add", "-A")
    w(path / "meter/serial_read.py", READ_ATTEMPTS.format(
        attempts=5, debug='\n        print("DEBUG reply", address, reply)'))
    w(path / "config/meter.ini", "[serial]\nport = COM3\nbaud = 9600\n")
    w(path / "meter/units.py", UNITS_BASE + '\n\ndef kwh_to_mwh(kwh: float) -> float:\n    return kwh / 1000\n')
    w(path / "tests/test_units.py", 'from meter.units import kwh_to_mwh\n\n\ndef test_kwh_to_mwh():\n'
                                    '    assert kwh_to_mwh(2500) == 2.5\n')
    expect_status(path, ["MM meter/serial_read.py", "MM config/meter.ini", "M  docs/meter.md",
                         " M meter/units.py", "?? tests/"])
    return path.name


# --------------------------------------------------------------------------- c12
LABEL_BASE = '''\
"""Render part labels for the packing station."""


def render(part_no: str, qty: int) -> list[str]:
    """Return the printable lines of one label."""
    return [f"PART {part_no}", f"QTY  {qty}"]
'''

LABEL_STAGED = '''\
"""Render part labels for the packing station."""

MAX_PART_WIDTH = 20


def render(part_no: str, qty: int, width: int = MAX_PART_WIDTH) -> list[str]:
    """Return the printable lines of one label, cutting long part numbers to width."""
    return [f"PART {part_no[:width]}", f"QTY  {qty}"]
'''

LABEL_WORKTREE = '''\
"""Render part labels for the packing station."""

MAX_PART_WIDTH = 20


def render(part_no: str, qty: int, width: int = MAX_PART_WIDTH) -> list[str]:
    """Return the printable lines of one label, cutting long part numbers to width.

    The last line repeats the full part number as Code 39 text (*PART*) for the barcode font.
    """
    return [f"PART {part_no[:width]}", f"QTY  {qty}", f"*{part_no.upper()}*"]
'''

LABEL_CLI = '''\
"""labelgen PART QTY"""
import argparse

from .label import render


def main(argv=None) -> None:
    parser = argparse.ArgumentParser(prog="labelgen")
    parser.add_argument("part")
    parser.add_argument("qty", type=int)
    args = parser.parse_args(argv)
    print("\\n".join(render(args.part, args.qty)))
'''


def build_c12(base):
    """Explicit unstaged scope (index -> working tree) on top of a staged change."""
    path = base / "c12-labelgen"
    init(path, {
        "labelgen/__init__.py": "",
        "labelgen/label.py": LABEL_BASE,
        "labelgen/cli.py": LABEL_CLI,
        "tests/test_label.py": 'from labelgen.label import render\n\n\ndef test_two_lines():\n'
                               '    assert render("ab-12", 3) == ["PART ab-12", "QTY  3"]\n',
        "README.md": "# labelgen\n\nPrint part labels for the packing station.\n",
    })
    w(path / "labelgen/label.py", LABEL_STAGED)
    w(path / "labelgen/cli.py", LABEL_CLI.replace(
        '    parser.add_argument("qty", type=int)\n',
        '    parser.add_argument("qty", type=int)\n'
        '    parser.add_argument("--width", type=int, default=20, help="cut part numbers to this width")\n').replace(
        "render(args.part, args.qty)", "render(args.part, args.qty, args.width)"))
    git(path, "add", "labelgen/label.py", "labelgen/cli.py")
    w(path / "labelgen/label.py", LABEL_WORKTREE)
    w(path / "README.md", "# labelgen\n\nPrint part labels for the packing station. The last line of each "
                          "label is the part number in Code 39 form; print it with a barcode font.\n")
    w(path / "tests/test_barcode.py", 'from labelgen.label import render\n\n\ndef test_barcode_line():\n'
                                      '    assert render("ab-12", 3)[-1] == "*AB-12*"\n')
    expect_status(path, ["MM labelgen/label.py", "M  labelgen/cli.py", " M README.md",
                         "?? tests/test_barcode.py"])
    return path.name


# --------------------------------------------------------------------------- c13
INVOICE_BASE = '''\
"""Invoice totals."""
from decimal import Decimal

from .rates import vat_rate


def total(lines, discount=Decimal("0")):
    """Return the invoice total. VAT is due on the discounted price."""
    subtotal = sum(Decimal(str(line["price"])) * line["qty"] for line in lines)
    vat = subtotal * vat_rate(lines[0]["category"])
    return (subtotal + vat - discount).quantize(Decimal("0.01"))
'''

INVOICE_FIXED = '''\
"""Invoice totals."""
from decimal import Decimal

from .rates import vat_rate


def total(lines, discount=Decimal("0")):
    """Return the invoice total. VAT is due on the discounted price."""
    # Taxing the gross subtotal overcharged every discounted invoice.
    subtotal = sum(Decimal(str(line["price"])) * line["qty"] for line in lines) - discount
    vat = subtotal * vat_rate(lines[0]["category"])
    return (subtotal + vat).quantize(Decimal("0.01"))
'''

RATES_PY = '''\
"""VAT rates by product category, read from rates.csv."""
import csv
from decimal import Decimal
from pathlib import Path

with Path(__file__).with_name("rates.csv").open(encoding="utf-8", newline="") as fh:
    _RATES = {row["category"]: Decimal(row["vat"]) for row in csv.DictReader(fh)}


def vat_rate(category: str) -> Decimal:
    return _RATES[category]
'''

INVOICE_TEST = ('from decimal import Decimal\n\nfrom src.billing.invoice import total\n\n\n'
                'def test_food_vat():\n'
                '    assert total([{"price": 10, "qty": 1, "category": "food"}]) == Decimal("10.80")\n')


def build_c13(base):
    """A folder boundary (src/billing/) with related and unrelated changes outside it."""
    path = base / "c13-shopapp"
    init(path, {
        ".gitignore": "*.tmp\n",
        "src/billing/__init__.py": "",
        "src/billing/invoice.py": INVOICE_BASE,
        "src/billing/rates.py": RATES_PY,
        "src/billing/rates.csv": "category,vat\nfood,0.08\ntools,0.10\n",
        "src/auth/__init__.py": "",
        "src/auth/session.py": '"""Login sessions."""\n\nSESSION_MINUTES = 30\n',
        "tests/billing/test_invoice.py": INVOICE_TEST,
        "README.md": "# shopapp\n\nShop back office: billing and staff logins.\n",
    })
    w(path / "README.md", "# shopapp\n\nShop back office: billing and staff logins. Staff stay signed in "
                          "for two hours.\n")
    git(path, "add", "README.md")
    # A staged deletion recreated untracked with different content: a net modification.
    git(path, "rm", "-q", "src/billing/rates.csv")
    w(path / "src/billing/rates.csv", "category,vat\nfood,0.08\ntools,0.10\nbooks,0.05\n")
    w(path / "src/billing/invoice.py", INVOICE_FIXED)
    w(path / "src/billing/scratch.tmp", "check rounding for 3-line invoices\n")
    w(path / "src/auth/session.py", '"""Login sessions."""\n\nSESSION_MINUTES = 120\n')
    w(path / "tests/billing/test_invoice.py", INVOICE_TEST + '\n\ndef test_discount_comes_off_before_vat():\n'
                                              '    lines = [{"price": 100, "qty": 1, "category": "food"}]\n'
                                              '    assert total(lines, Decimal("10")) == Decimal("97.20")\n')
    expect_status(path, ["M  README.md", "D  src/billing/rates.csv", "?? src/billing/rates.csv",
                         " M src/billing/invoice.py", " M src/auth/session.py",
                         " M tests/billing/test_invoice.py"])
    return path.name


# --------------------------------------------------------------------------- c15
PAY_VALIDATED = '''\
const express = require("express");
const { charge } = require("./processor");

const router = express.Router();

router.post("/payments", async (req, res) => {
  const amount = Number(req.body.amount);
  if (!(amount > 0)) return res.status(400).json({ error: "amount must be positive" });
  const payment = await charge(req.body.card, amount);
  res.status(201).json(payment);
});

module.exports = router;
'''

PAY_IDEMPOTENT = '''\
const express = require("express");
const { charge } = require("./processor");

const router = express.Router();

// Responses by Idempotency-Key, kept in this process's memory only.
const responses = new Map();

router.post("/payments", async (req, res) => {
  const key = req.get("Idempotency-Key");
  if (key && responses.has(key)) return res.status(201).json(responses.get(key));
  const amount = Number(req.body.amount);
  if (!(amount > 0)) return res.status(400).json({ error: "amount must be positive" });
  const payment = await charge(req.body.card, amount);
  if (key) responses.set(key, payment);
  res.status(201).json(payment);
});

module.exports = router;
'''


def build_c15(base):
    """The user requires commitlint (config-conventional) to accept the message."""
    path = base / "c15-paygate"
    init(path, {
        "package.json": '{\n  "name": "paygate",\n  "version": "0.3.0",\n  "private": true,\n'
                        '  "scripts": { "test": "node --test", "prepare": "husky" },\n'
                        '  "dependencies": { "express": "^4.19.2" },\n'
                        '  "devDependencies": {\n    "@commitlint/cli": "^19.3.0",\n'
                        '    "@commitlint/config-conventional": "^19.2.2",\n    "husky": "^9.0.11"\n  }\n}\n',
        "commitlint.config.js": 'module.exports = { extends: ["@commitlint/config-conventional"] };\n',
        ".husky/commit-msg": 'npx --no -- commitlint --edit "$1"\n',
        "src/processor.js": 'let next = 1;\n\nasync function charge(card, amount) {\n'
                            '  return { id: `pay_${next++}`, amount, status: "captured" };\n}\n\n'
                            'module.exports = { charge };\n',
        "src/payments.js": PAY_VALIDATED.replace(
            '  const amount = Number(req.body.amount);\n'
            '  if (!(amount > 0)) return res.status(400).json({ error: "amount must be positive" });\n'
            '  const payment = await charge(req.body.card, amount);\n',
            '  const payment = await charge(req.body.card, Number(req.body.amount));\n'),
    }, message="chore: set up the payment gateway service")
    w(path / "README.md", "# paygate\n\nPayment gateway for the web shop.\n")
    commit_all(path, "docs: add a README")
    w(path / "src/payments.js", PAY_VALIDATED)
    commit_all(path, "fix(payments): reject non-positive amounts")
    w(path / "src/payments.js", PAY_IDEMPOTENT)
    w(path / "test/payments.test.js", 'const test = require("node:test");\n'
                                      'test.todo("replays the stored response for a repeated Idempotency-Key");\n')
    expect_status(path, [" M src/payments.js", "?? test/"])
    return path.name


# --------------------------------------------------------------------------- c16
def build_c16(base):
    """A repository without commits: every view compares against an empty baseline."""
    path = base / "c16-inventory"
    files = {
        ".gitignore": ".venv/\n__pycache__/\n*.log\n",
        "pyproject.toml": '[project]\nname = "inventory"\nversion = "0.1.0"\nrequires-python = ">=3.8"\n',
        "src/inventory/__init__.py": '"""Stock records for the parts store."""\n\n__version__ = "0.1.0"\n',
    }
    for rel, text in files.items():
        w(path / rel, text)
    git(path, "init", "-q", "-b", "main")
    git(path, "add", *files)
    w(path / "pyproject.toml", '[project]\nname = "inventory"\nversion = "0.1.0"\nrequires-python = ">=3.10"\n')
    w(path / "src/inventory/py.typed", "")
    w(path / "README.md", "# inventory\n\nStock records for the parts store. Requires Python 3.10+.\n")
    w(path / "tests/test_version.py", 'import inventory\n\n\ndef test_version():\n'
                                      '    assert inventory.__version__ == "0.1.0"\n')
    w(path / "debug.log", "2024-06-12 store sync failed: timeout\n")
    expect_status(path, ["A  .gitignore", "AM pyproject.toml", "A  src/inventory/__init__.py",
                         "?? README.md", "?? src/inventory/py.typed", "?? tests/"])
    return path.name
