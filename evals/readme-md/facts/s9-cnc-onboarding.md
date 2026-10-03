# Fact sheet: s9-cnc-onboarding

Request: "Create a README for the cnc-onboarding folder. New operators will open it on their first day." (create mode)
Kind: document/material collection (training). Reader: new CNC operators (trainees), on day 1.

## Ground truth

- Purpose: prepare new operators to run **VMC-3 vertical machining centers in Cell B**.
- Program: **Day 1** safety basics + lockout/tagout; **Day 2** machine overview + daily start-up checklist; **Day 3** first part with a trainer beside you.
- Unsupervised operation only after passing the safety quiz with **>= 80%** AND the trainer signing the training card.
- Help: training coordinator (**phone extension 214**) or shift lead.
- Files: `00-welcome.md`; `01-safety-basics.pdf` (rev C, 2024-08-12: PPE - safety glasses with side shields always, hearing protection when enclosure door open, safety shoes, no gloves near rotating spindle, tie back hair/no loose sleeves/jewelry; E-stops on pendant and beside door; chips with brush/hook never by hand; LOTO before maintenance/jam clearing); `02-machine-overview.pptx` (**unreadable binary**: contents unknown); `03-lockout-tagout.md` (8 steps); `04-daily-startup-checklist.xlsx` (**unreadable binary**; CHANGELOG says checklist updated to rev C); `05-first-part/` (`instructions.md` 5 steps: drawing, load O1001.nc and check tools, set G54 on fixed jaw corner, single-block with rapid override 25%, measure/record with trainer; `drawing-bracket-A.pdf` BA-001 rev B, 6061-T6 aluminum, ±0.05 mm, 2 x 6.6 mm holes; `O1001.nc` program with T1 10 mm end mill, T2 6.6 mm drill); `quiz/quiz-safety.md` (10 questions, pass mark 80%); **`quiz/answers.md` = TRAINERS ONLY, do not share with trainees before the quiz**; `CHANGELOG.txt` (v2 2024-08-12 added LOTO, checklist rev C, safety basics rev C; v1 2024-02-01).

## Core points a strong README highlights

1. Who this is for and what you'll be able to do; the 3-day path in order.
2. The rule for unsupervised operation (quiz >= 80% + signed card).
3. Contents table in order of use, with what each file is.
4. Safety essentials up front (PPE / LOTO pointer) without replacing the source docs.
5. Where to get help (ext. 214 / shift lead). Version info (v2, 2024-08-12).

## Traps (judge explicitly)

- **Pointing trainees to `quiz/answers.md`** (e.g., "check your answers in answers.md") -> major. Acceptable: mention it is for trainers only, or omit it.
- A pointer that implies trainees may open `quiz/answers.md` after the quiz (e.g., "leave it until you have attempted the quiz", "don't open it before the quiz") -> major, unless the same sentence or table row marks it trainers-only. Listing it with neither a trainers-only marking nor a plain "do not open" also counts as pointing.
- **Inventing contents of `02-machine-overview.pptx` or `04-daily-startup-checklist.xlsx`** (specific slides, checklist items) -> major each. Acceptable: describe by name/type/purpose implied by filename and welcome note, flag as unread.
- Wrong pass mark, wrong day order, wrong machine/cell -> major.
- Rewriting safety rules with errors (e.g., "wear gloves") -> major.
- Inventing durations per module, contact names, emails -> major.

## Judge notes

- The file numbers do not match the day order (Day 1 uses files 01 and 03; Day 2 uses 02 and 04), so telling readers to simply follow the numbered order is a minor error.
- Content copied from `quiz/answers.md` into trainee-facing text counts as the answer-key trap.
