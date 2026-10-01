---
name: commit-message
description: >-
  Write accurate, concise commit descriptions for Git or SVN projects after
  file changes or when requested. Select scope automatically unless specified,
  prefer staged changes when present, and report scope separately. Use a plain
  summary and typed bullets in a fixed order. Never commit without explicit
  authorization.
---

# Commit Message

Describe what the selected changes accomplish and preserve the context needed
by future readers.

## 1. Select and report the scope

Detect Git or SVN from repository metadata, configuration, or the established
workflow. Read `scope` from the request or invocation arguments; accept
unambiguous equivalent wording. Default to `scope=auto`.

Apply any requested repository, file, or task boundary before selecting changes.
Otherwise, use the selected repository. Changes outside the boundary must not
influence automatic selection.

For Git working changes:

| Scope | Comparison | Contents |
| --- | --- | --- |
| `staged` | HEAD → index | Staged changes only |
| `unstaged` | Index → working tree | Unstaged edits plus eligible untracked files |
| `working-tree` | HEAD → working tree | Final combined changes plus eligible untracked files |

Eligible untracked files are within the requested boundary and are not ignored
or excluded unless explicitly included. They count as part of the unstaged
side for both selection and reporting.

Honor a concrete scope when explicitly requested. Otherwise, resolve `auto`:

1. If staged changes exist, select `staged`.
2. Otherwise, if unstaged edits or eligible untracked files exist, select
   `unstaged`.
3. Otherwise, report no changes and omit the commit description.

An empty selected comparison produces a report only. Never switch an explicit
scope because it is empty. Use an empty baseline where appropriate when Git
has no HEAD; do not create a commit to establish one.

Explicit commits, revision ranges, or supplied diffs take precedence over
automatic working-change selection. Do not mix incompatible selections.
Ask only when a material ambiguity cannot be resolved from available context.
The selection option is independent of component scopes such as `fix(parser):`.

For SVN, `auto` and `working-tree` select working-copy changes against BASE.
Report that SVN has no staging area; reject explicitly requested `staged` or
`unstaged` scopes without silently substituting another selection.

Before the message, give a scope report in the conversation's language,
normally in one or two sentences. State the requested scope, including whether
`auto` was the default, the resolved scope, and the reason for automatic
selection when applicable. Include the comparison, any narrower boundary,
and material exclusions.

Whenever staged changes coexist with unstaged edits or eligible untracked
files, explicitly report the detected states, the selected scope, whether
any paths overlap, and which categories are excluded. Keep this report
outside the commit message.

Example report:
> Scope: auto (default) → staged (HEAD → index), because staged changes exist.
> Both staged and unstaged edits exist, including overlapping paths; exclude
> unstaged edits and untracked files.

Use only facts actually detected. For multiple repositories, provide a
separate report and message for each.

## 2. Ground the content in evidence

- Inspect the selected diff and new files, including intentional generated
  or configuration changes. Inspect other states only as needed to resolve
  scope and report exclusions.
- Describe the net difference between the selected baseline and target;
  omit intermediate edits that cancel out in that comparison.
- Read changed files and necessary surrounding code, callers, configuration,
  or tests from the selected target snapshot. Never use unstaged contents
  to justify claims about staged behavior.
- Describe demonstrated implementation effects, not merely intended outcomes.
  Claim completed integration, successful tests, measured performance gains,
  deployment, or safety guarantees only with evidence applicable to the
  selected snapshot.
- Explain non-obvious reasons, constraints, or trade-offs when supported.
  Do not invent intent or manufacture a rationale for an obvious change.
- Preserve material behavior limits, compatibility breaks, migration
  requirements, and necessary user actions in the message. Keep task status,
  routine logs, temporary inspection limitations, and next steps outside it.
- Group edits by purpose, not by file, and describe each logical change once.
  Keep supporting code, tests, docs, and configuration with their logical
  change unless separately material.
  Exclude plans and out-of-scope claims; describe partial implementations
  honestly.
- If independent goals would benefit from separate commits, recommend that
  outside the message while still covering the requested scope. Do not
  recommend splitting solely because several types are present.
- Use identifiers and paths only when useful; never expose secrets or
  private data.

When repository access is unavailable, use supplied evidence and disclose
inspection limits in the separate report. Do not label a supplied diff as
staged without evidence. If no reliable change is evidenced, omit the message.

## 3. Write the message

