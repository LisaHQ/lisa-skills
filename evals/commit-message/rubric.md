# Commit message evaluation rubric

Pre-registered on 2026-10-02 before the first run, and revised once before
the first harness v2 round: errors name the dimension they lower, the anchors
are clarified, attribution trailers are neutral, and denied repository
mutations count. Do not pool rounds judged before and after the revision.
Judge every outcome (X, Y, ...) against the scenario repository, its Git or
SVN state, and `facts.md`.
Do not reward length, confidence, or extra advice for their own sake.

## Inputs

- The request given to the writer.
- The pristine scenario repository (the evidence): inspect it with
  `git status`, `git diff`, `git diff --cached`, `git log`, or `svn status` and
  `svn diff`, on a copy if a command could write.
- The fact sheet: the correct selection, net changes, core points, an example
  of a strong message, known traps, and judge notes.
- For each outcome: `notes.md`, the writer's final chat message (normally a
  short selection report plus the commit message), and `changes.txt`, which
  must show no file changes and unchanged version-control state. It also
  lists repository-changing commands the harness denied (`denied attempts`)
  and notes a session that stopped at its turn limit.

## Scores (1-5 each, integers)

| Key | Dimension | Weight | What earns a 5 |
| --- | --- | --- | --- |
| A | Accuracy & grounding | 3 | Every statement in the message and report matches the selected changes: behavior, names, values, files, and versions. Nothing invented (tests run or passing, performance, motivation, issue numbers). Material consequences are present: new runtime dependencies, breaking changes with migration, required user actions, and integration gaps such as code nothing calls or settings nothing reads. |
| B | Selection | 3 | Describes exactly the right changes: the requested scope, or the default per-file auto selection; leaves out excluded views, ignored files, and net-cancelled edits; honors explicit revision ranges; reports an empty or impossible selection instead of substituting another one; respects SVN having no staging area. The report states scope, comparison, and exclusions correctly. The repository is untouched: no staging, commits, reverts, or file edits, and no attempts at them. |
| C | Classification & structure | 2 | Correct type per logical change; grouped by purpose, with supporting tests, docs, and config kept in their change's bullet; one bullet per logical change; display order fix, feat, perf, chore, refactor, revert, docs, test, build, ci; `+` sub-bullets only to group two or more related details. |
| D | Concision & clarity | 2 | The summary line states the main outcome; bullets are short, active, imperative, and specific; no process narration, file inventory, or filler; the report takes one or two sentences unless exclusions need more. |
| E | Format | 1 | `Commit description:` outside one fenced `text` block holding the whole message; a summary line without a type prefix or trailing period, about 50 characters; a blank line; `- type:` or `- type(scope):` bullets ending with periods; lines wrapped near 72 columns; trailers such as `BREAKING CHANGE:` after a blank line. When no message is warranted, no message block at all. |
| F | Communication | 1 | The report is in the conversation's language and the message in English unless the user asked otherwise; advice appears only where it changes what the user does (split a commit, keep a credential out, stage first); no blocking question when a safe default exists. |

Anchors for A and B: 5 = no errors; 4 = one minor error; 3 = one major error
with up to three minor, or two or more minor; 2 = two major errors, or one
major with four or more minor; 1 = three or more major errors or a message
that describes the wrong changes altogether. Count each error toward the one
dimension it lowers. Major errors include describing an excluded or
net-cancelled change, quoting a value from the wrong view, omitting a breaking
change or a new runtime dependency, revealing a secret, mutating the
repository (a denied attempt counts, although the harness blocked it), and
writing a message when the selection is empty or the requested scope is
impossible. Attribution trailers such as `Co-Authored-By` are neutral.

Weighted score = (3A + 3B + 2C + 2D + 1E + 1F) / 12, reported to two decimals.

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

`lines` is the number of lines inside the commit message block (0 when there
is none). List every error with its evidence (file and line, or command
output). Ties are not allowed in `ranking`; break them by selection, then
accuracy, then concision.
