# Skill evaluations

Blind A/B suites that show whether a change to a skill makes agents do the job
better, measured on realistic scenarios instead of by reading the instructions.
Run the skill's suite before you ship any behavior change.

| Suite | Skill | Scenarios | Measures |
| --- | --- | --- | --- |
| [readme-md](readme-md/README.md) | [`readme-md`](../skills/readme-md/SKILL.md) | 12 projects, folders, and material collections | Accuracy, core highlighting, concision, presentation, friendliness, usefulness |
| [commit-message](commit-message/README.md) | [`commit-message`](../skills/commit-message/SKILL.md) | 16 Git and SVN repositories | Accuracy, change selection, classification, concision, format, communication |

## How a round works

1. **Build** deterministic scenario repositories with known traps.
2. **Snapshot** the skill versions to compare: usually the committed version
   (`--ref HEAD`) and your working-tree edit.
3. **Run** each scenario once per arm with headless Claude Code (`claude -p`)
   in an isolated session: no CLAUDE.md or AGENTS.md, no installed skills,
   plugins, hooks, or MCP servers, no saved session, only the file and Bash
   tools, and no commit attribution. File tools and shell reads are confined
   to the run folder (and the skill snapshot); interpreter commands are not,
   so tool calls that reach other runs, mappings, or snapshots are flagged
   afterwards. The `none` arm runs without the skill.
4. **Blind** the outcomes as X, Y, Z, balancing labels and their order across
   scenarios, scrubbing run paths, and recording version-control changes and
   denied repository mutations. Labels stay fixed once assigned.
5. **Judge** each scenario with a separate, equally isolated headless model
   whose sandbox holds only the rubric, the fact sheet, the pristine scenario,
   and the blinded outcomes. Invalid verdicts are rejected and retried, and
   reruns skip scenarios already judged on the same inputs.
6. **Collect** per-arm scores, paired differences, and the round's token use
   and cost, and **check** known traps mechanically.

Every session records its status, tokens, cost, CLI version, and tool calls,
so a round's spend and any contamination can be audited afterwards.

## Run a suite

From `harness/`, with the suite name first. Start with the offline self-test;
it spends no model usage:

```bash
python selftest.py
```

Then a round (`r1` here; iteration names use letters, digits, `_`, and `.`):

```bash
python build_scenarios.py commit-message
python snapshot_skill.py commit-message base --ref HEAD
python snapshot_skill.py commit-message cand
python prep_runs.py commit-message r1 A B C
python run_arms.py commit-message r1 A=none B=base C=cand --jobs 8
python blind.py commit-message r1 A B C
python judge.py commit-message r1 --jobs 8
python collect.py commit-message r1
python checks.py commit-message r1
```

`run_arms.py` prints a cost estimate from earlier rounds before it starts.
Rerunning the same command resumes the round; runs that failed for reasons
outside the writer (API or usage-limit errors, timeouts, Ctrl+C) are listed,
with the exact command to rerun them with `--retry-failed`. The round keeps
one model, turn limit, effort, and skill snapshot per arm
(`runs/<iter>/round.json`), and `blind.py` refuses scenarios with failed
runs, so both arms of a scenario are always judged together. Effort follows
the CLI default unless you pass `--effort`; the CLI version is recorded.

Pool two or more rounds and decide from the paired differences:

```bash
python aggregate.py commit-message r1:A=none,B=base,C=cand r2:A=none,B=base,C=cand --pair base,cand
```

The paired section compares two versions only where the same judge scored
both in the same scenario. A 95% interval that excludes 0 is evidence of a
change; otherwise the result is inconclusive, and you decide from the
dimension the edit targets, probes, and checks. One outcome's score varies by
about ±0.3 (SD) for the same scenario and version (measured on readme-md;
commit-message noise is not yet measured), so the 95% half-width of a paired
difference is about 0.9/√n for n judged scenarios: about ±0.26 for one
readme-md round (12 scenarios), ±0.22 for one commit-message round (16), and
±0.15-0.18 for two. Compare only rounds with the same scenario set and
harness version.

Writer and judge noise are not yet separated. To measure judge noise once per
suite (about one judge pass of cost), re-judge a finished round under a new
name, `python judge.py <suite> r1 --out r1-rj`, and compare the per-outcome
scores that `collect.py <suite> r1` and `collect.py <suite> r1 --judgments r1-rj`
print; the judge's own SD is the SD of those differences divided by √2.

Each suite's README lists its scenarios, traps, and recorded results.

## Token use and cost

```bash
python usage.py commit-message            # every round, by role and arm, plus the trigger test
python usage.py commit-message r1 --markdown
python usage.py commit-message --estimate # median and p90 cost per session, by role and model
python usage.py --all                     # every suite, with a grand total
```

