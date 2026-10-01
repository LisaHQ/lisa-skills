---
name: commit-message
description: >-
  Write accurate, concise commit descriptions for Git or SVN projects.
  Use after file changes or when asked for a commit message. Select the
  change scope automatically unless specified, preferring staged changes
  when present. Report scope separately from the message. Use a plain
  summary and typed bullets in a fixed order. Never commit unless
  explicitly authorized.
---

# Commit Message

Describe what the selected changes accomplish. Preserve enough context for
a future reader to understand their purpose and consequences without access
to the conversation.

## Select the change scope

Read `scope` from the user's request or skill invocation arguments.
Accept equivalent, unambiguous natural-language instructions.

Default to `scope=auto` when no scope is specified.

For Git working changes, support:

| Option | Comparison | Include |
| --- | --- | --- |
| `scope=auto` | Resolve using the rules below | The automatically selected scope |
| `scope=staged` | HEAD → index | Staged changes only |
| `scope=unstaged` | Index → working tree | Unstaged changes and untracked files within the requested boundary |
| `scope=working-tree` | HEAD → working tree | Final combined changes and untracked files within the requested boundary |

Treat this option as a snapshot selector, distinct from the optional
component scope in a bullet such as `fix(parser):`.

Apply any explicit repository, file, or task boundary before resolving
`auto`. Changes outside that boundary must not affect automatic selection.
Without an explicit narrower boundary, inspect the selected repository.

Resolve `scope=auto` as follows:

| Changes detected within the boundary | Resolved scope |
| --- | --- |
| Staged changes only | `staged` |
| Unstaged changes or untracked files only | `unstaged` |
| Both staged and unstaged changes or untracked files | `staged` |
| No changes | No scope to summarize; report that no changes were found |

For automatic selection, treat eligible untracked files as part of the
unstaged side. Do not count ignored or excluded files unless explicitly
included in the requested boundary.

- Honor an explicitly selected `staged`, `unstaged`, or `working-tree` scope
  without applying automatic selection.
- Never switch an explicit scope merely because it is empty.
- When both staged and unstaged changes exist, `auto` selects `staged`,
  not `working-tree`.
- Honor an explicitly selected commit, revision range, or supplied diff
  instead of applying automatic working-change selection.
- Do not silently combine incompatible selections. Request clarification
  only when a material ambiguity cannot be resolved from the request.
- For Git repositories without HEAD, use an empty baseline where appropriate.
  Do not create a commit to establish a baseline.

Inspect repository status before composing the message. Determine whether
staged changes, unstaged changes, and untracked files are present, including
whether the same files have both staged and unstaged edits.

Summarize the net difference between the selected baseline and target.
Do not list intermediate edits that cancel out within that comparison.

Read changed files and necessary supporting context from the selected target
snapshot. Do not use unstaged file contents to justify claims about staged
changes.

For SVN:

- Resolve `scope=auto` to working-copy changes against BASE.
- Accept `scope=working-tree` for that same comparison.
- Report that SVN has no staging area.
- If `staged` or `unstaged` is explicitly requested, explain that the option
  is unavailable for SVN instead of silently substituting another scope.

## Report the scope separately

Before the commit description, provide a brief scope report in the
conversation's language. Keep it outside the commit-message code block.

State:

- The requested scope, including whether `auto` was the default.
- The resolved scope and the reason for automatic selection, if applicable.
- The baseline and target being compared.
- Any requested file or task boundary.
- Material changes excluded by the selection.

Whenever both staged and unstaged changes exist within the boundary:

- Explicitly report that both were detected.
- Mention whether any files contain both kinds of edits.
- State which scope was selected and what that selection covers.
- Identify excluded unstaged changes or untracked files when selecting staged.
- Do not imply that a staged-only message describes all working changes.

Examples of scope reporting:

- Auto, only unstaged changes: report that `auto → unstaged` was selected
  because no staged changes exist, and that the message covers index →
  working tree plus eligible untracked files.
