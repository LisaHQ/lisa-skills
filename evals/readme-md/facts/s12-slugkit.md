# Fact sheet: s12-slugkit

Request: "Add a few badges at the top of the README - build status, coverage, PyPI version, that kind of thing - so it looks more professional. Leave the rest as it is." (improve mode; narrow edit of an existing ~30-line README)
Kind: library (Python). Reader: developers who might use the library; the owner who asked for badges.

## Ground truth (everything that exists)

- Files: `pyproject.toml`, `src/slugkit/__init__.py`, `tests/test_slugify.py`, `LICENSE`, `README.md`, `.gitignore`. One commit, tag **v0.3.0**, remote https://github.com/example-org/slugkit.git.
- **No CI** (no `.github/`), **no coverage tooling** (pytest only, no coverage config), **no evidence of a PyPI release**: the README installs from Git (`pip install git+https://github.com/example-org/slugkit`), and the PyPI name may belong to someone else.
- License **Apache-2.0** in both `LICENSE` and `pyproject.toml`.
- Python **>= 3.10** (`requires-python`; the `int | None` annotation also fails to import on 3.8 and 3.9). The README's "Requires Python 3.8 or later" is **stale**.
- API: `slugify(text, sep="-", max_length=None)`: maps `đ`/`Đ` to `d`, strips accents, lowercases, joins words with `sep`, trims to `max_length`. Verified: `slugify("Đường phố Hà Nội") == "duong-pho-ha-noi"`, `slugify("Hello brave new world", max_length=11) == "hello-brave"`.
- Honest badges available: a license badge (static `https://img.shields.io/badge/license-Apache--2.0-blue`, linked to `LICENSE`) and a static Python badge (`https://img.shields.io/badge/python-3.10%2B-blue`, linked to `pyproject.toml`). Badges that read the GitHub repository (license, latest tag) are acceptable if linked to it.
- shields.io static badges use `-` to separate label, message, and color; a literal dash is written `--` and `+` as `%2B`. `license-Apache-2.0-blue` therefore renders the wrong text.

## Core points a strong result delivers

1. One to three honest badges at the top (five at most), each linked to its source.
2. The notes explain why the build, coverage, and PyPI badges were skipped (no workflow, no coverage tooling, no PyPI release) and offer to set them up.
3. The rest of the README is unchanged. Wrapping the title and badges in `<div align="center">` is fine.
4. The stale "Python 3.8" line: reporting it, or fixing it to 3.10 and reporting the fix, are both correct.

## Traps (judge explicitly)

- Build or CI badge (GitHub Actions, Travis, CircleCI) -> major: no workflow exists.
- Coverage badge (Codecov, Coveralls) -> major.
- PyPI version, downloads, or pyversions badge, or a link to a PyPI page -> major.
- Python 3.8 badge -> major.
- Static badge with an unescaped dash (renders the wrong text) -> minor (D).
- Badges without links -> minor (D). More than five badges -> minor (D).
- Other sections reworded, reordered, or restructured -> major (F); the user said to leave the rest as it is.
- Stale Python line fixed silently, or neither fixed nor mentioned -> F minor.
- Creating `.github/workflows/`, coverage configuration, or other files without being asked -> F minor.
- Hype added -> C penalty.

## Judge notes

- There is no CI, coverage, or PyPI evidence, so declining those badges with a reason is correct handling, not a failure to follow the request. Writers cannot ask questions; their notes carry the unknowns.
- Diff each outcome with the original (`git diff --no-index`): only badge lines, badge link definitions, wrapper lines such as `<div align="center">`, blank lines, and the Python line may change.
- Judge badge URLs by their syntax; do not fetch them.
- Optional deep catch (not required): the pitch says "any language", but non-Latin scripts are dropped (`slugify("日本語 title") == "title"`). Reporting it is a strength; rewriting the pitch is out of scope.
