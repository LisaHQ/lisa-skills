"""Scenario s14: 'hookshelf', a collection of Git hooks with an installer script (create mode, catalog README)."""
import json

from fixture import w, git_init

ROOT = "s14-hookshelf"

# name, stage, status, summary, settings {variable: (default, help)}
HOOKS = [
    ("big-file-guard", "pre-commit", "stable", "Block staged files larger than a size limit.",
     {"HOOKSHELF_MAX_KB": ("500", "Largest allowed size of a staged file, in kilobytes.")}),
    ("no-debug", "pre-commit", "stable", "Block leftover debug statements in added lines.",
     {"HOOKSHELF_DEBUG_ALLOW": ("", "Comma-separated glob patterns of paths to skip, such as scripts/*,*.md.")}),
    ("msg-ticket", "commit-msg", "stable", "Require a ticket id such as ABC-123 in the commit message.",
     {"HOOKSHELF_TICKET_PATTERN": ("[A-Z][A-Z0-9]+-[0-9]+",
                                   "Regular expression that must match somewhere in the commit message.")}),
    ("branch-name", "pre-push", "stable", "Reject pushes from branches that do not match a naming pattern.",
     {"HOOKSHELF_BRANCH_PATTERN": ("^(feature|fix|chore)/[a-z0-9._-]+$",
                                   "Regular expression a branch name must match; main, master, and develop "
                                   "always pass.")}),
    ("secrets-scan", "pre-commit", "experimental",
     "Block staged lines that look like an AWS access key id or a private key.", {}),
    ("whitespace-fix", "pre-commit", "deprecated",
     "Strip trailing whitespace from staged files (does not re-stage them).", {}),
]

# Shared by the hooks that read a setting; each hook is copied on its own, so each carries its copy.
SETTING = r'''def setting(name):
    """The environment variable, or its default from hook.json."""
    meta = json.loads(Path(__file__).with_name("hook.json").read_text(encoding="utf-8"))
    return os.environ.get(name) or meta["settings"][name]["default"]
'''

ADDED_LINES = r'''def added_lines():
    """Yield (path, line number, text) for every line the staged diff adds."""
    diff = subprocess.run(["git", "-c", "core.quotepath=off", "diff", "--cached", "--unified=0", "--no-color",
                           "--no-ext-diff", "--src-prefix=a/", "--dst-prefix=b/", "--diff-filter=AM"],
                          check=True, capture_output=True).stdout
    path, number, in_hunk = None, 0, False
    for line in diff.decode("utf-8", "replace").split("\n"):
        if line.startswith("diff --git "):
            path, in_hunk = None, False
        elif not in_hunk and line.startswith("+++ b/"):
            path = line[6:].rstrip("\t")
        elif line.startswith("@@ "):
            number, in_hunk = int(re.match(r"@@ -\S+ \+(\d+)", line).group(1)), True
        elif in_hunk and line.startswith("+"):
            yield path, number, line[1:]
            number += 1
'''


