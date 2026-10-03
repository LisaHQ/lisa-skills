# Fact sheet: c2-notes-api

Request: "Write a commit message for my staged changes." Scope `staged`
(HEAD → index) for every file.

## Repository state

```text
MM src/routes/notes.js     staged: GET /notes/:id with handler getNoteById, 404 when missing;
                           unstaged on top: handler renamed findNote, plus DELETE /notes/:id (removeNote)
M  test/notes.test.js      staged only: test that store.get finds a note by id
 M src/store.js            unstaged only: new remove(id)
?? scratch.http            untracked request scratchpad
```

## Correct selection

Staged view only: the index version of `src/routes/notes.js` and
`test/notes.test.js`. Excluded: every unstaged edit (the findNote rename, the
DELETE route, `store.remove`) and the untracked `scratch.http`.

## Net change

- New route `GET /notes/:id` returns the note, or 404 with
  `{ error: "note not found" }` when the id does not exist.
- A test checks that `store.get` finds a note by id.

## Core points

1. One feat: fetch a single note by id, with 404 for unknown ids.
2. Names and behavior from the index (`getNoteById` if a name is used).
3. Report: scope staged (HEAD → index); `notes.js` also has unstaged edits
   that were left out; `store.js` and `scratch.http` excluded.

Example of a strong message:

```text
Add an endpoint to fetch a note by id

- feat(notes): Add `GET /notes/:id`, returning 404 when the note does not
  exist.
```

## Traps

- Any mention of DELETE, `removeNote`, `findNote`, or `store.remove` in the
  message → major (describes excluded unstaged changes).
- Reading the working-tree version of `notes.js` instead of the index → major.
- Claiming the endpoint is tested end to end (the staged test covers
  `store.get` only) or that tests pass → minor or major by impact.

## Judge notes

- Compare `git diff --cached` (the selection) with `git diff` (excluded).
- An attribution trailer such as `Co-Authored-By:` is neutral.
