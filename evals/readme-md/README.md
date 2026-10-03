# readme-md evaluation suite

Blind A/B suite for [`skills/readme-md`](../../skills/readme-md/SKILL.md):
does a change make agents write READMEs that are more accurate, clearer about
what matters, shorter, better presented, and friendlier? The shared harness
and the round workflow are described in [`evals/README.md`](../README.md).

## What's here

```text
evals/readme-md/
├── suite.json         # Skill name, rubric weights, pinned commit for s8
├── rubric.md          # Pre-registered scoring criteria and verdict format
├── requests.json      # The user request for each scenario
├── facts/             # Ground truth, traps, and judge notes per scenario
├── scenarios/         # Deterministic builders for the nine test projects
├── suite_checks.py    # Mechanical checks, one function per scenario
├── trigger.json       # Queries for the trigger test
└── results/
    └── history.md     # Every round so far, version scores, and lessons
```

## Compare an edit with the committed skill

From `evals/harness/`:

```bash
python build_scenarios.py readme-md
python snapshot_skill.py readme-md base --ref HEAD
python snapshot_skill.py readme-md cand
python prep_runs.py readme-md r1 A B C
python run_arms.py readme-md r1 A=none B=base C=cand --jobs 9
python blind.py readme-md r1 A B C
python judge.py readme-md r1 --jobs 9
python collect.py readme-md r1
python checks.py readme-md r1
```

Run a second round with fresh runs and pool them before deciding:
`python aggregate.py readme-md r1:A=none,B=base,C=cand r2:A=none,B=base,C=cand`.

## Improvement loop

1. **Pin the yardstick.** Leave `rubric.md` unchanged during a comparison; add
   new traps to `facts/` before you run, never after you see results.
2. **Fix mechanisms, not symptoms.** Read why losing outcomes lost, find the
   rule that caused it, and change the smallest wording that fixes it.
3. **Probe cheaply.** Rerun only the affected scenario 3–5 times and check it
   mechanically, for example
   `python prep_runs.py readme-md p1 A1 A2 A3 --only s8-lisa-skills`,
   `python run_arms.py readme-md p1 A1=cand A2=cand A3=cand --only s8-lisa-skills`,
   then `python checks.py readme-md p1`.
4. **Confirm with full rounds** and watch scenarios you did not target.
5. **Validate the final version with a stronger writer**: `--model opus`
   against `none`.

## Scenarios

| ID | Kind | Mode | What it probes |
| --- | --- | --- | --- |
| `s1-logslice` | Python CLI | Create | Command name differs from the package, unpublished package, binary-search caveats |
| `s2-fetchkit` | TypeScript library | Improve | Stale v1 README: renamed API, removed caching, hype, sponsors to keep |
| `s3-hanoi-air-quality` | Dataset | Create | Units, local time, missing-value code, non-commercial license, row counts |
| `s4-shopfloor` | Monorepo | Create | Repository map, one-command start, ports, no license file |
| `s5-sao-luu-erp` | Internal scripts | Create | Vietnamese output, plaintext password in config, destructive restore |
| `s6-grepl` | Tiny Go tool | Create | Thin evidence: no license, CI, or published module path |
| `s7-tasklog` | Node CLI | Review | Findings only, with no file changes |
| `s8-lisa-skills` | This repository at `668ba4f` | Polish | Over-editing a strong README; a stale example |
| `s9-cnc-onboarding` | Training material | Create | Unreadable binaries, a trainers-only answer key, PDF content |

`s4` has stub implementations; its judge notes tell judges not to penalize
honest reports of stubs. `s8` clones this repository at `repo_ref` in
`suite.json`; pass `--ref` to `build_scenarios.py` to retarget it, then update
`facts/s8-lisa-skills.md` and `suite_checks.py` to match.

## Results and archive

[`results/history.md`](results/history.md) records every round, version
scores, and lessons. The raw material of the 2026-10-02 rounds is in
`archive/readme-md-eval-2026-10-02.zip` (Dropbox only). To revisit it, unzip
it into `<LISA_EVAL_WORK>/readme-md/` and run `collect.py`, `aggregate.py`, or
`checks.py` with the suite name.

## Add a scenario

1. Add a builder module in `scenarios/` with `ROOT` and `build(base)`, and
   register it in `BUILDERS` in `scenarios/suite_build.py`.
2. Add the request to `requests.json` and a fact sheet in `facts/` with core
   points, traps, and judge notes.
3. Add a check function to `suite_checks.py` if a trap can be checked
   mechanically.
