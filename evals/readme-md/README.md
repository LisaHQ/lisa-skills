# readme-md evaluation

A blind A/B harness that tells you whether a change to
[`skills/readme-md`](../../skills/readme-md/SKILL.md) makes agents write better
READMEs: more accurate, clearer about what matters, shorter, better presented,
and friendlier. Use it before you ship any edit to the skill.

Writers run in headless Claude Code on nine realistic scenarios, a separate
model judges the outcomes without knowing which version wrote them, and the
scripts turn verdicts into per-version scores.

## What's here

```text
evals/readme-md/
├── rubric.md          # Pre-registered scoring criteria and verdict format
├── requests.json      # The user request for each scenario
├── facts/             # Ground truth, traps, and judge notes per scenario
├── scenarios/         # Deterministic builders for the nine test projects
├── harness/           # Scripts: build, snapshot, run, blind, judge, score
└── results/
    └── history.md     # Every round so far, version scores, and lessons
```

Generated material never lands here. It goes to a work directory:
`$README_EVAL_WORK`, or `<system temp>/readme-md-eval` by default. Keep that
directory out of Dropbox and Git; a full round writes thousands of files and
nested `.git` folders. Archives of finished rounds belong in `archive/`, which
Git ignores.

## Requirements

- Python 3.10 or newer (standard library only) and Git.
- The Claude Code CLI, signed in, so `claude -p` works. Set `CLAUDE_BIN` if
  the harness cannot find it.
- Budget: one Sonnet writer run costs about $0.10–0.30 and 20–60 seconds; one
  headless Opus judge about $0.30–1. A full round (9 scenarios × 3 arms plus
  9 judges) takes about 20 minutes at 9 parallel jobs.

## Compare an edit with the committed skill

Run everything from `harness/`:

```bash
python build_scenarios.py                  # once per machine; rebuilds identical fixtures
python snapshot_skill.py base --ref HEAD   # the committed version
python snapshot_skill.py cand              # your working-tree edit
python prep_runs.py r1 A B C
python run_arms.py r1 A=none B=base C=cand --jobs 9
python blind.py r1 A B C
python judge.py r1 --jobs 9
python collect.py r1
python checks.py r1
```

`collect.py` prints each scenario's weighted score per arm (1–5), the six
dimension scores, error counts, and the judge's ranking, then per-arm means.
`checks.py` adds fast pass/fail signals for known traps, such as a leaked
password or a dropped badge.

One round is not enough: single runs vary by about ±0.3. Run a second round
(`r2`) with fresh runs, then pool them:

```bash
python aggregate.py r1:A=none,B=base,C=cand r2:A=none,B=base,C=cand
```

Treat a difference as real only when it exceeds about twice the reported
standard error, and read the judges' `weaknesses` before trusting a mean.

## The improvement loop

1. **Pin the yardstick.** Leave `rubric.md` unchanged during a comparison.
   Add new traps to `facts/` before you run, never after you see results.
2. **Run baseline and candidate together** with the same writer model, from
   neutral directories (`run_arms.py` does this).
3. **Blind, judge, collect.** `blind.py` scrubs run paths from the writers'
   notes, because paths name the arm.
4. **Fix mechanisms, not symptoms.** Read why the losing outcomes lost, find
   the rule that caused it, and change the smallest wording that fixes it.
5. **Probe cheaply.** Rerun only the affected scenario 3–5 times and check
   it mechanically:
   `python prep_runs.py p1 A1 A2 A3 --only s8-lisa-skills`, then
   `python run_arms.py p1 A1=cand A2=cand A3=cand --only s8-lisa-skills` and
   `python checks.py p1`.
6. **Confirm with full rounds** before keeping a change, and watch for
   regressions in scenarios you did not target.
7. **Validate the final version with a stronger writer:** after
   `python prep_runs.py rN A B`, run
   `python run_arms.py rN A=none B=cand --model opus`, then blind and judge.
8. **Archive** the work directory when you finish (see below).

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

## Judging

`judge.py` runs one headless judge per scenario (Opus by default) in a
sandbox holding only the rubric, the fact sheet, the request, the pristine
scenario, and the blinded outcomes. To judge with subagents in an interactive
session instead, run `python judge.py r1 --print-prompts` and give each
subagent its prompt and sandbox; save each verdict as
`<work>/judgments/r1/<scenario>.json`.

## Trigger test

```bash
python trigger_test.py cand
```

It installs the skill in a throwaway project and checks that ten queries load
it, or leave it alone, as expected. Edit `QUERIES` in the script to probe new
near-misses.

## Archive a round

```bash
python export_archive.py ../archive/readme-md-eval-<date>.zip --note ../results/history.md
```

The zip keeps snapshots, blinded outcomes, verdicts, mappings, run notes and
metadata, and the files each writer changed, but drops the regenerable run
copies. To revisit it, unzip into a folder, set `README_EVAL_WORK` to that
folder, and run `collect.py`, `aggregate.py`, or `checks.py`.

## Gotchas

- **Do not run writer arms as subagents inside this repository.** They inherit
  `AGENTS.md` and `CLAUDE.md`, which lift the no-skill baseline far above what
  users see in their own projects.
- **Headless permissions:** writers may read, count, inspect Git, and run local
  interpreters; installs and web access stay denied. Extend `WRITER_BASH` in
  `evalenv.py` only with read-only commands.
- **Windows:** the harness calls the `claude.exe` behind npm's `claude.cmd`
  shim. Work directories on drives that do not record file ownership pass
  `safe.directory=*` to Git through the environment, so your Git config stays
  untouched.
- **Fixtures are trimmed:** `s4` has stub implementations; its judge notes
  tell judges not to penalize honest reports of stubs.
- **`s8` is pinned** to commit `668ba4f`. Pass `--s8-ref` to retarget it, and
  update `facts/s8-lisa-skills.md` and `checks.py` to match.

## Add a scenario

1. Add a builder in `scenarios/` with a `ROOT` name and a `build(base)`
   function, and register it in `BUILDERS` in `harness/build_scenarios.py`.
2. Add the request to `requests.json` and a fact sheet in `facts/` with core
   points, traps, and judge notes.
3. Optionally add a mechanical check function in `harness/checks.py`.
