# Fact sheet: s2-fetchkit

Request: "Our README is out of date. Please update it." (improve mode; stale v1 README exists)
Kind: library (TypeScript, npm). Reader: JS/TS developers calling HTTP JSON APIs; also v1 users upgrading.

## Ground truth (v2.1.0)

- Package name **`@example-org/fetchkit`** (scoped). The unscoped `fetchkit` is deprecated (CHANGELOG 2.0.0). Published per CHANGELOG ("Publish as @example-org/fetchkit").
- API: **`createClient(options)`** returns `{ get, post, put, patch, delete }`; each returns a Promise of parsed JSON (`undefined` for 204). Generic type parameter for typed responses (`api.get<User[]>("users")`).
- Options and defaults: `baseUrl` (relative paths resolve against it), `retries` = **2** extra attempts, `retryOn` = **408, 425, 429, 500, 502, 503, 504**, `retryNonIdempotent` = **false** (POST and PATCH are **not** retried unless enabled; GET/HEAD/PUT/DELETE/OPTIONS are), `timeoutMs` = **10000** per attempt, `headers`.
- Retries: exponential backoff with full jitter (random up to 200 ms x 2^attempt, capped 5 s); **honors `Retry-After` on 429 and 503** (capped 30 s); network errors and timeouts are retried for retryable methods.
- Errors: throws **`FetchkitError`** with `status`, `url`, `body` for non-2xx after retries and for network failures/timeouts (status undefined then).
- Node.js **>= 18** (native fetch). Ships ESM and CJS (`exports` import/require) with TypeScript types. Tests run only on Node 18/20/22 (GitHub Actions `test.yml`); **no evidence for browser or Deno support**.
- **No caching** (removed in 2.0.0).
- Dev: pnpm (`packageManager pnpm@9.12.0`, `pnpm-lock.yaml`): `pnpm install`, `pnpm test` (vitest), `pnpm lint`, `pnpm build` (tsup).
- License MIT (Copyright (c) 2023 Example Org contributors).
- Breaking changes from v1 (CHANGELOG 2.0.0): default object -> `createClient()`, `timeout` -> `timeoutMs`, default retries 3 -> 2, cache removed, Node 18+, scoped package name.

## Existing README content to preserve

- Sponsors section (Example Hosting link) and Contributors thanks/link: valuable, should be kept.
- License: MIT (correct).

## Core points a strong README highlights

1. One-liner: fetch wrapper with retries, timeouts, typed JSON.
2. Correct install (`npm install @example-org/fetchkit` or equivalent) and a working `createClient` example.
3. Accurate options table with real defaults; safe retry semantics (POST not retried by default; Retry-After honored).
4. Upgrade/migration note for v1 users (link CHANGELOG).

## Traps (judge explicitly)

- Keeping or showing `npm install fetchkit` / `fetchkit.get(...)` / `timeout` option / `cache` option / "Caching" feature -> major each.
- Wrong defaults (retries 3, timeout 5000) -> major.
- Claiming all requests (incl. POST) are retried -> major.
- Keeping "Works everywhere (Node 14+, browsers, Deno)" or claiming browser/Deno support as fact -> major (Node 14 wrong) / minor (browsers unverified).
- Keeping the Travis badge (CI is GitHub Actions) or an npm badge for unscoped `fetchkit` -> minor each.
- Dropping the Sponsors or Contributors acknowledgments silently -> process failure (F), minor.
- Hype left in ("blazing fast", 🚀🚀🚀) -> C/E penalty.

## Judge notes

- Verify against `src/`, `package.json`, `CHANGELOG.md`, the workflow, and `LICENSE`; the original `README.md` is the stale input.
- With `baseUrl` "https://api.example.com/v1/", a path with a leading slash such as "/users" resolves to https://api.example.com/users (dropping /v1), so examples must use relative paths.
- A `baseUrl` with a path must end with `/`: "users" against "https://api.example.com/v1" resolves to https://api.example.com/users. The doc comment in `src/index.ts` shows the base URL without the slash; the test uses it with the slash. Count an example that relies on the slash-less form as a major error.
- Only `get`, `post`, `put`, `patch`, and `delete` exist on the client; HEAD and OPTIONS cannot be sent.