def build(base):
    r = base / ROOT
    w(r / "hookshelf.py", r'''"""hookshelf: a shelf of Git hooks, and the installer that puts them into a repository.

Clone the repository and run this script with Python. It is not packaged; it
needs only Python 3.9 or later and Git.

    python hookshelf.py list
    python hookshelf.py install <name> [<name> ...] [--repo PATH] [--force] [--allow-deprecated]
    python hookshelf.py uninstall <name> [--repo PATH]

install copies each hook to .git/hookshelf/<name>/ and writes a dispatcher at
.git/hooks/<stage>. The dispatcher runs the installed hooks of that stage in
installation order and stops at the first one that fails.
"""
import argparse
import json
import shutil
import sys
from pathlib import Path

__version__ = "0.6.0"

if sys.version_info < (3, 9):
    sys.exit("hookshelf needs Python 3.9 or later")

SHELF = Path(__file__).resolve().parent / "hooks"
MARKER = "# Written by hookshelf."


class ShelfError(Exception):
    """A problem reported to the user as one line, without a traceback."""


def load_shelf():
    """Every hook on the shelf, by name."""
    hooks = {}
    for meta in SHELF.glob("*/hook.json"):
        hook = json.loads(meta.read_text(encoding="utf-8"))
        hooks[hook["name"]] = hook
    return hooks


def git_dir(repo):
    path = Path(repo) / ".git"
    if not path.is_dir():
        raise ShelfError(f"{repo} is not a Git repository (no .git directory)")
    return path


def write_text(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as out:
        out.write(text)


def read_installed(git):
    """Names of the installed hooks, in installation order."""
    record = git / "hookshelf" / "installed.json"
    return json.loads(record.read_text(encoding="utf-8")) if record.exists() else []


def write_installed(git, installed):
    write_text(git / "hookshelf" / "installed.json", json.dumps(installed, indent=2) + "\n")


def stage_of(git, name):
    return json.loads((git / "hookshelf" / name / "hook.json").read_text(encoding="utf-8"))["stage"]


def ours(path):
    """Whether hookshelf wrote this hook file."""
    return MARKER in path.read_text(encoding="utf-8", errors="replace")


def write_dispatcher(git, stage, installed):
    """Write .git/hooks/<stage> for the installed hooks of that stage; remove it when none is left."""
    target = git / "hooks" / stage
    names = [name for name in installed if stage_of(git, name) == stage]
    if not names:
        if target.exists() and ours(target):
            target.unlink()
        return
    python = Path(sys.executable).as_posix()  # hooks run with the interpreter that installed them
    lines = ["#!/bin/sh", f'{MARKER} Do not edit: use "hookshelf.py install" or "uninstall".',
             'shelf="${0%/*}/../hookshelf"']
    lines += [f'"{python}" "$shelf/{name}/run.py" "$@" || exit $?' for name in names]
    write_text(target, "\n".join(lines) + "\n")
    target.chmod(0o755)


def cmd_list(args):
    hooks = load_shelf()
    rows = [("NAME", "STAGE", "STATUS", "SUMMARY")]
    rows += [(h["name"], h["stage"], h["status"], h["summary"]) for h in (hooks[name] for name in sorted(hooks))]
    widths = [max(len(row[i]) for row in rows) for i in range(3)]
    for row in rows:
        print("  ".join(cell.ljust(width) for cell, width in zip(row, widths)) + "  " + row[3])
    return 0


def cmd_install(args):
    shelf, git = load_shelf(), git_dir(args.repo)
    for name in args.names:
        if name not in shelf:
            raise ShelfError(f'unknown hook "{name}"; run "python hookshelf.py list" to see the shelf')
        if shelf[name]["status"] == "deprecated" and not args.allow_deprecated:
            raise ShelfError(f"{name} is deprecated; pass --allow-deprecated to install it anyway")
    stages = sorted({shelf[name]["stage"] for name in args.names})
    for stage in stages:
        target = git / "hooks" / stage
        if target.exists() and not ours(target) and not args.force:
            raise ShelfError(f".git/hooks/{stage} exists and was not written by hookshelf; "
                             "pass --force to replace it")
    installed = read_installed(git)
    for name in args.names:
        copy = git / "hookshelf" / name
        if copy.exists():
            shutil.rmtree(copy)
        shutil.copytree(SHELF / name, copy, ignore=shutil.ignore_patterns("__pycache__"))
        if name not in installed:
            installed.append(name)
        print(f"installed {name} ({shelf[name]['stage']})")
    write_installed(git, installed)
    for stage in stages:
        write_dispatcher(git, stage, installed)
    return 0


def cmd_uninstall(args):
    git = git_dir(args.repo)
    installed = read_installed(git)
    if args.name not in installed:
        raise ShelfError(f"{args.name} is not installed in {args.repo}")
    stage = stage_of(git, args.name)
    installed.remove(args.name)
    write_installed(git, installed)
    write_dispatcher(git, stage, installed)
    shutil.rmtree(git / "hookshelf" / args.name)
    print(f"uninstalled {args.name} ({stage})")
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(prog="hookshelf.py",
                                     description="List, install, and uninstall the Git hooks on this shelf.")
    parser.add_argument("--version", action="version", version=f"hookshelf {__version__}")
    commands = parser.add_subparsers(dest="command", required=True, metavar="{list,install,uninstall}")
    commands.add_parser("list", help="show every hook with its stage and status").set_defaults(run=cmd_list)
    install = commands.add_parser("install", help="install one or more hooks into a repository")
    install.add_argument("names", nargs="+", metavar="name", help="hook to install (see list)")
    install.add_argument("--repo", default=".", metavar="PATH",
                         help="repository to install into (default: the current directory)")
    install.add_argument("--force", action="store_true",
                         help="replace an existing hook that hookshelf did not write")
    install.add_argument("--allow-deprecated", action="store_true", help="install a hook marked deprecated")
    install.set_defaults(run=cmd_install)
    uninstall = commands.add_parser("uninstall", help="remove one installed hook from a repository")
    uninstall.add_argument("name", help="hook to remove")
    uninstall.add_argument("--repo", default=".", metavar="PATH",
                           help="repository to remove it from (default: the current directory)")
    uninstall.set_defaults(run=cmd_uninstall)
    args = parser.parse_args(argv)
    try:
        return args.run(args)
    except ShelfError as exc:
        print(f"hookshelf: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
''')
    for name, stage, status, summary, settings in HOOKS:
        meta = {"name": name, "stage": stage, "status": status, "summary": summary,
                "settings": {key: {"default": default, "help": text} for key, (default, text) in settings.items()}}
        w(r / f"hooks/{name}/hook.json", json.dumps(meta, indent=2) + "\n")

    # big-file-guard
    w(r / "hooks/big-file-guard/run.py",
      r'''"""big-file-guard: block staged files larger than HOOKSHELF_MAX_KB kilobytes."""
import json
import os
import subprocess
import sys
from pathlib import Path


''' + SETTING + r'''

def git(*args):
    return subprocess.run(["git", *args], check=True, capture_output=True).stdout.decode("utf-8", "replace")


def main():
    limit = int(setting("HOOKSHELF_MAX_KB"))
    blocked = False
    for path in filter(None, git("diff", "--cached", "--name-only", "--diff-filter=ACM", "-z").split("\0")):
        size = int(git("cat-file", "-s", f":{path}"))  # the staged size, not the working file's
        if size > limit * 1024:
            print(f"big-file-guard: {path} is {-(-size // 1024)} KB, over the {limit} KB limit", file=sys.stderr)
            blocked = True
    return 1 if blocked else 0


if __name__ == "__main__":
    sys.exit(main())
''')
    w(r / "hooks/big-file-guard/README.md", '''\
# big-file-guard

Blocks a commit when a staged file is larger than a size limit, so large
binaries do not slip into history.

- Stage: `pre-commit`
- Status: stable

## What it checks

The staged size of every file the commit adds or modifies. Deleted files are
ignored. A file exactly at the limit passes.

## Settings

| Variable | Default | Meaning |
| --- | --- | --- |
| `HOOKSHELF_MAX_KB` | `500` | Largest allowed size of a staged file, in kilobytes (1 KB = 1024 bytes). |

Raise the limit for one commit:

```bash
HOOKSHELF_MAX_KB=2000 git commit -m "ABC-123 Add the demo video"
```

## When it blocks

One line per file, with the size rounded up:

```text
big-file-guard: assets/demo.bin is 600 KB, over the 500 KB limit
```
''')

    # no-debug
    w(r / "hooks/no-debug/run.py", r'''"""no-debug: block leftover debug statements in the lines a commit adds."""
import fnmatch
import json
import os
import re
import subprocess
import sys
from pathlib import Path

STATEMENTS = ("breakpoint()", "import pdb", "console.log(", "debugger;")


''' + SETTING + "\n\n" + ADDED_LINES + r'''

def main():
    allowed = [pattern.strip() for pattern in setting("HOOKSHELF_DEBUG_ALLOW").split(",") if pattern.strip()]
    blocked = False
    for path, number, text in added_lines():
        if any(fnmatch.fnmatchcase(path, pattern) for pattern in allowed):
            continue
        for statement in STATEMENTS:
            if statement in text:
                print(f"no-debug: {path}:{number}: {statement}", file=sys.stderr)
                blocked = True
    return 1 if blocked else 0


if __name__ == "__main__":
    sys.exit(main())
''')
    w(r / "hooks/no-debug/README.md", '''\
# no-debug

Blocks a commit that adds a leftover debug statement.

- Stage: `pre-commit`
- Status: stable

## What it checks

Lines the commit adds (not lines that were already there) that contain one of:

- `breakpoint()`
- `import pdb`
- `console.log(`
- `debugger;`

The match is plain text, so a statement inside a comment or a string is
blocked too.

## Settings

| Variable | Default | Meaning |
| --- | --- | --- |
| `HOOKSHELF_DEBUG_ALLOW` | empty | Comma-separated glob patterns of paths to skip, such as `scripts/*,*.md`. |

In a pattern, `*` also matches `/`.

## When it blocks

One line per statement, as `path:line: statement`:

```text
no-debug: app.py:2: breakpoint()
```
''')

    # msg-ticket
    w(r / "hooks/msg-ticket/run.py", r'''"""msg-ticket: require a ticket id in the commit message."""
import json
import os
import re
import sys
from pathlib import Path


''' + SETTING + r'''

def main(argv):
    text = Path(argv[1]).read_text(encoding="utf-8", errors="replace")  # Git passes the message file
    lines = [line for line in text.split("\n") if not line.startswith("#")]
    first = next((line for line in lines if line.strip()), "")
    if first.startswith(("Merge ", "Revert ")):
        return 0
    pattern = setting("HOOKSHELF_TICKET_PATTERN")
    if re.search(pattern, "\n".join(lines)):
        return 0
    print(f"msg-ticket: the commit message has no ticket id matching {pattern}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
''')
    w(r / "hooks/msg-ticket/README.md", '''\
# msg-ticket

Blocks a commit whose message does not name a ticket, so every change can be
traced back to the tracker.

- Stage: `commit-msg`
- Status: stable

## What it checks

The commit message, without its comment lines, must contain a ticket id such
as `ABC-123` anywhere. Merge and revert commits (messages that start with
`Merge ` or `Revert `) are skipped.

## Settings

| Variable | Default | Meaning |
| --- | --- | --- |
| `HOOKSHELF_TICKET_PATTERN` | `[A-Z][A-Z0-9]+-[0-9]+` | Regular expression that must match somewhere in the message. |

For issue numbers such as `#42`, set `HOOKSHELF_TICKET_PATTERN='#[0-9]+'`.

## When it blocks

```text
msg-ticket: the commit message has no ticket id matching [A-Z][A-Z0-9]+-[0-9]+
```
''')

    # branch-name
    w(r / "hooks/branch-name/run.py",
      r'''"""branch-name: reject pushes from branches that do not match a naming pattern."""
import json
import os
import re
import sys
from pathlib import Path

ALWAYS_ALLOWED = ("main", "master", "develop")


''' + SETTING + r'''

def main():
    pattern = setting("HOOKSHELF_BRANCH_PATTERN")
    blocked = False
    for line in sys.stdin:  # Git writes one line per pushed ref: local ref, local id, remote ref, remote id
        fields = line.split()
        if len(fields) != 4 or not fields[0].startswith("refs/heads/"):
            continue  # tags and deletions
        branch = fields[0][len("refs/heads/"):]
        if branch in ALWAYS_ALLOWED or re.search(pattern, branch):
            continue
        print(f"branch-name: branch {branch} does not match {pattern}", file=sys.stderr)
        blocked = True
    return 1 if blocked else 0


if __name__ == "__main__":
    sys.exit(main())
''')
    w(r / "hooks/branch-name/README.md", '''\
# branch-name

Rejects a push from a branch whose name does not follow the naming pattern.

- Stage: `pre-push`
- Status: stable

## What it checks

Every branch in the push. `main`, `master`, and `develop` always pass; tags
and branch deletions are ignored. With the default pattern,
`feature/login-form`, `fix/login-redirect`, and `chore/bump-deps` pass.

## Settings

`HOOKSHELF_BRANCH_PATTERN` is the regular expression a branch name must
match. Default:

```text
^(feature|fix|chore)/[a-z0-9._-]+$
```

## When it blocks

One line per branch:

```text
branch-name: branch fix_login does not match ^(feature|fix|chore)/[a-z0-9._-]+$
```
''')

    # secrets-scan
    w(r / "hooks/secrets-scan/run.py",
      r'''"""secrets-scan: block added lines that look like an AWS access key id or a private key (experimental)."""
import re
import subprocess
import sys

# Two patterns only. This is a last check before a commit, not a secret scanner.
PATTERNS = (
    (re.compile(r"(?<![0-9A-Z])AKIA[0-9A-Z]{16}(?![0-9A-Z])"), "an AWS access key id"),
    (re.compile(r"-----BEGIN (?:[A-Z]+ )?PRIVATE KEY-----"), "a private key"),
)


''' + ADDED_LINES + r'''

def main():
    blocked = False
    for path, number, text in added_lines():
        for pattern, label in PATTERNS:
            if pattern.search(text):
                print(f"secrets-scan: {path}:{number}: looks like {label}", file=sys.stderr)  # never the match
                blocked = True
    return 1 if blocked else 0


if __name__ == "__main__":
    sys.exit(main())
''')
    w(r / "hooks/secrets-scan/README.md", '''\
# secrets-scan

Blocks a commit that adds a line that looks like a credential.

- Stage: `pre-commit`
- Status: **experimental** (added in 0.6.0; patterns and messages may change)

## What it checks

Lines the commit adds, for two patterns only:

- an AWS access key id (`AKIA` followed by 16 capital letters or digits)
- the first line of a private key (`-----BEGIN ... PRIVATE KEY-----`)

It does not know passwords, API tokens, or any other provider's keys, and it
does not look at history. It does not replace a real secret scanner: treat it
as a last check before a commit, not as your only one.

## Settings

None.

## When it blocks

One line per finding. The message names the place, never the secret:

```text
secrets-scan: config.py:1: looks like an AWS access key id
secrets-scan: deploy/id.pem:1: looks like a private key
```
''')

    # whitespace-fix
    w(r / "hooks/whitespace-fix/run.py",
      r'''"""whitespace-fix: strip trailing whitespace from the files in a commit (deprecated since 0.6.0).

The hook rewrites files in the working tree and does not stage the result, so
the commit still holds the old content. It stays on the shelf for repositories
that already use it; README.md says what to use instead.
"""
import re
import subprocess
import sys
from pathlib import Path


def main():
    names = subprocess.run(["git", "diff", "--cached", "--name-only", "--diff-filter=ACM", "-z"],
                           check=True, capture_output=True).stdout.decode("utf-8", "replace")
    for name in filter(None, names.split("\0")):
        path = Path(name)
        if not path.is_file():
            continue
        data = path.read_bytes()
        if b"\0" in data:
            continue  # binary
        clean = re.sub(rb"[ \t]+(?=\r?\n|\Z)", b"", data)
        if clean != data:
            path.write_bytes(clean)
            print(f"whitespace-fix: stripped trailing whitespace in {name} (not re-staged)", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
''')
    w(r / "hooks/whitespace-fix/README.md", '''\
# whitespace-fix

> **Deprecated since 0.6.0.** Do not add it to new repositories. Strip
> trailing whitespace with an editor setting (trim trailing whitespace on
> save) or with your formatter instead.

Strips trailing whitespace from the files in a commit.

- Stage: `pre-commit`
- Status: deprecated

## Why it is deprecated

The hook rewrites the files in the working tree but does not stage the
result. The commit therefore still contains the trailing whitespace, and the
cleaned files show up as unstaged changes right after it.

`python hookshelf.py install` refuses this hook unless you pass
`--allow-deprecated`.

## Settings

None.

## What it prints

It never blocks a commit. For each file it rewrites:

```text
whitespace-fix: stripped trailing whitespace in notes.txt (not re-staged)
```
''')

    # Tests: every hook's verdict and exact message, and the installer, in temporary repositories.
    w(r / "tests/support.py",
      r'''"""Shared by the tests: a temporary Git repository and runners for the hooks and the installer."""
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Ignore the developer's own Git configuration, identity, and hook settings.
ENV = {key: value for key, value in os.environ.items() if not key.startswith("HOOKSHELF_")}
ENV.update(GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_NOSYSTEM="1",
           GIT_AUTHOR_NAME="Test", GIT_AUTHOR_EMAIL="test@example.invalid",
           GIT_COMMITTER_NAME="Test", GIT_COMMITTER_EMAIL="test@example.invalid")


class RepoTest(unittest.TestCase):
    """A test with an empty Git repository in self.repo, inside the plain folder self.outside."""

    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.outside = Path(tmp.name)
        self.repo = self.outside / "repo"
        self.run_in(self.outside, ["git", "init", "-q", "-b", "main", "repo"])

    def run_in(self, cwd, command, env=None, stdin=""):
        return subprocess.run(command, cwd=cwd, env=dict(ENV, **(env or {})), input=stdin,
                              capture_output=True, text=True)

    def git(self, *args):
        return self.run_in(self.repo, ["git", *args])

    def stage(self, path, content):
        file = self.repo / path
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_bytes(content if isinstance(content, bytes) else content.encode("utf-8"))
        self.git("add", path)

    def hook(self, name, *args, env=None, stdin=""):
        """Run one hook as Git would: from the top of the repository."""
        return self.run_in(self.repo, [sys.executable, str(ROOT / "hooks" / name / "run.py"), *args], env, stdin)

    def shelf(self, *args, cwd=None):
        return self.run_in(cwd or self.repo, [sys.executable, str(ROOT / "hookshelf.py"), *args])
''')
    w(r / "tests/test_hooks.py", r'''"""Each hook's verdict, and the exact message it prints when it blocks."""
from support import RepoTest

# Built at run time, so this file holds nothing that looks like a secret.
FAKE_KEY_ID = "AKIA" + "EXAMPLE0EXAMPLE0"
KEY_HEADER = "-----BEGIN " + "PRIVATE KEY-----"


class BigFileGuard(RepoTest):
    def test_blocks_a_file_over_the_limit(self):
        self.stage("assets/demo.bin", b"\0" * (600 * 1024))
        result = self.hook("big-file-guard")
        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stderr, "big-file-guard: assets/demo.bin is 600 KB, over the 500 KB limit\n")

    def test_passes_a_file_at_the_limit(self):
        self.stage("assets/demo.bin", b"\0" * (500 * 1024))
        self.assertEqual(self.hook("big-file-guard").returncode, 0)

    def test_limit_is_configurable(self):
        self.stage("assets/demo.bin", b"\0" * (600 * 1024))
        self.assertEqual(self.hook("big-file-guard", env={"HOOKSHELF_MAX_KB": "1000"}).returncode, 0)


class NoDebug(RepoTest):
    def test_blocks_debug_statements_in_added_lines(self):
        self.stage("app.py", "def total(prices):\n    breakpoint()\n    return sum(prices)\n")
        self.stage("web/cart.js", "console.log(cart);\ndebugger;\n")
        result = self.hook("no-debug")
        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stderr, "no-debug: app.py:2: breakpoint()\n"
                                        "no-debug: web/cart.js:1: console.log(\n"
                                        "no-debug: web/cart.js:2: debugger;\n")

    def test_ignores_lines_the_commit_does_not_add(self):
        self.stage("app.py", "import pdb\n")
        self.git("commit", "-q", "-m", "Add the app")
        self.stage("app.py", "import pdb\nprint('ready')\n")
        self.assertEqual(self.hook("no-debug").returncode, 0)

    def test_allow_list_skips_matching_paths(self):
        self.stage("scripts/repl.py", "import pdb\n")
        self.assertEqual(self.hook("no-debug").returncode, 1)
        self.assertEqual(self.hook("no-debug", env={"HOOKSHELF_DEBUG_ALLOW": "scripts/*,*.md"}).returncode, 0)


class MsgTicket(RepoTest):
    def verdict(self, message, env=None):
        (self.repo / "MSG").write_bytes(message.encode("utf-8"))
        return self.hook("msg-ticket", "MSG", env=env)

    def test_blocks_a_message_without_a_ticket(self):
        result = self.verdict("Fix the login redirect\n")
        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stderr,
                         "msg-ticket: the commit message has no ticket id matching [A-Z][A-Z0-9]+-[0-9]+\n")

    def test_accepts_a_ticket_and_skips_merges_and_reverts(self):
        for message in ("ABC-123 Fix the login redirect\n", "Merge branch 'main' into feature/login\n",
                        'Revert "Fix the login redirect"\n'):
            self.assertEqual(self.verdict(message).returncode, 0, message)

    def test_pattern_is_configurable(self):
        env = {"HOOKSHELF_TICKET_PATTERN": "#[0-9]+"}
        self.assertEqual(self.verdict("Fix the login redirect (#42)\n", env).returncode, 0)


class BranchName(RepoTest):
    def push(self, ref):
        """What Git writes to a pre-push hook for one pushed ref."""
        return self.hook("branch-name", "origin", "https://example.invalid/repo.git",
                         stdin=f"{ref} {'1' * 40} {ref} {'0' * 40}\n")

    def test_blocks_a_branch_that_does_not_match(self):
        result = self.push("refs/heads/fix_login")
        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stderr,
                         "branch-name: branch fix_login does not match ^(feature|fix|chore)/[a-z0-9._-]+$\n")

    def test_accepts_matching_and_always_allowed_branches(self):
        for ref in ("refs/heads/fix/login-redirect", "refs/heads/main", "refs/heads/master",
                    "refs/heads/develop", "refs/tags/v1.0"):
            self.assertEqual(self.push(ref).returncode, 0, ref)


class SecretsScan(RepoTest):
    def test_blocks_the_two_patterns_it_knows(self):
        self.stage("config.py", f'AWS_KEY_ID = "{FAKE_KEY_ID}"\n')
        self.stage("deploy/id.pem", KEY_HEADER + "\n")
        result = self.hook("secrets-scan")
        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stderr, "secrets-scan: config.py:1: looks like an AWS access key id\n"
                                        "secrets-scan: deploy/id.pem:1: looks like a private key\n")

    def test_misses_other_kinds_of_secrets(self):
        self.stage("settings.py", 'DB_PASSWORD = "example-password"\nAPI_TOKEN = "example-token-0123456789"\n')
        self.assertEqual(self.hook("secrets-scan").returncode, 0)


class WhitespaceFix(RepoTest):
    def test_rewrites_the_file_but_does_not_restage_it(self):
        self.stage("notes.txt", "one  \ntwo\n")
        result = self.hook("whitespace-fix")
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stderr, "whitespace-fix: stripped trailing whitespace in notes.txt (not re-staged)\n")
        self.assertEqual((self.repo / "notes.txt").read_bytes(), b"one\ntwo\n")
        self.assertEqual(self.git("show", ":notes.txt").stdout, "one  \ntwo\n")  # what the commit would hold
''')
    w(r / "tests/test_cli.py", r'''"""The installer: list, install, uninstall, and what it refuses to do."""
from support import RepoTest

LIST = """\
NAME            STAGE       STATUS        SUMMARY
big-file-guard  pre-commit  stable        Block staged files larger than a size limit.
branch-name     pre-push    stable        Reject pushes from branches that do not match a naming pattern.
msg-ticket      commit-msg  stable        Require a ticket id such as ABC-123 in the commit message.
no-debug        pre-commit  stable        Block leftover debug statements in added lines.
secrets-scan    pre-commit  experimental  Block staged lines that look like an AWS access key id or a private key.
whitespace-fix  pre-commit  deprecated    Strip trailing whitespace from staged files (does not re-stage them).
"""


class Shelf(RepoTest):
    def test_list_shows_every_hook_sorted_by_name(self):
        result = self.shelf("list")
        self.assertEqual((result.returncode, result.stdout), (0, LIST))

    def test_installed_hooks_run_in_order_and_stop_at_the_first_failure(self):
        result = self.shelf("install", "big-file-guard", "no-debug", "msg-ticket")
        self.assertEqual(result.stdout, "installed big-file-guard (pre-commit)\n"
                                        "installed no-debug (pre-commit)\n"
                                        "installed msg-ticket (commit-msg)\n")
        self.stage("assets/demo.bin", b"\0" * (600 * 1024))
        self.stage("app.py", "breakpoint()\n")
        blocked = self.git("commit", "-m", "ABC-123 Add the demo")
        self.assertNotEqual(blocked.returncode, 0)
        self.assertIn("big-file-guard: assets/demo.bin is 600 KB, over the 500 KB limit", blocked.stderr)
        self.assertNotIn("no-debug:", blocked.stderr)  # big-file-guard was installed first and failed
        self.git("rm", "-q", "--cached", "assets/demo.bin")
        self.assertIn("no-debug: app.py:1: breakpoint()", self.git("commit", "-m", "ABC-123 Add the app").stderr)
        self.stage("app.py", "print('ready')\n")
        self.assertIn("msg-ticket:", self.git("commit", "-m", "Add the app").stderr)
        self.assertEqual(self.git("commit", "-m", "ABC-123 Add the app").returncode, 0)

    def test_refuses_to_replace_a_hook_it_did_not_write(self):
        own = self.repo / ".git" / "hooks" / "pre-commit"
        own.parent.mkdir(exist_ok=True)
        own.write_bytes(b"#!/bin/sh\necho team hook\n")
        result = self.shelf("install", "no-debug")
        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stderr, "hookshelf: .git/hooks/pre-commit exists and was not written by hookshelf; "
                                        "pass --force to replace it\n")
        self.assertEqual(own.read_bytes(), b"#!/bin/sh\necho team hook\n")
        self.assertEqual(self.shelf("install", "no-debug", "--force").returncode, 0)
        self.assertIn(b"no-debug/run.py", own.read_bytes())

    def test_refuses_a_deprecated_hook(self):
        result = self.shelf("install", "whitespace-fix")
        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stderr,
                         "hookshelf: whitespace-fix is deprecated; pass --allow-deprecated to install it anyway\n")
        self.assertEqual(self.shelf("install", "whitespace-fix", "--allow-deprecated").returncode, 0)

    def test_unknown_hook_and_missing_repository(self):
        result = self.shelf("install", "spell-check")
        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stderr,
                         'hookshelf: unknown hook "spell-check"; run "python hookshelf.py list" to see the shelf\n')
        result = self.shelf("install", "no-debug", cwd=self.outside)
        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stderr, "hookshelf: . is not a Git repository (no .git directory)\n")

    def test_repo_option_and_uninstall(self):
        result = self.shelf("install", "branch-name", "no-debug", "--repo", "repo", cwd=self.outside)
        self.assertEqual(result.returncode, 0)
        hooks = self.repo / ".git" / "hooks"
        self.assertTrue((hooks / "pre-push").exists() and (hooks / "pre-commit").exists())
        result = self.shelf("uninstall", "branch-name", "--repo", "repo", cwd=self.outside)
        self.assertEqual(result.stdout, "uninstalled branch-name (pre-push)\n")
        self.assertFalse((hooks / "pre-push").exists())
        self.assertTrue((hooks / "pre-commit").exists())
''')

    w(r / "docs/writing-a-hook.md", '''\
# Writing a hook

A hook is a folder under `hooks/`. The installer finds it through its
`hook.json`; nothing else needs to be registered.

## Folder layout

```text
hooks/<name>/
  hook.json    what the installer and "list" read
  run.py       the hook itself
  README.md    what it checks, its settings, and the message it prints
```

## hook.json

| Field | Meaning |
| --- | --- |
| `name` | The folder name. |
| `stage` | The Git hook that runs it, such as `pre-commit`, `commit-msg`, or `pre-push`. |
| `status` | `stable`, `experimental`, or `deprecated`. A new hook starts as `experimental`. |
| `summary` | One sentence for `python hookshelf.py list`. |
| `settings` | Environment variables the hook reads, each with a `default` and a `help` text; `{}` for none. |

`python hookshelf.py install` refuses a `deprecated` hook unless
`--allow-deprecated` is given.

## run.py

- Use the standard library only, and keep it running on Python 3.9.
- Git starts the hook at the top of the repository with the arguments of its
  stage: `commit-msg` gets the path of the message file; `pre-push` gets the
  remote name and URL, and the pushed refs on standard input.
- Read staged content with Git plumbing (`git diff --cached`,
  `git cat-file`), not from the working tree, so that the check sees what the
  commit will contain.
- Read each setting from its environment variable and fall back to the
  default in `hook.json`.

## Exit codes

| Code | Meaning |
| --- | --- |
| `0` | Pass: Git continues, and the next hook of the stage runs. |
| `1` | Block: print one line per problem to standard error, starting with the hook name and a colon. |

Do not change files in a hook. A hook that rewrites files without re-staging
them leaves the commit out of step with the working tree, which is why
`whitespace-fix` is deprecated.

## Test

Add a test class to `tests/test_hooks.py`. Stage a file in the temporary
repository, run the hook, and compare the exit code and the exact message.
Then run every test from the repository root:

```bash
python -m unittest discover -s tests
```
''')
    w(r / "CHANGELOG.md", '''\
# Changelog

## 0.6.0 - 2024-06-10

- Deprecate `whitespace-fix`: it rewrites files without re-staging them, so
  the commit keeps the old content. Use an editor or formatter setting
  instead. `install` now refuses a deprecated hook unless `--allow-deprecated`
  is given.
- Add `secrets-scan` as experimental. It knows two patterns only.

## 0.5.0 - 2024-04-22

- Add `branch-name` (pre-push).
- `install` takes several hook names; hooks of the same stage run in
  installation order.

## 0.4.0 - 2024-03-04

- `install` no longer replaces an existing hook that hookshelf did not write;
  pass `--force` to replace it.
- Add `uninstall`.

## 0.3.0 - 2024-01-29

- Add `msg-ticket` (commit-msg) and `--repo`.

## 0.2.0 - 2023-12-11

- Add `no-debug` and `whitespace-fix`.

## 0.1.0 - 2023-11-20

- First version: `big-file-guard`, `list`, and `install`.
''')
    w(r / "LICENSE", '''\
MIT License

Copyright (c) 2023 Example Org

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
''')
    w(r / ".github/workflows/test.yml", '''\
name: test

on:
  push:
    branches: [main]
  pull_request:

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python: ["3.9", "3.12"]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python }}
      - run: python -m unittest discover -s tests
''')
    w(r / ".gitignore", "__pycache__/\n*.pyc\n")
    git_init(r, remote="https://github.com/example-org/hookshelf.git")
