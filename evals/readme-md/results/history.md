# readme-md evaluation history

Results of the rounds run while creating the skill on 2026-10-02 (iter1-iter5
and probes, harness v1), the first harness v2 baseline (iter6), and the v10
and v11 revision of 2026-10-03 (iter7-iter11), the harness v3 baseline
(iter12, p3, iter13), the judge command guidance of 2026-10-04 (p4 and two
re-judges of iter13), and the v12 revision of the same day (p5, iter14,
iter15). The raw material is in
`archive/readme-md-eval-2026-10-02.zip` (snapshots v1-v9, blinded outcomes,
verdicts, mappings, run notes), `archive/readme-md-eval-2026-10-02-v2.zip`
(iter6), `archive/readme-md-eval-2026-10-03.zip` (iter6-iter11),
`archive/readme-md-eval-2026-10-04.zip` (iter6-iter13, p3, p4, and every
judgment set), and `archive/readme-md-eval-2026-10-04-v12.zip` (p5, iter14,
iter15), kept in Dropbox only.

Scores are weighted rubric scores from 1 to 5 (see `rubric.md`). One outcome
varies by about ±0.3 (SD), so decide from paired differences across rounds
(`aggregate.py --pair`), not from single runs.

## Rounds

| Round | Harness | Writer environment | Writer | Arms (versions) | Judge |
| --- | --- | --- | --- | --- | --- |
| iter1 | v1 | Subagents inside this repository | Sonnet | A = no skill, B = v1 | Opus subagent, pairwise |
| iter2 | v1 | Headless `claude -p`, neutral folders | Sonnet | A = no skill, B = v1, C = v2 | Opus subagent, three-way |
| iter3 | v1 | Headless, neutral | Sonnet | B = v1, C = v2, D = v3 | Opus subagent, three-way |
| iter4 | v1 | Headless, neutral | Sonnet | C = v2, D = v3, E = v4 | Opus subagent, three-way |
| iter5 | v1 | Headless, neutral | Opus | A = no skill, V = v8 | Opus subagent, pairwise |
| probe2, probe8, probe9 | v1 | Headless, neutral | Sonnet | Repeated runs of v4-v9 on s2, s8, s9 | `checks.py` assertions |
| iter6 | v2 | Headless, isolated | Sonnet | A = no skill, B = HEAD (v9) | Opus, headless, pairwise |
| iter6-facts | v2 | (iter6 s2 outcomes) | — | A, B | Opus, headless; s2 re-judged under the corrected fact sheet |
| iter7 | v2 | Headless, isolated | Sonnet | B = HEAD (v9), C = v10 draft | Opus, headless, pairwise |
| iter8, iter9 | v2 | Headless, isolated | Sonnet | B = HEAD (v9), C = v10 | Opus, headless, pairwise |
| iter10, iter11 | v2 | Headless, isolated | Sonnet | B = HEAD (v9), C = v11 | Opus, headless, pairwise |
| iter12 | v3 | Headless, isolated, no writer note | Sonnet | A = no skill, B = HEAD (v11) | Opus, headless, pairwise |
| p3 | v3 | Headless, isolated | Sonnet | A = no skill, B = HEAD (v11); s1, s11, s12 only | `checks.py` assertions |
| iter13 | v3 | Headless, isolated | Sonnet | A = no skill, B = HEAD (v11) | Opus, headless, pairwise |
| p4 | v3 | Headless, isolated | Sonnet | B1-B6 = HEAD (v11); s8 only | `checks.py` assertions |
| iter13-rj0 | v3 | (iter13 outcomes) | — | A, B | Opus, headless; control re-judge with the same judge prompt |
| iter13-j2 | v3 | (iter13 outcomes) | — | A, B | Opus, headless; judge prompt of 2026-10-04 |
| p5 | v3 | Headless, isolated | Sonnet | H1-H4 = HEAD (v11), A1-A10 = candA (v12), B1-B10 = candB; s8 only | `checks.py` assertions |
| iter14, iter15 | v3 | Headless, isolated | Sonnet | B = HEAD (v11), C = v12 | Opus, headless, pairwise |

iter1 is not comparable with later rounds: the writers inherited this
repository's `AGENTS.md`, which made the no-skill baseline unrealistically
strong (4.49 against 4.59 for v1). iter1-iter5 were judged by Opus subagents
of an interactive session, with fact sheets that did not yet have judge notes.
Probe labels map to versions as E, F, G = v4, v5, v6; H = v7; J = v8; K = v9.

## Version scores (iter2-iter4 pooled, Sonnet writers)

| Version | Runs | Mean | SE | Major errors | Minor errors per run |
| --- | --- | --- | --- | --- | --- |
| No skill | 9 | 4.03 | 0.11 | 3 | 1.56 |
| v1 | 18 | 4.37 | 0.08 | 0 | 0.89 |
| v2 | 27 | 4.36 | 0.06 | 0 | 0.81 |
| v3 | 18 | 4.43 | 0.09 | 1 | 0.83 |
| v4 | 9 | 4.45 | 0.10 | 0 | 0.78 |

