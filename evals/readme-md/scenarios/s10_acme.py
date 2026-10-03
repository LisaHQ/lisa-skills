"""Scenario s10: package README inside a pnpm monorepo subfolder (create mode, subfolder kind)."""
from fixture import w, git_init

ROOT = "s10-acme-platform"


def build(base):
    r = base / ROOT
    # Root of the monorepo: its README already links the missing package README.
    w(r / "package.json", '''\
{
  "name": "acme-platform",
  "private": true,
  "packageManager": "pnpm@9.12.0",
  "engines": {
    "node": ">=20"
  },
  "scripts": {
    "build": "pnpm -r build",
    "test": "pnpm -r test",
    "docs": "pnpm -r docs"
  }
}
''')
    w(r / "pnpm-workspace.yaml", "packages:\n  - apps/*\n  - packages/*\n")
    w(r / "pnpm-lock.yaml",
      "lockfileVersion: '9.0'\n\nimporters:\n\n  .: {}\n\n  apps/checkout: {}\n\n  packages/money: {}\n")
    w(r / ".nvmrc", "20\n")
    w(r / ".markdownlint.jsonc", '''\
{
  // House style for hand-written Markdown; generated API docs are ignored.
  "MD004": { "style": "asterisk" },
  "MD013": { "line_length": 100, "code_blocks": false, "tables": false }
}
''')
    w(r / ".markdownlintignore", "packages/*/docs/api/\n")
    w(r / ".github/CODEOWNERS", "/packages/money/ @acme/payments-team\n/apps/checkout/ @acme/storefront-team\n")
    w(r / "LICENSE", '''\
                                 Apache License
                           Version 2.0, January 2004
                        http://www.apache.org/licenses/

   TERMS AND CONDITIONS FOR USE, REPRODUCTION, AND DISTRIBUTION

   [Remaining text of the Apache License 2.0 omitted in this fixture.]

   Copyright 2024 Acme Retail Ltd.
''')
    w(r / "README.md", '''\
# Acme platform

Code for the Acme online store: the checkout app and the packages it shares.

## Repository map

| Path | What it is |
| --- | --- |
| [`apps/checkout`](apps/checkout) | Checkout web app |
| [`packages/money`](packages/money/README.md) | Money amounts and currency math |

## Set up

You need Node.js 20 and pnpm 9.

```bash
pnpm install
pnpm test
```

`pnpm test` runs the tests of every package.

## License

Apache-2.0. See [LICENSE](LICENSE).
''')
    # The package the request targets.
    w(r / "packages/money/package.json", '''\
{
  "name": "@acme/money",
  "version": "0.2.0",
  "private": true,
  "description": "Exact money amounts in integer minor units, with safe allocation and formatting.",
  "type": "module",
  "main": "./dist/index.js",
  "types": "./dist/index.d.ts",
  "scripts": {
    "build": "tsup src/index.ts --format esm --dts",
    "test": "vitest run",
    "docs": "typedoc"
  },
  "license": "MIT",
  "devDependencies": {
    "tsup": "^8.3.0",
    "typedoc": "^0.26.7",
    "typedoc-plugin-markdown": "^4.2.9",
    "typescript": "^5.6.0",
    "vitest": "^2.1.0"
  }
}
''')
    w(r / "packages/money/typedoc.json", '''\
{
  "entryPoints": ["src/index.ts"],
  "out": "docs/api",
  "plugin": ["typedoc-plugin-markdown"]
}
''')
    w(r / "packages/money/src/index.ts", '''\
/** ISO 4217 codes this package supports, with their minor units (digits after the decimal point). */
export const MINOR_UNITS = { VND: 0, USD: 2, EUR: 2 } as const;
export type Currency = keyof typeof MINOR_UNITS;

/** An exact amount: `minor` is an integer count of the currency's minor unit (cents for USD). */
export interface Money {
  readonly minor: bigint;
  readonly currency: Currency;
}

export class CurrencyMismatchError extends Error {
  constructor(a: Currency, b: Currency) {
    super(`Cannot combine ${a} and ${b}`);
    this.name = "CurrencyMismatchError";
  }
}

/**
 * Parse a decimal string such as "19.99" into Money.
 * Throws RangeError when the string has more decimals than the currency allows ("1.005" USD).
 */
export function money(amount: string, currency: Currency): Money {
  const digits = MINOR_UNITS[currency];
  const match = /^(-?)(\\d+)(?:\\.(\\d+))?$/.exec(amount);
  if (!match) throw new RangeError(`Not a decimal amount: ${amount}`);
  const [, sign, whole, frac = ""] = match;
  if (frac.length > digits) throw new RangeError(`${currency} allows ${digits} decimals: ${amount}`);
  const minor = BigInt(whole + frac.padEnd(digits, "0")) * (sign ? -1n : 1n);
  return { minor, currency };
}

/** Add amounts of the same currency; throws CurrencyMismatchError otherwise. */
export function add(a: Money, b: Money): Money {
  if (a.currency !== b.currency) throw new CurrencyMismatchError(a.currency, b.currency);
  return { minor: a.minor + b.minor, currency: a.currency };
}

/**
 * Split an amount by integer ratios without losing a minor unit.
 * Leftover minor units go one each to the first parts: allocate(money("100", "USD"), [1, 1, 1])
 * gives 33.34, 33.33, 33.33.
 */
export function allocate(m: Money, ratios: number[]): Money[] {
  const total = ratios.reduce((s, r) => s + BigInt(r), 0n);
  if (total <= 0n) throw new RangeError("ratios must sum to more than zero");
  const parts = ratios.map((r) => (m.minor * BigInt(r)) / total);
  let rest = m.minor - parts.reduce((s, p) => s + p, 0n);
  for (let i = 0; rest > 0n; i++, rest--) parts[i] += 1n;
  return parts.map((minor) => ({ minor, currency: m.currency }));
}

/** Format for display with Intl.NumberFormat, for example format(money("1250000", "VND"), "vi-VN"). */
export function format(m: Money, locale = "en-US"): string {
  const digits = MINOR_UNITS[m.currency];
  const value = Number(m.minor) / 10 ** digits;
  return new Intl.NumberFormat(locale, { style: "currency", currency: m.currency }).format(value);
}
''')
    w(r / "packages/money/test/money.test.ts", '''\
import { describe, expect, it } from "vitest";
import { add, allocate, CurrencyMismatchError, money } from "../src/index.js";

describe("money", () => {
  it("parses decimal strings into minor units", () => {
    expect(money("19.99", "USD").minor).toBe(1999n);
    expect(money("1250000", "VND").minor).toBe(1250000n);
  });
  it("rejects extra decimals", () => {
    expect(() => money("1.005", "USD")).toThrow(RangeError);
  });
  it("refuses to add different currencies", () => {
    expect(() => add(money("1", "USD"), money("1", "EUR"))).toThrow(CurrencyMismatchError);
  });
  it("allocates leftovers to the first parts", () => {
    const parts = allocate(money("100", "USD"), [1, 1, 1]).map((p) => p.minor);
    expect(parts).toEqual([3334n, 3333n, 3333n]);
  });
});
''')
    # Generated reference docs (typedoc-plugin-markdown output), committed.
    w(r / "packages/money/docs/api/README.md", '''\
**@acme/money**

***

# @acme/money

## Classes

- [CurrencyMismatchError](classes/CurrencyMismatchError.md)

## Interfaces

- [Money](interfaces/Money.md)

## Type Aliases

- [Currency](type-aliases/Currency.md)

## Variables

- [MINOR\\_UNITS](variables/MINOR_UNITS.md)

## Functions

- [add](functions/add.md)
- [allocate](functions/allocate.md)
- [format](functions/format.md)
- [money](functions/money.md)
''')
    for name, sig in [
        ("add", "add(a: Money, b: Money): Money"),
        ("allocate", "allocate(m: Money, ratios: number[]): Money[]"),
        ("format", 'format(m: Money, locale: string = "en-US"): string'),
        ("money", "money(amount: string, currency: Currency): Money"),
    ]:
        w(r / f"packages/money/docs/api/functions/{name}.md", f'''\
[**@acme/money**](../README.md)

***

# Function: {name}()

> **{sig}**

Defined in: [index.ts](../../../src/index.ts)
''')
    w(r / "packages/money/docs/api/interfaces/Money.md", '''\
[**@acme/money**](../README.md)

***

# Interface: Money

## Properties

### currency

> `readonly` **currency**: `Currency`

### minor

> `readonly` **minor**: `bigint`
''')
    w(r / "packages/money/docs/api/classes/CurrencyMismatchError.md", '''\
[**@acme/money**](../README.md)

***

# Class: CurrencyMismatchError

Defined in: [index.ts](../../../src/index.ts)

## Extends

- `Error`

## Constructors

### Constructor

> **new CurrencyMismatchError**(`a`, `b`): `CurrencyMismatchError`
''')
    w(r / "packages/money/docs/api/type-aliases/Currency.md", '''\
[**@acme/money**](../README.md)

***

# Type Alias: Currency

> **Currency** = keyof *typeof* [`MINOR_UNITS`](../variables/MINOR_UNITS.md)

Defined in: [index.ts](../../../src/index.ts)
''')
    w(r / "packages/money/docs/api/variables/MINOR_UNITS.md", '''\
[**@acme/money**](../README.md)

***

# Variable: MINOR\\_UNITS

> `const` **MINOR\\_UNITS**: `object`

Defined in: [index.ts](../../../src/index.ts)

ISO 4217 codes this package supports, with their minor units (digits after the decimal point).

## Type Declaration

### EUR

> `readonly` **EUR**: `2` = `2`

### USD

> `readonly` **USD**: `2` = `2`

### VND

> `readonly` **VND**: `0` = `0`
''')
    # A consumer that shows real usage from the rest of the repository.
    w(r / "apps/checkout/package.json", '''\
{
  "name": "@acme/checkout",
  "private": true,
  "version": "0.5.0",
  "type": "module",
  "dependencies": {
    "@acme/money": "workspace:*"
  }
}
''')
    w(r / "apps/checkout/src/cart.ts", '''\
import { add, format, money, type Money } from "@acme/money";

export function cartTotal(lines: { price: string; qty: number }[]): string {
  let total: Money = money("0", "VND");
  for (const line of lines) {
    for (let i = 0; i < line.qty; i++) total = add(total, money(line.price, "VND"));
  }
  return format(total, "vi-VN");
}
''')
    w(r / ".gitignore", "node_modules/\ndist/\n")
    git_init(r, remote="https://github.com/example-org/acme-platform.git")
