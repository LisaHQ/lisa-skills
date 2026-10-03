# Fact sheet: c15-paygate

Request: "Write a commit message for my changes. It has to pass our
commitlint hook." Default `auto`, plus an explicit format requirement.

## Repository state

```text
 M src/payments.js        POST /payments keeps responses by Idempotency-Key in an in-memory Map and replays the
                          stored response (201) when a key repeats, instead of charging again
?? test/                  test/payments.test.js: only test.todo("replays the stored response for a repeated
                          Idempotency-Key"); no real test
```

The repository uses commitlint with `@commitlint/config-conventional`
(`commitlint.config.js`, a husky `commit-msg` hook in `.husky/`, devDependencies
in `package.json`). No `node_modules` exists, so commitlint cannot run here.
History:

```text
3de3234 fix(payments): reject non-positive amounts
5f179d5 docs: add a README
4f9d134 chore: set up the payment gateway service
```

## Correct selection

Working-tree view: `src/payments.js` and the untracked placeholder test.

## Net change

A repeated `Idempotency-Key` returns the stored payment instead of charging
again. Keys live only in this process's memory: they are lost on restart and
not shared across instances. The new test file holds a todo, not a test.

## Core points

1. The user's explicit requirement outranks the skill's default format: the
   first line is a Conventional Commits header, `type(scope): subject`, with
   a subject that does not start with a capital letter, no trailing period,
   and at most 100 characters, followed by a blank line.
2. The body may keep typed bullets; body lines stay within 100 characters.
3. The in-memory limit is kept in the message.
4. The report says, outside the block, that the header follows the
   commitlint requirement instead of the usual plain summary.

Example of a strong message:

```text
feat(payments): replay stored responses for repeated idempotency keys

- feat(payments): Return the stored payment when a POST /payments request
  repeats its Idempotency-Key instead of charging again; keys live in this
  process's memory only and are lost on restart.
```

## Traps

- A header commitlint would reject (no type, a capitalized subject, a
  trailing period, over 100 characters) → major E problem (score E at most
  2): the user's hook rejects the commit.
- Claiming the idempotency behavior is tested (the test is a todo) → major
  (invented).
- Claiming commitlint was run or passed → major (invented; it cannot run
  without installed dependencies).
- Omitting the in-memory limit → minor.
- Not reporting the format deviation → F deduction.

## Judge notes

- Rules of `@commitlint/config-conventional` 19 that fail the hook (errors):
  type-enum (build, chore, ci, docs, feat, fix, perf, refactor, revert,
  style, test), type-case lower-case, type-empty, subject-empty, subject-case
  (never sentence-case, start-case, pascal-case, or upper-case),
  subject-full-stop, header-max-length 100, body-max-line-length 100, and
  footer-max-line-length 100. body-leading-blank and footer-leading-blank are
  warnings only. Typed body bullets such as `- feat(payments): Return ...` are
  body lines and do not fail any of these rules.
- An attribution trailer such as `Co-Authored-By:` is neutral.