Head to head in the same judged scenarios, only v1 against no skill is
clear: +0.39, 95% interval [+0.16, +0.63], 8 wins and 1 loss, with accuracy
+0.67, core highlighting +0.78, concision −0.67, presentation +0.67,
friendliness +0.11, and usefulness +0.67. v2 against v1 (+0.01), v3 against v2
(+0.07), and v4 against v3 (+0.09) are all inconclusive, so the v2-v9 choices
rest on probes and checks, not on these means.

Reproduce from `evals/harness/` after unzipping the archive into a separate
work root (`LISA_EVAL_WORK=<folder>`, under `<folder>/readme-md/`):

```bash
python aggregate.py readme-md iter2:A=none,B=v1,C=v2 iter3:B=v1,C=v2,D=v3 iter4:C=v2,D=v3,E=v4
```

## Validation with Opus writers (iter5)

| Version | Mean | Firsts | Accuracy | Highlighting | Concision | Presentation |
| --- | --- | --- | --- | --- | --- | --- |
| No skill | 4.37 | 4/9 | 4.00 | 4.56 | 4.44 | 4.44 |
| v8 | 4.49 | 5/9 | 4.22 | 4.78 | 4.22 | 5.00 |

Paired v8 − no skill: +0.13, 95% interval [−0.13, +0.39], wins/ties/losses
4/2/3: inconclusive. A stronger writer gains less from the skill, but the
skill still removed the baseline's worst failures: four minor errors in s5
and an unverified `go install` path in s6.

## Probes

| Probe | Version | Result |
| --- | --- | --- |
| s8 polish, preservation | v4-v6 | 8 of 11 runs dropped a badge, the TIP alert, the footer, or emoji |
| s8 polish, preservation | v7 | 0 of 5 runs dropped owner content |
| s8 polish, preservation | v8 | 1 of 3 runs dropped the TIP alert |
| s2 stale update | v7 | 1 of 3 runs deleted Sponsors and Contributors as "unsupported" |
| s2 stale update | v8 | 4 of 4 runs passed every check |
| s9 answer key | v9 | 0 of 3 runs leaked trainers-only content |
| Trigger test (10 queries, s6) | v3, then v9 | 10 of 10 as expected, both times |

Until iter6, v9 was validated only by probe9 and the trigger test.

## Version changes and the evidence behind them

| Version | Change | Evidence |
| --- | --- | --- |
| v1 | First draft from the research | — |
| v2 | Say each fact once, length budget, sharper cut pass; concise reviews with a one-line verdict; improve mode audits first and keeps the owner's design; checks examples and the conditions behind claims | iter1: lower concision, verbose review, over-edited s8 |
| v3 | Scale edits to the request (update, polish, rewrite); replace hype; highlights cover contents and pitfalls for data and materials; first screen names the first command | iter2: v2 kept hype emoji in s2 and changed nothing in s8 |
| v4 | Inferences stay unknown until confirmed; read every openable document, PDFs included; link instead of copying | iter3: over-inference errors; PPE missed in s9 |
| v5 | Badge rule applies only to badges you add; update stale examples from their source | iter4: v4 removed static badges in s8 |
| v6 | Cut pass in improve mode touches only text you added or changed | Probe: removals continued |
| v7 | Keep badges, emoji, and alerts unless broken or misleading; writing rules apply to text you add or change | Probe: removals continued in v6 |
| v8 | Keep owner-only facts such as sponsors; fix only project claims the evidence contradicts or cannot support | Probe: v7 deleted Sponsors in s2 |
| v9 | Keep content marked for a narrower audience out of the README | iter5: v8 copied answer-key wording in s9 |
| v10 | v9 plus: build examples from tested calls and show output only from a run or a recording file; compare sample outputs line by line with their producer's format; an upgrade note for breaking changes; a static license badge; and five rules without discriminating evidence (translated outline section names, CODEOWNERS, trace a file-changing script instead of running it, absolute claims name their limits, a rules slot in the materials outline) | iter6 audit; iter7-iter9 |
| v11 | v10 without the five unevidenced rules; First success shows output only when a run or a file records it; the upgrade note follows the audit rather than the update scale | iter8-iter9 (v10 tied, concision fell); iter10-iter11 |
| v12 | In improve mode, treat each sample output as a copy of the producer's own passage for the same case: replace the lines that original covers, keep the rest, and add the label or wrapper the format requires | iter10-iter13 and p4 (v11 fixed s8's example in 3 of 10 runs); p5, iter14-iter15 |

## Harness v2 boundary

Never pool iter6 or later with iter1-iter5. Between them: isolated sessions
(safe mode, so s8 writers no longer load the clone's `CLAUDE.md` and
`AGENTS.md`; no MCP servers, plugins, or auto-memory; confined file reads),
the same extra sentences in every arm's note, label rotation, the rubric
revision (error dimensions and clarified accuracy anchors), three new
scenarios (s10-s12), corrected fact sheets and checks (151 self-test cases),
s8 cloned with only `main`, and a trigger test of 19 queries on s2.

## Baseline (iter6, harness v2)

| Arm | Mean | Firsts | Accuracy | Highlighting | Concision | Presentation | Friendliness | Usefulness |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| No skill | 4.04 | 1/12 | 4.08 | 3.92 | 4.58 | 4.17 | 3.58 | 3.58 |
| HEAD (v9) | 4.52 | 11/12 | 4.42 | 4.75 | 4.42 | 4.67 | 4.08 | 4.67 |

