"""SVN scenarios for the commit-message suite (c10, c14).

Each builder creates its own local repository with svnadmin in
<work>/commit-message/svn-repos/<scenario>/ (other scenarios' repositories are
left alone), checks out trunk as the scenario folder, and leaves a precise mix
of working-copy changes. A fixed UUID, author, and revision dates make every
build produce the same repository history. The repository files end
read-only, so a commit from a run copy or a judge sandbox fails instead of
changing what other runs see. Run copies keep pointing at the same file://
repository; `svn status` and `svn diff` work offline against BASE.
"""
import shutil
import stat
import subprocess
from pathlib import Path

from evalenv import SESSION_ENV, force_rmtree
from fixture import w

AUTHOR = "example-dev"
REVISION_DATE = "2024-06-12T10:00:00.000000Z"


def svn(*args, cwd=None):
    return subprocess.run(["svn", "--non-interactive", *args], cwd=cwd, env=SESSION_ENV,
                          check=True, capture_output=True, text=True).stdout


def svnadmin(*args):
    subprocess.run(["svnadmin", *args], env=SESSION_ENV, check=True, capture_output=True, text=True)


def pin_date(repo: Path, revision: int) -> None:
    """Replace the wall-clock svn:date of a revision with the suite's fixed date."""
    date_file = repo.parent / f"{repo.name}.date"
    date_file.write_text(REVISION_DATE, encoding="ascii")
    svnadmin("setrevprop", str(repo), "-r", str(revision), "svn:date", str(date_file))
    date_file.unlink()


def new_repo(base: Path, name: str, uuid: str, seed_files: dict[str, str]) -> tuple[Path, str]:
    """Create svn-repos/<name> with one pinned import revision; return (repository, trunk URL).

    The UUID and date are set before any checkout, so working copies record the
    fixed values.
    """
    if not shutil.which("svn") or not shutil.which("svnadmin"):
        raise SystemExit("the SVN scenarios need the svn and svnadmin command-line tools")
    repos = base.parent / "svn-repos"
    repos.mkdir(parents=True, exist_ok=True)
    repo, seed = repos / name, repos / f"seed-{name}"
    force_rmtree(repo)
    force_rmtree(seed)
    svnadmin("create", str(repo))
    url = repo.resolve().as_uri() + "/trunk"
    for rel, text in seed_files.items():
        w(seed / rel, text)
    svn("import", str(seed), url, "-m", "Initial import", "--username", AUTHOR)
    force_rmtree(seed)
    svnadmin("setuuid", str(repo), uuid)
    pin_date(repo, 1)
    return repo, url


def make_read_only(repo: Path) -> None:
    """Clear the write bits of every repository file; force_rmtree restores them on rebuild."""
    for p in repo.rglob("*"):
        if p.is_file():
            p.chmod(p.stat().st_mode & ~(stat.S_IWUSR | stat.S_IWGRP | stat.S_IWOTH))


def expect_svn_status(wc: Path, expected: list[str]) -> None:
    """Fail the build unless `svn status` lists exactly the expected entries.

    Keeps the seven status columns ("M src/a.py" is a text change, " M src/a.py"
    a property-only change) and normalizes path separators.
    """
    actual = sorted(f"{line[:7].rstrip()} {line[8:].replace(chr(92), '/')}"
                    for line in svn("status", cwd=wc).splitlines() if line.strip())
    if actual != sorted(expected):
        raise SystemExit(f"{wc.name}: unexpected svn status\n  expected {sorted(expected)}\n  actual   {actual}")


# --------------------------------------------------------------------------- c10
REPORT_BASE = '''\
"""Monthly production report for the press line."""
from .old_util import fmt_int


def render(rows):
    """Return report lines: one per machine with its part count."""
    return [f"{row['machine']:<10}{fmt_int(row['parts'])}" for row in rows]
'''

