<div align="center">

# lisa-skills

**Reusable AI agent skills for everyday workflows.**<br>
Built for personal use, shared with the community.

[![License: MIT](https://img.shields.io/badge/license-MIT-2ea44f?style=flat-square)](LICENSE)
[![Format: Agent Skills](https://img.shields.io/badge/format-Agent%20Skills-6e40c9?style=flat-square)](https://agentskills.io)
[![Install with npx skills](https://img.shields.io/badge/install-npx%20skills%20add-cb3837?style=flat-square&logo=npm&logoColor=white)](#quick-start)
[![Last commit](https://img.shields.io/github/last-commit/LisaHQ/lisa-skills?style=flat-square&color=0969da)](https://github.com/LisaHQ/lisa-skills/commits/main)

[Quick start](#quick-start) ·
[Skill catalog](#skill-catalog) ·
[Usage](#usage) ·
[Create a skill](#create-a-skill) ·
[Contributing](#contributing)

</div>

**lisa-skills** is a curated collection of skills that teach AI agents to handle
everyday tasks consistently. Each skill is a small folder of readable Markdown
instructions: install it once, and your agent applies it whenever a task calls
for it — no copy-pasting prompts.

Skills follow the open [Agent Skills](https://agentskills.io) format, supported
by Claude Code, Codex, Cursor, GitHub Copilot, Gemini CLI, OpenCode, and many
other agents.

## Highlights

- 🎯 **Focused** — Each skill does one job, with clear inputs, outputs, and
  success criteria.
- 🔍 **Grounded** — Skills work from evidence in your project, not assumptions.
- 🧩 **Portable** — No hard-coded names, brands, or paths; skills adapt to any
  project.
- 🪶 **Lightweight** — Plain Markdown you can review before installing, loaded
  only when a task needs it.

## Skill catalog

| Skill | What it does |
| --- | --- |
| 📝 [**commit-message**](skills/commit-message/SKILL.md) | Writes accurate, concise commit messages from your actual Git or SVN changes. |

> [!TIP]
> Run `npx skills add LisaHQ/lisa-skills --list` to see the current catalog
> from your terminal without installing anything.

## Quick start

You need [Node.js](https://nodejs.org) (current LTS recommended) to run the
[`skills`](https://github.com/vercel-labs/skills) CLI through `npx`. No
Node.js? See [Manual installation](#manual-installation).

**1. Install the skills**

```bash
npx skills add LisaHQ/lisa-skills
```

The CLI detects the agents on your machine and guides you through the remaining
choices.

**2. Ask your agent**

Start a new session and describe the task in plain language — for example,
*"Write a commit message for my changes."* Your agent loads the matching skill
automatically.

**3. Stay up to date**

```bash
npx skills update
```

### Common commands

| Task | Command |
| --- | --- |
| Preview skills without installing | `npx skills add LisaHQ/lisa-skills --list` |
| Install a specific skill | `npx skills add LisaHQ/lisa-skills --skill commit-message` |
| Install for all your projects | `npx skills add LisaHQ/lisa-skills --global` |
| Install for specific agents | `npx skills add LisaHQ/lisa-skills --agent claude-code codex` |
| List installed skills | `npx skills list` |
| Update installed skills | `npx skills update` |
| Remove a skill | `npx skills remove commit-message` |

> [!NOTE]
> By default, skills install into the current project (for example,
> `.claude/skills/` for Claude Code), so you can commit them and share them
> with your team. Add `--global` to install them in your user directory (for
> example, `~/.claude/skills/`) and use them in every project.

### Manual installation

Every skill is just a folder, so you can also copy it into your agent's skills
directory by hand. For Claude Code:

```bash
git clone https://github.com/LisaHQ/lisa-skills.git
mkdir -p ~/.claude/skills
cp -r lisa-skills/skills/commit-message ~/.claude/skills/
```

To limit a skill to one project, copy it into that project's `.claude/skills/`
folder instead. Other agents read skills from their own folders — see your
agent's documentation or the
[skills CLI's list of supported agents](https://github.com/vercel-labs/skills#supported-agents).

## Usage

Skills work in the background, so there are no commands to memorize.

- **Just ask.** Describe what you need. Your agent compares the request with
  each skill's description and loads the right one.
- **Call a skill by name.** Many agents also let you invoke a skill directly —
  in Claude Code, type `/<skill-name>` (e.g., `/commit-message`).
- **Fine-tune with options.** Add details in plain language, such as
  *"only my staged changes"*, or pass arguments like
  `/commit-message scope=staged`.

For example, with the `commit-message` skill:

> **You:** Write a commit message for my staged changes.
>
> **Agent:** Scope: staged (HEAD → index) — 3 files selected.
>
> ```text
> Support per-job retry limits
>
> - feat(retries): Allow each job to override its retry limit.
>   + Treat zero as an explicit request to disable retries.
>   + Preserve the configured default when no override is provided.
> ```

The skill only drafts the message. It never stages, commits, or pushes without
your permission.

## How skills work

A skill is a folder containing a `SKILL.md` file: a short YAML header with a
`name` and `description`, followed by step-by-step instructions for the agent.

1. **Discover** — At startup, the agent reads only each skill's name and
   description.
2. **Activate** — When a request matches a description, the agent loads that
   skill's full instructions.
3. **Execute** — The agent follows the workflow, opening bundled references or
   scripts only when needed.

Because full instructions load on demand, you can keep many skills installed
with very little overhead. Learn more at [agentskills.io](https://agentskills.io).

## Repository structure

```text
lisa-skills/
├── skills/
│   └── <skill-name>/
│       ├── SKILL.md       # Required: metadata and instructions
│       ├── references/    # Optional: detailed docs, loaded on demand
│       ├── scripts/       # Optional: helper scripts
│       └── assets/        # Optional: templates and other resources
├── AGENTS.md              # Conventions for AI agents working on this repo
├── CLAUDE.md              # Claude Code–specific additions
├── LICENSE
└── README.md
```

## Create a skill

1. Scaffold a new skill from the `skills/` folder:

   ```bash
   cd skills
   npx skills init my-skill
   ```

2. Edit `skills/my-skill/SKILL.md`:
   - **`name`** — Match the folder name, using lowercase letters, numbers, and
     hyphens only.
   - **`description`** — Say what the skill does *and when to use it*. Agents
     rely on this text to decide when to load the skill.
   - **Instructions** — Keep the skill to one purpose, with clear inputs,
     outputs, and success criteria.
3. From the repository root, confirm that the skill is discovered:

   ```bash
   npx skills add . --list
   ```

4. Test it with realistic requests, including incomplete, out-of-scope, and
   failure cases — not just the happy path.
5. Add the skill to the [skill catalog](#skill-catalog) with a one-line
   description.

See [AGENTS.md](AGENTS.md) for the complete authoring and verification
conventions, and the
[Agent Skills specification](https://agentskills.io/specification) for the
full format.

## Contributing

Ideas, bug reports, and improvements are welcome.

- **Report a problem or suggest a skill** —
  [Open an issue](https://github.com/LisaHQ/lisa-skills/issues).
- **Propose a change** — Fork the repository, follow [AGENTS.md](AGENTS.md),
  and open a pull request that explains what changed and how you tested it.

Please keep personal data, credentials, and confidential material out of
skills, examples, and logs.

## License

Released under the [MIT License](LICENSE). Copyright © 2026 LisaHQ.

---

<div align="center">
<sub>Made with care by <a href="https://github.com/LisaHQ">LisaHQ</a>. If a skill saves you time, consider giving the repo a ⭐.</sub>
</div>
