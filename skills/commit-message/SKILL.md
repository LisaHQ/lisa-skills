---
name: commit-message
description: >-
  Write concise commit descriptions for any Git or SVN project.
  Use after file changes and whenever asked to write, revise, or summarize
  a commit message. Require one plain imperative summary followed by typed
  bullets grouped in a fixed order. Leave changes uncommitted unless
  explicitly authorized.
---

# Commit Message

Describe the actual completed changes, not the conversation or implementation
process. Apply these rules across projects, languages, frameworks, and tools.

## Output contract

If the project uses Git or SVN, include a concise commit description in every
response following file changes. Detect version control from repository
metadata, configuration, or the established project workflow.

Use English unless the user explicitly requests another language.

Use exactly this structure:

Commit description:

```text
Describe the overall completed change directly without a type or scope prefix.

- type(scope): Describe the first material logical change.
- type(scope): Describe each additional material logical change.
```

- Put `Commit description:` outside the code block.
- Enclose the entire message in one standalone fenced code block labeled `text`.
- Begin with exactly one plain-language summary line, followed by one blank line.
- Start the summary directly with an imperative change description.
- Never prefix the summary with a type, scope, issue key, label, or equivalent
  decoration. Do not use `feat:`, `fix(api):`, `Summary:`, or similar prefixes.
- Always include the per-change bullets, even when there is only one change.
- Use exactly one bullet for a change set containing one material logical change.
- Keep commentary, verification results, limitations, and next steps outside
  the commit description.

Use project terminology and established scopes where helpful. Do not infer
permission to replace this format from commit history or templates.

## Describe logical changes

- Keep every summary and bullet concise, specific, and imperative:
  `Add`, `Fix`, `Prevent`, `Remove`, `Update`, or another concrete action.
- Describe what the completed change accomplishes. Include the reason only
  when it clarifies the effect.
- Avoid vague descriptions such as `Update files`, `Make improvements`,
  `Address feedback`, or `Apply requested changes`.
- Group related edits by purpose, not by file, tool, execution order, or author.
  One logical change may span multiple files; one file may contain several
  logical changes.
- Use one bullet per material logical change. Do not combine unrelated changes
  merely because they share a type.
- Include supporting edits in the same bullet when they serve the same outcome.
  Give tests, documentation, or configuration their own bullets only when
  they represent separately material changes.
- Describe each change once. Do not repeat it under several types.
- Exclude plans, abandoned edits, unrelated work, and unsupported claims.
  Do not imply that unfinished functionality is complete.
- Mention identifiers or paths only when they help identify the change.
  Never expose secrets or private data.
- Omit the summary's trailing period. End each bullet description with a period.

## Classify and order bullets

Use the following fixed group order. Skip absent groups.

| Order | Type | Use for |
| --- | --- | --- |
| 1 | `fix` | Correct defects or unintended behavior |
| 2 | `feat` | Add or extend functionality or capabilities |
| 3 | `perf` | Improve speed, resource use, or efficiency |
| 4 | `chore` | Perform maintenance or formatting not covered by a more specific type |
| 5 | `refactor` | Restructure internals without changing intended behavior |
| 6 | `revert` | Reverse a previous change |
| 7 | `docs` | Add or correct documentation, comments, or documentation translations |
| 8 | `test` | Add or improve tests, fixtures, or test infrastructure |
| 9 | `build` | Change build tooling, dependencies, compilation, or packaging |
| 10 | `ci` | Change continuous integration or delivery workflows |

Apply these rules:

- Keep all bullets of the same type contiguous, regardless of scope.
- Within each group, put the most consequential change first and keep related
  areas together.
- Use a flat bullet list. Do not add group headings, nested bullets, empty
  groups, or blank lines between groups.
- Prefix every bullet with exactly one lowercase type and an optional scope:
  `- fix: ...` or `- fix(parser): ...`.
- Use a short, meaningful component or functional area as the scope.
  Reuse established scopes; omit the scope when it adds no useful information.
- Classify by the primary intent of the logical change, not merely by the
  files touched. Choose the most specific applicable type.
- Use `docs`, `test`, `build`, or `ci` for changes confined to those concerns.
  A documentation typo is `docs`; a broken pipeline correction is `ci`.
- Use `fix` or `feat` for behavioral changes, even when restructuring code
  is the main implementation technique.
- Use `perf` for performance improvements without intended functional changes.
- Use `revert` for an explicit reversal, even when that reversal remedies a defect.
- Reserve `chore` for changes that do not fit another type.

## Ground the description in evidence

1. Establish the requested change set: the current task, staged changes,
   a specified revision range, or another scope explicitly selected by the user.
   Do not silently include unrelated pre-existing edits.
2. Inspect the actual changes with read-only commands:
  - Git: inspect status, staged diffs, unstaged diffs, and relevant new files.
  - SVN: inspect status, diffs, and relevant added or unversioned files.
  - Use revision-specific inspection when the user selects existing history.
3. Inspect relevant new files separately when the diff does not include their
   contents. Do not automatically exclude intentional generated or configuration
   changes that belong to the requested change set.
4. Derive the logical changes, assign their types, and apply the fixed group order.
5. Write the summary from the completed bullet list. Capture the overall outcome
   without turning it into a file inventory.
6. Verify that each bullet is supported by the inspected changes and that
   no material logical change is omitted.

When repository access is unavailable, use supplied diffs or other concrete
evidence and state the limitation outside the code block. Never claim to have
inspected unavailable changes. If no change is evidenced, do not fabricate
a commit description.

For changes spanning multiple repositories, provide a separate description
for each repository and identify it outside its code block.

## Leave version control unchanged

Generating a commit description does not authorize a version-control mutation.

- Leave changes uncommitted by default.
- Do not run any command that creates or modifies a commit unless the user
  explicitly requests it.
- Do not stage files, revert working changes, rewrite history, or push merely
  to prepare the description.
- When a version-control action is explicitly authorized, perform only the
  authorized action on the intended change set. A request to commit does not
  imply permission to amend, rebase, or push.
