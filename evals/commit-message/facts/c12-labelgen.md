# Fact sheet: c12-labelgen

Request (Vietnamese): "Viết commit message bằng tiếng Việt cho các thay đổi
chưa stage (unstaged) giúp mình nhé." (Write a commit message in Vietnamese
for the unstaged changes.) Scope `unstaged` (index → working tree) for every
file, and the user asks for a Vietnamese message.

## Repository state

```text
MM labelgen/label.py      staged: MAX_PART_WIDTH = 20 and a width parameter that cuts part_no[:width];
                          unstaged on top: a last label line f"*{part_no.upper()}*" (Code 39 text) and a docstring line
M  labelgen/cli.py        staged only: --width option passed to render()
 M README.md              unstaged only: the last label line is the part number in Code 39 form
?? tests/test_barcode.py  untracked: asserts render("ab-12", 3)[-1] == "*AB-12*"
```

## Correct selection

Unstaged view for every file: `labelgen/label.py` (the barcode line only),
`README.md`, and the untracked `tests/test_barcode.py`, compared against the
index as an addition. Excluded: the staged width cut in `label.py` and
`labelgen/cli.py`, which has only staged changes.

## Net change

`render` adds a last line holding the part number in upper case between
asterisks, the Code 39 text for a barcode font; the README explains it and a
test covers it.

## Core points

1. One feat about the barcode line, with the README and test folded in.
2. The message in Vietnamese, as requested. Type tokens stay in English
   (`- feat(label):`).
3. The report in Vietnamese: scope unstaged (index → working tree); the
   untracked test included as an addition; the staged width change and
   `cli.py` excluded.

Example of a strong message:

```text
Thêm dòng mã vạch Code 39 vào nhãn

- feat(label): Thêm dòng cuối in số linh kiện viết hoa trong dấu * (dạng
  Code 39) để in bằng font mã vạch.
```

## Traps

- The width cut, `MAX_PART_WIDTH`, the 20-character limit, or `--width` in
  the message → major (staged view, excluded).
- Describing `labelgen/cli.py` → major (staged only).
- An English message → major F problem (score F at most 2).
- A report in English → F deduction.
- Translated type tokens (for example `- tính năng:`) → C or E deduction.
- Leaving the untracked test out of the report, or calling it excluded →
  minor.
- Claiming tests pass → major (invented).
- Separate `test:` or `docs:` bullets → C deduction.

## Judge notes

- `git diff` is the selection; `git diff --cached` is excluded. The unstaged
  hunk's context and removed line show `MAX_PART_WIDTH` and
  `part_no[:width]`: they come from the index, not from the selected change.
  Read the untracked test directly.
- Verified: in the working tree, `render('ab-12', 3)` returns
  `['PART ab-12', 'QTY  3', '*AB-12*']`.
- A translated label before the message block (for example
  `Mô tả commit:`) is acceptable (owner decision); the English
  `Commit description:` is too.
- An attribution trailer such as `Co-Authored-By:` is neutral.
