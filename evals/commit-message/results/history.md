# commit-message evaluation history

Scores are weighted rubric scores from 1 to 5 (see `rubric.md`). One outcome
varies by about ±0.3 (SD), so decide from paired differences across rounds
(`aggregate.py --pair`), not from single runs. The raw material is in
`archive/commit-message-eval-2026-10-02.zip` (r1-r2, harness v1) and
`archive/commit-message-eval-2026-10-02-v2.zip` (r3, harness v2), and
`archive/commit-message-eval-2026-10-03.zip` (r3-r6 and probes p0-p2), kept in
Dropbox only.

## Rounds

| Round | Harness | Scenarios | Writers | Arms | Judge | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| r1 | v1 | 10 | Sonnet, headless | A = no skill, B = HEAD | — | Discarded: the no-skill arm loaded the installed `anthropic-skills:commit-message` plugin skill |
| r2 | v1 | 10 | Sonnet, headless, Skill tool denied | A = no skill, B = HEAD | Opus, headless, pairwise | Baseline for harness v1 |
| r3 | v2 | 16 | Sonnet, headless, isolated | A = no skill, B = HEAD | Opus, headless, pairwise | Baseline for harness v2 |
| p0 | v2 | c10 only | Sonnet, isolated | B1-B4 = HEAD | — | Probe of r3's c10 scope substitution |
| r3-facts | v2 | c9, c13-c16 | (r3 outcomes) | A, B | Opus, headless | Re-judge under the revised fact sheets |
| r4 | v2 | 16 | Sonnet, isolated | B = HEAD, C = cand | — (checks only) | First candidate, read mechanically |
| p1, p2 | v2 | c10 only | Sonnet, isolated | C1-C4 = cand, cand2 | — | c10 probes of each candidate |
| r5, r6 | v2 | 16 | Sonnet, isolated | B = HEAD, C = cand2 | Opus, headless, pairwise | The revision's A/B rounds |

HEAD is the skill as committed in `668ba4f`; it is unchanged through
`ba87af4` (content hash `5b706b2d9989`). cand (`7a1ba2b6d3b1`) and cand2
(`5ed79aea9501`) are the 2026-10-03 working-tree revisions; cand2 is the one
kept.

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

`checks.py` (the checks of `ba87af4`): HEAD 250 of 254 (c1 and c12 type
order, c10 wrote a message, c12 mentioned the excluded `width`); no skill 179
of 217, with 37 not applicable.
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

## Revision of 2026-10-03 (r4-r6)

The r3 audit found three skill problems: supporting tests, docs, and
configuration in their own bullets (C errors in 11 of 16 scenarios), long
reports, and one c10 run that substituted the SVN working copy for an
impossible `staged` scope. Eight diagnosis agents, each proposal checked by
two refuting agents, and two review rounds of the edited text led to these
changes:

- **Grouping:** "Give each change one bullet, even across modules: fold in
  the code, tests, docs, configuration, and new dependencies that serve it,
  and state each new dependency only in that bullet." The type rule became
  "Reserve `docs`, `test`, and `ci` for work that serves no other change in
  the selection." Check-before-output item 3 now names the bullets to fold:
  tests, docs, configuration, and added dependencies.
- **Report:** "inspection limits" instead of "evidence limits", "or fixed
  selection" for ranges, a count-based example, and "Mention whether tests
  ran only when the request asks, and leave claims omitted from the message
  unexplained."
- **SVN:** a request for staged or unstaged changes, "however worded", gives
  only the report and an offer to describe the working-copy changes.

