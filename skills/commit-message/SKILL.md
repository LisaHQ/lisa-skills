---
name: commit-message
description: >-
  Write accurate, concise commit descriptions for Git or SVN projects after
  file changes or when requested. Honor an explicit scope or select diffs per
  file using configurable auto-priority, and report selection separately.
  Use a plain summary and typed bullets in a fixed order. Never commit
  without explicit authorization.
metadata:
  allow_implicit_invocation: true
---

# Commit Message

Describe what the selected changes accomplish and preserve the context needed
by future readers.

## 1. Select and report the diffs

Detect Git or SVN from repository metadata, configuration, or the established
workflow. Read these options from the request or invocation arguments; accept
unambiguous equivalent wording:

| Option | Default | Meaning |
| --- | --- | --- |
| `scope` | `auto` | Select per file automatically, or enforce `staged`, `unstaged`, or `working-tree` across the requested boundary |
| `auto-priority` | `staged,unstaged,working-tree` | In `auto` only, rank candidate views from highest to lowest priority for each file |

When used, require `auto-priority` to list all three views once, in the desired
order; it ranks alternatives, never filters files. A concrete `scope` overrides it.
These options are independent of component scopes such as `fix(parser):`.

Apply any requested repository, file, or task boundary before selection.
Otherwise, use the selected repository. Out-of-boundary changes must not
influence selection. Explicit commits, revision ranges, or a designated
supplied diff take precedence over working-change selection; do not blend
other views into them. Apply `auto` to supplied alternatives only when their
file identities and comparisons are established. Never infer missing states
or label a supplied diff as staged without evidence.

For Git working changes:

| View | Comparison | Contents |
| --- | --- | --- |
| `staged` | HEAD → index | Staged changes only |
| `unstaged` | Index → working tree | Unstaged edits plus eligible untracked files |
| `working-tree` | HEAD → working tree | Final combined changes plus eligible untracked files |

Eligible untracked files are within the boundary and are not ignored or
excluded unless explicitly included. Inspect their full contents as additions;
ordinary Git diffs omit them. Count them on the unstaged side for selection
and reporting, and include them in `unstaged` or `working-tree` as applicable.

`working-tree` is a combined view, not a third independent set of edits.
Never append it to another view of the same file or count equivalent views
as additional changes. Use an empty baseline where appropriate if Git has
no HEAD; do not create a commit to establish one.

Select as follows:

1. **Concrete scope:** Use that comparison for every file in the boundary.
   Omit files with no change in it. Never fall back to another comparison,
   even when the entire selection is empty.
2. **Auto:** For each file independently, identify the available, nonempty
   candidate diffs. Select the sole candidate directly; otherwise select
   the first candidate in `auto-priority`. Skip files with no candidates.
   A staged file must never suppress an unstaged-only file elsewhere.
3. Select one complete view per file, not different views for different
   hunks. Preserve proven rename identities and their old/new path pairing.
   Combine the selected per-file diffs into the message's evidence set;
   never add excluded edits back through another view or surrounding code.

An empty net `working-tree` diff does not erase nonempty staged or unstaged
candidates in `auto`. Distinguish empty comparisons from unavailable evidence:
an inspection failure is not permission to fall back silently. A sole supplied
view may be used without claiming other states are empty. Ask only when a
material ambiguity cannot be resolved from available context. If nothing is
selected, report that and omit the commit description.

For SVN, `auto` and `working-tree` select working-copy changes against BASE.
Report that SVN has no staging area and `auto-priority` is inapplicable;
reject explicit `staged` or `unstaged` without substituting another scope.

Before the message, report selection in the conversation's language, normally
in one or two sentences. State the requested scope (including default `auto`),
resolved comparison(s), boundary, and material exclusions. For `auto`, include
the priority and group selected files by view; use counts when clearer, but
identify files whose competing views were excluded. Do not label a mixed
selection as globally staged or as one existing repository snapshot.

Whenever staged and unstaged changes coexist within the boundary, report
whether they overlap on any files and what was selected or excluded for
those files. Do not claim all unstaged changes were excluded when unstaged-only
files were selected. Keep this report outside the commit message.

Example with default priority:
> Scope: auto (default), priority staged → unstaged → working-tree.
> Select staged diffs for A and C (HEAD → index), and unstaged changes for B
> and untracked D (index → working tree). C has both staged and unstaged
> changes; exclude only C's unstaged diff.

Use only facts actually detected. For multiple repositories, provide a
separate report and message for each.

## 2. Ground the content in evidence

- Inspect every selected per-file diff and new file, including intentional
  generated or configuration changes. Inspect other states only as needed
  for selection, exclusions, or necessary context.
- Describe each net difference between its selected baseline and target;
  omit intermediate edits that cancel out in that comparison.
- Read each changed file from its selected target: the index for `staged`,
  the working tree for `unstaged` or `working-tree`, or the designated revision
  or supplied evidence for fixed selections. Read necessary callers, tests,
  configuration, and surrounding code from compatible versions. Never use
  an excluded view to justify behavior attributed to a selected diff.
- Describe demonstrated implementation effects, not merely intended outcomes.
  Claim completed integration, successful tests, measured performance gains,
  deployment, or safety guarantees only with evidence applicable to the
  selected evidence set. A mixed `auto` selection is not necessarily an
  existing or tested snapshot; current working-tree tests alone cannot
  verify selected staged content that differs from the working tree.
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
inspection limits in the separate report. If no reliable change is evidenced,
omit the message.

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

Prefer flat bullets. Use a `+` sub-list only when it contains at least two
distinct, related supporting details of the same main bullet and makes
them easier to scan. With only one supporting detail, include it in the
main bullet. Wrap long sentences as aligned continuation lines; never
use a single-item sub-list or split one idea to meet the minimum.
Do not invent details to create a sub-list.

Allow only one nested level, with `+` sub-bullets indented by two spaces.
Do not repeat type prefixes on children. Keep independent material changes
as main bullets; never hide unrelated changes beneath a vague parent such
as `fix: Fix several issues.`

Example of useful supporting details:

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

1. Verify the boundary and each file's selected baseline and target; enforce
   concrete scope globally or auto-priority per file. Check fallback,
   overlaps, exclusions, and the report against the actual selection.
2. Verify that every selected diff and new file was inspected, with no
   double-counted views or claims unsupported by the selected versions.
3. Cover each material logical change once; check grouping and whether
   independent goals warrant a separate-commit recommendation.
4. Verify type classification and ordering, nesting, summary, punctuation,
   references, trailers, and code-block format.
5. Keep scope reports, inspection limitations, split recommendations, and
   task status outside the commit-message block.
