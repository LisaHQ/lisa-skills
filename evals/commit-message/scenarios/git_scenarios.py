"""Git scenarios for the commit-message suite (c1-c9).

Each builder commits a small project, then leaves a precise mix of staged,
unstaged, untracked, and ignored changes, and checks the resulting
`git status --porcelain` so a build fails loudly if the state drifts.
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
        "tests/test_parser.py": 'import pytest\n\nfrom csvtool.parser import parse_line\n\n\n'
                                'def test_fields_are_trimmed():\n    assert parse_line(" a , b ") == ["a", "b"]\n\n\n'
                                'def test_missing_key_is_rejected():\n    with pytest.raises(ValueError):\n'
                                '        parse_line(",b")\n',
    })
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
                         " M csvtool/parser.py", " M tests/test_parser.py"])
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
        "requirements.txt": "flask==3.0.3\n",
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
    init(path, {
        "ledger/__init__.py": "",
        "ledger/export.py": EXPORT_BASE,
        "ledger/cli.py": '"""ledger CLI."""\nimport argparse\n\nfrom . import export\n\n\n'
                         'def main(argv=None):\n    parser = argparse.ArgumentParser(prog="ledger")\n'
                         '    sub = parser.add_subparsers(dest="command", required=True)\n'
                         '    export.add_arguments(sub.add_parser("export", help="export entries to CSV"))\n'
                         '    args = parser.parse_args(argv)\n    export.export_csv([], args.out)\n',
        "tests/test_export.py": 'from ledger.export import export_csv\n\n\ndef test_header_only(tmp_path):\n'
                                '    out = tmp_path / "a.csv"\n    export_csv([], out)\n'
                                '    assert out.read_text().splitlines() == ["date,account,amount"]\n',
        "README.md": "# ledger\n\nExport ledger entries:\n\n```bash\nledger export --out report.csv\n```\n",
    })
    git(path, "mv", "ledger/export.py", "ledger/exporter.py")
    w(path / "ledger/exporter.py", EXPORT_BASE.replace("ledger export: write", "ledger exporter: write").replace(
        'parser.add_argument("-o", "--out", required=True, help="CSV file to write")',
        'parser.add_argument("-o", "--output", required=True, help="CSV file to write")'))
    w(path / "ledger/cli.py", '"""ledger CLI."""\nimport argparse\n\nfrom . import exporter\n\n\n'
                              'def main(argv=None):\n    parser = argparse.ArgumentParser(prog="ledger")\n'
                              '    sub = parser.add_subparsers(dest="command", required=True)\n'
                              '    exporter.add_arguments(sub.add_parser("export", help="export entries to CSV"))\n'
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
