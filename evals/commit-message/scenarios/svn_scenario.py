"""SVN scenario for the commit-message suite (c10).

Creates a local repository with svnadmin (kept beside the scenarios in
<work>/commit-message/svn-repos/), checks out trunk as the scenario folder, and
leaves a modified file, a scheduled deletion, a scheduled addition, and an
unversioned note. Run copies keep pointing at the same file:// repository;
`svn status` and `svn diff` work offline against BASE.
"""
import shutil
import subprocess

from evalenv import SESSION_ENV, force_rmtree
from fixture import w

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


def svn(*args, cwd=None):
    return subprocess.run(["svn", "--non-interactive", *args], cwd=cwd, env=SESSION_ENV,
                          check=True, capture_output=True, text=True).stdout


def build_c10(base):
    if not shutil.which("svn") or not shutil.which("svnadmin"):
        raise SystemExit("c10 needs the svn and svnadmin command-line tools")
    repos = base.parent / "svn-repos"
    force_rmtree(repos)
    repos.mkdir(parents=True)
    repo = repos / "c10-reports"
    subprocess.run(["svnadmin", "create", str(repo)], check=True)
    url = repo.resolve().as_uri() + "/trunk"
    seed = repos / "seed"
    w(seed / "src/__init__.py", "")
    w(seed / "src/report.py", REPORT_BASE)
    w(seed / "src/old_util.py", '"""Formatting helpers."""\n\n\ndef fmt_int(value):\n    return f"{value:>8}"\n')
    w(seed / "README.txt", "Monthly production report for the press line.\n")
    svn("import", str(seed), url, "-m", "Initial import", "--username", "example-dev")
    force_rmtree(seed)
    wc = base / "c10-reports"
    svn("checkout", "-q", url, str(wc))
    w(wc / "src/report.py", REPORT_NEW)
    svn("delete", "-q", "src/old_util.py", cwd=wc)
    w(wc / "src/fmt.py", '"""Formatting helpers."""\n\n\ndef fmt_qty(value):\n    """Right-align a quantity with thousands separators."""\n'
                         '    return f"{value:>10,}"\n')
    svn("add", "-q", "src/fmt.py", cwd=wc)
    w(wc / "notes.txt", "ask maintenance about press 3 counts\n")
    status = sorted(" ".join(line.replace("\\", "/").split()) for line in svn("status", cwd=wc).splitlines() if line)
    expected = sorted(["M src/report.py", "D src/old_util.py", "A src/fmt.py", "? notes.txt"])
    if status != expected:
        raise SystemExit(f"c10-reports: unexpected svn status\n  expected {expected}\n  actual   {status}")
    return wc.name
