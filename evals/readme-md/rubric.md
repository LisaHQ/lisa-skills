# README evaluation rubric

Pre-registered on 2026-10-02 before the first run. Dimensions and weights
have not changed since; judge notes in `facts/` and the notes-versus-README
rule were added after the archived rounds, and the harness v2 revision added
error dimensions and clarified the accuracy anchors. Do not pool rounds
judged under different revisions. Judge every outcome (X, Y, Z, ...) against
the scenario's evidence and `facts.md`. Do not reward length, polish, confidence,
or the amount of change for their own sake.

## Inputs

- The request given to the writer.
- The pristine scenario files (the evidence).
- The fact sheet: ground truth, core points, known traps, and judge notes.
- For each outcome: the files the writer added or modified (or, in review
  scenarios, nothing) and the writer's chat summary (`notes.md`).

## Scores (1-5 each, integers)

| Key | Dimension | Weight | What earns a 5 |
| --- | --- | --- | --- |
| A | Accuracy | 3 | Zero factual errors: every command, flag, name, version, path, URL, license, feature, number, and status claim matches the evidence. Nothing invented (badges, install channels, URLs, maintainers, roadmap, benchmarks, contents of unreadable files). |
| B | Core highlighting | 2 | The first ~25 rendered lines tell a newcomer what it is, who it is for, why it matters, and how to start. The fact sheet's core points are present and prominent, ordered by reader value. |
| C | Concision & clarity | 2 | Short, plain sentences; no filler, hype, hedging, or repetition; length proportional to the project's surface; easy to scan. |
| D | Presentation | 1.5 | Professional, modern Markdown: clear hierarchy, sentence-case headings, tagged copy-pasteable code blocks, tables where apt, legitimate badges and visual elements only, renders correctly (closed fences, valid relative links and anchors). |
| E | Friendliness & engagement | 1 | Warm, direct, second person; inviting without hype or condescension ("simply", "just", "easy"); a reader wants to try it. |
| F | Usefulness & honesty | 1.5 | Gives the target reader what they need (prerequisites, install or setup, usage, configuration, help, license or terms when evidenced). Unknowns are surfaced to the requester instead of guessed or padded with placeholders. Request constraints honored (language, review-only, preservation of valuable existing content, no secrets). |

Accuracy anchors: 5 = no errors; 4 = one minor error (cosmetic, low impact);
3 = one major error (a reader following it would fail or be misled) with up
to three minor, or two or more minor; 2 = two major errors, or one major with
four or more minor; 1 = three or more major errors or a fabricated section.
Count each error toward the one dimension it lowers. Score README claims under A; weigh mistakes that appear
only in `notes.md` under F.

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
