# Fact sheet: s10-acme-platform

Request: "Add a README for packages/money - other teams in this repo keep asking how to use it." (create mode; target `packages/money/README.md`)
Role: component guide for developers on other teams in the same repository.
Kind: package inside a pnpm monorepo (TypeScript library, internal). Reader: developers on other teams in the same repository who want to depend on the package.

## Ground truth

- Monorepo root: `package.json` (private, `packageManager` pnpm@9.12.0, engines node >= 20, scripts `build`/`test`/`docs` = `pnpm -r ...`), `pnpm-workspace.yaml` (`apps/*`, `packages/*`), `.nvmrc` 20, root `README.md` (repository map linking `packages/money/README.md`, which does not exist yet; set up with Node.js 20 and pnpm 9, `pnpm install`, `pnpm test` runs every package's tests; license Apache-2.0), `LICENSE` = **Apache-2.0**. Remote https://github.com/example-org/acme-platform.git; no tags.
- Owners (`.github/CODEOWNERS`): `/packages/money/` -> **@acme/payments-team**; `/apps/checkout/` -> @acme/storefront-team.
- Markdown house style (`.markdownlint.jsonc`): **MD004 asterisk** (`*` bullets), MD013 line length 100 (code blocks and tables excluded). `.markdownlintignore` excludes the generated `packages/*/docs/api/`.
- Package `@acme/money` 0.2.0, **`private: true`** (never published), ESM, `main`/`types` point to `./dist` (git-ignored; built by `tsup`). Scripts: `build` (tsup), `test` (`vitest run`), `docs` (typedoc into `docs/api`). `package.json` says **`"license": "MIT"`**, which conflicts with the repository's Apache-2.0 LICENSE.
- API (`src/index.ts`):
  - `MINOR_UNITS`: **VND 0, USD 2, EUR 2**; `Currency` = one of those three codes (a type-level guard only: plain JavaScript callers can pass another code without an error).
  - `Money` = `{ minor: bigint, currency }`: an integer count of minor units, never a float.
  - `money(amount: string, currency)` parses a **decimal string**; throws `RangeError` for more decimals than the currency allows (`money("1.005", "USD")`, `money("1.5", "VND")`) or a non-decimal string (`"1,000"`). Fewer decimals are padded (`"19.9"` -> 1990n); negatives are accepted.
  - `add(a, b)` throws **`CurrencyMismatchError`** across currencies.
  - `allocate(m, ratios)` splits by integer ratios; leftover minor units go **one each to the first parts**: 100 USD by `[1, 1, 1]` -> 33.34, 33.33, 33.33. Non-integer ratios or ratios summing to zero or less throw `RangeError`.
  - `format(m, locale = "en-US")` uses `Intl.NumberFormat`: `$20.00`; `format(money("1250000", "VND"), "vi-VN")` -> `1.250.000 ₫`.
- Tests: `test/money.test.ts` (vitest, 4 cases matching the behaviour above). Package tests: `pnpm --filter @acme/money test`.
- Generated reference: `docs/api/` (typedoc-plugin-markdown) is committed and covers every export; regenerate with `pnpm --filter @acme/money docs`.
- Consumer: `apps/checkout` depends on `"@acme/money": "workspace:*"` and uses `money`, `add`, `format` with VND and `vi-VN` (`src/cart.ts`).
- How another workspace package depends on it: add `"@acme/money": "workspace:*"` to its `package.json` and run `pnpm install` at the root, or `pnpm --filter <app> add @acme/money --workspace` (or `@acme/money@workspace:*`).

## Core points a strong README highlights

1. What the package is for (exact money amounts in integer minor units, safe splitting, formatting), where it fits, and a link up to `../../README.md`.
2. Owners: @acme/payments-team.
3. How to depend on it from another workspace package (`workspace:*`, then `pnpm install` at the root).
4. A short import example that passes decimal strings.
5. Pitfalls: `bigint` minor units, `RangeError`, `CurrencyMismatchError`, the allocate remainder rule, only VND/USD/EUR.
6. A link to `docs/api/README.md` and how to regenerate it; how to run the package's tests.
7. The notes report the license conflict (MIT in `package.json`, Apache-2.0 in `LICENSE`).

## Traps (judge explicitly)

- README written at the repository root, or the root `README.md` rewritten -> major (F).
- Registry install (`npm install @acme/money`, `yarn add @acme/money`, `pnpm add @acme/money` without `--workspace` or `workspace:*`) -> major.
- Amounts described or shown as numbers or floats (`money(19.99, "USD")`, "`minor` is a number") -> major.
- Wrong remainder rule or currency list -> major each.
- License stated as MIT -> major. License conflict not reported in the README or notes -> F minor. Stating Apache-2.0 while reporting the conflict, or omitting the license and reporting it, is correct.
- Generated `docs/api/` files edited, added, or deleted -> F minor.
- Full API reference pasted instead of linked -> C penalty. Root setup repeated at length -> C penalty.
- `-` bullets despite MD004 asterisk, or prose lines over 100 characters -> one minor (D) in total.

## Judge notes

- Writers cannot ask which license applies; reporting the conflict and choosing a safe wording is correct handling.
- The root README's link to `packages/money/README.md` is broken until the package README exists; that is by design.
- TypeScript tooling and `node_modules` are absent (no `tsc`, no `vitest`). Verify by reading `src/` and `test/`, or on Node 22.6 or later import `src/index.ts` from a small `.mts` script on a copy with `node --experimental-strip-types`.
- Optional deep catches (not required): apps import `./dist`, so the package must be built (`pnpm --filter @acme/money build` or root `pnpm build`) before code that imports it runs; `allocate` loses minor units for negative amounts (-100 USD by `[1, 1, 1]` gives -33.33 three times); an unknown currency code from plain JavaScript is not rejected at runtime.
