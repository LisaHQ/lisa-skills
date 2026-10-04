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
├── scenarios/         # Deterministic builders for the twelve test projects
├── suite_checks.py    # Mechanical checks, one function per scenario
├── mdcheck.py         # Link, anchor, fence, and heading checks for any README
├── check_cases.json   # Self-test cases with expected check results
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

Start with `python selftest.py --quick --suite readme-md`, which spends no
model usage. Run a second round with fresh runs and pool them before deciding:
`python aggregate.py readme-md r1:A=none,B=base,C=cand r2:A=none,B=base,C=cand --pair base,cand`.

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
| `s10-acme-platform` | Package in a pnpm monorepo | Create | Subfolder README, workspace install, license conflict, generated docs, lint style |
| `s11-csvdelta` | Python CLI | Improve | Vietnamese request for an English README, stale translation, renamed flags, broken links |
| `s12-slugkit` | Python library | Narrow edit | Requested badges without a source, unescaped static badges, scope, a stale line |

`s4` has stub implementations; its judge notes tell judges not to penalize
honest reports of stubs. `s8` clones this repository at `repo_ref` in
`suite.json`, keeping only `main` and its history. The build refuses a commit
whose history contains `evals/` or `skills/readme-md`, because writers could
read the fact sheets and the skill under test. Retarget `s8` only to a commit
that predates the eval harness (before `314060f`), with `--ref` or `repo_ref`,
then update `facts/s8-lisa-skills.md` and `suite_checks.py` to match; a later
commit would need a filtered history.

Checks named `md_*` are advisory Markdown hygiene from `mdcheck.py`: broken
relative links and anchors, unclosed or untagged code fences, and heading
problems. They count only problems the original README did not already have,
and are skipped when the README is absent or unchanged.

Some checks read the session rather than the files: `no_script_run` (s3)
reads the command log, because the aggregation script rewrites its output
byte for byte. `example_output` (s11) requires all three verified rows, so a
hand-traced output with a wrong row fails.

## Results and archive

[`results/history.md`](results/history.md) records every round, version
scores, and lessons. The raw material is in `archive/` (Dropbox only):
`readme-md-eval-2026-10-02.zip` (harness v1), `-2026-10-02-v2.zip` (iter6),
`-2026-10-03.zip` (iter6-iter11), and `-2026-10-04.zip` (iter6-iter13 with
every judgment set, harness v2 and v3). To revisit the first one, unzip
it into a separate work root (`LISA_EVAL_WORK=<other folder>`, under
`<that folder>/readme-md/`) so its older scenario build does not replace the
current one, and run `collect.py`, `aggregate.py`, `checks.py`, or `usage.py`
with the suite name. Those rounds ran `s1`–`s9` under harness v1, so compare
pooled means only between rounds with the same scenario set and harness.

## Add a scenario

1. Add a builder module in `scenarios/` with `ROOT` and `build(base)`, and
   register it in `BUILDERS` in `scenarios/suite_build.py`. Build twice and
   confirm the files and commits are identical.
2. Add the request to `requests.json` and a fact sheet in `facts/` with ground
   truth, core points, traps with severities, and judge notes. Verify every
   fact against the built scenario, running the code on a copy.
3. Add a check function to `CHECKS` in `suite_checks.py` for the traps that can
   be checked mechanically, merged with `markdown(ctx)`, and a row to the
   scenario table above.
4. Add at least one good and one bad outcome to `check_cases.json`, plus a case
   for every false result you fix. A case names its scenario, the files it
   writes or deletes, optional notes, and the expected result of each check it
   asserts. From `evals/harness/`, run
   `python selftest.py --quick --suite readme-md` until every expectation
   passes.