REPORT_NEW = '''\
"""Monthly production report for the press line."""
from .fmt import fmt_qty


def render(rows):
    """Return report lines: one per machine, then a total line."""
    lines = [f"{row['machine']:<10}{fmt_qty(row['parts'])}" for row in rows]
    lines.append(f"{'TOTAL':<10}{fmt_qty(sum(row['parts'] for row in rows))}")
    return lines
'''


def build_c10(base):
    repo, url = new_repo(base, "c10-reports", "00000000-0000-4000-8000-00000000c010", {
        "src/__init__.py": "",
        "src/report.py": REPORT_BASE,
        "src/old_util.py": '"""Formatting helpers."""\n\n\ndef fmt_int(value):\n    return f"{value:>8}"\n',
        "README.txt": "Monthly production report for the press line.\n",
    })
    wc = base / "c10-reports"
    svn("checkout", "-q", url, str(wc))
    w(wc / "src/report.py", REPORT_NEW)
    svn("delete", "-q", "src/old_util.py", cwd=wc)
    w(wc / "src/fmt.py", '"""Formatting helpers."""\n\n\ndef fmt_qty(value):\n    """Right-align a quantity with thousands separators."""\n'
                         '    return f"{value:>10,}"\n')
    svn("add", "-q", "src/fmt.py", cwd=wc)
    w(wc / "notes.txt", "ask maintenance about press 3 counts\n")
    expect_svn_status(wc, ["M src/report.py", "D src/old_util.py", "A src/fmt.py", "? notes.txt"])
    make_read_only(repo)
    return wc.name


# --------------------------------------------------------------------------- c14
PRESS_REPORT_BASE = '''\
"""Monthly production report for the press line."""


def render(rows):
    """Return report lines: one per machine with its part count."""
    return [f"{row['machine']:<10}{row['parts']:>8}" for row in rows]
'''

PRESS_REPORT_CSV = '''\
"""Monthly production report for the press line."""
from .csvout import write_rows


def render(rows):
    """Return report lines: one per machine with its part count."""
    return [f"{row['machine']:<10}{row['parts']:>8}" for row in rows]


def export_csv(rows, path):
    """Write the report as CSV with a machine,parts header."""
    write_rows(path, ["machine", "parts"], ([row["machine"], row["parts"]] for row in rows))
'''

CSVOUT = '''\
"""CSV output for reports."""
import csv


def write_rows(path, header, rows):
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(header)
        writer.writerows(rows)
'''


def build_c14(base):
    """Auto scope in SVN: a text change, a property-only change, an unversioned module, a missing file."""
    repo, url = new_repo(base, "c14-pressline", "00000000-0000-4000-8000-00000000c014", {
        "src/__init__.py": "",
        "src/report.py": PRESS_REPORT_BASE,
        "scripts/export.sh": '#!/bin/sh\npython -c "import src.report"\n',
        "docs/press-codes.txt": "P1 Schuler 400t\nP2 Aida 250t\n",
    })
    # Revision 2 sets svn:ignore on trunk from a throwaway checkout, so the
    # scenario checkout below records the pinned date of every revision.
    tmp = repo.parent / "wc-c14-pressline"
    force_rmtree(tmp)
    svn("checkout", "-q", url, str(tmp))
    svn("propset", "-q", "svn:ignore", "*.log", ".", cwd=tmp)
    svn("commit", "-q", "-m", "Ignore run logs", "--username", AUTHOR, cwd=tmp)
    force_rmtree(tmp)
    pin_date(repo, 2)
    wc = base / "c14-pressline"
    svn("checkout", "-q", url, str(wc))
    w(wc / "src/report.py", PRESS_REPORT_CSV)
    w(wc / "src/csvout.py", CSVOUT)
    svn("propset", "-q", "svn:executable", "ON", "scripts/export.sh", cwd=wc)
    w(wc / "press.log", "2024-06-12 export ok\n")
    (wc / "docs/press-codes.txt").unlink()
    expect_svn_status(wc, ["M src/report.py", "? src/csvout.py", " M scripts/export.sh", "! docs/press-codes.txt"])
    make_read_only(repo)
    return wc.name
