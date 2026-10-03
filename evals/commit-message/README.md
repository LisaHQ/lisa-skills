# commit-message evaluation suite

Blind A/B suite for [`skills/commit-message`](../../skills/commit-message/SKILL.md):
does a change make agents pick exactly the right changes and describe them in
accurate, concise, well-formed commit messages, without touching the
repository? The shared harness and the round workflow are described in
[`evals/README.md`](../README.md).

## What's here

```text
evals/commit-message/
├── suite.json         # Skill name, rubric weights, read-only Git and SVN commands
├── rubric.md          # Pre-registered scoring criteria and verdict format
├── requests.json      # The user request for each scenario
├── facts/             # Correct selection, net changes, traps, and judge notes
├── scenarios/         # Deterministic Git (c1-c9) and SVN (c10) builders
├── suite_checks.py    # Format, content, and repository-state checks
├── trigger.json       # Queries for the trigger test
└── results/
    └── history.md     # Rounds so far and lessons
```

## Compare an edit with the committed skill

From `evals/harness/`:

```bash
python build_scenarios.py commit-message
python snapshot_skill.py commit-message base --ref HEAD
python snapshot_skill.py commit-message cand
python prep_runs.py commit-message r1 A B C
python run_arms.py commit-message r1 A=none B=base C=cand --jobs 10
python blind.py commit-message r1 A B C
python judge.py commit-message r1 --jobs 10
python collect.py commit-message r1
python checks.py commit-message r1
```

A round of 10 scenarios × 3 arms takes about 10 minutes. Pool at least two
rounds with `aggregate.py` before keeping a change.

## Scenarios

| ID | Request | State | What it probes |
| --- | --- | --- | --- |
| `c1-shipcalc` | My changes (auto) | Staged and unstaged edits to one file, unstaged-only files, untracked test | Combined working-tree view; the staged-only value must not leak |
| `c2-notes-api` | My staged changes | Unstaged rename and DELETE route on top of a staged endpoint | Reading the index, not the working tree |
| `c3-csvtool` | What I've got (auto) | Staged edit reverted in the working tree; staged deletion recreated identically | Net-cancelled changes stay out |
| `c4-dashboard` | These changes (auto) | New httpx dependency, new module nothing calls, settings nothing reads | Dependencies and integration gaps survive concision |
| `c5-ledger` | My changes (auto) | Renamed module and CLI option | Rename pairing, `BREAKING CHANGE:` with migration |
| `c6-todo-cli` | Staged only | Nothing staged; unstaged change present | Report an empty selection; no substitution |
| `c7-catalog-api` | Vietnamese request (auto) | Off-by-one fix with test | Report in Vietnamese, message in English |
| `c8-invoices` | Squash HEAD~3..HEAD | Three commits plus an uncommitted debug print | Net range diff, no intermediate "fix", no working changes |
| `c9-notifier` | My changes (auto) | Untracked config with a live-looking token; ignored `.env` | No secrets in output; warn before committing a credential |
| `c10-reports` | My staged changes | SVN working copy with modify, add, delete | SVN has no staging: report, do not substitute |

Every scenario also checks that the writer staged, committed, reverted, or
edited nothing: `blind.py` records version-control changes in each outcome's
`changes.txt`, and `checks.py` compares HEAD, index, and stash (or the SVN
schedule) with the pristine scenario.

## Results

[`results/history.md`](results/history.md) records each round. Archive a
round with `python export_archive.py commit-message
../commit-message/archive/<name>.zip --note ../commit-message/results/history.md`;
the zip stays in Dropbox only.

## Add a scenario

1. Add a builder to `scenarios/git_scenarios.py` (or a new module) that ends
   with `expect_status(...)`, and register it in `scenarios/suite_build.py`.
2. Add the request to `requests.json` and a fact sheet with the correct
   selection, net change, an example message, traps, and judge notes.
3. Add a check function to `suite_checks.py` for traps that can be checked
   mechanically.