Paired HEAD − no skill: +0.47, 95% interval [+0.20, +0.75], wins/ties/losses
10/1/1. `checks.py` (the checks of `ba87af4`): HEAD 120 of 123, no skill 107
of 120. Trigger test: 19 of 19 as expected.

What iter6 shows:

- **The new scenarios work as intended.** s10 (a package README in a
  monorepo) separates the arms most: 3.32 against 4.45, with the no-skill
  arm missing the license conflict and the root link.
- **s12 (add badges, nothing else) went to the no-skill arm**, 4.91 against
  4.77: both avoided every trap, and the judge preferred static badges over
  HEAD's GitHub-backed license badge. **s11 tied**: both missed the upgrade
  note and a real example.
- **Both arms still miss s8's stale Usage example**, and the no-skill arm
  changed nothing at all while claiming the example matched; s9's PDF-only
  safety details were missed by both.

## Revision of 2026-10-03 (v10 and v11, iter7-iter11)

The iter6 audit found unexecuted examples (s2's base URL dropped `/v1`),
over-general guarantees (s4, s10), the stale s8 example, no upgrade note in
s11, a GitHub-API license badge copied from `references/markdown.md` (s12),
an unrequested run of a data-regenerating script (s3), an English outline
heading in a Vietnamese README (s5), and PDF-only safety rules left out (s9).
Diagnosis agents with two refuting reviewers per proposal, and a review of
every edited text, produced three versions:

| Version | Content hash | Rounds | Paired − HEAD (95% interval) | W/T/L |
| --- | --- | --- | --- | --- |
| v10 draft | `1684e08f4a53` | iter7 | −0.07 [−0.35, +0.21] | 5/0/7 |
| v10 | `094f3334d6e8` | iter8, iter9 | +0.01 [−0.14, +0.16] | 14/1/9 |
| v11 (kept) | `13cf10d250f9` | iter10, iter11 | +0.06 [−0.05, +0.17] | 12/2/10 |

- **v10 draft:** its s11 writer, unable to run the tool, published a
  hand-traced example output with a wrong row (`added A3` instead of `A4`),
  a major error (3.64 against 4.64). v10 therefore shows output only from a
  run or a file that records it.
- **v10:** tied HEAD. Its targeted checks held (below), but concision fell
  (C −0.12; READMEs 6% longer in total), accuracy errors were 14 against
  HEAD's 14, and five of its rules had no discriminating evidence: HEAD also
  passed s5's headings, s3's no-run check, and s10's owners in iter7-iter9,
  v10 still wrote "always sum to the original" in s10, and the materials
  slot went +0.45 then −0.55 in s9. Per scenario, v10 won s2, s11, s12, s7,
  and s8, and lost s6, s3, and s4 in both rounds (s6 −0.64, −0.27; s3 −0.14,
  −0.50; s4 −0.14, −0.19). In iter8 s6 it showed no output where HEAD showed
  a hand-traced but correct one; in iter9 s6 it lost on a `grepl.exe` slip.
- **v11:** v10 without those five rules, with First success matching the
  output rule, and the upgrade note tied to the audit instead of the update
  scale.

| v11 against HEAD, iter10 + iter11 | HEAD | v11 |
| --- | --- | --- |
| Judged mean (24 pairs) | 4.55 | 4.60 |
| Accuracy A | 4.42 | 4.71 |
| Accuracy errors, major / minor | 1 / 14 | 0 / 7 |
| Highlighting B, concision C, friendliness E | 4.79, 4.58, 4.12 | 4.67, 4.50, 4.00 |
| README lines in total | 1990 | 2057 |

Per dimension: A +0.29, B −0.12, C −0.08, D +0.08, E −0.12, F +0.12.
HEAD's major error was in iter11 s9: it pointed trainees at the answer key.

Targeted checks over all rounds (HEAD in iter6-iter11; the v10 family in
iter7-iter11):

| Check | HEAD | v10 draft, v10, v11 |
| --- | --- | --- |
| s2 `base_url_example` | 3 of 6 | 5 of 5 |
| s11 `upgrade_note` | 3 of 6 | 5 of 5 |
| s8 `example_label` | 0 of 6 | 5 of 5 |
| s8 `example_flat` | 0 of 6 | 0 of 5 |
| s11 `example_output` | 1 of 6 (iter11, traced by hand) | 0 of 5 (the draft's wrong output fails) |
| s1 `no_bare_pypi_install` | 6 of 6 | 4 of 5 (v11 in iter10) |

The total is inconclusive, so v11 was kept on the dimension the revision
targeted: accuracy errors halved (14 to 7) with no major error, the
targeted checks held in every round, and v11 is shorter than v10. What it
costs: highlighting and friendliness dropped slightly, READMEs are still 3%
longer than HEAD's, and one v11 README (iter10 s1) installed the zstd extra
from PyPI without a caveat.

Still open:

- **s8's nested `+` sub-bullets:** every version adds the missing label but
  keeps the nesting, although the producer's own example of that change is
  one flat bullet. v12 replaced the body with that flat bullet in all 12 of
  its runs (revision of 2026-10-04, below).
- **s11's real example:** with runs denied, no version shows verified
  output, which is now the intended behaviour.
- **One conduct slip:** in iter9 s3, v10 left a helper script,
  `scripts/_check.py`, in the dataset; no other outcome of iter6-iter11 in
  either arm added a file besides its README.
- **Harness limit:** every attempt in both arms to run a documented example
  in s1, s6, s10, and s11 (`PYTHONPATH=src python -m`, `python -c`,
  `node -e`, `go`) was denied; the allowed `python -m <package>` calls lacked
  `src` on the path, and the one allowed `python -m pytest` found pytest not
  installed. These rounds test only the branch where a writer cannot run
  examples; harness v3 lifts that for the src-layout packages (below).

### Eval changes made with the revision

- **Checks:** `base_url_example` (s2; fenced and inline code, ignoring code
  a comment marks wrong and prose that explains the slash rule),
  `no_script_run` (s3; from the command log, because the script rewrites its
  output byte for byte, so the file diff stays clean), `headings_translated`
  (s5), `upgrade_note` and `example_output` (s11; the latter needs all three
  verified rows and rejects a row for the unchanged A3), `example_flat` (s8)
  now judged by the example's content instead of its blockquote, and s1's
  publish caveat accepts "once you install the package from an index". Old
  and new checks agree on every existing key for iter6; on the 20 archived
  harness-v1 s2 outcomes, `base_url_example` fails
  only the one the judge had flagged, and in iter6 it fails both arms, which
  the judge marked major. Totals under this check version: iter6 HEAD 120 of
  128, no skill 109 of 125. The self-test has 184 cases.
- **Fact sheet s2:** the ground truth no longer lists HEAD and OPTIONS as
  retried methods (the client cannot send them), and the traps now give the
  severities the judges were improvising: an example URL that drops the base
  path is major, counted once; listing HEAD or OPTIONS as retried is minor.
  Re-judging iter6 s2 (`iter6-facts`, $0.26) reproduced the same errors and
  severities; only one D score moved.
- **s12:** the fact sheet does not require the static badge, but the judges
  preferred it in iter6, iter8, and iter9.

## Harness v3 boundary and baseline (iter12, p3, iter13)

Never pool iter12 or later with iter6-iter11. Harness v3 starts every writer
and judge session with `PYTHONPATH` listing `src` and `scenario/src`, and
with `PYTHONDONTWRITEBYTECODE=1`, so the src-layout packages of s1, s11,
and s12 import without a path prefix, and `python -m logslice` and
`python -m csvdelta` run (s12's `slugkit` is a library with no `__main__`).
Scenarios, requests, and the rubric are unchanged. The s1 and s11 fact
sheets now tell judges how to run the package from the sandbox root, and add
a minor trap: documenting `python -m` or `PYTHONPATH=src` as the way to use
an uninstalled checkout. No judge ran a package in iter12 or in iter13's
first judging: the s1 judge in both and the s11 judge in iter13 prefixed
`PYTHONPATH` or used `python -c`, and the CLI denied each attempt, because
the judge prompt then had no counterpart of `writer_note` (see the judge
command guidance below); iter12's s11 judge did not try. Those verdicts
rest on the code and the fact sheets.

- **iter12, a pilot without a note:** writers still prefixed
  `PYTHONPATH=src`, which the CLI denies, and gave up. No session ran a
  package. Since then every writer prompt in this suite, in both arms,
  carries the suite's `writer_note` in its closing note: "Commands cannot
  start with environment-variable assignments; PYTHONPATH already includes
  src."
  iter12's s1 and s11 verdicts also used earlier drafts of those fact
  sheets.
- **p3, a writer-only probe with the note (s1, s11, s12):** the sentence
  was then hard-coded in the shared prompt, before `writer_note` and its
  fingerprint existed, so p3's `round.json` and `meta.json` carry no
  `note`. HEAD ran `python -m logslice` and `python -m csvdelta`, and its
  s11 README passed `example_output`; the no-skill arm ran neither.

iter13, the v3 baseline (HEAD is v11 as committed in `18b16b2`; judgment set
`iter13`, made before the judge command guidance below):

| Arm | Mean | Firsts | Accuracy | Highlighting | Concision | Presentation | Friendliness | Usefulness |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| No skill | 4.06 | 0/12 | 4.17 | 3.92 | 4.58 | 4.00 | 3.75 | 3.58 |
| HEAD (v11) | 4.67 | 12/12 | 4.58 | 5.00 | 4.42 | 4.83 | 4.17 | 4.92 |

Paired HEAD − no skill: +0.61, 95% interval [+0.32, +0.90], wins/ties/losses
12/0/0 (iter12: +0.41 [+0.16, +0.65], 10/1/1). `checks.py`: HEAD 128 of
128, no skill 111 of 125 with 3 not applicable.

The same version under both harnesses (separate rounds, judges, and
opponents: v9 in iter10-iter11, no skill in iter13, so the means are not
paired):

| v11 | v2 (iter10 + iter11) | v3 (iter13) |
| --- | --- | --- |
| Runs | 24 | 12 |
| Judged mean | 4.60 | 4.67 |
| Denied calls per run | 1.00 | 0.83 |
| Runs that ran the scenario's package | 0 (6 attempts in s1 and s11, all denied) | 2 (s1, s11) |
| Checks passed | 250 of 255 | 128 of 128 |
| s11 `example_output` | 0 of 2 | 1 of 1 |
| s8 `example_flat` | 0 of 2 | 1 of 1 (iter12 too) |

The no-skill arm scored 4.04 (iter6), 4.09 (iter12), and 4.06 (iter13) and
never ran a package.

What the v3 rounds show:

- **The skill now verifies examples when it can.** HEAD's s11 README showed
  output from a real run for the first time; the only earlier pass of any
  version (v9 in iter11) was a correct hand trace.
- **The space form of relative times still slips through.** In s1 both
  arms wrote `--from -15m` and `--from -1h` from the code. HEAD ran only
  absolute-time examples, and its notes list the examples that use the form
  as not run. The judge counted the fact sheet's minor error in both arms:
  the form fails on the argparse of Python 3.10, the project's minimum. The
  local Python 3.14 accepts it, so a run here would not have caught it
  either.
- **HEAD's remaining denials** are commands outside the allowed list,
  `go` (s6, not installed), `pnpm` (s10), and `pdftotext` and `xxd` (s9),
  and forms the CLI denies: inline `python -c` and `python -` heredocs (s3,
  s8, s9, s11) and a `for` loop (s3).
- **s8's flat example** passed in both v3 HEAD runs (iter12, iter13) after
  failing in all 11 skill runs of iter6-iter11. s8 has nothing to run, so v3
  does not explain it, and a six-run probe of HEAD on s8 (p4) showed chance:
  `example_flat` passed in 2 of 6. Over its ten runs, v11 flattened the
  example in 4, added the label in 6, and dropped the TIP alert in 1; three
  p4 runs left the stale example as it was. The skill's audit of sample
  outputs was not reliable in a polish request until v12 (below).

## Judge command guidance (2026-10-04)

The judge logs of iter13 showed why judges ran so little: their prompt said
nothing about command forms, so most judges opened with `cd "<sandbox>";
...` or a `for` loop and were denied. The prompt also told judges to copy
`scenario/` to a folder such as `work/` without naming a command, and the
`cp -r` that judges used for it in iter6-iter11 was always denied (the CLI
rejects `cp` with any flag). The prompt now names the forms that run:
`git -C scenario <command>`, `python -m <package>` on the preset path, a
script file run with `python <file>`, and `mkdir` with flag-free `cp` for
copies. Judges may run
every allowed git command as `git -C scenario ...`. `judge.py` also rejects
an attempt in which the judge changed `scenario/`, audits the files a
judge writes, and records a digest of the judge's session arguments in each
verdict's provenance; `collect.py` warns when one set mixes judge prompts.

The same blinded iter13 outcomes, judged three times:

| Judgment set | Judge prompt | Denied calls per session | Ran git | Ran a package or script | Turns per session | No skill | HEAD | Paired HEAD − no skill | W/T/L | Judges, USD |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- | ---: |
| `iter13` | earlier | 1.50 | 1 of 12 | 1 of 12 | 18.0 | 4.06 | 4.67 | +0.61 [+0.32, +0.90] | 12/0/0 | 2.74 |
| `iter13-rj0`, control | earlier | 2.00 | 2 of 12 | 1 of 12 | 14.2 | 4.08 | 4.61 | +0.53 [+0.21, +0.85] | 10/1/1 | 2.62 |
| `iter13-j2` | 2026-10-04 | 0.58 | 6 of 12 | 3 of 12 | 6.0 | 4.06 | 4.59 | +0.53 [+0.23, +0.84] | 10/1/1 | 2.01 |

The accept rule, written before the new pass: denied calls per session at
most half the earlier level (0.9 here); no denial of a form the prompt
names; no reach flag; `scenario/` unchanged; one attempt per scenario on the
same CLI and model; and the mean score and the paired gap within a noise
band of the mean of the two earlier passes, else a second new-prompt pass.
The band is twice the SD of the differences between the two earlier passes,
divided by √n (outcomes for scores, scenarios for the gap). Outcomes that
move by 0.3 or more are reviewed one by one; they do not fail the rule.

- **Judge noise, measured by the control:** the two earlier-prompt passes
  differ by an SD of 0.14 per outcome, so one judgment's own SD is about
  0.10; the paired gap moved by −0.08 and one ranking flipped (s5).
- **The accept rule held.** Denied calls fell to a third; no `iter13-j2`
  session was flagged for reach or changed `scenario/` (the earlier sets
  did not record the latter); every verdict of the three sets came from one
  attempt on the same CLI and model. Against the mean of the two earlier
  passes, scores moved by −0.02 (band ±0.06) and the paired gap by −0.04
  (band ±0.08).
- **The control's one reach warning is a false positive.** `collect.py`
  flags s10 in `iter13-rj0` for a denied `cat > verdict.json <<'EOF'` whose
  verdict text quotes the README's `../../README.md` link; the judge read
  nothing outside its sandbox.
- **What judges now run:** the s1 and s11 judges ran the packages
  (`python -m logslice`, `python -m csvdelta`), and the s3 judge ran a
  count script. The seven remaining denials were git sub-commands outside
  the allowed list (`branch`, `show-ref`), two `cd scenario; ...` chains, an
  output redirect, and one long compound command.
- **Four outcomes moved by 0.3 or more** from the earlier mean (s3, s4, s9,
  and s10, all in the no-skill arm) and were reviewed. None of the changes
  rests on command output: no error list holds a finding the earlier passes
  lacked (s9's adds a notes claim the control gave as a weakness, and s10's
  grades one notes claim major instead of minor), and s9's accuracy score
  of 2 contradicts the judge's own error list (one major and two minor
  accuracy errors suggest 3). The new pass differs from the earlier mean by
  an SD of 0.17 per outcome, against about 0.12 expected from the control,
  and the new prompt's own noise has no second pass to measure it.

Use `iter13-j2` when pooling iter13 with later rounds, which are judged with
this prompt (`aggregate.py readme-md iter13-j2:A=none,B=head3 ...`); `iter13`
stays as the record of the earlier prompt. Do not rerun `judge.py readme-md
iter13` (or `--out iter13-rj0`) without a new `--out`: their digests no
longer match, so all 12 scenarios would be re-judged in place with the new
prompt.

## Revision of 2026-10-04 (v12: p5, iter14, iter15)

v11 brought s8's stale Usage example fully up to date in 3 of its 10 runs
(one each in iter10-iter13 and six in p4, above). A diagnosis of those runs
found that every writer had read the producer, and that the outcome
followed the question the writer asked. The four that replaced the body
named the producer's own example of the same change. The six that did not
had checked the sample against the producer's rules, which its body obeys:
nested sub-bullets are still allowed. The sample as a whole does not obey
them, because it lacks the required label, which three of the six added and
three missed. v11's sentence asks for exactly that conformance check ("Compare each
sample output, line by line, with the format its producer ... defines,
including the producer's own examples"). Label and body also failed
independently, because the producer's same-case example carries no label.

Three diagnosis agents, three proposals, and two refuting reviewers per
proposal led to one replacement inside the improve-mode paragraph (v12,
content hash `45b247e16189`):

> Treat each sample output as a copy: search the project for its title,
> command, or first line to find where its producer (the code or rules that
> generate it) shows the same case. Where that original differs, replace the
> lines it covers with its current text, even when the producer's rules still
> allow the old form, and keep the sample's other lines. Also add any label or
> wrapper the producer's format requires around the output. Update any other
> stale example from its current source.

A second candidate (candB) added an end state to Verify item 9 and a report
line naming each sample's original. Two reviewers of the final texts found
both additions defective (whole-sample equality contradicts "keep the
sample's other lines"; the report line scripts a claim about a search), and
the probe showed no gain from them, so they were dropped.

Probe p5 (writers only, s8, one batch):

| Arm | Runs | Both example checks | `example_current` | `example_label` | `scope_line_kept` | `tip_kept` | Changed lines, median | Runs changing nothing else |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| base (v11) | 4 | 2 | 4 | 2 | 3 | 1 | 20 | 0 |
| candA (v12) | 10 | 10 | 10 | 10 | 10 | 10 | 7 | 6 |
| candB | 10 | 10 | 10 | 10 | 9 | 10 | 9 | 6 |

The accept rule written before the probe asked for both example checks in
at least 8 of 10 runs with the kept-checks intact; candA met it and is the
smaller text. The base arm of this batch behaved unlike its ten earlier
runs: it replaced the body in 4 of 4 and dropped the TIP alert in 3 of 4,
with the same CLI and model alias. Only same-batch comparisons count.

Rounds iter14 and iter15 (B = v11, C = v12):

| Round | v11 | v12 | Paired v12 − v11 | W/T/L | Checks v11 | Checks v12 | s8 judged, v11 / v12 |
| --- | ---: | ---: | --- | --- | --- | --- | --- |
| iter14 | 4.69 | 4.52 | −0.18 [−0.35, −0.01] | 3/1/8 | 129 of 132 | 131 of 132 | 4.73 / 4.91 |
| iter15 | 4.47 | 4.66 | +0.19 [+0.01, +0.38] | 7/2/3 | 127 of 132 | 130 of 131 | 4.18 / 4.91 |
| pooled | 4.58 | 4.59 | +0.01 [−0.13, +0.15] | 10/3/11 | 256 of 264 | 261 of 263 | |

Per dimension, pooled: A +0.08, B −0.12, C −0.04, D +0.12, E −0.21, F +0.12;
every paired interval includes 0. Errors: v11 one major and 15 minor, v12 no
major and 11 minor. README lines in total (the judges' `lines`, as in the
v11 table above; s7 writes none): 2047 against 2049 (+0.1%; iter14 +2.6%,
iter15 −2.3%).

- **Target met.** v12 passed `example_current` and `example_label` in all 12
  of its runs (p5 and both rounds); v11 passed both in 2 of its 6 runs of the
  same batches. In iter15, v11 left the example untouched and told the owner
  it "follows the skill's own format", which the judge counted as a major
  error.
- **iter14 looked like a regression; iter15 did not reproduce it.** Its
  interval excluded 0, which tripped a guard of the accept rule written
  before iter14; that rule said to stop there and revise the text. The
  deficit sat in the seven create-mode scenarios (mean −0.29), where the
  edited sentence does not apply. v12 had more judged errors than v11 in
  four of them (s1, s4, s5, s9; five errors), and four of the five repeat
  slips of earlier rounds: s1's zstd hint (v11 in iter10), s9's file order
  (v11 in iter10, iter11, and iter13), s5's sample log shown after a
  `-SkipCopy` run (v11 in iter13), and s4's `gen:types` (earlier versions
  and the no-skill arm; v11 itself in iter15). The fifth, an invented
  reading time in s9, is new. A revision therefore had no target, and the
  rule was amended with iter14's result known and before iter15 ran: iter15
  would run as a replication, and v12 would be kept only if the pooled
  intervals of the total and of accuracy included 0 or lay above it and the
  s8 target held in both rounds. iter15 reversed the sign. Pooled by mode:
  improve-mode scenarios (s2, s8, s11, s12) +0.09 [−0.35, +0.52], the seven
  create-mode scenarios −0.04 [−0.25, +0.18]; s7, the review scenario, is in
  neither.
- **One guard was missed by its letter.** v12 alone failed two checks, one
  per round (s1 `no_bare_pypi_install` in iter14, s8 `tip_kept` in iter15),
  where the rule allowed one. Both are slips of v11 as well: v11 failed the
  s1 check in iter15 and dropped the TIP alert in 3 of its 6 same-batch s8
  runs, against 1 of 12 for v12. v11 alone failed eight checks.

v12 was kept on that amended rule, not on the rule as first written, which
iter14 had failed: the pooled intervals of the total and of accuracy
include 0, and the target held in both rounds.

Limits:

- **The two rounds disagree.** Per scenario, iter15's paired difference
  exceeds iter14's by 0.37 on average (95% interval [+0.11, +0.63]) with
  identical settings, so no cause is identified. The pooled interval treats
  the 24 pairs as independent and allows for no shift shared by a whole
  round. Read [−0.13, +0.15] as "no regression shown", not as a bound of
  ±0.14; the accept rule only needs the interval to include 0.
- **The search never ran.** No writer in any arm searched for the sample;
  all read the producer whole and paired the two by reading. Whatever v12
  gained came from the rest of the sentence, so the search clause has no
  evidence. The runs cannot split that gain between the copy framing and the
  label clause: in the same batches v11 replaced the body in 4 of 6 runs (4
  of 4 in p5) and added the label in 3 of 6, where v12 did each in 12 of 12.
  Prune the search clause, or add a scenario whose producer is too large to
  read whole.
- **Lighter polish.** In p5, 6 of 10 v12 runs changed nothing outside the
  example, where every v11 run changed something else. Both judged v12
  outcomes scored 4.91 with 1 and 3 changed lines outside it: a reworded
  sentence in iter14, and in iter15 the TIP alert turned into a pointer (the
  `tip_kept` slip above). Both judges called that change near-neutral churn
  and listed light polish as a weakness ("Polish is very light"; "Did little
  to make the first screen more inviting, though it was already strong");
  neither counted an error for it. The iter14 judge, at low confidence, also
  named two improvements v11 made and v12 missed. s8 is the suite's only
  polish request, on an already strong README, so the suite cannot tell
  whether v12 under-polishes a weaker one.
- **Computed wrappers.** A producer that prints a label from a format string
  has no text to copy; no scenario has that shape.
- **Friendliness** is the dimension to watch: −0.21 pooled, [−0.49, +0.08].

### Eval changes made with the v12 revision

- **Checks:** s8 gained `example_kept`, `example_current` (the example
  contains the producer's bullet; every run that passes it here holds
  exactly the producer's example), `scope_line_kept`, and
  `safety_sentence_kept`, added with their cases before any candidate ran. Under them, v11's ten
  earlier runs pass `example_current` in 4, both example checks in 3, and
  `scope_line_kept` in 9. The self-test has 188 cases.
- **Work root:** p5, iter14, and iter15 ran with `LISA_EVAL_WORK` on another
  drive (`D:\lisa-skills-tmp\lisa-evals`), because the system temp drive
  was full. The scenarios rebuilt there have the tree digests recorded for
  iter13.

## Token use and cost

Recorded by the harness for iter6 (API list prices):

| Round | Role | Group | Sessions | Turns | Input | Cache write | Cache read | Output | USD |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| iter6 | writer | A (no skill) | 12 | 77 | 100 | 65.7k | 379.0k | 23.4k | 0.57 |
| iter6 | writer | B (HEAD) | 12 | 137 | 138 | 150.9k | 796.6k | 36.8k | 1.13 |
| iter6 | judge | Opus | 12 | 210 | 178 | 194.6k | 1.11M | 46.4k | 2.71 |
| iter6 | total | | 36 | 424 | 416 | 411.2k | 2.28M | 106.5k | 4.41 |
| trigger | query | HEAD | 19 | 110 | 140 | 340.9k | 1.39M | 38.8k | 2.03 |

The 2026-10-03 revision, by round (writers Sonnet, judges Opus):

| Round | Sessions | Writers | Judges | USD |
| --- | ---: | ---: | ---: | ---: |
| iter6-facts (re-judge s2) | 1 | — | 0.26 | 0.26 |
| iter7 | 36 | 2.36 | 2.83 | 5.19 |
| iter8 | 36 | 2.36 | 2.92 | 5.29 |
| iter9 | 36 | 2.37 | 2.80 | 5.17 |
| iter10 | 36 | 2.26 | 2.73 | 5.00 |
| iter11 | 36 | 2.37 | 2.83 | 5.20 |
| total | 181 | 11.72 | 14.37 | 26.11 |

The harness v3 rounds:

| Round | Sessions | Writers | Judges | USD |
| --- | ---: | ---: | ---: | ---: |
| iter12 (pilot) | 36 | 1.76 | 2.69 | 4.45 |
| p3 (writers only) | 6 | 0.41 | — | 0.41 |
| iter13 | 36 | 1.79 | 2.74 | 4.53 |
| p4 (writers only, s8) | 6 | 0.75 | — | 0.75 |
| iter13-rj0 (re-judge) | 12 | — | 2.62 | 2.62 |
| iter13-j2 (re-judge) | 12 | — | 2.01 | 2.01 |
| total | 108 | 4.71 | 10.05 | 14.76 |

The v12 revision (work root on drive D, so `usage.py` there lists only these
rounds):

| Round | Sessions | Writers | Judges | USD |
| --- | ---: | ---: | ---: | ---: |
| p5 (writers only, s8) | 24 | 2.81 | — | 2.81 |
| iter14 | 36 | 2.34 | 2.08 | 4.42 |
| iter15 | 36 | 2.31 | 1.93 | 4.24 |
| total | 96 | 7.47 | 4.00 | 11.47 |

Totals come from the unrounded records, so they can differ from the column
sums by a cent.

The diagnosis and review agents of the interactive session are not included.

Earlier spend, before token tracking existed. Recorded figures are the CLI's
own costs from the archived `meta.json` files or harness output; estimates
price token counts recovered from Claude Code subagent transcripts at the
2026-10-02 list prices, with output tokens estimated to about ±50%:

| Round | Writers | Judges (Opus subagents) | Total |
| --- | --- | --- | --- |
| iter1 | $23.64 estimated (Sonnet subagents) | $11.51 estimated | $35.15 |
| iter2 | $4.72 recorded, plus at least $1.81 in an aborted first attempt | $13.30 estimated | $19.84 |
| iter3 | $5.39 recorded | $11.81 estimated | $17.19 |
| iter4 | $5.60 recorded | $11.60 estimated | $17.20 |
| iter5 | $9.46 recorded (Opus writers) | $11.58 estimated | $21.05 |
| probe2, probe8, probe9 | $5.95 recorded | — | $5.95 |

Together with harness smoke tests and setup probes ($0.68), the v1 rounds
cost about $117 at list prices, $34 of it recorded. Their trigger tests and
the token counts of headless sessions were not recorded. Reproduce or extend
the recorded figures with `python usage.py readme-md`.

## Lessons

- Name what a sample is a copy of, not what it must conform to. Asked to
  compare a sample "with the format its producer ... defines", writers
  checked that the stale sample was still allowed and called it a match in
  6 of v11's 10 earlier runs; asked to treat it as a copy of the producer's
  own passage, 12 of 12 replaced it (v11 in the same batches: 4 of 6).
- One round can mislead in either direction: iter14 and iter15 compared the
  same two versions and gave −0.18 [−0.35, −0.01] and +0.19 [+0.01, +0.38].
  Write the decision rule down first, and say in it what happens when one
  round trips a guard: here the rule had to be amended with iter14's result
  known. Replicate before acting on a single interval, check where a deficit
  sits before blaming the edit, and do not read the pooled interval of two
  rounds that disagree as a tight bound.
- Make sure writers can run what the skill tells them to check, and tell
  them how: presetting `PYTHONPATH` changed nothing until the prompt said
  that it was set and that prefixes are denied. Judges needed the same:
  once their prompt named the forms that run, their denied calls fell from
  1.5-2.0 to 0.6 per session and a judge pass cost about a quarter less.
- A verification rule needs a fallback for when the check cannot run: "trace
  each example" alone produced a confidently wrong traced output in s11, the
  costliest error of the revision.
- Judges reward visible output even when it was worked out by hand, so a
  rule that drops unverified output costs points in scenarios where the hand
  trace happened to be right (s6).
- Prune rules the checks cannot separate: v10's five unevidenced rules cost
  concision, and removing them (v11) kept the targeted gains and halved the
  accuracy errors.
- A scenario that is already good (s8) is the best probe for over-editing;
  a stale one (s2) is the best probe for under-editing. Test both.
- Wording that tightens one mode leaks into others: a concision rule removed
  an owner's TIP alert, and an evidence rule deleted sponsors.
- Mechanical checks catch preservation and leak regressions in seconds; use
  them for probes and keep judges for quality.
- Pooled per-version means hide small differences: decide from paired
  intervals, and expect one round of 12 scenarios to resolve about ±0.26.
- Subagent judges cost more than they seemed: about $11-13 per nine-scenario
  round at list prices, more than the writers. Headless judges in iter6 cost
  $0.13-0.31 per scenario.
