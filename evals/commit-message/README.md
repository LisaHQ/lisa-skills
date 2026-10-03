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
├── scenarios/         # Deterministic Git (c1-c9, c11-c13, c15, c16) and SVN (c10, c14) builders
├── suite_checks.py    # Format, content, and repository-state checks
├── check_cases.json   # Crafted and archived outcomes with the check results they must get
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
python collect.py commit-message r1 --drop E
python checks.py commit-message r1
python aggregate.py commit-message r1:A=none,B=base,C=cand --pair base,cand --drop E
```

Start with `python selftest.py --quick --suite commit-message`, which spends
no model usage. A round of 16 scenarios × 3 arms is 48 writer runs and 16
judge runs. The 10-scenario rounds took about 10 minutes, so expect about 15.
Pool at least two rounds with `aggregate.py` before keeping a change.

The rubric encodes the skill's own output contract: B rewards the selection
report, C the type order, and E the `Commit description:` format. A
none-versus-skill difference therefore includes format conformance by design;
`--drop E` reports it without E as well. Between two skill versions both arms
share the contract, so the full score is the measure.

## Scenarios

| ID | Request | State | What it probes |
| --- | --- | --- | --- |
| `c1-shipcalc` | My changes (auto) | Staged and unstaged edits to one file, unstaged-only files, untracked test | Combined working-tree view; the staged-only value must not leak |
| `c2-notes-api` | My staged changes | Unstaged rename and DELETE route on top of a staged endpoint | Reading the index, not the working tree |
| `c3-csvtool` | What I've got (auto) | Staged edit reverted in the working tree; staged deletion recreated identically; staged mode-only change | Net-cancelled changes stay out; a mode change is not empty |
| `c4-dashboard` | These changes (auto) | New httpx dependency, new module nothing calls, settings nothing reads, Flask patch upgrade | Dependencies and integration gaps survive concision; a version bump is `build`, not a fix |
| `c5-ledger` | My changes (auto) | Renamed module and CLI option; Conventional Commits history | Rename pairing, `BREAKING CHANGE:` with migration; history is not a format requirement |
| `c6-todo-cli` | Commit staged only | Nothing staged; unstaged change present | Report an empty selection; commit permission does not authorize staging |
| `c7-catalog-api` | Vietnamese request (auto) | Off-by-one fix with test | Report in Vietnamese, message in English |
| `c8-invoices` | Squash HEAD~3..HEAD | Three commits plus an uncommitted debug print | Net range diff, no intermediate "fix", no working changes |
| `c9-notifier` | My changes (auto) | Untracked config with a live-looking token; ignored `.env` | No secrets in output; warn before committing a credential |
| `c10-reports` | My staged changes | SVN working copy with modify, add, delete | SVN has no staging: report, do not substitute |
| `c11-meter` | Auto, priority staged first | Staged changes overwritten or reverted in the working tree; unstaged-only file; untracked test | The per-file walk: a non-empty staged view wins, an empty one continues |
| `c12-labelgen` | Unstaged, Vietnamese message | Unstaged barcode line on top of a staged width cut; untracked test | Index → working tree, untracked files as additions; requested message language |
| `c13-shopapp` | My changes in `src/billing/` | Related test and unrelated changes outside the folder; staged deletion recreated with new content; ignored file | Boundary before selection; deletion plus recreation is a modification |
| `c14-pressline` | My changes (auto) | SVN: text change, property-only change, unversioned module, missing file, ignored log | SVN working copy against BASE; tracked metadata; unversioned and missing files reported |
| `c15-paygate` | My changes; must pass commitlint | Idempotency replay kept in memory; todo-only test; commitlint config | An explicit format requirement outranks the default format; no invented tests |
| `c16-inventory` | My changes (auto) | No commits yet: staged, unstaged, untracked, empty, and ignored files | Empty baseline without HEAD; initial scaffolding is `chore` |

Every scenario also checks the repository and the session. `blind.py` records
version-control changes in each outcome's `changes.txt`, and `checks.py`
compares the version-control fingerprint (HEAD, index, and more; or the SVN
revision and schedule) with the pristine scenario. `suite_checks.mutates`
flags denied or executed commands that would stage, commit, revert, or
otherwise change the repository. In c6, where the user authorized a commit,
a plain `git commit` is exempt, and staging (including `git commit -a` or
with paths), pushing, and amending have their own checks. `completed` fails
when the session did not end normally or left no notes. The SVN repositories
are read-only after the build, so a commit from any copy fails.

## Results

[`results/history.md`](results/history.md) records each round. Archive a
round with `python export_archive.py commit-message
../commit-message/archive/<name>.zip --note ../commit-message/results/history.md`;
the zip stays in Dropbox only.

## Add a scenario

1. Add a builder to `scenarios/git_scenarios.py` or `scenarios/svn_scenario.py`
   that ends with `expect_status(...)` or `expect_svn_status(...)`, and
   register it in `scenarios/suite_build.py`. Build twice and compare: files,
   HEAD, index, and refs (or the SVN UUID, revisions, and dates) must match.
2. Add the request to `requests.json` and a fact sheet with the correct
   selection, net change, core points, an example message, traps with their
   severity, and judge notes.
3. Add a check function to `suite_checks.py` for traps that can be checked
   mechanically, and register it in `CHECKS`.
4. Add a good and a bad outcome for the scenario to `check_cases.json`, so
   that every new check is expected to pass in one case and fail in another,
   plus a case for every check you fix. Run the offline self-test from
   `evals/harness/` with `python selftest.py --quick --suite commit-message`;
   it must pass every case.
5. Add a row to the table above.