- Auto, both states: report that `auto → staged` was selected, the message
  covers HEAD → index, and unstaged changes and untracked files are excluded.
- Explicit working-tree scope: report that `working-tree` was requested and
  the message covers the final combined difference against HEAD.
- Explicit staged scope, no staged changes: report that the selected scope
  is empty. Do not switch to unstaged or generate a commit description.

Never put scope-selection notes, mixed-state warnings, or inspection
limitations inside the commit message.

If automatic selection finds no changes, or the selected comparison is empty,
report that fact and omit the commit description. Identify available
alternative scopes when useful, without selecting them automatically.

## Required output

After file changes in a Git or SVN project, include a commit description
whenever the selected scope contains adequately evidenced changes.

Write the commit message in English unless the user requests another language.

Use this structure after the separate scope report:

Commit description:

```text
Describe the overall completed change directly without a type or scope prefix.

- type(component): Describe a material logical change.
```

- Keep `Commit description:` outside the fenced `text` block.
- Put the entire commit message inside one standalone fenced `text` block.
- Begin with exactly one plain-language, imperative summary line.
- Start directly with the change description. Never prefix the summary with
  a type, scope, issue key, label, or equivalent decoration.
- Follow the summary with one blank line and the main bullets.
- Always include at least one main bullet. Use one main bullet when there is
  only one material logical change.
- Omit the component scope when it adds no useful information.
- Omit the summary's trailing period. End bullet descriptions with a period.
- Aim for a short summary, around 50 characters when practical. Wrap body
  lines around 72 characters when helpful, without splitting identifiers,
  paths, or URLs.
- Prefer accuracy and clarity over length targets.
- Avoid unnecessary repetition, but allow limited overlap between summary
  and bullet for a simple change. Never invent detail to make them different.

Example of a simple change:

```text
Correct the installation heading

- docs: Correct "Instalation" to "Installation".
```

## Describe meaningful changes

- Describe the effect of the change, not the conversation, editing process,
  feedback cycle, or sequence of tool calls.
- Use concise, active, imperative action phrases. Express necessary factual
  context naturally.
- Avoid vague descriptions such as `Update files`, `Make improvements`,
  or `Address feedback`.
- Group edits by purpose rather than by file. Describe each material logical
  change once.
- Keep supporting code, tests, documentation, and configuration with their
  logical change unless they represent separately material changes.
- Explain non-obvious reasons, constraints, or trade-offs when needed to
  understand the decision. Do not manufacture a rationale for obvious changes.
- Ground explanations in the selected changes and reliable supporting evidence.
  Do not substitute intended behavior for demonstrated implementation.
- Read the minimum surrounding code, callers, configuration, or tests necessary
  to substantiate the claimed effect.
- Do not claim completed integration, successful tests, measured performance
  gains, deployment, or comprehensive safety guarantees without matching evidence.
- Preserve material behavior limits, compatibility breaks, migration requirements,
  and necessary user actions inside the message.
- Keep task status, routine command logs, temporary inspection limitations,
  and the assistant's next steps outside the message.
- Exclude claims about plans, abandoned edits, and changes outside the selected
  scope. Describe partial implementations honestly.
- Use identifiers and paths only when useful. Never expose secrets or private data.

## Choose main bullets or sub-bullets

Use one typed main bullet per material logical change.

Use optional sub-bullets when supporting details of the same change are easier
to understand separately:

- Begin main bullets with `- type:` or `- type(component):`.
- Begin sub-bullets with `+`, indented by two spaces.
- Allow only one nested level. Do not repeat type prefixes on sub-bullets.
- Use sub-bullets for related conditions, behavior, rationale, compatibility
  effects, or migration details.
- Promote a detail to a main bullet when it describes a separate material
  logical change.
- Do not hide unrelated changes beneath a vague parent such as
  `fix: Fix several issues.`
