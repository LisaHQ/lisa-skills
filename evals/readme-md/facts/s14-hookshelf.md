# Fact sheet: s14-hookshelf

Request: "We're making this repository public next week and it still has no README. Please write one." (create mode; target `README.md` at the repository root, which does not exist yet)
Role: collection or catalog, combined with a project overview. Readers arrive looking for a Git hook to use; the README must let them see what the shelf holds, choose a hook, and install it.
Kind: collection of Git hooks with a Python installer script. Reader: developers who want a ready-made hook for their own repository; people who add a hook to the shelf come second.

## Ground truth

- Repository: one commit on `main`, **no tags**, remote https://github.com/example-org/hookshelf.git. Version **0.6.0** (`python hookshelf.py --version` prints `hookshelf 0.6.0`; top entry of `CHANGELOG.md`). License **MIT** (`LICENSE`, Example Org).
- **Not packaged**: no `pyproject.toml`, no `setup.py`, no installed command. People clone the repository and run `python hookshelf.py ...` (the file has no shebang and mode 100644). Needs **Python 3.9 or later** and Git; standard library only.
- `python hookshelf.py list` is read-only and prints NAME, STAGE, STATUS, SUMMARY for the six hooks, sorted by name, from `hooks/<name>/hook.json`:
  - `big-file-guard`: **pre-commit**, stable. Blocks staged files larger than `HOOKSHELF_MAX_KB`, default **500** (1 KB = 1024 bytes; a file exactly at the limit passes).
  - `branch-name`: **pre-push**, stable. Rejects pushes from branches that do not match `HOOKSHELF_BRANCH_PATTERN`, default `^(feature|fix|chore)/[a-z0-9._-]+$`; `main`, `master`, and `develop` always pass.
  - `msg-ticket`: **commit-msg**, stable. Requires a ticket id such as `ABC-123` in the commit message (`HOOKSHELF_TICKET_PATTERN`, default `[A-Z][A-Z0-9]+-[0-9]+`); skips merge and revert commits.
  - `no-debug`: pre-commit, stable. Blocks `breakpoint()`, `import pdb`, `console.log(`, and `debugger;` in the lines a commit adds; `HOOKSHELF_DEBUG_ALLOW` (default empty) lists comma-separated glob patterns of paths to skip.
  - `secrets-scan`: pre-commit, **experimental** (added in 0.6.0). Blocks added lines that look like an AWS access key id or a private key header. Its README: two patterns only, and it "does not replace a real secret scanner". No settings.
  - `whitespace-fix`: pre-commit, **deprecated since 0.6.0**. Strips trailing whitespace but rewrites files without re-staging them, so the commit keeps the old content; its README says to use an editor or formatter setting instead. Never blocks. No settings.
- Settings are environment variables. Defaults are in `hook.json` and in each hook's `README.md`, which also shows the message the hook prints.
- Blocking messages recorded in `tests/test_hooks.py` (standard error, exit code 1): `big-file-guard: assets/demo.bin is 600 KB, over the 500 KB limit`; `no-debug: app.py:2: breakpoint()`; `msg-ticket: the commit message has no ticket id matching [A-Z][A-Z0-9]+-[0-9]+`; `branch-name: branch fix_login does not match ^(feature|fix|chore)/[a-z0-9._-]+$`; `secrets-scan: config.py:1: looks like an AWS access key id`.
- `python hookshelf.py install <name> [<name> ...] [--repo PATH] [--force] [--allow-deprecated]`: PATH defaults to the current directory and must be the top folder of a repository (the one that holds `.git`). It copies each hook to `.git/hookshelf/<name>/`, records the order in `.git/hookshelf/installed.json`, and writes a small `sh` dispatcher at `.git/hooks/<stage>` that runs the installed hooks of that stage **in installation order and stops at the first failure**. It prints `installed <name> (<stage>)` per hook.
- Refusals, each with exit code 1 and nothing installed: an existing `.git/hooks/<stage>` that hookshelf did not write (`hookshelf: .git/hooks/pre-commit exists and was not written by hookshelf; pass --force to replace it`; `--force` overwrites it and keeps no backup); a deprecated hook (`hookshelf: whitespace-fix is deprecated; pass --allow-deprecated to install it anyway`); an unknown name (`hookshelf: unknown hook "spell-check"; run "python hookshelf.py list" to see the shelf`); a PATH without `.git` (`hookshelf: . is not a Git repository (no .git directory)`).
- `python hookshelf.py uninstall <name> [--repo PATH]` removes one hook (one name per call), prints `uninstalled <name> (<stage>)`, and deletes the dispatcher when no hook of that stage is left.
- Tests: `python -m unittest discover -s tests` from the root (20 tests, in temporary Git repositories). CI (`.github/workflows/test.yml`) runs them on **ubuntu-latest only**, with Python 3.9 and 3.12.
- Also present: `docs/writing-a-hook.md` (folder layout, `hook.json` fields, exit codes, how to test a hook) and `CHANGELOG.md` (0.1.0 to 0.6.0; 0.6.0 deprecates `whitespace-fix` and adds `secrets-scan` as experimental).

