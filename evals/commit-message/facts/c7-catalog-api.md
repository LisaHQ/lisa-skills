# Fact sheet: c7-catalog-api

Request (Vietnamese): "Viết commit message cho các thay đổi hiện tại giúp mình
nhé." (Write a commit message for the current changes.) Default `auto`.

## Repository state

```text
 M src/paginate.js         offset = page * size  →  offset = (page - 1) * size (pages are 1-based)
 M test/paginate.test.js   page 1 now expects [1, 2]; adds page 2 → [3, 4]; the old test encoded the bug
```

## Correct selection

Working-tree view for both files.

## Net change

`paginate(items, page, size)` treats `page` as 1-based: page 1 now starts at
the first item instead of skipping the first `size` items. Tests cover pages
1 and 2.

## Core points

1. One fix bullet; the test folded in.
2. The selection report in Vietnamese, the commit message in English (the
   user did not ask for a Vietnamese message).

Example of a strong message:

```text
Start pagination at the first item on page 1

- fix: Compute the page offset as (page - 1) * size, so page 1 no longer
  skips the first `size` items.
```

## Traps

- A commit message written in Vietnamese → major F problem (score F at most 2).
- A report written in English → F deduction.
- Typing it as feat or refactor → C deduction.

## Judge notes

- A translated label before the message block (for example `Mô tả commit:`)
  is acceptable (owner decision); the English `Commit description:` is too.
- An attribution trailer such as `Co-Authored-By:` is neutral.