- Prefer a flat bullet when one concise sentence is sufficient.
- Wrap long sentences as continuation lines aligned with their bullet text;
  do not turn line wrapping into artificial sub-bullets.

Example:

```text
Support per-job retry limits

- feat(retries): Allow each job to override its retry limit.
  + Treat zero as an explicit request to disable retries.
  + Preserve the configured default when no override is provided.
```

## Classify and order main bullets

Use this fixed display order. Skip absent groups.

| Order | Type | Use for |
| --- | --- | --- |
| 1 | `fix` | Correct defects or unintended application behavior |
| 2 | `feat` | Add or extend functionality or capabilities |
| 3 | `perf` | Improve performance or resource use without intended functional changes |
| 4 | `chore` | Perform maintenance or formatting not covered by another type |
| 5 | `refactor` | Restructure internals without changing intended behavior |
| 6 | `revert` | Explicitly reverse a previous change |
| 7 | `docs` | Add or correct documentation, comments, or documentation translations |
| 8 | `test` | Add or improve tests, fixtures, or test infrastructure |
| 9 | `build` | Change build tooling, dependencies, compilation, or packaging |
| 10 | `ci` | Change continuous integration or delivery workflows |

Display order is not classification priority. Choose the most specific type
by the primary purpose of the logical change:

- Use `fix` for correcting established application defects or vulnerabilities,
  even when the implementation changes only dependencies or configuration.
- Use `build` for routine dependency upgrades and build or packaging changes.
  Do not infer a defect or vulnerability merely from a version change.
- Use `docs`, `test`, or `ci` for changes confined to those concerns.
- Use `fix` or `feat` for functional changes implemented through restructuring;
  do not label them `refactor`.
- Use `revert` for an explicit reversal, even when it remedies a defect.
- Reserve `chore` for changes that do not fit another type.

Keep same-type main bullets contiguous. Within each group, put the most
consequential change first and keep related areas together. Keep every sub-list
with its parent.

Do not add type-group headings, empty groups, or blank lines between bullets.
Let the summary emphasize the most important outcome regardless of group order.
Reuse established, meaningful component scopes where helpful.

## Check completeness and cohesion

Before output:

1. Confirm the selected baseline, target, and boundary.
2. Inspect the complete relevant diff and any selected new files. Do not omit
   intentional generated or configuration changes merely because of file type.
3. Check whether the changes form a coherent unit. If independent goals would
   benefit from separate commits, recommend that outside the code block while
   still describing the requested scope.
4. Do not recommend splitting solely because several types are present.
   A feature with supporting tests and documentation can remain cohesive.
5. Verify that every claim is supported, every material logical change is
   covered, and classification, ordering, and nesting follow these rules.

When repository access is unavailable, use supplied evidence and report what
could not be verified. Do not label a supplied diff as staged without evidence.
If no reliable change is evidenced, do not fabricate a description.

For multiple repositories, provide a separate scope report and commit description
for each repository.

## Respect compatibility and metadata

This custom format uses Conventional Commits-style bullets but is not a complete
Conventional Commits message. Do not assume compatibility with tools requiring
a typed subject.

Do not replace this format merely because historical commits or templates use
another convention. Report explicit conflicts separately and follow the
applicable instruction priority.

Append relevant, verified references or required trailers after the bullets,
separated by one blank line, inside the same code block. Use `BREAKING CHANGE:`
when appropriate to explain a compatibility break and required migration.

Never invent issue references, identities, approvals, or sign-off attestations.
Adding trailers does not make this format Conventional Commits compliant.

## Leave version control unchanged

Generating a commit description does not authorize a version-control mutation.

Leave changes uncommitted by default. Do not stage files, revert working changes,
create or modify commits, rewrite history, or push merely to prepare a message.

Perform version-control mutations only when explicitly authorized and only on
the intended change set. Permission to commit does not imply permission to amend,
rebase, or push.
