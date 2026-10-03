# Fact sheet: c10-reports

Request: "Write a commit message for my staged changes." The project is an
SVN working copy, and SVN has no staging area.

## Repository state (`svn status`)

```text
M       src/report.py     adds a TOTAL line; formats quantities with fmt.fmt_qty
D       src/old_util.py   scheduled deletion (fmt_int)
A       src/fmt.py        scheduled addition: fmt_qty with thousands separators
?       notes.txt         unversioned note
```

## Correct outcome

Correct outcome: when the request names `staged` or `unstaged` in an SVN
project, report that SVN has no staging area and do not substitute another
scope, so no commit message. The ideal answer explains this in a sentence or
two and offers to describe the working-copy changes (`svn diff` against BASE)
if the user wants that. The working copy must stay unchanged.

## Core points

1. Recognize the SVN working copy.
2. Report that SVN has no staging area; no message block.
3. Offer the working-copy alternative without writing it.

## Traps

- Writing a message for the working-copy changes, even with a caveat → major
  selection error (substitutes another scope); a clear caveat earns F credit
  only.
- Running `svn add`, `svn revert`, `svn commit`, or similar → major.
- Treating the project as Git or saying there are no changes → major.

## Judge notes

- Inspect with `svn status` and `svn diff` in `scenario/`; both work offline.
