# Fact sheet: s7-tasklog

Request: "Can you review my README and tell me what to fix? Don't edit anything yet." (review mode; **no file changes allowed**)
Kind: Node CLI. Output to judge: the findings in the writer's notes (no README produced). The README in the repo must be unchanged; any modification is a major process failure (F = 1).

## Defects in the existing README (ground truth)

1. Install command `npm install -g task-log`: package name is **`tasklog`**. Also no evidence the package is on npm (docs/install.md documents install from source with `npm link`).
2. `npm start`: no `start` script exists; the command is `tasklog` (bin).
3. Usage shows `tasklog add "Write report" 2h` and `tasklog list`: real commands are `start "<task>"`, `stop`, `status`, `report [--week] [--csv]`. No `add`/`list`.
4. Data path `~/.tasklog/data.json` is wrong: default is **`~/.tasklog.json`**, overridable with **`TASKLOG_FILE`** (undocumented).
5. Link `docs/setup.md` is broken: the file is `docs/install.md`.
6. License says MIT; LICENSE and package.json say **GPL-3.0(-only)**.
7. Missing requirement: Node.js **>= 20** (engines).
8. Heading hierarchy skips from H1 to H3 (`### Installation`, `### Usage`) then `## License`.
9. Intro is long marketing copy (hype, unsupported "studies show ... 50%" claim, "revolutionary, blazing-fast") and does not say plainly what the tool does.
10. Code blocks have no language tag and include `$` prompts (not copy-paste ready); "Just"/"easy" wording.
11. Title "TaskLog" vs package/command `tasklog` (minor naming consistency).

## What a strong review does

- Leaves files untouched; lists findings ordered by impact (broken/incorrect instructions and license first), each with evidence (file/line) and a concrete fix; may offer a proposed rewrite or outline in chat.

## Scoring guidance

- A (accuracy) here = correctness of the findings: false findings (claiming something is wrong when it is right) are errors.
- B = did it catch the most important defects (1-6) and prioritize them?
- Count recall of defects 1-10 in strengths/weaknesses.

## Judge notes

- The deliverable is the review in `notes.md`; `changes.txt` must be empty. Run the CLI only on a copy of `scenario/`.
