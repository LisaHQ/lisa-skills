---
name: commit-message
description: >-
  Write accurate, concise commit messages for Git or SVN projects. Use after
  file changes or when a commit message or commit description is requested.
---

# Commit Message

Describe what the selected changes accomplish and preserve context useful
to future readers.

Preparing a description authorizes no version-control mutation. Leave changes
uncommitted; do not stage, revert working changes, create or modify commits,
rewrite history, or push without explicit authorization. Permission to commit
does not imply permission to amend, rebase, or push.

## 1. Select the diffs

Detect Git or SVN from repository metadata, configuration, or the established
workflow. Read these options from the request or invocation arguments; accept
unambiguous equivalent wording:

| Option | Default | Meaning |
| --- | --- | --- |
| `scope` | `auto` | Select per file automatically, or enforce `working-tree`, `staged`, or `unstaged` across the requested boundary |
| `auto-priority` | `working-tree,staged,unstaged` | In `auto` only, rank views from highest to lowest priority for each file |

When used, require `auto-priority` to list all three views once; it ranks
alternatives, never filters files. A concrete `scope` overrides it. These
options are independent of component scopes such as `fix(parser):`.

Apply any requested repository, file, or task boundary before selection;
otherwise, use the selected repository. Out-of-boundary changes must not
influence selection. Explicit commits, revision ranges, or a designated
supplied diff take precedence over working-change selection; do not blend
other views into them. Apply `auto` to supplied alternatives only when their
file identities and comparisons are established. Never infer missing states
or label a supplied diff as staged without evidence.

For Git, use these comparisons, with an empty baseline where appropriate
when HEAD does not exist:

| View | Comparison | Contents |
| --- | --- | --- |
| `working-tree` | HEAD → working tree | Final combined changes plus eligible untracked files |
| `staged` | HEAD → index | Staged changes only |
| `unstaged` | Index → working tree | Unstaged edits plus eligible untracked files |

Include untracked files only within the boundary and not ignored or excluded,
unless explicitly included. Inspect their full contents; ordinary Git diffs
omit them. For `unstaged`, compare against the index as additions; for
`working-tree`, compare against HEAD, treating an absent HEAD path as an
addition. Reconcile staged deletion and same-path untracked recreation into
one net change. Count untracked files on the unstaged side for reporting.

An **empty** comparison verifies no difference in file existence, content, or
tracked metadata; an empty new file is still an addition. **Unavailable**
means the comparison cannot be established. Resolve inspection failures
where possible and retain remaining limitations for the report.

**Concrete scope:** Use that comparison for every file in the boundary.
Omit empty results and report unavailable evidence. Never substitute another
view, even if the entire selection is empty.

**Auto:** Walk `auto-priority` independently for each file, in order, without
prefiltering empty results or bypassing the walk for a sole nonempty candidate:

| Result of the current view | Action for this file |
| --- | --- |
| Changed | Select this complete diff and stop |
| Empty `working-tree` | Omit the file and stop; do not revive lower-priority staged or unstaged changes |
| Empty `staged` or `unstaged` | Continue to the next view |
| Unavailable | Continue using supported evidence; record the fallback and its limitation |

Select one view per file, not different views for different hunks. Preserve
proven rename identities and old/new path pairing. Combine selected per-file
diffs without duplication: `working-tree` already combines both sides, so
never append it to another view of the same file. Ask only when a material
ambiguity cannot be resolved from context.

For SVN, `auto` and `working-tree` select working-copy changes against BASE.
Report that SVN has no staging area and `auto-priority` is inapplicable;
reject explicit `staged` or `unstaged` without substituting another scope.

## 2. Ground the content in evidence

- Inspect every selected diff and new file, including intentional generated
  or configuration changes. Inspect other states only for selection,
  exclusions, or necessary context. When repository access is unavailable,
  use supplied evidence and record inspection limits.
- Describe each net difference between its selected baseline and target;
  omit intermediate edits that cancel out in that comparison.
