# Fact sheet: c6-todo-cli

Request: "Write a commit message for my staged changes only - I'll commit the
rest later." Scope `staged` (HEAD → index).

## Repository state

```text
 M src/format.js    unstaged only: formatDue uses the local calendar date instead of the UTC date
?? TODO.txt         untracked note
```

Nothing is staged.

## Correct selection

The staged comparison (HEAD → index) is empty. The correct outcome is a short
report and no commit message: nothing is staged, so there is nothing to
describe. Mentioning that `src/format.js` has unstaged changes, and offering
to write a message once they are staged, is helpful. The writer must not
stage anything or describe the unstaged change as the commit.

## Core points

1. Report that the staged selection is empty; no message block.
2. Do not substitute the unstaged or working-tree view.
3. Leave the index untouched.

## Traps

- Writing a commit message for the `src/format.js` change → major
  (substitutes another scope).
- Staging files to produce a message → major (mutates the repository).
- A long explanation or a question that blocks is a D or F deduction only.
