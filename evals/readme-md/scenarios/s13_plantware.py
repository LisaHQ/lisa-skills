"""Scenario s13: README for a PyPI-published package that lives in a subfolder of an internal monorepo (create mode)."""
from fixture import w, git_init, commit_all

ROOT = "s13-plantware"

SHIFTCAL_PYPROJECT = '''\
[build-system]
requires = ["hatchling>=1.24"]
build-backend = "hatchling.build"

[project]
name = "shiftcal"
version = "1.2.0"
description = "Work out which crew is on shift at any moment from a rotating pattern."
readme = "README.md"
requires-python = ">=3.10"
license = "MIT"
authors = [{ name = "Example Org", email = "opensource@example.invalid" }]
keywords = ["shift", "rota", "roster", "crew", "manufacturing"]
classifiers = [
  "Programming Language :: Python :: 3",
  "Typing :: Typed",
]
dependencies = []

[project.urls]
Source = "https://github.com/example-org/plantware/tree/main/packages/shiftcal"
Changelog = "https://github.com/example-org/plantware/blob/main/packages/shiftcal/CHANGELOG.md"
Issues = "https://github.com/example-org/plantware/issues"

[tool.hatch.build.targets.wheel]
packages = ["src/shiftcal"]

[tool.pytest.ini_options]
pythonpath = ["src"]
testpaths = ["tests"]
'''
README_FIELD = 'readme = "README.md"\n'