Each writer, judge, and trigger session writes a record to
`<work>/<suite>/usage/`, retries and failures included, with input,
cache-write, cache-read, and output tokens per model and the cost Claude Code
reports. `collect.py` prints the round's table too. Costs are API list-price
equivalents: an API-key user is billed about that amount, while a subscription
counts the usage against the plan's five-hour and weekly limits, whose last
reported use the report shows. Rounds before harness v2 recorded writer costs
only; their tokens and judge costs show as `?` or `unrecorded`.

Measured under harness v2, per session at list prices: Sonnet writers
$0.01-0.06 (commit-message) and $0.02-0.13 (readme-md), Opus pairwise judges
$0.13-0.20 and $0.13-0.31, and trigger queries $0.05-0.14. One two-arm round
of both suites with their trigger tests cost $11.30 (commit-message $4.86,
readme-md $6.44). Opus writers cost $0.21-0.88 under harness v1. Quote the
`--estimate` figures for writers and judges, then ask for approval before a
round.

## Requirements

- Python 3.10 or newer (standard library only) and Git; SVN command-line tools
  for the commit-message SVN scenarios.
- The Claude Code CLI, signed in, so `claude -p` works. Set `CLAUDE_BIN` if the
  harness cannot find it.
- Runs spend model usage. Get approval before starting a round.

Generated material goes to `$LISA_EVAL_WORK/<suite>` (default
`<system temp>/lisa-evals/<suite>`), never into this repository or any other
checkout. Archive a finished round from `harness/` with
`python export_archive.py <suite> ../<suite>/archive/<name>.zip --note ../<suite>/results/history.md`;
Git ignores `archive/`, so the zip lives in Dropbox only.

## Harness scripts

| Script | Purpose |
| --- | --- |
| `build_scenarios.py` | Build a suite's scenarios and verify their intended state |
| `snapshot_skill.py` | Freeze a skill version from the working tree or a Git ref, with its content hash |
| `prep_runs.py` | Copy scenarios into one folder per run and fingerprint them |
| `run_arms.py` | Run writers in isolated headless sessions; resume and retry failed runs |
| `blind.py` | Rotate outcomes into labels, scrub identifying paths, and flag leaks |
| `judge.py` | Run isolated judges, validate verdicts, or print prompts for subagent judges |
| `collect.py` | Unblind one round and summarize scores, paired differences, and usage |
| `aggregate.py` | Pool rounds by skill version and compare versions head to head |
| `checks.py` | Run the suite's mechanical checks |
| `usage.py` | Report token use and cost per round and in total |
| `trigger_test.py` | Check that the skill's description loads it at the right times |
| `export_archive.py` | Zip a suite's work directory, slimmed for storage |
| `selftest.py` | Test the harness and every suite's checks offline with a fake CLI |

`evalenv.py`, `session.py`, `stats.py`, and `fixture.py` hold the shared code.

## Add a suite

1. Create `evals/<skill>/` with `suite.json` (skill name, rubric weights,
   extra read-only Bash commands), `rubric.md`, `requests.json`, `facts/`,
   `trigger.json`, `suite_checks.py`, `check_cases.json`, and
   `scenarios/suite_build.py` exposing `build_all(base, ref)`.
2. Write the rubric and fact sheets before the first run, and keep them fixed
   while you compare versions.
3. Seed `check_cases.json` with a good and a bad outcome per scenario, and run
   `selftest.py`.
4. Document scenarios and results in the suite's `README.md` and
   `results/history.md`.

## Gotchas

- **Never run writer arms as subagents inside this repository.** They inherit
  `AGENTS.md` and `CLAUDE.md`, which inflate the no-skill baseline. Subagent
  judging (`judge.py --print-prompts`) is not blind-equivalent either; use it
  only from a neutral folder, and say so in the history.
- **Harness version boundary:** v2 (2026-10-02) changed session isolation,
  prompts, label rotation, and several scenarios. Do not pool v2 rounds with
  earlier ones; every record carries its `harness` version.
- **Permissions:** writers may read, inspect version control, and run local
  interpreters. Other commands are denied and listed in each run's
  `meta.json`; interpreters and the write forms of some allowed commands
  (`git tag`, `git branch`, `git remote`, `find -delete`, `sort -o`) could
  still write or reach the network, so the
  harness detects repository changes after the run (HEAD, branches, tags,
  index, stash, config, hooks; SVN schedule and repository head) instead of
  preventing them. Git network transports are blocked.
- **Trigger tests** cannot use safe mode, because the skill must load: the
  other skills installed on your machine compete with it, so results can
  differ between machines. The test stops if another skill with the same name
  is installed.
- **Windows:** the harness calls the `claude.exe` behind npm's `claude.cmd`
  shim, kills a timed-out session's whole process tree, and passes
  `safe.directory=*` and `core.autocrlf=false` to Git through the environment
  for work folders on drives without ownership records, leaving your Git
  config alone.
