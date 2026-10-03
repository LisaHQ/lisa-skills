# Fact sheet: s8-lisa-skills (real repository)

Request: "Polish the README of this repository - make it as clear and inviting as possible without losing anything important." (improve mode; the existing README is already strong)
Kind: repository of AI agent skills (Agent Skills format). Readers: people who want to install and use the skills; contributors.

## Ground truth

- Existing README (223 lines) is accurate and well structured: centered header with badges (MIT, Agent Skills format, npx skills install, last commit), nav links, intro, Highlights, Skill catalog (only `commit-message`), Quick start (Node.js LTS; `npx skills add LisaHQ/lisa-skills`; `npx skills update`), Common commands table (`--list`, `--skill commit-message`, `--global`, `--agent claude-code codex`, `npx skills list`, `npx skills update`, `npx skills remove commit-message`), Manual installation (git clone + cp to `~/.claude/skills/`), Usage (just ask; `/commit-message`; `scope=staged` example with sample output), How skills work, Repository structure, Create a skill (`npx skills init my-skill`, `npx skills add . --list`), Contributing, License (MIT, Copyright © 2026 LisaHQ), footer.
- Facts to preserve exactly: the commands above; MIT license; catalog content; links to AGENTS.md, LICENSE, agentskills.io, vercel-labs/skills; supported-agent list in the intro (Claude Code, Codex, Cursor, GitHub Copilot, Gemini CLI, OpenCode).
- Only one skill exists: `skills/commit-message/SKILL.md`. The commit-message skill drafts messages and never stages/commits/pushes without permission (true per SKILL.md).

## What a strong result does

- Makes targeted improvements (e.g., tighter wording, clearer first screen, fixes any real inconsistency) and keeps structure, voice, facts, and anchors. Minimal churn is a virtue here; a near-identical README with a few real improvements can win.
- Reports what changed and why.

## Traps (judge explicitly)

- Breaking or changing any command/flag, link, or the license -> major.
- Dropping valuable sections (manual install, common commands, create a skill, contributing) -> major (F).
- Inventing skills, star counts, agent support claims, or features not in the repo -> major.
- Changing anchors that the nav links use without updating them -> minor (major if links break).
- Large rewrites that add length or hype without improving clarity -> C/E penalty.

## Judge notes

- Compare each outcome with the original README line by line (for example `git diff --no-index --word-diff`), ignoring pure line-ending differences. Classify each change as a real improvement, neutral churn, or a loss, and check that the outcome delivers the requested polish. An outcome that changed nothing is judged as the original README plus its notes.
- The original Usage example (nested `+` sub-bullets, no "Commit description:" label) is out of date relative to `skills/commit-message/SKILL.md`, which shows the same change as one merged bullet and requires the label.
- The clone contains this repository's `CLAUDE.md` and `AGENTS.md` as of `668ba4f`. Writers run in safe mode (harness v2) and do not load them as instructions, though they may read them as evidence. A trailing commit message in the notes is neutral: neither a strength nor an error.
