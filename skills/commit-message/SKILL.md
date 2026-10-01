---
name: commit-message
description: >-
  Write concise, evidence-grounded commit descriptions for any Git or SVN
  project. Use after file changes and when asked to write or revise a commit
  message. Require a plain imperative summary and typed main bullets grouped
  in a fixed order. Allow one level of supporting sub-bullets when useful.
  Leave changes uncommitted unless explicitly authorized.
---

# Commit Message

Describe what the completed changes accomplish. Preserve the context needed
for a future reader to understand their purpose and consequences without
access to the conversation.

## Required output

Detect Git or SVN from repository metadata, configuration, or the established
project workflow. If the project uses either, include a concise commit
description in every response following file changes.

Use English unless the user explicitly requests another language.

Commit description:

```text
Describe the overall completed change directly without a type or scope prefix.

- type(scope): Describe a material logical change.
  + Add a supporting detail only when it improves understanding.
- type(scope): Describe another material logical change when applicable.
```

- Put `Commit description:` outside the code block.
- Enclose the entire message in one standalone fenced code block labeled `text`.
- Begin with exactly one plain-language summary line, followed by one blank line.
- Start the summary directly with an imperative change description.
- Never prefix the summary with a type, scope, issue key, label, or equivalent
  decoration, such as `feat:`, `fix(api):`, or `Summary:`.
- Always include the main bullets. Use exactly one main bullet when there is
  only one material logical change.
- Omit optional sub-bullets and additional main bullets when unnecessary.
- Let the summary state the overall outcome and the bullets explain the
  material changes. Avoid merely repeating the summary in the body.
- Omit the summary's trailing period. End bullet descriptions with a period.
- Keep the summary short; aim for about 50 characters when practical without
  sacrificing meaning. Wrap body lines around 72 characters when helpful.
  Do not split identifiers, paths, or URLs merely to meet a length target.

## Describe meaningful changes

- Write the summary and bullet actions in concise, active, imperative language.
- Describe the effect of the completed change, not the conversation, feedback
  cycle, editing process, or sequence of tool calls.
- Avoid vague descriptions such as `Update files`, `Make improvements`,
  `Address feedback`, or `Apply requested changes`.
- Group edits by purpose rather than by file. One logical change may span
  multiple files; one file may contain several logical changes.
- Include supporting code, tests, documentation, and configuration in the same
  logical change unless they represent separately material changes.
- Describe each material change once. Do not repeat it under multiple types.
- For non-obvious changes, preserve the necessary reason, constraint, or
  trade-off. Explain why the chosen behavior matters when the diff alone
  would not make that clear.
- Ground explanations in available requirements, discussion, code, or other
  evidence. Do not invent intent or justification.
- Keep obvious changes brief. Do not manufacture a rationale merely to fill
  the body.
- State material compatibility changes, behavior limits, migration requirements,
  and required follow-up actions inside the message when they are consequences
  of the change.
- Keep task status, routine command logs, temporary environment limitations,
  and the assistant's next steps outside the message.
- Exclude unrelated work, abandoned edits, plans, and unsupported claims.
  Do not imply that unfinished functionality is complete.
- Use identifiers or paths only when they help explain the change.
  Never expose secrets or private data.

## Choose main bullets or sub-bullets

Use one main bullet for each material logical change.

Use a sub-list only when several supporting details of the same change are
easier to understand separately than in one sentence.

- Start every main bullet with `- type:` or `- type(scope):`.
- Start each sub-bullet with `+`, indented by two spaces.
- Allow only one level of sub-bullets. Do not nest further.
- Do not repeat a type prefix on sub-bullets; they belong to their parent.
- Keep sub-bullets specific: relevant conditions, related behavior, necessary
  rationale, compatibility effects, or migration requirements.
- Promote a detail to a typed main bullet when it describes a separate material
  logical change.
- Do not use a vague main bullet as a category heading for unrelated changes.
- Do not create a sub-list when one concise sentence is sufficient.
- Wrap a long sentence onto a continuation line instead of splitting it into
  artificial sub-bullets. Align continuation lines with their bullet text.

Example of one logical change with useful supporting details:

```text
Support per-job retry limits

- feat(retries): Allow each job to override its retry limit.
  + Treat zero as an explicit request to disable retries.
  + Preserve the configured default when no override is provided.
```

## Classify and order main bullets

