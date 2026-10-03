# lisa-skills

`LisaHQ/lisa-skills` provides reusable AI agent skills for personal use and
community sharing. These instructions govern repository work; each skill owns
its task workflow.

## Operating Contract

- Communicate in the requester's language.
- Use English for canonical documentation, code, comments, public APIs,
  identifiers, file names, commit messages, and command examples unless the
  project explicitly requires otherwise.
- For other outputs, follow the explicitly requested language; otherwise
  follow the applicable skill's output contract.
- Keep existing matching `.<lang>.md` translations aligned when editing. Use
  canonical instructions as the source of truth; consult translations when
  editing or checking them.
- Be direct, practical, architecture-aware, and shop-floor aware. Never
  over-explain obvious details.
- Explain tradeoffs only when they materially affect correctness, reliability,
  maintainability, production accuracy, recoverability, or user intent.
- Before editing, read the task and relevant README guidance; inspect the
  current branch, relevant files, and existing changes. Use actual repository
  state.
- Select relevant skills by their current descriptions and read their full
  instructions before use.
- Stay within the requested scope and preserve unrelated work.
- Explicit user requirements may revise repository conventions. Flag material
  conflicts; update shared guidance for permanent changes to shared conventions.
- State a concise plan before large, destructive, security-sensitive, or
  non-trivial changes.
- Ask questions only when a missing decision or required authorization blocks
  correct or safe progress. Otherwise make the safest minimal assumption and
  proceed.
- NEVER claim a command, build, test, deployment, migration, or validation
  succeeded unless it was actually executed and completed successfully.

## Authorization and data

Reuse existing authorization within its approved scope.

- Leave changes uncommitted by default. Stage, commit, amend, rewrite history,
  push, publish, change repository visibility, or change real project/global
  skill installations only when explicitly authorized for that action.
- Use the existing sign-in and billing setup. Obtain explicit authorization
  before enabling overage, attaching API billing, buying credits, changing
  model/speed/effort, or starting parallel agents.
- Use synthetic examples and `example.invalid` for example email addresses.
  Exclude personal data, customer-confidential material, credentials, and
  sensitive output from tracked artifacts and logs. Never request credentials
  through chat.

## Skill authoring

- Store skills at `skills/<skill-name>/SKILL.md` with valid YAML frontmatter:
  `name` matches the directory; `description` states the purpose and triggers.
  Track revisions through Git.
- Give each skill one purpose with explicit inputs, outputs, and success
  criteria. Split materially different workflows; consolidate equivalent requests.
- Write actionable rules with one main requirement per bullet; number ordered
  steps. Remove duplication; retain evidence requirements and meaningful edge cases.
- Keep core workflow and output rules in `SKILL.md`. Add `references/`,
  `scripts/`, and `assets/` only as needed; link resources relative to the
  skill directory.
- Keep task rules in each skill and the catalog in README. Adding a skill
  alone requires no update to shared guidance.
- Use inputs or labeled examples for customer identity, branding, and
  project-specific paths; keep reusable behavior independent of them.
- Optional `agents/` configuration, such as `agents/openai.yaml`, must follow
  the target client's documented schema and align with the skill's metadata,
  invocation policy, and tool dependencies. Claim only tested compatibility.
- Keep repository instructions out of skill installation requirements for
  consumer projects.

## Verification

- Validate affected Markdown/YAML, required fields, unique skill names, local
  references, examples, translations, and optional client configuration using
  existing checks. Do not assume tools or validation commands exist.
- When layout or discovery changes, run `npx skills add . --list` from the
  repository root if the CLI is available. Use isolated temporary locations
  for installation tests.
- When skill behavior changes, exercise representative valid, incomplete,
  out-of-scope, and failure cases. Syntax and discovery checks alone do not
  validate behavior.
- When `evals/<skill-name>/` exists, compare the skill before and after a
  change with that suite, following `evals/README.md`. Its runs spend model
  usage, so get authorization before starting them. Keep generated work and
  archives out of Git.
- When scripts or tooling change, run relevant checks and fix failures
  introduced by the change.

## Delivery

- Briefly report changed files, purpose, verification commands/results, and
  limits. Distinguish executed checks, manual review, results reported by
  others, and blocked or unrun checks. Claim independent review only when a
  separate reviewer performed it.
- If work remains, give one concrete next action. For an interruption, use an
  existing handoff convention or a brief continuation note. Provide additional
  deliverables only when required by the task.
- If the task leaves file changes to commit, end the final response with a
  ready-to-use commit message for the selected change set. Follow the repository
  format and applicable skill; if neither is available, use a summary and
  factual bullets. Put all explanations, scope notes, verification results,
  and next actions before the commit message.