Include a commit description after file changes in Git/SVN projects or when
explicitly requested, provided the selected scope contains adequately
evidenced changes.

Write the message in English unless the user requests another language.
Keep `Commit description:` outside one standalone fenced `text` block
containing the entire message.

Required structure, illustrated with a simple change:

Commit description:

```text
Correct the installation heading

- docs: Correct "Instalation" to "Installation".
```

- Begin with exactly one plain-language, imperative summary line describing
  the overall result. Start directly with the change description; never
  prefix it with a type, scope, issue key, or label.
- Follow it with one blank line and one typed main bullet per material
  logical change. A single change still requires both summary and bullet.
- Use `- type:` or `- type(component):`. Reuse meaningful component scopes;
  omit them when unhelpful.
- Write concise, active, imperative action phrases. Express supporting facts
  naturally. Avoid process narration and vague wording such as
  `Update files` or `Address feedback`.
- Avoid needless repetition, but allow limited overlap between summary and
  bullet for a simple change. Never invent details to make them different.
- Omit the summary's trailing period; end bullet descriptions with a period.
  Aim for about 50 characters in the summary and wrap body lines around 72
  when helpful. Preserve clarity and intact identifiers, paths, and URLs.

Prefer flat bullets. When related supporting details are easier to scan
separately, allow one level of `+` sub-bullets indented by two spaces.
Do not repeat type prefixes on children. Keep independent material changes
as main bullets; never hide unrelated changes beneath a vague parent such
as `fix: Fix several issues.`

Wrap a long sentence as an aligned continuation line, not an artificial
sub-bullet. Example of useful supporting details:

```text
Support per-job retry limits

- feat(retries): Allow each job to override its retry limit.
  + Treat zero as an explicit request to disable retries.
  + Preserve the configured default when no override is provided.
```

## 4. Classify and order the bullets

Choose the most specific type by purpose, not by the files touched.
Use the following display order; it is not classification priority.

| Order | Type | Purpose |
| --- | --- | --- |
| 1 | `fix` | Correct established defects or vulnerabilities, including fixes through dependencies or configuration |
| 2 | `feat` | Add or extend functionality or capabilities |
| 3 | `perf` | Improve performance or resource use without intended functional changes |
| 4 | `chore` | Perform maintenance or formatting not covered by another type |
| 5 | `refactor` | Restructure internals without changing intended behavior |
| 6 | `revert` | Explicitly reverse an earlier change, including reversals that remedy defects |
| 7 | `docs` | Change documentation, comments, or documentation translations |
| 8 | `test` | Change tests, fixtures, or test infrastructure |
| 9 | `build` | Change builds, packaging, or tooling; perform routine dependency upgrades |
| 10 | `ci` | Change continuous integration or delivery workflows |

Use `docs`, `test`, or `ci` when the purpose is confined to those concerns.
Do not infer a defect or vulnerability from a dependency version change alone.
Functional changes implemented through restructuring remain `fix` or `feat`.

Keep same-type main bullets contiguous, order them by consequence within each
group, and keep children with their parent. Skip absent groups; add no group
headings or blank lines between bullets. Let the summary emphasize the most
important outcome regardless of display order.

## 5. Preserve metadata and authorization boundaries

This custom format uses Conventional Commits-style bullets but lacks a typed
subject. Do not assume compatibility with tools requiring Conventional Commits.

Do not replace the format merely because historical messages or templates use
another convention. Report explicit conflicts separately and follow the
applicable instruction priority.

Append relevant, verified references or required trailers after the bullets,
separated by one blank line inside the same code block. Use `BREAKING CHANGE:`
when appropriate to explain a compatibility break and required migration.
Never invent issue references, identities, approvals, or sign-off attestations.

Preparing a description authorizes no version-control mutation. Leave changes
uncommitted; do not stage, revert working changes, create or modify commits,
rewrite history, or push without explicit authorization. Permission to commit
does not imply permission to amend, rebase, or push.

## 6. Check before output

1. Confirm the baseline, target, and boundary match the reported scope;
   explain automatic selection and material exclusions.
2. Verify that the complete selected diff and new files were inspected and
   every claim has evidence applicable to the selected snapshot.
3. Cover each material logical change once; check grouping and whether
   independent goals warrant a separate-commit recommendation.
4. Verify type classification and ordering, nesting, summary, punctuation,
   references, trailers, and code-block format.
5. Keep scope reports, inspection limitations, split recommendations, and
   task status outside the commit-message block.
