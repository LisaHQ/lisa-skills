# readme-md evaluation history

Results of the rounds run while creating the skill on 2026-10-02 (iter1-iter5
and probes, harness v1) and the first harness v2 baseline (iter6). The raw
material is in `archive/readme-md-eval-2026-10-02.zip` (snapshots v1-v9,
blinded outcomes, verdicts, mappings, run notes) and
`archive/readme-md-eval-2026-10-02-v2.zip` (iter6), kept in Dropbox only.

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
10/1/1. `checks.py`: HEAD 120 of 123, no skill 107 of 120. Trigger test: 19 of
19 as expected.

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

## Token use and cost

Recorded by the harness for iter6 (API list prices):

| Round | Role | Group | Sessions | Turns | Input | Cache write | Cache read | Output | USD |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| iter6 | writer | A (no skill) | 12 | 77 | 100 | 65.7k | 379.0k | 23.4k | 0.57 |
| iter6 | writer | B (HEAD) | 12 | 137 | 138 | 150.9k | 796.6k | 36.8k | 1.13 |
| iter6 | judge | Opus | 12 | 210 | 178 | 194.6k | 1.11M | 46.4k | 2.71 |
| iter6 | total | | 36 | 424 | 416 | 411.2k | 2.28M | 106.5k | 4.41 |
| trigger | query | HEAD | 19 | 110 | 140 | 340.9k | 1.39M | 38.8k | 2.03 |

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
