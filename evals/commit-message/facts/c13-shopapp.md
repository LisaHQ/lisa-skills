# Fact sheet: c13-shopapp

Request: "Write a commit message for my changes in src/billing/ only." A
folder boundary; inside it, default `auto` with priority working-tree →
staged → unstaged.

## Repository state

```text
 M src/billing/invoice.py         unstaged: the discount comes off before VAT (was: VAT on the gross subtotal,
                                  then the discount); a comment says taxing the gross subtotal overcharged
                                  every discounted invoice
D  src/billing/rates.csv          staged deletion ...
?? src/billing/rates.csv          ... recreated untracked with an extra row: books,0.05
!! src/billing/scratch.tmp        ignored (*.tmp)
M  README.md                      outside the boundary: "Staff stay signed in for two hours."
 M src/auth/session.py            outside the boundary: SESSION_MINUTES 30 → 120
 M tests/billing/test_invoice.py  outside the boundary: test_discount_comes_off_before_vat (100, discount 10 → 97.20)
```

HEAD's `total()` docstring already says "VAT is due on the discounted
price", while its code taxes the gross subtotal: the defect is established
inside the boundary.

## Correct selection

Inside `src/billing/`, working-tree view: `invoice.py`, and `rates.csv` as
one net modification (the staged deletion plus the untracked recreation add
a books row at 5%). Excluded: everything outside the boundary
(`README.md`, `src/auth/session.py`, `tests/billing/test_invoice.py`) and the
ignored `scratch.tmp`.

## Net change

- `total()` subtracts the discount before computing VAT. For a 100 food
  invoice (8% VAT) with a discount of 10, the total is 97.20 instead of 98.00.
- A books category with 5% VAT; before, a books invoice raised `KeyError`.

## Core points

1. A fix for the discount and VAT order, before a separate bullet for the
   books rate (feat or chore). A split recommendation is a plus.
2. Nothing from outside the boundary in the message, including the related
   regression test. Mentioning that test in the report, or suggesting to
   include it, is optional credit.
3. `rates.csv` described as changed (a books rate added), not as deleted.
4. Report: auto (default) within `src/billing/`; `rates.csv`'s deletion and
   recreation reconciled into one modification; out-of-boundary paths
   excluded. Naming the ignored `scratch.tmp` in the report is neutral.

Example of a strong message:

```text
Apply invoice discounts before VAT

- fix(billing): Subtract the discount before computing VAT instead of
  taxing the gross subtotal.
- feat(billing): Add a 5% VAT rate for the books category.
```

## Traps

- The regression test in the message → major (out of boundary).
- The session timeout, 120 minutes, or the README → major (out of boundary).
- `rates.csv` described as deleted, or as deleted and re-added → major.
- `scratch.tmp` in the message → major (ignored file).
- Claiming tests pass → major (invented; the only test is outside the
  boundary).
- One merged bullet that hides the books rate → C deduction.
- The rate bullet before the fix → C deduction (order).
- Typing the discount change as feat → C deduction (the defect is
  established).

## Judge notes

- `git diff HEAD` lists `src/billing/rates.csv` as deleted because it ignores
  the untracked recreation; compare `git show HEAD:src/billing/rates.csv`
  with the working file.
- An attribution trailer such as `Co-Authored-By:` is neutral.
