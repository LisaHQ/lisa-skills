# Fact sheet: c8-invoices

Request: "I'm going to squash my last three commits into one. Write the
commit message for HEAD~3..HEAD." An explicit revision range: it takes
precedence over working changes.

## Repository state

```text
35d83f5 Add export tests        tests/test_export.py
0d732df Fix header escaping     header written through csv.writer instead of ",".join
e9ed527 Add CSV export          invoices/export.py with export_csv
7d898b8 Initial import          (the range's base)
 M invoices/models.py           uncommitted: DEBUG print in load()
```

## Correct selection

The net diff of HEAD~3..HEAD (7d898b8 → 35d83f5). The uncommitted change in
`invoices/models.py` is excluded.

## Net change

- New `invoices/export.py`: `export_csv(invoices, fh)` writes a CSV with the
  header Number, Customer, Total (VND) and one row per invoice through
  `csv.writer`, so fields with commas are quoted; totals are whole numbers.
- New test `tests/test_export.py` for the header and a quoted customer name.
- The "header escaping" commit fixed code that never existed at the base, so
  the squashed change contains no fix.

## Core points

1. One feat for CSV export, describing the net result.
2. No separate fix bullet for header escaping; no mention of the DEBUG print.
3. Report: explicit range HEAD~3..HEAD; uncommitted changes excluded.

Example of a strong message:

```text
Add CSV export for invoices

- feat(export): Export invoices to CSV with a Number, Customer, and Total
  (VND) header, quoting fields that contain commas.
```

## Traps

- Mentioning the DEBUG print or `models.py` → major (blends working changes).
- A fix bullet for header escaping → major (describes an intermediate edit
  that is not part of the net change).
- Listing the three commits one by one instead of the net change → C or D
  deduction.