def build(base):
    r = base / ROOT
    # Root of the monorepo: an internal guide whose map already links the missing package README.
    w(r / "README.md", '''\
# plantware

Software that runs on the shop floor at Example Org, kept in one repository by
the plant software team. This page is for team members; ask in
`#plant-software` when something here is out of date.

## Repository map

| Path | What it is |
| --- | --- |
| [`apps/andon-board`](apps/andon-board) | Andon display for the press hall (internal app) |
| [`packages/shiftcal`](packages/shiftcal/README.md) | Shift rota calculations; published to PyPI as `shiftcal` |

## Set up

You need [uv](https://docs.astral.sh/uv/). From the repository root:

```bash
uv sync --all-packages
uv run pytest packages/shiftcal
```

`uv sync` creates `.venv` with Python 3.12 and installs every workspace member
in editable mode, so the apps always run against the `shiftcal` in this
checkout.

## Releasing shiftcal

Bump `version` in `packages/shiftcal/pyproject.toml`, add the release to its
`CHANGELOG.md`, and push a tag named `shiftcal-v<version>`. The
`publish-shiftcal` workflow builds the package and uploads it to PyPI.

## License

The repository is public so that `shiftcal` users can read the source and
report issues. The apps under `apps/` are proprietary and for internal use at
Example Org only; no license is granted for them. `packages/shiftcal` is open
source under the MIT license (see
[`packages/shiftcal/LICENSE`](packages/shiftcal/LICENSE)).
''')
    w(r / "pyproject.toml", '''\
# Workspace root of the plant software monorepo. Nothing is built or published
# from here; every app and package has its own pyproject.toml.
[project]
name = "plantware"
version = "0.0.0"
description = "Plant software monorepo (workspace root, never published)"
requires-python = ">=3.12"
dependencies = []

[dependency-groups]
dev = ["pytest>=8", "ruff>=0.6"]

[tool.uv]
package = false

[tool.uv.workspace]
members = ["apps/*", "packages/*"]
''')
    w(r / ".python-version", "3.12\n")
    w(r / ".gitignore", ".venv/\n__pycache__/\n*.egg-info/\ndist/\n")
    w(r / ".github/workflows/ci.yml", '''\
name: CI

on:
  push:
    branches: [main]
  pull_request:

jobs:
  shiftcal:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python: ["3.10", "3.11", "3.12", "3.13"]
    defaults:
      run:
        working-directory: packages/shiftcal
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python }}
      - run: python -m pip install . pytest
      - run: python -m pytest -q
''')
    w(r / ".github/workflows/publish-shiftcal.yml", '''\
name: Publish shiftcal

on:
  push:
    tags: ["shiftcal-v*"]

jobs:
  pypi:
    runs-on: ubuntu-latest
    environment: pypi
    permissions:
      id-token: write  # PyPI trusted publishing; no API token is stored
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v5
      - run: uv build --package shiftcal --out-dir dist
      - uses: pypa/gh-action-pypi-publish@release/v1
''')
    # An internal consumer: shows real use, and must not leak into the public page.
    w(r / "apps/andon-board/pyproject.toml", '''\
[build-system]
requires = ["hatchling>=1.24"]
build-backend = "hatchling.build"

[project]
name = "andon-board"
version = "0.9.0"
description = "Andon display for the press hall: line status and the crew on duty. Internal."
requires-python = ">=3.12"
classifiers = ["Private :: Do Not Upload"]
dependencies = ["shiftcal"]

[tool.uv.sources]
shiftcal = { workspace = true }

[tool.hatch.build.targets.wheel]
packages = ["src/andon_board"]
''')
    w(r / "apps/andon-board/src/andon_board/__init__.py", '''\
"""Banner line for the andon display: which crew is on duty in the press hall."""
from datetime import date, datetime

from shiftcal import Pattern, Roster

# Press hall rota: two day shifts, two night shifts, four days off.
# Crew A worked the first day shift of the rotation on 1 January 2024.
ROSTER = Roster(Pattern.parse("2D 2N 4O"), crews=["A", "B", "C", "D"], start=date(2024, 1, 1))


def banner(now: datetime | None = None) -> str:
    """Text for the top of the board. `now` is plant local time (the board PC runs in it)."""
    shift = ROSTER.on_duty(now or datetime.now())
    if shift is None:
        return "No crew rostered"
    name = "Day" if shift.code == "D" else "Night"
    return f"Crew {shift.crew} - {name} shift until {shift.end:%H:%M}"
''')
    # The published package the request targets. Its README does not exist yet.
    w(r / "packages/shiftcal/pyproject.toml", SHIFTCAL_PYPROJECT.replace(README_FIELD, ""))
    w(r / "packages/shiftcal/LICENSE", '''\
MIT License

Copyright (c) 2024 Example Org

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
    w(r / "packages/shiftcal/CHANGELOG.md", '''\
# Changelog

## 1.2.0 - 2024-06-12

- Add `Roster.shifts_for(crew, first, last)`, which lists a crew's working
  days in a date range.

## 1.1.0 - 2024-04-03

- Add `day_start` and `night_start` to `Roster` for plants whose shifts do not
  change at 06:00 and 18:00.

## 1.0.0 - 2024-02-19

First stable release.

- **Breaking:** `Roster.on_duty` rejects timezone-aware datetimes with
  `ValueError`. Earlier versions converted them to the machine's time zone
  without saying so, which named the wrong crew on servers that do not run in
  plant time. Pass naive datetimes in plant local time.
- **Breaking:** `Roster` raises `ValueError` when two crews would hold the same
  shift on one day, instead of reporting the first crew it finds.
''')
    w(r / "packages/shiftcal/docs/patterns.md", '''\
# Shift patterns

A pattern describes the rotation one crew works, one shift code per calendar
day. `shiftcal` repeats it without end and staggers the other crews along it.

## Syntax

A pattern is a string of tokens separated by whitespace. Each token is a count
followed by a shift code:

| Code | Meaning | Default hours |
| --- | --- | --- |
| `D` | Day shift | 06:00 to 18:00 |
| `N` | Night shift | 18:00 to 06:00 the next morning |
| `O` | Off | |

`2D 2N 4O` reads "two day shifts, two night shifts, four days off": an
eight-day cycle. The rules:

- Counts are whole numbers from 1 up. `0D` is rejected.
- Codes are upper case. `2d` is rejected.
- A token has no space inside: write `2D`, not `2 D`.
- A code may appear more than once: `3D 1O 3N 3O` is valid.
- Any other token, or an empty string, raises `ValueError`.

`Pattern.parse` returns a `Pattern`. `len(pattern)` is the cycle length in
days, `pattern.codes` holds the code for each day, and `str(pattern)` gives the
pattern back in its shortest form (`"1D 1D 2N 4O"` becomes `"2D 2N 4O"`).

## How crews share a pattern

A `Roster` puts every crew on the same pattern. With a cycle of `L` days and
`n` crews, crew number `i` (counting from 0, in the order you list them) runs
`i * L / n` days behind the first crew. The first crew works day 1 of the
pattern on the roster's `start` date; the rotation also runs backwards from
there, so dates before `start` are answered too.

For `2D 2N 4O` and crews A to D, each crew is two days behind the one before:

| Crew | Day 1 | Day 2 | Day 3 | Day 4 | Day 5 | Day 6 | Day 7 | Day 8 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A | D | D | N | N | O | O | O | O |
| B | O | O | D | D | N | N | O | O |
| C | O | O | O | O | D | D | N | N |
| D | N | N | O | O | O | O | D | D |

`Roster` raises `ValueError` when either of these rules is broken:

- The cycle length must be divisible by the number of crews. Eight days cannot
  be shared by three crews.
- Two crews may not hold the same shift on the same day. `4D 4O` with four
  crews puts two crews on days at once; with two crews it is valid.

A roster does not have to cover every shift. `5D 2O` with one crew and a
Monday `start` works weekday day shifts only, and `on_duty` returns `None` at
night and at the weekend.

## Shift hours

A day has two shifts. The day shift runs from `day_start` to `night_start` on
the same date. The night shift runs from `night_start` to `day_start` on the
next date and belongs to the date it starts on. A shift owns its first minute:
at 18:00 sharp the night crew is on duty.

The defaults are 06:00 and 18:00. Pass `day_start` and `night_start` to
`Roster` to change them; `day_start` must be the earlier of the two.
Three-shift systems (early, late, night) cannot be described.

## Common patterns

| Name | Pattern | Crews | Covers |
| --- | --- | --- | --- |
| 2-2-4 | `2D 2N 4O` | 4 | Every shift |
| Four on, four off | `4D 4O 4N 4O` | 4 | Every shift |
| DuPont | `4N 3O 3D 1O 3N 3O 4D 7O` | 4 | Every shift |
| Day crews, four on, four off | `4D 4O` | 2 | Day shifts, every day |
| Weekdays | `5D 2O` | 1 | Day shifts, five days in seven |
''')
    w(r / "packages/shiftcal/src/shiftcal/py.typed", "")
    w(r / "packages/shiftcal/src/shiftcal/__init__.py", '''\
"""Work out which crew is on shift at any moment from a rotating pattern.

A Pattern is the rotation one crew works ("2D 2N 4O": two day shifts, two
night shifts, four days off). A Roster staggers several crews along that
pattern from a start date and answers who is on duty at a given moment.

Every datetime is naive and means plant local time. shiftcal has no notion of
time zones or daylight saving time.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from itertools import groupby
from typing import Sequence

__all__ = ["Pattern", "Roster", "Shift"]
__version__ = "1.2.0"

DAY, NIGHT, OFF = "D", "N", "O"
_TOKEN = re.compile("([0-9]+)([DNO])")


@dataclass(frozen=True, slots=True)
class Pattern:
    """The rotation one crew works: a shift code ("D", "N", or "O") for each day of the cycle."""

    codes: tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.codes:
            raise ValueError("a pattern needs at least one day")
        for code in self.codes:
            if code not in (DAY, NIGHT, OFF):
                raise ValueError(f"unknown shift code {code!r}: use D, N, or O")

    @classmethod
    def parse(cls, text: str) -> Pattern:
        """Read whitespace-separated <count><code> tokens, such as "2D 2N 4O"."""
        codes: list[str] = []
        for token in text.split():
            match = _TOKEN.fullmatch(token)
            if match is None or int(match.group(1)) == 0:
                raise ValueError(f"invalid pattern token {token!r}: expected <count><code>, such as 2D, 2N, or 4O")
            codes.extend(match.group(2) * int(match.group(1)))
        return cls(tuple(codes))

    def __len__(self) -> int:
        return len(self.codes)

    def __str__(self) -> str:
        return " ".join(f"{len(list(run))}{code}" for code, run in groupby(self.codes))


@dataclass(frozen=True, slots=True)
class Shift:
    """One crew's shift. `day` is the date the shift starts on, also after midnight on a night shift."""

    crew: str
    code: str
    day: date
    start: datetime
    end: datetime


class Roster:
    """Crews that work one pattern, each a fixed number of days behind the crew before it.

    Crew number i (counting from 0) runs i * len(pattern) / len(crews) days
    behind the first crew, which works day 1 of the pattern on `start`.
    """

    def __init__(self, pattern: Pattern, crews: Sequence[str], start: date, *,
                 day_start: time = time(6, 0), night_start: time = time(18, 0)) -> None:
        crews = tuple(crews)
        if not crews:
            raise ValueError("a roster needs at least one crew")
        if len(set(crews)) != len(crews):
            raise ValueError("crew names must be unique")
        if len(pattern) % len(crews):
            raise ValueError(f"a cycle of {len(pattern)} days cannot be shared evenly by {len(crews)} crews")
        if not day_start < night_start:
            raise ValueError("day_start must be earlier than night_start")
        self.pattern = pattern
        self.crews = crews
        self.start = start
        self.day_start = day_start
        self.night_start = night_start
        self._lag = len(pattern) // len(crews)
        for offset in range(len(pattern)):
            day = start + timedelta(days=offset)
            for code, name in ((DAY, "day"), (NIGHT, "night")):
                clash = [crew for index, crew in enumerate(crews) if self._code(index, day) == code]
                if len(clash) > 1:
                    raise ValueError(f"crews {clash[0]} and {clash[1]} would both work the {name} shift "
                                     f"on day {offset + 1} of the cycle")

    def _code(self, index: int, day: date) -> str:
        position = ((day - self.start).days - index * self._lag) % len(self.pattern)
        return self.pattern.codes[position]

    def _shift(self, crew: str, code: str, day: date) -> Shift:
        if code == DAY:
            return Shift(crew, code, day, datetime.combine(day, self.day_start),
                         datetime.combine(day, self.night_start))
        return Shift(crew, code, day, datetime.combine(day, self.night_start),
                     datetime.combine(day + timedelta(days=1), self.day_start))

    def on_duty(self, when: datetime) -> Shift | None:
        """The shift being worked at `when`, or None when nobody is rostered then.

        `when` is a naive datetime in plant local time; a timezone-aware one
        raises ValueError. A moment before `day_start` belongs to the night
        shift that started on the previous date.
        """
        if when.tzinfo is not None:
            raise ValueError("on_duty() takes a naive datetime in plant local time, not a timezone-aware one")
        if when.time() < self.day_start:
            day, code = when.date() - timedelta(days=1), NIGHT
        elif when.time() < self.night_start:
            day, code = when.date(), DAY
        else:
            day, code = when.date(), NIGHT
        for index, crew in enumerate(self.crews):
            if self._code(index, day) == code:
                return self._shift(crew, code, day)
        return None

    def shifts_for(self, crew: str, first: date, last: date) -> list[tuple[date, str]]:
        """(date, code) for every day the crew works from `first` to `last`, both included.

        Days off are left out. An unknown crew raises KeyError.
        """
        if crew not in self.crews:
            raise KeyError(crew)
        index = self.crews.index(crew)
        worked = []
        for offset in range((last - first).days + 1):
            day = first + timedelta(days=offset)
            code = self._code(index, day)
            if code != OFF:
                worked.append((day, code))
        return worked
''')
    w(r / "packages/shiftcal/tests/test_roster.py", '''\
"""Roster behaviour as plain asserts; run with pytest."""
from datetime import date, datetime, time, timezone

from shiftcal import Pattern, Roster, Shift

PATTERN = Pattern.parse("2D 2N 4O")
ROSTER = Roster(PATTERN, crews=["A", "B", "C", "D"], start=date(2024, 1, 1))


def raises(error, call, *args, **kwargs):
    try:
        call(*args, **kwargs)
    except error:
        return True
    return False


def test_pattern_parse():
    assert PATTERN.codes == ("D", "D", "N", "N", "O", "O", "O", "O")
    assert len(PATTERN) == 8
    assert str(Pattern.parse("1D 1D 2N 4O")) == "2D 2N 4O"


def test_pattern_rejects_bad_tokens():
    for text in ("2X", "D2", "2d", "0D", "2 D", ""):
        assert raises(ValueError, Pattern.parse, text), text


def test_day_shift():
    assert ROSTER.on_duty(datetime(2024, 1, 1, 9, 30)) == Shift(
        crew="A", code="D", day=date(2024, 1, 1),
        start=datetime(2024, 1, 1, 6, 0), end=datetime(2024, 1, 1, 18, 0))


def test_night_shift_belongs_to_the_date_it_starts_on():
    late = ROSTER.on_duty(datetime(2024, 1, 1, 22, 0))
    early = ROSTER.on_duty(datetime(2024, 1, 2, 2, 0))  # 02:00 on 2 January: still the night of 1 January
    assert late == early == Shift(
        crew="D", code="N", day=date(2024, 1, 1),
        start=datetime(2024, 1, 1, 18, 0), end=datetime(2024, 1, 2, 6, 0))


def test_a_shift_owns_its_first_minute():
    assert ROSTER.on_duty(datetime(2024, 1, 1, 17, 59)).crew == "A"
    assert ROSTER.on_duty(datetime(2024, 1, 1, 18, 0)).crew == "D"
    assert ROSTER.on_duty(datetime(2024, 1, 2, 5, 59)).crew == "D"
    assert ROSTER.on_duty(datetime(2024, 1, 2, 6, 0)).crew == "A"


def test_rotation_over_one_cycle():
    days = [ROSTER.on_duty(datetime(2024, 1, d, 12, 0)).crew for d in range(1, 10)]
    nights = [ROSTER.on_duty(datetime(2024, 1, d, 23, 0)).crew for d in range(1, 10)]
    assert days == ["A", "A", "B", "B", "C", "C", "D", "D", "A"]
    assert nights == ["D", "D", "A", "A", "B", "B", "C", "C", "D"]


def test_the_rotation_runs_backwards_from_start():
    shift = ROSTER.on_duty(datetime(2024, 1, 1, 2, 0))  # the night of 31 December 2023
    assert (shift.crew, shift.day) == ("C", date(2023, 12, 31))


def test_custom_start_times():
    roster = Roster(PATTERN, crews=["A", "B", "C", "D"], start=date(2024, 1, 1),
                    day_start=time(7, 0), night_start=time(19, 0))
    assert roster.on_duty(datetime(2024, 1, 2, 6, 30)).crew == "D"  # the night of 1 January ends at 07:00
    assert roster.on_duty(datetime(2024, 1, 1, 18, 30)).crew == "A"
    assert raises(ValueError, Roster, PATTERN, crews=["A", "B", "C", "D"], start=date(2024, 1, 1),
                  day_start=time(18, 0), night_start=time(6, 0))


def test_aware_datetime_is_rejected():
    assert raises(ValueError, ROSTER.on_duty, datetime(2024, 1, 1, 9, 30, tzinfo=timezone.utc))


def test_nobody_rostered_returns_none():
    weekdays = Roster(Pattern.parse("5D 2O"), crews=["A"], start=date(2024, 1, 1))  # a Monday
    assert weekdays.on_duty(datetime(2024, 1, 5, 9, 0)).crew == "A"  # Friday
    assert weekdays.on_duty(datetime(2024, 1, 6, 9, 0)) is None  # Saturday
    assert weekdays.on_duty(datetime(2024, 1, 5, 20, 0)) is None  # this pattern has no night shift


def test_cycle_length_must_be_divisible_by_the_number_of_crews():
    assert raises(ValueError, Roster, PATTERN, crews=["A", "B", "C"], start=date(2024, 1, 1))


def test_two_crews_on_one_shift_are_rejected():
    four_on_four_off = Pattern.parse("4D 4O")
    assert raises(ValueError, Roster, four_on_four_off, crews=["A", "B", "C", "D"], start=date(2024, 1, 1))
    assert Roster(four_on_four_off, crews=["A", "B"], start=date(2024, 1, 1)).on_duty(
        datetime(2024, 1, 5, 9, 0)).crew == "B"


def test_shifts_for():
    assert ROSTER.shifts_for("A", date(2024, 1, 1), date(2024, 1, 8)) == [
        (date(2024, 1, 1), "D"), (date(2024, 1, 2), "D"), (date(2024, 1, 3), "N"), (date(2024, 1, 4), "N")]
    assert ROSTER.shifts_for("B", date(2024, 1, 1), date(2024, 1, 2)) == []
    assert raises(KeyError, ROSTER.shifts_for, "E", date(2024, 1, 1), date(2024, 1, 8))
''')
    # The released state: 1.2.0 went to PyPI without a long description.
    git_init(r, remote="https://github.com/example-org/plantware.git", tag="shiftcal-v1.2.0")
    # Since the release, main declares the README that this scenario asks for.
    w(r / "packages/shiftcal/pyproject.toml", SHIFTCAL_PYPROJECT)
    commit_all(r, "shiftcal: use README.md as the PyPI description")