cand, the first version, folded only partly in r4 (`supporting_folded` 8 of
13 against HEAD's 1 of 12) and changed no report metric. cand2 added the
check item, the dependency wording, the test sentence, and "however worded"
for SVN, and dropped cand's "omit unsupported ones silently".

| Measure | HEAD | cand2 |
| --- | --- | --- |
| Judged mean, r5 + r6 (32 pairs) | 4.66 | 4.78 |
| Classification C | 4.06 | 4.81 |
| C minor errors | 26 | 4 |
| `supporting_folded` (HEAD r3-r6, cand2 r5-r6) | 8 of 50 | 24 of 25 |
| `dependency_with_feature` (c4, same rounds) | 0 of 4 | 1 of 2 |
| `breaking_names_module` (c5, same rounds) | 0 of 4 | 1 of 2 |
| c10 refusals (rounds and probes) | 6 of 8 | 6 of 6 |
| Report words, mean, r5 + r6 (`report_metrics.py`) | 89.0 | 85.2 |
| Reports that state test status, r5 + r6 | 25 of 32 | 27 of 32 |
| Main bullets of four or more lines, r5 + r6 | 5 of 32 | 8 of 32 |

The c10 row cannot separate the versions yet: at HEAD's refusal rate, six
refusals in a row happen by chance about one time in five. Report words
differ by −3.8 (95% interval [−11.7, +4.2]), so the reports are no shorter.

Paired cand2 − HEAD: +0.12, 95% interval [−0.00, +0.24], wins/ties/losses
20/2/10; without the format dimension E: +0.14 [+0.00, +0.27]. Per dimension:
A −0.03, B −0.03, C +0.75, D +0.06, E −0.09, F +0.06. The total is borderline,
so the decision rests on the targeted dimension and the checks, which both
moved clearly; no guard check (`goals_kept_apart`, `changes_kept_apart`, the
two `*_own_bullet` checks) failed in any run.

What the rounds show:

- **Folding works.** The one remaining split is c2's `test(notes)` bullet in
  r6: the writer argued that a test of `store.get` does not serve the new
  route.
- **c4 is half fixed.** cand2 kept httpx in a `build` bullet with Flask once,
  and once folded it as "via httpx" without saying it is a new dependency,
  which the judge counted as a major A error.
- **Reports did not get shorter.** Writers still add "I didn't run the
  tests" to most reports; cand2 only dropped the explanation that followed
  it ("so the message makes no claim that they pass"). Folding also made a
  few bullets longer, which the concision score D (+0.06) did not penalize.
- **c15 once wrote untyped body bullets** under the commitlint header (major
  C and E); the other run was clean.
- **Blinding:** r5 and r6 notes mention "the skill" three and four times
  (`blind/r5.leaks.txt`, `blind/r6.leaks.txt`). Both arms carry the skill, so
  the leak cannot reveal which version wrote an outcome.

### Eval changes made with the revision

- **Checks:** `supporting_folded` in 13 scenarios, guards against merging
  independent changes (`goals_kept_apart`, `changes_kept_apart`,
  `mode_change_own_bullet`, `property_change_own_bullet`),
  `dependency_with_feature` (c4), and `breaking_names_module` (c5). The
  bullet checks are None for untyped prose bullets; `dependency_with_feature`
  is None when no bullet names httpx and `breaking_names_module` when there
  is no `BREAKING CHANGE:` trailer, so a missing dependency or trailer is not
  counted twice. Old and new checks agree on
  every existing key for r3; the new keys fail HEAD in exactly the scenarios
  the r3 judge marked with folding errors. Totals under this check version:
  r3 HEAD 256 of 273, no skill 179 of 218. The self-test has 162 cases.
- **`report_metrics.py`:** report words, sentences, test status, file names,
  long bullets, and recall of the exclusions each fact sheet requires.
- **Fact sheets:** naming an ignored file in the report is neutral in c9,
  c13, c14, and c16 (the judges had penalized its omission in some runs and
  not others), and c15 now scores a separate `test` bullet for its todo
  placeholder as a minor C error. Re-judging r3 on those five scenarios
  (`r3-facts`, $0.78) removed every ignored-file error in both arms and kept
  c15's C error; other scores moved by ±1 on single dimensions, which is the
  judge noise. Do not pool c9 and c13-c16 verdicts from before this revision.

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

The 2026-10-03 revision, by round (writers Sonnet, judges Opus):

| Round | Sessions | Writers | Judges | USD |
| --- | ---: | ---: | ---: | ---: |
| p0, p1, p2 (c10 probes) | 12 | 0.46 | — | 0.46 |
| r3-facts (re-judge) | 5 | — | 0.78 | 0.78 |
| r4 (writers only) | 32 | 1.41 | — | 1.41 |
| r5 | 48 | 1.39 | 2.16 | 3.55 |
| r6 | 48 | 1.42 | 2.35 | 3.77 |
| total | 145 | 4.68 | 5.29 | 9.97 |

The diagnosis and review agents of the interactive session are not included.

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

- **Test status in reports:** 27 of 32 cand2 reports still say the tests
  were not run (HEAD 25 of 32 in the same rounds; the no-skill arm 0 of 16
  in r3). Three wordings failed; the next lever is the report's slot list
  ("material exclusions or inspection limits"), which writers seem to fill
  with it. "Mention whether tests ran only when the request asks" stays
  only because cand2 was tested with it; drop it with that change.
- **c10:** probe about ten more runs per version before calling the SVN
  wording a fix.
- **c4's new dependency:** writers group it with the Flask bump by file, or
  fold it in without calling it new.
- **Report length:** about 85 words in both versions; D stays near 4.4.

Use this suite to A/B any fix: `snapshot_skill.py commit-message base --ref
HEAD`, `snapshot_skill.py commit-message cand`, then a round with arms
`A=none B=base C=cand`, decided with `aggregate.py --pair base,cand`.

## Lessons

- An instruction the text already implies can still fail until a checkable
  step names the concrete case. HEAD's "keep supporting tests with their
  change" folded in 8 of 50 runs; cand's fold and "reserve" wording reached 8
  of 13 (r4); cand2's check-before-output item that names test, docs,
  configuration, and dependency bullets, added with the dependency wording,
  reached 24 of 25 (r5-r6). Which of cand2's changes did the most is a
  hypothesis; they were tested together.
- Rare failures need many cheap probes: c10 failed in 2 of 8 HEAD runs, so a
  single round can neither show nor rule out a fix.

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
