# README evaluation rubric

Pre-registered on 2026-10-02 before the first run. Dimension names and
weights have not changed since; judge notes in `facts/` and the
notes-versus-README rule were added after the archived rounds, and the
harness v2 revision added error dimensions and clarified the accuracy
anchors. The role revision of 2026-10-05, written before any round used it,
rewrote what earns a 5 in B to F: each is judged for the reader of the
README's role, which every fact sheet now names; C sizes length by what the
fact sheet's readers must do and marks copied content; D scores how easily
that reader reads and finds things, on a default surface and only for
elements the writer added; F counts linked documents. It also added the
rule for visual elements and plainness below, the one-weakness-one-score
routing, and the guidance for review scenarios. Do not pool rounds judged
under different revisions. Judge every outcome (X, Y, Z, ...) against the
scenario's evidence and `facts.md`. Do not reward length, polish, confidence,
or the amount of change for their own sake, and neither reward nor penalize
visual elements or plainness for their own sake.

## Inputs

- The request given to the writer.
- The pristine scenario files (the evidence).
- The fact sheet: the README's role, ground truth, core points, known traps,
  and judge notes.
- For each outcome: the files the writer added or modified (or, in review
  scenarios, nothing) and the writer's chat summary (`notes.md`).

## Roles

The fact sheet's `Role:` line names the job the README does. Judge B to F by
what the README does for the reader of that role. When the line combines
roles, the reader it names first gets the first screen, and F covers every
role named. Writers do not see the fact sheet, and some skill versions have
them name a role in their notes: a role named there, whether or not it
matches the fact sheet, is neither a strength nor an error.

| Role | What its reader must be able to do |
| --- | --- |
| Project overview | Understand what it is and whether it fits them, and reach a first result |
| Component guide | Use, integrate, or change the part from the rest of the system |
| Development or operations guide | Carry out the work the files support: set up, run, verify, or recover |
| Collection or catalog | See what the collection holds, choose an item, and use it |

## Scores (1-5 each, integers)

| Key | Dimension | Weight | What earns a 5 |
| --- | --- | --- | --- |
| A | Accuracy | 3 | Zero factual errors: every command, flag, name, version, path, URL, license, feature, number, and status claim matches the evidence. Nothing invented (badges, install channels, URLs, maintainers, roadmap, benchmarks, contents of unreadable files). |
| B | Core highlighting | 2 | The first ~25 rendered lines give the role's reader what they need first: what it is, whether it is for them, why it matters, and the first step of that reader's job (Roles table). The fact sheet's core points are present and prominent, ordered by reader value. |
| C | Concision & clarity | 2 | Short, plain sentences; no filler, hype, hedging, or repetition; length proportional to what the fact sheet's readers must do (a passage none of them needs is excess, whatever the total); nothing the writer copied that a link to an existing document would serve. |
| D | Presentation | 1.5 | Easy to read and to find things in, as a GitHub-style Markdown renderer shows it unless the fact sheet names another surface: each heading says what its section answers, and nothing the reader came for sits under an unrelated heading (a README that fits one screen needs few headings); tables where items are compared, and lists, prose, or subsections where those read better; sentence-case headings; tagged copy-pasteable code blocks; no badge, emoji, alert, image, centered header, or navigation row the writer added gets in the way of reading or finding; renders correctly (closed fences, valid relative links and anchors). Decoration and plainness neither raise nor lower the score by themselves. |
| E | Friendliness & engagement | 1 | Warm, direct, second person; inviting without condescension ("simply", "just", "easy"); the reader feels invited to take the next step: to try the project, or to start the task. |
| F | Usefulness & honesty | 1.5 | The role's reader can do their job from the README and its links (prerequisites, install or setup, usage, configuration, help, license or terms when evidenced). Unknowns are surfaced to the requester instead of guessed or padded with placeholders. Request constraints honored (language, review-only, preservation of valuable existing content, no secrets). |

Accuracy anchors: 5 = no errors; 4 = one minor error (cosmetic, low impact);
3 = one major error (a reader following it would fail or be misled) with up
to three minor, or two or more minor; 2 = two major errors, or one major with
four or more minor; 1 = three or more major errors or a fabricated section.
Count each error toward the one dimension it lowers. Score README claims under A; weigh mistakes that appear
only in `notes.md` under F. One weakness lowers one score: a wrong claim,
command, or example, A; what the first screen lacks, or a core point placed
too low, B; excess, hype, and wording, C; layout and rendering, D; tone, E;
anything else the reader needs that is missing, F. A fact-sheet trap counts
under the dimension its line names, or under A when it names none.

In a review scenario, judge the review itself for the owner who asked for
it: C, D, and E are its wording, its order and layout, and its tone, and the
first-screen, heading, and renderer tests do not apply; F is whether the
owner can act on every finding with no file changed.

Weighted score = (3A + 2B + 2C + 1.5D + 1E + 1.5F) / 11, reported to two
decimals.

## Output (JSON)

Judge each outcome on its own against the evidence first, then compare them.

```json
{
  "scenario": "<id>",
  "X": {
    "scores": {"A": 0, "B": 0, "C": 0, "D": 0, "E": 0, "F": 0},
    "weighted": 0.0,
    "lines": 0,
    "errors": [{"severity": "major|minor", "dimension": "A|B|C|D|E|F", "claim": "...", "evidence": "..."}],
    "strengths": ["..."],
    "weaknesses": ["..."]
  },
  "Y": {"...": "same shape, one entry per outcome"},
  "ranking": ["best label", "...", "worst label"],
  "confidence": "low|medium|high",
  "decisive_reasons": ["..."]
}
```

`lines` is the README's line count (0 for review-only outcomes). List every
factual error with its evidence (file and line, or command output). Rank by
overall quality under this rubric; ties are not allowed in `ranking`, so break
them by accuracy, then core highlighting, then concision.