## Core points a strong README highlights

1. What the shelf is and how to get a hook in two commands (`list`, `install`), on the first screen.
2. The full catalog: all six hooks with stage, status, and what each does, in a form a reader can compare.
3. Experimental and deprecated status marked; `whitespace-fix` not recommended.
4. A short example grounded in the tests or the hook code for the hooks readers most likely pick: the blocking message, or the setting with its default.
5. Requirements and install mechanics: clone, Python 3.9+, Git, `--repo`, several hooks per stage run in order, existing hooks are not replaced without `--force`, `uninstall`.
6. Settings with defaults, or a link to each hook's README.
7. Where to learn to add a hook (`docs/writing-a-hook.md`); MIT license.

## Traps (judge explicitly)

- A current hook missing from the catalog, or a hook that does not exist -> major each. The deprecated `whitespace-fix` left out altogether -> minor (F).
- `whitespace-fix` listed without its deprecated status, or recommended -> major.
- `secrets-scan` not marked experimental -> minor; presented as a complete secret scanner -> major.
- Wrong stage or wrong default for a hook -> major each.
- An invented install channel (pip, pipx, npm, Homebrew, the pre-commit framework) or an installed `hookshelf` command (`hookshelf list`, `./hookshelf.py`) -> major.
- Install shown only as run inside the hookshelf clone, without `--repo` and without saying to run it from the target repository (the hooks land in the clone's own `.git`) -> major; minor when the README explains `--repo` or the working folder elsewhere.
- An invented example message or output -> major.
- Claims that it is tested on Windows or macOS -> minor (the workflow runs on ubuntu-latest only).
- Invented badges (coverage, version, downloads) -> major. A license badge and a badge for `test.yml` are acceptable.
- Every hook README pasted in full instead of summarised and linked -> C penalty.
- Catalog details buried so that a reader cannot compare hooks at a glance -> D penalty.
- The default branch pattern in a table cell with its `|` unescaped (the row breaks; it needs `\|`) -> minor (D).
- Hooks installed into the project's own `.git` while exploring (`changes.txt` reports `vcs hooks: CHANGED`) -> F minor.

## Judge notes

- From the sandbox root, run `python scenario/hookshelf.py list` and `python -m unittest discover -s scenario/tests` (20 tests, a few seconds). Both leave `scenario/` untouched; the tests work in the system temp folder.
- To try `install`, `uninstall`, or a setting, write a script that creates a throwaway repository under `work/` (`git init` through `subprocess`), passes it as `--repo`, and sets variables through `env=`; the sandbox denies environment-variable prefixes. Never point `--repo` at `scenario/`. Without `--repo`, the sandbox root only gets `hookshelf: . is not a Git repository (no .git directory)`.
- An example message with other file names or numbers is fine when its wording matches the hook's `run.py`. One hook may print several lines, but a stage stops at the first failing hook, so one commit never shows blocking messages from two hooks; count such a combined output as one minor error.
- Verified on Windows with Python 3.14 and Git 2.55. The code parses with the Python 3.9 grammar but was not run on 3.9, and the workflow has not run; `git clone` of the remote cannot run here. argparse usage and error text (exit code 2) varies between Python versions, so judge it by meaning.
- The tests also pass on Windows here, but the project's own evidence is the Ubuntu workflow; a README may say where CI runs, not that other systems are tested.
- Acceptable either way: `whitespace-fix` in the catalog marked deprecated, or in a separate deprecation note; settings stated in the README or left to the linked hook READMEs; running the script by path from the target repository or with `--repo`.
- Optional deep catches (not required): `--force` keeps no backup of the hook it replaces; the dispatcher calls the Python interpreter that ran `install` by its full path; a subfolder of a repository is refused as PATH; `secrets-scan` never prints the matched text.
