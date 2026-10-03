# readme-md evaluation history

Results of the rounds run while creating the skill on 2026-10-02. The raw
material (snapshots v1–v9, blinded outcomes, verdicts, mappings, run notes)
is in `archive/readme-md-eval-2026-10-02.zip`, kept in Dropbox only.

Scores are weighted rubric scores from 1 to 5 (see `rubric.md`). One run
varies by about ±0.3, so compare versions across rounds, not single runs.

## Rounds

| Round | Writer environment | Writer | Arms (versions) | Judge |
| --- | --- | --- | --- | --- |
| iter1 | Subagents inside this repository | Sonnet | A = no skill, B = v1 | Opus subagent, pairwise |
| iter2 | Headless `claude -p`, neutral folders | Sonnet | A = no skill, B = v1, C = v2 | Opus subagent, three-way |
| iter3 | Headless, neutral | Sonnet | B = v1, C = v2, D = v3 | Opus subagent, three-way |
| iter4 | Headless, neutral | Sonnet | C = v2, D = v3, E = v4 | Opus subagent, three-way |
| iter5 | Headless, neutral | Opus | A = no skill, V = v8 | Opus subagent, pairwise |
| probe2, probe8, probe9 | Headless, neutral | Sonnet | Repeated runs of v4–v9 on s2, s8, s9 | `checks.py` assertions |

iter1 is not comparable with later rounds: the writers inherited this
repository's `AGENTS.md`, which made the no-skill baseline unrealistically
strong (4.49 against 4.59 for v1).

## Version scores (iter2–iter4 pooled, Sonnet writers)

| Version | Runs | Mean | SE | Major errors | Minor errors per run |
| --- | --- | --- | --- | --- | --- |
| No skill | 9 | 4.03 | 0.11 | 3 | 1.56 |
| v1 | 18 | 4.37 | 0.08 | 0 | 0.89 |
| v2 | 27 | 4.36 | 0.06 | 0 | 0.81 |
| v3 | 18 | 4.43 | 0.09 | 1 | 0.83 |
| v4 | 9 | 4.45 | 0.10 | 0 | 0.78 |

Dimension means for the no-skill baseline against v4: accuracy 3.67 → 4.33,
core highlighting 3.89 → 4.78, concision 4.56 → 3.89, presentation 4.22 →
4.78, friendliness 3.89 → 4.33, usefulness 4.11 → 4.78. The skill trades some
brevity for completeness and correctness.

Reproduce with:

```bash
python aggregate.py iter2:A=base,B=v1,C=v2 iter3:B=v1,C=v2,D=v3 iter4:C=v2,D=v3,E=v4
```

## Final validation (iter5, Opus writers)

| Version | Mean | Firsts | Accuracy | Highlighting | Concision | Presentation |
| --- | --- | --- | --- | --- | --- | --- |
| No skill | 4.37 | 4/9 | 4.00 | 4.56 | 4.44 | 4.44 |
| v8 | 4.49 | 5/9 | 4.22 | 4.78 | 4.22 | 5.00 |

A stronger writer gains less from the skill, but the skill still removed the
baseline's worst failures: four minor errors in s5 and an unverified
`go install` path in s6.

## Probes

| Probe | Version | Result |
| --- | --- | --- |
| s8 polish, preservation | v4–v6 | 8 of 11 runs dropped a badge, the TIP alert, the footer, or emoji |
| s8 polish, preservation | v7 | 0 of 5 runs dropped owner content |
| s2 stale update | v7 | 1 of 3 runs deleted Sponsors and Contributors as "unsupported" |
| s2 stale update | v8 | 4 of 4 runs passed every check |
| s9 answer key | v9 | 0 of 3 runs leaked trainers-only content |
| Trigger test (10 queries) | v3, then v9 | 10 of 10 as expected, both times |

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

## Lessons

- A scenario that is already good (s8) is the best probe for over-editing;
  a stale one (s2) is the best probe for under-editing. Test both.
- Wording that tightens one mode leaks into others: a concision rule removed
  an owner's TIP alert, and an evidence rule deleted sponsors.
- Mechanical checks catch preservation and leak regressions in seconds; use
  them for probes and keep judges for quality.
- Single-run scores swing by ±0.3. Pool at least two rounds before choosing
  between versions.