- Read each changed file from its selected target: the index for `staged`,
  the working tree for `unstaged` or `working-tree`, or the designated revision
  or supplied evidence for fixed selections. Read necessary callers, tests,
  configuration, and surrounding code from compatible versions. Never justify
  selected behavior with an excluded view or reintroduce excluded changes
  through contextual code.
- Describe demonstrated effects, not merely intended outcomes. Claim completed
  integration, successful tests, measured performance gains, deployment, or
  safety guarantees only with evidence applicable to the selection. Mixed
  `auto` selections need not form an existing or tested snapshot; current
  working-tree tests alone cannot verify different selected staged content.
- Explain supported, non-obvious reasons, constraints, or trade-offs. Do not
  invent intent or manufacture a rationale for an obvious change.
- Preserve material behavior limits, compatibility breaks, migration
  requirements, and necessary user actions in the message.
- Group by purpose, not by file; describe each logical change once. Keep its
  supporting code, tests, docs, and configuration together unless separately
  material. Exclude plans and out-of-scope claims; describe partial work honestly.
- Recommend separate commits for independent goals when useful, while still
  covering the requested scope. Different types alone do not justify a split.
- Use identifiers and paths only when useful; never expose secrets or private data.

## 3. Classify and order the bullets

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

## 4. Present the result

Provide a separate report and message for each repository. If the selection
is empty or no reliable change is evidenced, give only the report; distinguish
no changes from insufficient evidence.

Keep reports, inspection limitations, split recommendations, format conflicts,
routine logs, task status, and task next steps outside the commit-message block.

### Selection report

Before the message, report in the conversation's language, normally in one
or two sentences. State the requested scope (mark default `auto`), resolved
comparison(s), boundary, and material exclusions or evidence limits, including
fallback caused by unavailable evidence. For `auto`, include the priority
and group selected files by view; use counts when clearer. Identify paths
with excluded changes or net cancellations.

When staged and unstaged changes coexist within the boundary, report whether
paths overlap and whether the selection combines both sides, selects one, or
omits their cancelled net result. Do not claim an entire category was excluded
when some of it was included, or label mixed views as globally staged or one
existing snapshot.

Example with default priority:
> Scope: auto (default), priority working-tree → staged → unstaged.
> Select working-tree changes for A, B, C and untracked D (HEAD → working
> tree), including C's combined staged and unstaged result once; omit E
> because its staged and unstaged changes cancel out.

### Commit message

Write in English unless the user requests another language. Keep
`Commit description:` outside one standalone fenced `text` block containing
the entire message.

This custom format uses Conventional Commits-style bullets but lacks a typed
subject; do not assume compatibility with tools requiring Conventional Commits.
Do not replace it merely because historical messages or templates use another
convention. Report explicit conflicts separately and follow applicable
instruction priority.

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

Prefer flat bullets. Use one level of `+` sub-bullets, indented two spaces,
only for at least two distinct, related supporting details of the same main
bullet that are easier to scan. Put a single detail in its parent; wrap prose
as aligned continuation lines. Do not repeat types on children, invent or
split details to justify nesting, or hide independent changes under vague
parents; keep them as main bullets.

Example of useful supporting details:

```text
Support per-job retry limits

- feat(retries): Allow each job to override its retry limit.
  + Treat zero as an explicit request to disable retries.
  + Preserve the configured default when no override is provided.
```

Append relevant, verified references or required trailers after the bullets,
separated by one blank line inside the same code block. Use `BREAKING CHANGE:`
when appropriate to explain a compatibility break and required migration.
Never invent issue references, identities, approvals, or sign-off attestations.

## 5. Check before output

1. Verify the boundary, per-file baselines and targets, scope or priority,
   empty/unavailable handling, stopping, fallback, and reported exclusions.
2. Confirm every selected diff and new file was inspected, with no duplicate
   views or claims unsupported by the selected versions.
3. Cover each material logical change once; check grouping and split advice.
4. Check classification, order, summary, nesting, punctuation, references,
   trailers, and code-block format.
5. Keep the report and other commentary outside the commit-message block.
