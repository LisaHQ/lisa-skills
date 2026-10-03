"""Scenario s2: TypeScript library 'fetchkit' with a stale v1 README (improve mode)."""
from fixture import w, git_init

ROOT = "s2-fetchkit"


def build(base):
    r = base / ROOT
    w(r / "package.json", '''\
{
  "name": "@example-org/fetchkit",
  "version": "2.1.0",
  "description": "Tiny fetch wrapper with retries, timeouts, and typed JSON responses.",
  "type": "module",
  "main": "./dist/index.cjs",
  "module": "./dist/index.js",
  "types": "./dist/index.d.ts",
  "exports": {
    ".": {
      "types": "./dist/index.d.ts",
      "import": "./dist/index.js",
      "require": "./dist/index.cjs"
    }
  },
  "files": ["dist"],
  "sideEffects": false,
  "engines": {
    "node": ">=18"
  },
  "packageManager": "pnpm@9.12.0",
  "scripts": {
    "build": "tsup src/index.ts --format esm,cjs --dts",
    "test": "vitest run",
    "lint": "eslint src",
    "prepublishOnly": "pnpm build"
  },
  "repository": {
    "type": "git",
    "url": "git+https://github.com/example-org/fetchkit.git"
  },
  "license": "MIT",
  "devDependencies": {
    "eslint": "^9.12.0",
    "tsup": "^8.3.0",
    "typescript": "^5.6.0",
    "vitest": "^2.1.0"
  }
}
''')
    w(r / "pnpm-lock.yaml", '''\
lockfileVersion: '9.0'

settings:
  autoInstallPeers: true
  excludeLinksFromLockfile: false

importers:

  .:
    devDependencies:
      eslint:
        specifier: ^9.12.0
        version: 9.12.0
      tsup:
        specifier: ^8.3.0
        version: 8.3.0(typescript@5.6.3)
      typescript:
        specifier: ^5.6.0
        version: 5.6.3
      vitest:
        specifier: ^2.1.0
        version: 2.1.2
''')
    w(r / "src/index.ts", '''\
import { backoffDelay, retryAfterMs } from "./backoff.js";

export interface ClientOptions {
  /** Prefix for relative request paths, for example "https://api.example.com/v1". */
  baseUrl?: string;
  /** Extra attempts after the first failure. Default: 2. */
  retries?: number;
  /** HTTP statuses that trigger a retry. Default: 408, 425, 429, 500, 502, 503, 504. */
  retryOn?: number[];
  /** Also retry POST and PATCH requests. Default: false (only idempotent methods retry). */
  retryNonIdempotent?: boolean;
  /** Per-attempt timeout in milliseconds. Default: 10000. */
  timeoutMs?: number;
  /** Headers sent with every request. */
  headers?: Record<string, string>;
}

/** Thrown for non-2xx responses after all retries, and for timeouts. */
export class FetchkitError extends Error {
  constructor(
    message: string,
    readonly status: number | undefined,
    readonly url: string,
    readonly body: unknown,
  ) {
    super(message);
    this.name = "FetchkitError";
  }
}

const DEFAULT_RETRY_ON = [408, 425, 429, 500, 502, 503, 504];
const IDEMPOTENT = new Set(["GET", "HEAD", "PUT", "DELETE", "OPTIONS"]);

export function createClient(options: ClientOptions = {}) {
  const {
    baseUrl = "",
    retries = 2,
    retryOn = DEFAULT_RETRY_ON,
    retryNonIdempotent = false,
    timeoutMs = 10_000,
    headers = {},
  } = options;

  async function request<T>(method: string, path: string, body?: unknown, init: RequestInit = {}): Promise<T> {
    const url = baseUrl ? new URL(path, baseUrl).toString() : path;
    const canRetry = retryNonIdempotent || IDEMPOTENT.has(method);
    for (let attempt = 0; ; attempt++) {
      let response: Response;
      try {
        response = await fetch(url, {
          ...init,
          method,
          headers: { "content-type": "application/json", ...headers, ...(init.headers as Record<string, string>) },
          body: body === undefined ? undefined : JSON.stringify(body),
          signal: AbortSignal.timeout(timeoutMs),
        });
      } catch (error) {
        // Network failures and timeouts.
        if (canRetry && attempt < retries) {
          await sleep(backoffDelay(attempt));
          continue;
        }
        throw new FetchkitError(`Request failed: ${String(error)}`, undefined, url, undefined);
      }
      if (response.ok) {
        return (response.status === 204 ? undefined : await response.json()) as T;
      }
      if (canRetry && attempt < retries && retryOn.includes(response.status)) {
        await sleep(retryAfterMs(response) ?? backoffDelay(attempt));
        continue;
      }
      const errorBody = await response.text();
      throw new FetchkitError(`HTTP ${response.status} for ${method} ${url}`, response.status, url, errorBody);
    }
  }

  return {
    get: <T>(path: string, init?: RequestInit) => request<T>("GET", path, undefined, init),
    post: <T>(path: string, body?: unknown, init?: RequestInit) => request<T>("POST", path, body, init),
    put: <T>(path: string, body?: unknown, init?: RequestInit) => request<T>("PUT", path, body, init),
    patch: <T>(path: string, body?: unknown, init?: RequestInit) => request<T>("PATCH", path, body, init),
    delete: <T>(path: string, init?: RequestInit) => request<T>("DELETE", path, undefined, init),
  };
}

function sleep(ms: number) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}
''')
    w(r / "src/backoff.ts", '''\
/** Exponential backoff with full jitter: random delay in [0, 200 ms * 2^attempt), capped at 5 s. */
export function backoffDelay(attempt: number): number {
  return Math.random() * Math.min(5_000, 200 * 2 ** attempt);
}

/** Honor Retry-After (seconds or HTTP date) on 429 and 503 responses, capped at 30 s. */
export function retryAfterMs(response: Response): number | undefined {
  if (response.status !== 429 && response.status !== 503) return undefined;
  const header = response.headers.get("retry-after");
  if (!header) return undefined;
  const seconds = Number(header);
  const ms = Number.isFinite(seconds) ? seconds * 1000 : Date.parse(header) - Date.now();
  return Number.isFinite(ms) ? Math.min(Math.max(ms, 0), 30_000) : undefined;
}
''')
    w(r / "test/client.test.ts", '''\
import { afterEach, describe, expect, it, vi } from "vitest";
import { createClient, FetchkitError } from "../src/index.js";

afterEach(() => vi.restoreAllMocks());

describe("createClient", () => {
  it("resolves relative paths against baseUrl and parses JSON", async () => {
    const fetchMock = vi.spyOn(globalThis, "fetch").mockResolvedValue(Response.json([{ id: 1 }]));
    const api = createClient({ baseUrl: "https://api.example.com/v1/" });
    await expect(api.get<{ id: number }[]>("users")).resolves.toEqual([{ id: 1 }]);
    expect(fetchMock.mock.calls[0][0]).toBe("https://api.example.com/v1/users");
  });

  it("retries GET on 503 and succeeds", async () => {
    vi.spyOn(globalThis, "fetch")
      .mockResolvedValueOnce(new Response("busy", { status: 503 }))
      .mockResolvedValueOnce(Response.json({ ok: true }));
    const api = createClient({ retries: 1 });
    await expect(api.get("https://api.example.com/status")).resolves.toEqual({ ok: true });
  });

  it("does not retry POST by default", async () => {
    const fetchMock = vi.spyOn(globalThis, "fetch").mockResolvedValue(new Response("busy", { status: 503 }));
    const api = createClient();
    await expect(api.post("https://api.example.com/orders", { sku: "A1" })).rejects.toBeInstanceOf(FetchkitError);
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });
});
''')
    w(r / ".github/workflows/test.yml", '''\
name: test

on:
  push:
    branches: [main]
  pull_request:

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        node: [18, 20, 22]
    steps:
      - uses: actions/checkout@v4
      - uses: pnpm/action-setup@v4
      - uses: actions/setup-node@v4
        with:
          node-version: ${{ matrix.node }}
          cache: pnpm
      - run: pnpm install --frozen-lockfile
      - run: pnpm lint
      - run: pnpm test
''')
    w(r / "CHANGELOG.md", '''\
# Changelog

## 2.1.0 - 2024-09-03

- Add `retryNonIdempotent` to retry POST and PATCH requests (off by default).
- Honor `Retry-After` on 429 and 503 responses.
- Add `patch()`.

## 2.0.0 - 2024-06-18

### Breaking changes

- Replace the default `fetchkit` object with `createClient()`; create one client per base URL.
- Rename `timeout` to `timeoutMs`; the default is now 10 seconds per attempt.
- Lower the default `retries` from 3 to 2.
- Remove the in-memory response cache (`cache: true`). Use HTTP caching or your own layer.
- Require Node.js 18 or later (native `fetch`); drop the `node-fetch` dependency.
- Publish as `@example-org/fetchkit`. The unscoped `fetchkit` package is deprecated.

## 1.4.0 - 2023-11-02

- Add the `cache` option.
''')
    w(r / "LICENSE", '''\
MIT License

Copyright (c) 2023 Example Org contributors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
''')
    w(r / "README.md", '''\
# fetchkit

[![npm](https://img.shields.io/npm/v/fetchkit.svg)](https://www.npmjs.com/package/fetchkit)
[![Build Status](https://travis-ci.org/example-org/fetchkit.svg?branch=master)](https://travis-ci.org/example-org/fetchkit)

A tiny, powerful and blazing fast fetch wrapper!!! 🚀🚀🚀

## Features

- ✅ Retries
- ✅ Timeouts
- ✅ Caching
- ✅ Works everywhere (Node 14+, browsers, Deno)

## Install

    npm install fetchkit

## Usage

```
const fetchkit = require('fetchkit')

fetchkit.get('https://api.example.com/users', { retries: 3, timeout: 5000 })
  .then(users => console.log(users))
```

## Options

| Option | Default | Description |
|--------|---------|-------------|
| retries | 3 | Number of retries |
| timeout | 5000 | Timeout in ms |
| cache | false | Cache responses in memory |

## Sponsors

Thanks to [Example Hosting](https://hosting.example.com) for supporting this project.

## Contributors

Thanks to everyone who has contributed! See the [contributors graph](https://github.com/example-org/fetchkit/graphs/contributors).

## License

MIT
''')
    w(r / ".gitignore", "node_modules/\ndist/\ncoverage/\n")
    git_init(r, remote="https://github.com/example-org/fetchkit.git", tag="v2.1.0")
