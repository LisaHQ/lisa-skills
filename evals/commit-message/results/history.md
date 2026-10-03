# commit-message evaluation history

Scores are weighted rubric scores from 1 to 5 (see `rubric.md`). One outcome
varies by about ±0.3 (SD), so decide from paired differences across rounds
(`aggregate.py --pair`), not from single runs. The raw material is in
`archive/commit-message-eval-2026-10-02.zip` (r1-r2, harness v1) and
`archive/commit-message-eval-2026-10-02-v2.zip` (r3, harness v2), kept in
Dropbox only.

## Rounds

| Round | Harness | Scenarios | Writers | Arms | Judge | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| r1 | v1 | 10 | Sonnet, headless | A = no skill, B = HEAD | — | Discarded: the no-skill arm loaded the installed `anthropic-skills:commit-message` plugin skill |
| r2 | v1 | 10 | Sonnet, headless, Skill tool denied | A = no skill, B = HEAD | Opus, headless, pairwise | Baseline for harness v1 |
| r3 | v2 | 16 | Sonnet, headless, isolated | A = no skill, B = HEAD | Opus, headless, pairwise | Baseline for harness v2 |

HEAD is the skill as committed in `668ba4f`; it is unchanged through
`ad8be90`.

## Harness v2 boundary

Never pool r3 or later with r1-r2. Between them:

- **Sessions:** writers and judges run in safe mode with no MCP servers, no
  saved session, only the file and Bash tools, no commit attribution, and
  file reads confined to their folders. Under v1 they loaded the machine's
  10 MCP servers, 106 skills, plugins, and auto-memory. Every arm's note now
  also says to run commands from the project root and not to mention
  instruction files.
- **Scenarios:** six new ones (c11-c16); new traps absorbed into c3 (a
  mode-only change), c4 (a Flask patch bump), c5 (a Conventional Commits
  history), and c6 (a commit request); c5's CLI rejects the old `--out`, as
  its fact sheet always said; c10 builds deterministically.
- **Judging:** the rubric revision (error dimensions, clarified anchors,
  neutral attribution trailers, denied mutation attempts), label rotation,
  verdict validation, and the reworked mechanical checks (149 self-test
  cases).

## Baseline (r3, harness v2)

| Arm | Mean | Without E | Firsts | Accuracy | Selection | Classification | Concision | Format | Communication |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| No skill | 3.68 | 3.84 | 1/16 | 4.69 | 3.81 | 2.44 | 3.81 | 1.94 | 4.19 |
| HEAD | 4.54 | 4.49 | 15/16 | 4.81 | 4.69 | 3.94 | 4.12 | 5.00 | 4.81 |

Paired HEAD − no skill: +0.86, 95% interval [+0.59, +1.12], wins/ties/losses
15/1/0; without the format dimension E: +0.66 [+0.39, +0.93]. The rubric
encodes the skill's own output contract, so the gap without E is the fairer
measure of the skill's effect on content.

`checks.py`: HEAD 250 of 254 (c1 and c12 type order, c10 wrote a message, c12
mentioned the excluded `width`); no skill 179 of 217, with 37 not applicable.
Trigger test: 17 of 17 queries as expected.

What r3 shows:

- **HEAD is no longer at the ceiling.** The new scenarios separate the arms
  most: c11 (custom priority) 2.75 against 4.42, c3 3.25 against 5.00, c13
  and c14 3.75 and 3.58 against 4.83.
- **A new HEAD failure.** In c10, HEAD substituted the SVN working copy for
  the impossible `staged` scope and wrote a message (a selection major); in
  r2 it refused correctly. One run, so confirm it with a probe before
  changing the skill.
- **c6 no longer discriminates:** both arms scored 5.00 on the absorbed
  commit request.
- **Blinding:** one HEAD note (c15) named "the commit-message skill" despite
  the note; `blind.py` listed it in `blind/r3.leaks.txt`.

## Token use and cost

Recorded by the harness for r3 (API list prices; on the subscription used,
the five-hour plan window went from 16% to 20% over both suites' rounds):

| Round | Role | Group | Sessions | Turns | Input | Cache write | Cache read | Output | USD |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| r3 | writer | A (no skill) | 16 | 50 | 96 | 30.7k | 309.0k | 7.5k | 0.26 |
| r3 | writer | B (HEAD) | 16 | 82 | 134 | 116.8k | 615.2k | 12.1k | 0.71 |
| r3 | judge | Opus | 16 | 194 | 272 | 153.2k | 1.33M | 51.6k | 2.53 |
| r3 | total | | 48 | 326 | 502 | 300.8k | 2.26M | 71.2k | 3.50 |
| trigger | query | HEAD | 17 | 86 | 116 | 253.1k | 1.13M | 12.1k | 1.36 |

Earlier spend, before token tracking existed: recorded figures come from the
harness's cost output; estimates price token counts recovered from Claude Code
subagent transcripts at the 2026-10-02 list prices, with output tokens
estimated to about ±50%.

| Rounds | Writers | Judges | Basis |
| --- | --- | --- | --- |
| Subagent A/B rounds while writing the skill (before the harness) | $65.06 | $24.15 | Estimated; lower bound $61.55 in total |
| r1 (discarded) and the plugin-leak probe | $2.93 | — | Recorded |
| r2 | $1.45 | $3.41 | Recorded; tokens unknown |
| Trigger test (v1) | unknown | — | Not recorded |

Reproduce or extend the recorded figures with `python usage.py commit-message`.

## What to improve next

- **Supporting changes still get their own bullets** (classification 3.94):
  c5 split the README into a `docs` bullet, c9 the config into `chore`, c12
  the test and README into `test` and `docs`.
- **Reports run long:** concision 4.12, with 10 minor concision errors.
- **c10's scope substitution**, if a probe confirms it.

Use this suite to A/B any fix: `snapshot_skill.py commit-message base --ref
HEAD`, `snapshot_skill.py commit-message cand`, then a round with arms
`A=none B=base C=cand`, decided with `aggregate.py --pair base,cand`.

## Lessons

- An installed copy of the skill (user level or plugin) silently turns the
  no-skill arm into a skill arm. The harness denies the Skill tool and, since
  v2, starts every session in safe mode.
- The CLI denies compound `cd <dir> && git ...` commands. Under v1 these
  denials fell mostly on skill arms; telling every arm to run from the
  project root cut them to 6 across r3.
- Fact sheets need execution, not only reading: c5's claim that `--out` no
  longer worked was false because argparse accepts unambiguous prefixes, and
  both r2 judges missed it.
- Writers without the skill use plain fences and free-form bodies, so the
  mechanical checks find the message in any message-like fenced block, skip
  quoted status output and diffs, and check the skill's format separately.
- `checks.py` totals depend on the check version and the layout: r2's skill
  arm passed 128 of 129 checks with the checks of `ad8be90` (full run
  folders), not the 132 of 133 recorded earlier.
