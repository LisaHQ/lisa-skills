# commit-message evaluation history

Scores are weighted rubric scores from 1 to 5 (see `rubric.md`). One outcome
varies by about ±0.3 (SD), so decide from paired differences across rounds
(`aggregate.py --pair`), not from single runs. The raw material is in
`archive/commit-message-eval-2026-10-02.zip` (r1-r2, harness v1) and
`archive/commit-message-eval-2026-10-02-v2.zip` (r3, harness v2),
`archive/commit-message-eval-2026-10-03.zip` (r3-r6 and probes p0-p2), and
`archive/commit-message-eval-2026-10-04.zip` (r3-r7, the probes, and every
judgment set), kept in Dropbox only.

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
| r7 | v3 | 16 | Sonnet, isolated | A = no skill, B = HEAD (cand2) | Opus, headless, pairwise | Baseline for harness v3 |
| r7-rj0 | v3 | 16 | (r7 outcomes) | A, B | Opus, headless | Control re-judge with the same judge prompt |
| r7-j2 | v3 | 16 | (r7 outcomes) | A, B | Opus, headless | Re-judge with the judge prompt of 2026-10-04 |

HEAD is the skill as committed in `668ba4f`; it is unchanged through
`ba87af4` (content hash `5b706b2d9989`). cand (`7a1ba2b6d3b1`) and cand2
(`5ed79aea9501`) are the 2026-10-03 working-tree revisions; cand2 is the one
kept, committed in `18b16b2`, and HEAD in r7.

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

## Harness v3 boundary and baseline (r7)

Never pool r7 or later with r3-r6. Harness v3 starts every writer and judge
session with `PYTHONPATH` listing `src` and `scenario/src`, and with
`PYTHONDONTWRITEBYTECODE=1`. This suite's writer prompts are unchanged (it
has no `writer_note`), and no writer in r3-r7 ran Python, so the change
could reach only the judges. In r7 one judge tried `python -c` (c11) and
was denied, so no r7 session ran Python. The c5 and c12 fact sheets now
state results
verified by running the working-tree code (`cli.main(['export', '--out',
'x.csv'])` exits 2; what `render('ab-12', 3)` returns), so judges need not
run it.

r7 compares the committed skill (cand2, in `18b16b2`) with no skill
(judgment set `r7`, made before the judge command guidance below):

| Arm | Mean | Without E | Firsts | Accuracy | Selection | Classification | Concision | Format | Communication |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| No skill | 3.59 | 3.72 | 0/16 | 4.38 | 3.88 | 2.56 | 3.50 | 2.19 | 4.06 |
| HEAD (cand2) | 4.75 | 4.73 | 16/16 | 4.88 | 4.94 | 4.75 | 4.12 | 4.94 | 4.88 |

Paired HEAD − no skill: +1.16, 95% interval [+0.79, +1.52], wins/ties/losses
16/0/0; without the format dimension E: +1.01 [+0.64, +1.39]. `checks.py`:
HEAD 269 of 273 (c4 `dependency_with_feature`, c5 `breaking_names_module`,
c12 `no_staged_width`, c15 `supporting_folded`), no skill 175 of 219 with 54
not applicable.

r3's +0.86 measured the previous HEAD. The same versions under both
harnesses (separate rounds and judges, so the means are not paired):

| Same version | v2 | v3 (r7) |
| --- | --- | --- |
| cand2 judged mean | 4.78 (r5 + r6, 32 runs) | 4.75 (16 runs) |
| No skill judged mean | 3.72 (r3 with r3-facts for c9 and c13-c16, 16 runs) | 3.59 (16 runs) |
| cand2 denied calls per run | 0.22 | 0.25 |
| cand2 checks passed | 540 of 545 | 269 of 273 |

Scenario by scenario, no skill moved by −0.13 [−0.37, +0.11] from r3
(with r3-facts) to r7, within noise. Under the revised fact sheets r3's
paired gap is +0.88 [+0.62, +1.13]; the rise to r7's +1.16 can come only
from the 2026-10-03 revision, the c5 and c12 fact-sheet edits, and
round-to-round noise.

**Check change:** c9's `credential_warned` failed both r7 reports, which did
warn about the credential in words the pattern missed. It now also accepts
a sentence that names the secret and says it goes into (or ends up in) the
history, as r7's no-skill report does, and keep-out advice two sentences
after the one that names the secret when that sentence gives advice
("consider", "should", "instead"), as r7's HEAD report does. Next-sentence
advice already counted; "keeping" and "leaving" now count like "keep" and
"leave". "Keep it out of the message" no longer counts as keep-out advice.
Re-checking every c9 outcome of r3-r7 changed only those two r7 values. The
self-test has 169 cases.

## Judge command guidance (2026-10-04)

No commit-message judge had run a git command since harness v2. A judge
works one folder above the checkout, and the CLI denies both
`cd scenario && git ...` and, without a matching rule, `git -C scenario ...`.
In r3 and r5-r7 judges were denied about four commands per session, only
the SVN scenarios' judges reached their working copy (c10, c14), and the
Git scenarios' version-control claims were judged from the fact sheets
alone, with one exception: the r6 judge of c7, denied git and `python -c`,
wrote a script that decoded the Git objects with `zlib` and cited the HEAD
blobs in its verdict.

