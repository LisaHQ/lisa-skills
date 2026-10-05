# Fact sheet: s13-plantware

Request: "packages/shiftcal has no README, so its PyPI page is empty. Can you write one?" (create mode; target `packages/shiftcal/README.md`)
Role: project overview and entry point for an independently published package. The README sits in a subfolder of an internal monorepo, but PyPI renders it and its readers are Python developers outside the organisation who have never seen the repository; it is not an internal component guide.
Kind: Python library published to PyPI from a subfolder of a uv monorepo. Reader: Python developers who find `shiftcal` on PyPI and want to know what it does and how to start.

## Ground truth

- Monorepo root: `README.md` is an internal guide for the plant software team (contact `#plant-software`; repository map with `apps/andon-board` as an internal app and `packages/shiftcal` as "Shift rota calculations; published to PyPI as `shiftcal`", linking `packages/shiftcal/README.md`, which does not exist yet; set up with `uv sync --all-packages`; release by pushing a tag `shiftcal-v<version>`). Its License section: the repository is public so that `shiftcal` users can read the source and report issues, the apps are **proprietary** and internal, `packages/shiftcal` is MIT. **No root `LICENSE`.** Root `pyproject.toml` is a uv workspace (`apps/*`, `packages/*`, Python >= 3.12); `.python-version` is 3.12.
- Publication evidence: `.github/workflows/publish-shiftcal.yml` (on tags `shiftcal-v*`: `uv build --package shiftcal`, then PyPI trusted publishing), tag **`shiftcal-v1.2.0`**, the root README, and the request. Remote https://github.com/example-org/plantware.git. Two commits: the tagged release, then `HEAD`, which only adds `readme = "README.md"` to `packages/shiftcal/pyproject.toml` (so PyPI renders this README from the next release).
- CI (`.github/workflows/ci.yml`): pip-installs `packages/shiftcal` and runs pytest on ubuntu-latest with Python **3.10, 3.11, 3.12, 3.13**.
- Package `shiftcal` **1.2.0** (`packages/shiftcal/pyproject.toml`): description "Work out which crew is on shift at any moment from a rotating pattern."; Python **>= 3.10** (3.12 is the workspace's version, not the package minimum); **no dependencies**; **MIT** (`packages/shiftcal/LICENSE`, Example Org); typed (`py.typed`). URLs: Source https://github.com/example-org/plantware/tree/main/packages/shiftcal, Changelog https://github.com/example-org/plantware/blob/main/packages/shiftcal/CHANGELOG.md, Issues https://github.com/example-org/plantware/issues. The pattern guide `docs/patterns.md` is https://github.com/example-org/plantware/blob/main/packages/shiftcal/docs/patterns.md.
- API (`src/shiftcal/__init__.py`; exports `Pattern`, `Roster`, `Shift`):
  - `Pattern.parse("2D 2N 4O")`: whitespace-separated `<count><code>` tokens with codes `D` (day), `N` (night), `O` (off), upper case, count from 1. Invalid tokens (`2X`, `2d`, `0D`) and an empty string raise `ValueError`. `len(pattern)` is the cycle length (8 here).
  - `Roster(pattern, crews, start, *, day_start=time(6, 0), night_start=time(18, 0))`: crew number `i` runs `i * len(pattern) / len(crews)` days behind the first crew, which works day 1 of the pattern on `start`. `ValueError` when the cycle length is **not divisible by the number of crews** (8 days, 3 crews), when two crews would hold the same shift on one day (`4D 4O` with 4 crews), or when `day_start` is not earlier than `night_start`. The two start times are keyword-only.
  - `roster.on_duty(when)` takes a **naive** datetime in plant local time and returns a frozen `Shift(crew, code, day, start, end)`, or **`None`** when nobody is rostered then. A timezone-aware datetime raises `ValueError` (since 1.0.0; earlier versions converted it silently). There is no time zone or daylight-saving handling.
  - A night shift **belongs to the date it starts on** (`Shift.day`). A shift owns its first minute: at 18:00 sharp the night crew is on duty.
  - `roster.shifts_for(crew, first, last)`: `(date, code)` for the crew's working days, both ends included, days off left out. An unknown crew raises `KeyError`.
  - A day has two shifts only; three-shift systems cannot be described.
- Verified with `Roster(Pattern.parse("2D 2N 4O"), crews=["A", "B", "C", "D"], start=date(2024, 1, 1))`:
  - `on_duty(datetime(2024, 1, 1, 9, 30))` -> crew **A**, code `D`, day 2024-01-01, 06:00 to 18:00.
  - `on_duty(datetime(2024, 1, 1, 22, 0))` and `on_duty(datetime(2024, 1, 2, 2, 0))` -> the same shift: crew **D**, code `N`, **day 2024-01-01**, start 2024-01-01 18:00, end 2024-01-02 06:00.
  - Day crews on 1 to 8 January: A A B B C C D D. Night crews: D D A A B B C C.
  - `shifts_for("A", date(2024, 1, 1), date(2024, 1, 8))` -> 1 Jan `D`, 2 Jan `D`, 3 Jan `N`, 4 Jan `N` (a list of `(datetime.date, str)` tuples).
  - `Roster(Pattern.parse("5D 2O"), crews=["A"], start=date(2024, 1, 1))` (a Monday): `on_duty` returns `None` on Saturday 6 January at 09:00 and at 20:00 on any day.
- `CHANGELOG.md`: 1.2.0 (2024-06-12) added `Roster.shifts_for`; 1.1.0 added `day_start` and `night_start`; 1.0.0, the first stable release, rejects aware datetimes and clashing crews. `docs/patterns.md` (77 lines) covers the syntax, how crews share a pattern, shift hours, and common patterns.
- Internal consumer: `apps/andon-board` depends on `shiftcal` from the workspace and calls `Roster.on_duty`.

## Core points a strong README highlights

1. A standalone opening: what `shiftcal` does and for whom (Python code that needs to know which crew is on shift), with no knowledge of the monorepo assumed.
2. `pip install shiftcal`, Python 3.10 or later, no dependencies.
3. A short example that runs as written, with the verified results.
4. Pitfalls: naive plant local time only; a night shift belongs to its start date; the cycle length must be divisible by the number of crews; `None` when nobody is rostered.
5. The pattern syntax in a line or a small table, with an absolute link to `docs/patterns.md` on GitHub; the changelog linked the same way.
6. License: MIT.

## Traps (judge explicitly)

- No registry install shown, or installation only from a checkout or the workspace (`git clone`, `uv sync`, `pip install -e`) -> major (F).
- README written for repository insiders (opens with the monorepo, sends the reader to the root README for setup, `uv sync` as the way to use it) -> B penalty. Count a missing registry install once, under F.
- Relative links or images (`docs/patterns.md`, `LICENSE`, `CHANGELOG.md`, `../../README.md`): they work on GitHub and break on PyPI -> minor (D), counted once.
- An example whose stated result is wrong, an example that passes an aware datetime, or a claim of time zone support -> major each.
- Wrong Python minimum (3.12 is the workspace's), invented dependencies, a coverage badge (there is no coverage tooling) -> major each. A PyPI version badge and a CI badge for `ci.yml` are acceptable; a downloads badge is evidenced too and is not an error.
- Root `README.md` or any other existing file rewritten -> major (F).
- Internal detail on the public page (the `andon-board` app, the proprietary notice, `#plant-software` as a contact) -> minor (F).
- Stating that the whole repository is MIT -> minor.
- `docs/patterns.md` pasted whole instead of summarised and linked -> C penalty.

## Judge notes

- `scenario/src` does not exist, so `import shiftcal` fails from the sandbox root. To run an outcome's example, write a script outside `scenario/` that starts with `import sys; sys.path.insert(0, "scenario/packages/shiftcal/src")`, paste the example, and run it with `python <file>`. The tests are plain asserts: also insert `scenario/packages/shiftcal/tests`, import `test_roster`, and call its 13 `test_*` functions.
- pytest, pip installs, and PyPI are out of reach. Judge publication from the evidence above; do not fetch URLs.
- Surface for D: the PyPI project page, not GitHub. Judge links by their form: PyPI resolves no relative target, so only absolute URLs and in-page anchors work. Any ref is fine in a GitHub URL (`blob/main`, `tree/main`, the tag). Judge everything except link targets as GitHub renders it.
- Acceptable either way: `python -m pip install shiftcal` or `uv add shiftcal` beside or instead of `pip install shiftcal`; a link to https://pypi.org/project/shiftcal/; saying where the source lives in the repository; a short contributor section at the end (clone, `uv sync --all-packages`, `uv run pytest packages/shiftcal`).
- The root README's link to `packages/shiftcal/README.md` is broken until the package README exists; that is by design. Writers cannot ask questions; unknowns belong in their notes.
- Verified on Python 3.14 only. The code uses nothing newer than 3.10 (`dataclass(slots=True)` sets that floor), and none of the results above depends on the Python version.
- Optional deep catches (not required): at `HEAD` the manifest declares `readme = "README.md"`, so a build of the package fails until the README exists (hatchling's rule; not run here), and a note saying so is correct; dates before `start` are answered too, because the rotation runs backwards (02:00 on 1 January 2024 is crew C's night of 31 December 2023); a shift's `start` and `end` are wall-clock times, so across a daylight-saving change the shift is not 12 real hours long.
