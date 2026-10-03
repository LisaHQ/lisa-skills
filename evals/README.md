# Skill evaluations

Blind A/B suites that show whether a change to a skill makes agents do the job
better, measured on realistic scenarios instead of by reading the instructions.
Run the skill's suite before you ship any behavior change.

| Suite | Skill | Scenarios | Measures |
| --- | --- | --- | --- |
| [readme-md](readme-md/README.md) | [`readme-md`](../skills/readme-md/SKILL.md) | 9 projects, folders, and material collections | Accuracy, core highlighting, concision, presentation, friendliness, usefulness |
| [commit-message](commit-message/README.md) | [`commit-message`](../skills/commit-message/SKILL.md) | 10 Git and SVN repositories | Accuracy, change selection, classification, concision, format, communication |

## How a round works

1. **Build** deterministic scenario repositories with known traps.
2. **Snapshot** the skill versions to compare: usually the committed version
   (`--ref HEAD`) and your working-tree edit.
3. **Run** each scenario once per arm with headless Claude Code (`claude -p`)
   from a neutral folder, so this repository's `AGENTS.md` cannot leak in.
   The `none` arm runs without the skill.
4. **Blind** the outcomes as X, Y, Z, scrubbing run paths that would reveal
   the arm, and record version-control changes the writer made.
5. **Judge** each scenario with a separate headless model that sees only the
   rubric, the fact sheet, the pristine scenario, and the blinded outcomes.
6. **Collect** per-arm scores, and **check** known traps mechanically.

## Run a suite

From `harness/`, with the suite name first:

```bash
python build_scenarios.py commit-message
python snapshot_skill.py commit-message base --ref HEAD
python snapshot_skill.py commit-message cand
python prep_runs.py commit-message r1 A B C
python run_arms.py commit-message r1 A=none B=base C=cand --jobs 9
python blind.py commit-message r1 A B C
python judge.py commit-message r1 --jobs 9
python collect.py commit-message r1
python checks.py commit-message r1
```

Pool two or more rounds before you decide; single runs vary by about ±0.3:

```bash
python aggregate.py commit-message r1:A=none,B=base,C=cand r2:A=none,B=base,C=cand
```

Each suite's README lists its scenarios, traps, and recorded results.

## Requirements

- Python 3.10 or newer (standard library only) and Git; SVN command-line tools
  for the commit-message SVN scenario.
- The Claude Code CLI, signed in, so `claude -p` works. Set `CLAUDE_BIN` if the
  harness cannot find it.
- Runs spend model usage: one Sonnet writer run costs about $0.10–0.30, one
  Opus judge about $0.30–1. Get approval before starting a round.

Generated material goes to `$LISA_EVAL_WORK/<suite>` (default
`<system temp>/lisa-evals/<suite>`), never into this repository. Archive a
finished round with `export_archive.py <suite> <suite>/archive/<name>.zip
--note <suite>/results/history.md`; Git ignores `archive/`, so the zip lives
in Dropbox only.

## Harness scripts

| Script | Purpose |
| --- | --- |
| `build_scenarios.py` | Build a suite's scenarios and verify their intended state |
| `snapshot_skill.py` | Freeze a skill version from the working tree or a Git ref |
| `prep_runs.py` | Copy scenarios into one folder per run |
| `run_arms.py` | Run writers headlessly, recording notes, cost, and denied tool calls |
| `blind.py` | Shuffle outcomes into labels and scrub identifying paths |
| `judge.py` | Run sandboxed judges, or print prompts for subagent judges |
| `collect.py` | Unblind one round and summarize it |
| `aggregate.py` | Pool rounds by skill version with standard errors |
| `checks.py` | Run the suite's mechanical checks |
| `trigger_test.py` | Check that the skill's description loads it at the right times |
| `export_archive.py` | Zip a suite's work directory, slimmed for storage |

## Add a suite

1. Create `evals/<skill>/` with `suite.json` (skill name, rubric weights,
   extra read-only Bash commands), `rubric.md`, `requests.json`, `facts/`,
   `trigger.json`, `suite_checks.py`, and `scenarios/suite_build.py`
   exposing `build_all(base, ref)`.
2. Write the rubric and fact sheets before the first run, and keep them fixed
   while you compare versions.
3. Document scenarios and results in the suite's `README.md` and
   `results/history.md`.

## Gotchas

- **Never run writer arms as subagents inside this repository.** They inherit
  `AGENTS.md` and `CLAUDE.md`, which inflate the no-skill baseline.
- **Headless permissions:** writers may read, inspect version control, and run
  local interpreters; installs, network, and repository mutations stay denied
  and show up in each run's `meta.json`.
- **Windows:** the harness calls the `claude.exe` behind npm's `claude.cmd`
  shim, and passes `safe.directory=*` to Git through the environment for work
  folders on drives without ownership records, leaving your Git config alone.