The judge prompt now names the forms that run: `git -C scenario <command>`,
`svn <command> scenario`, `python -m <package>` on the preset path, a script
file run with `python <file>`, and `mkdir` with flag-free `cp` for copies
(the earlier prompt asked for a copy without naming a command, and the CLI
rejects `cp` with any flag, so the `cp -r` judges used for it was always
denied). Judges may run every allowed git command as
`git -C scenario ...`. `judge.py` also rejects an attempt in which the judge
changed `scenario/`, audits the files a judge writes, and records a digest
of the judge's session arguments in each verdict's provenance; `collect.py`
warns when one set mixes judge prompts.

The same blinded r7 outcomes, judged three times:

| Judgment set | Judge prompt | Denied calls per session | Ran git or svn | Turns per session | No skill | HEAD | Paired HEAD − no skill | Without E | Judges, USD |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- | --- | ---: |
| `r7` | earlier | 4.19 | 2 of 16 | 11.4 | 3.59 | 4.75 | +1.16 [+0.79, +1.52] | +1.01 [+0.64, +1.39] | 2.46 |
| `r7-rj0`, control | earlier | 4.31 | 1 of 16 | 10.9 | 3.55 | 4.80 | +1.25 [+0.95, +1.55] | +1.12 [+0.81, +1.44] | 2.29 |
| `r7-j2` | 2026-10-04 | 0.50 | 16 of 16 | 5.2 | 3.62 | 4.78 | +1.16 [+0.82, +1.49] | +1.01 [+0.67, +1.34] | 1.72 |

HEAD won all 16 scenarios in every set.

The accept rule, written before the new pass: denied calls per session at
most half the earlier level (2.1 here); no denial of a form the prompt
names; no reach flag; `scenario/` unchanged; one attempt per scenario on the
same CLI and model; and the mean score and the paired gap within a noise
band of the mean of the two earlier passes, else a second new-prompt pass.
The band is twice the SD of the differences between the two earlier passes,
divided by √n (outcomes for scores, scenarios for the gap). Outcomes that
move by 0.3 or more are reviewed one by one; they do not fail the rule.

- **Judge noise, measured by the control:** the two earlier-prompt passes
  differ by an SD of 0.19 per outcome, so one judgment's own SD is about
  0.14; the paired gap moved by +0.09. The new prompt has one pass, so its
  own noise is not measured.
- **The accept rule held.** Denied calls fell to an eighth; no session of
  any set was flagged for reach, and no `r7-j2` session changed `scenario/`
  (the earlier sets did not record the latter); every verdict came from one
  attempt on the same CLI and model. Against the mean of the two earlier
  passes, scores moved by +0.03 (band ±0.07) and the paired gap by −0.05
  (band ±0.14). No outcome moved by 0.3 or more, so none needed review.
- **Judges now check the evidence.** By a keyword scan of the verdicts'
  evidence fields, 18 of 84 error items cite git or svn output, against 3
  of 89 and 1 of 85 before. The number of errors found did not change, so
  the fact sheets had been carrying the judging.
- **The eight remaining denials** are seven `for` loops over `outcomes/`
  and one `git -C scenario grep`, a sub-command outside the allowed list.

Use `r7-j2` when pooling r7 with later rounds, which are judged with this
prompt (`aggregate.py commit-message r7-j2:A=none,B=head3 ...`). `r7` stays
the set to compare with r3-r6, which share its judge prompt. Do not rerun
`judge.py commit-message r7` (or `--out r7-rj0`) without a new `--out`:
their digests no longer match, so all 16 scenarios would be re-judged in
place with the new prompt.

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

The harness v3 baseline:

| Round | Sessions | Writers | Judges | USD |
| --- | ---: | ---: | ---: | ---: |
| r7 | 48 | 0.95 | 2.46 | 3.41 |
| r7-rj0 (re-judge) | 16 | — | 2.29 | 2.29 |
| r7-j2 (re-judge) | 16 | — | 1.72 | 1.72 |
| total | 80 | 0.95 | 6.47 | 7.42 |

Permission probes for harness v3 and for the judge prompt (Haiku, outside
the harness) cost about $0.17. The diagnosis and review agents of the
interactive session are not included.

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

- **SVN judge notes:** the c10 and c14 fact sheets still give the svn
  commands as run inside `scenario/`. With the next fact-sheet revision,
  write them as the judge prompt does (`svn status scenario`,
  `svn proplist -v scenario/scripts/export.sh`); both r7-j2 judges already
  used that form.
- **Judges' opening loop:** 7 of 16 r7-j2 judges still tried a `for` loop
  over `outcomes/` first, and git sub-commands outside the allowed list
  (`git grep`) stay denied.
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
- Read the judges' session logs, not only their verdicts: for four rounds
  no judge could run git, and nothing in the scores showed it.
- Read the outcomes a check fails before trusting a round's totals, even
  when the check is old: c9's `credential_warned` passed all eight c9
  outcomes of r3-r6 but failed both r7 reports, which did warn in wordings
  the pattern missed.
- Fact sheets need execution, not only reading: c5's claim that `--out` no
  longer worked was false because argparse accepts unambiguous prefixes, and
  both r2 judges missed it.
- Writers without the skill use plain fences and free-form bodies, so the
  mechanical checks find the message in any message-like fenced block, skip
  quoted status output and diffs, and check the skill's format separately.
- `checks.py` totals depend on the check version and the layout: r2's skill
  arm passed 128 of 129 checks with the checks of `ad8be90` (full run
  folders), not the 132 of 133 recorded earlier.
