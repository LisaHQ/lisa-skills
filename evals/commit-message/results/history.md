# commit-message evaluation history

Scores are weighted rubric scores from 1 to 5 (see `rubric.md`). One run
varies by about ±0.3, so compare versions across rounds, not single runs. The
raw material is in `archive/commit-message-eval-2026-10-02.zip`, kept in
Dropbox only.

## Rounds

| Round | Writers | Arms | Judge | Notes |
| --- | --- | --- | --- | --- |
| r1 | Sonnet, headless | A = no skill, B = HEAD | — | Discarded: the no-skill arm loaded the installed `anthropic-skills:commit-message` plugin skill |
| r2 | Sonnet, headless, Skill tool denied | A = no skill, B = HEAD | Opus, headless, pairwise | Baseline round for this suite |

HEAD is the skill as committed in `668ba4f`.

## Baseline (r2)

| Arm | Mean | Firsts | Accuracy | Selection | Classification | Concision | Format | Communication |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| No skill | 3.45 | 1/10 | 4.30 | 3.90 | 2.30 | 3.40 | 1.80 | 3.60 |
| HEAD | 4.68 | 9/10 | 5.00 | 5.00 | 4.00 | 4.20 | 5.00 | 4.80 |

`checks.py` agrees: the skill arm passed 132 of 133 mechanical checks. Without
the skill, writers wrote a message for SVN "staged" changes that cannot exist
(c10), dropped the integration gap (c4), and wrote the message in Vietnamese
(c7). The no-skill arm won only c6, where both arms correctly refused to
write a message for an empty staged selection.

Trigger test (`trigger_test.py commit-message head`): 10 of 10 queries loaded
the repository's skill, or left it alone, as expected.

## What to improve next

The judges' weaknesses for the skill arm point at two rules the skill states
but agents do not follow consistently:

- **Supporting changes get their own bullets.** In 7 of 10 scenarios the
  writer split tests, docs, dependencies, or config into separate `test:`,
  `docs:`, `build:`, or `chore:` bullets, although the skill says to keep
  supporting code, tests, docs, and configuration with their change.
- **Reports run long.** Several reports narrate process (blocked commands,
  what was not done) beyond the one or two sentences the skill asks for.

Use this suite to A/B any fix: `snapshot_skill.py commit-message base --ref
HEAD`, `snapshot_skill.py commit-message cand`, then a round with arms
`A=none B=base C=cand`.

## Lessons

- An installed copy of the skill (user level or plugin) silently turns the
  no-skill arm into a skill arm. The harness now denies the Skill tool in
  writer and judge sessions; skill arms read their snapshot directly.
- Writers without the skill use plain fences and free-form bodies, so the
  mechanical checks locate the message in any non-shell fenced block and
  check the skill's format separately.