Use this fixed group order. Skip absent groups.

| Order | Type | Use for |
| --- | --- | --- |
| 1 | `fix` | Correct defects or unintended behavior |
| 2 | `feat` | Add or extend functionality or capabilities |
| 3 | `perf` | Improve performance or resource use without intended functional changes |
| 4 | `chore` | Perform maintenance or formatting not covered by another type |
| 5 | `refactor` | Restructure internals without changing intended behavior |
| 6 | `revert` | Reverse a previous change |
| 7 | `docs` | Add or correct documentation, comments, or documentation translations |
| 8 | `test` | Add or improve tests, fixtures, or test infrastructure |
| 9 | `build` | Change build tooling, dependencies, compilation, or packaging |
| 10 | `ci` | Change continuous integration or delivery workflows |

- Keep all main bullets of the same type contiguous, regardless of scope.
- Within each group, put the most consequential change first and keep related
  areas together.
- Keep each sub-list directly beneath its parent.
- Do not add type-group headings, empty groups, or blank lines between bullets.
- Let the summary emphasize the most important outcome regardless of group order.
- Classify by the primary intent of the logical change, not just the files
  touched. Choose the most specific applicable type.
- Use `docs`, `test`, `build`, or `ci` for changes confined to those concerns.
  A documentation correction is `docs`; a pipeline correction is `ci`.
- Use `fix` or `feat` for functional changes even when restructuring code
  is the main implementation technique.
- Use `revert` for an explicit reversal, even when it remedies a defect.
- Reserve `chore` for changes that do not fit another type.
- Use a short, meaningful component or functional area as an optional scope.
  Reuse established scopes; omit the scope when it adds no useful information.

## Inspect evidence and check cohesion

1. Establish the requested change set: the current task, staged changes,
   a selected revision range, or another explicitly requested scope.
   Do not silently include unrelated pre-existing edits.
2. Inspect the actual changes using read-only operations:
  - Git: inspect status, staged and unstaged diffs, and relevant new files.
  - SVN: inspect status, diffs, and relevant added or unversioned files.
  - Use revision-specific inspection when existing history is selected.
3. Read relevant new files separately when their contents are absent from
   the diff. Include intentional generated or configuration changes when
   they belong to the requested scope.
4. Check whether the change set serves a coherent purpose. Do not assume that
   all work completed in one session belongs in one commit.
5. When independent goals would benefit from separate commits, recommend the
   split outside the code block. Still describe the requested scope unless
   the user requests separate messages. Do not silently omit changes or
   perform the split.
6. Do not recommend splitting merely because several types are present.
   A feature with its supporting tests and documentation can remain cohesive.
7. Derive the logical changes, assign types, apply the fixed group order,
   and write the summary from the resulting body.
8. Verify that every claim is supported, every material logical change is
   covered, and the summary, bullets, and sub-bullets do not needlessly repeat.

When repository access is unavailable, use supplied diffs or other concrete
evidence and state the limitation outside the code block. Never claim to have
inspected unavailable changes. If no change is evidenced, do not fabricate
a description.

For multiple repositories, provide separate descriptions and identify each
repository outside its code block.

## Respect compatibility and required metadata

This is a custom format with Conventional Commits-style main bullets.
It is not a complete Conventional Commits message because its summary has
no type prefix. Do not assume compatibility with tools requiring that standard.

Use established project terminology and scopes. Do not replace this format
merely because historical commits or templates use another convention.
If an explicit project requirement conflicts with it, identify the conflict
outside the code block and follow the applicable instruction priority.

When genuinely relevant or explicitly required, append verified references
or trailers after the bullet list, separated by one blank line. Keep them
inside the same code block.

- Use a `BREAKING CHANGE:` footer when appropriate to explain a compatibility
  break and any required migration.
- Include issue references or other required metadata only when supported.
- Never invent issue IDs, approvals, identities, or sign-off attestations.
- Do not imply that adding trailers makes this format Conventional Commits
  compliant.

## Leave version control unchanged

Generating a commit description does not authorize a version-control mutation.

- Leave changes uncommitted by default.
- Do not run any command that creates or modifies a commit unless the user
  explicitly requests it.
- Do not stage files, revert working changes, rewrite history, or push merely
  to prepare the description.
- When an operation is explicitly authorized, perform only that operation
  on the intended change set. Permission to commit does not imply permission
  to amend, rebase, or push.
