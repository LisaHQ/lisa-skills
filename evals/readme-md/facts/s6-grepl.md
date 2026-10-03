# Fact sheet: s6-grepl

Request: "Make a nice, professional README for this repo." (create mode; thin evidence)
Kind: tiny CLI tool (Go). Reader: developers who might use or build it.

## Ground truth (everything that exists)

- `go.mod`: module `github.com/example-org/grepl`, `go 1.22`. `main.go` (~40 lines). `.gitignore` ignores the built binary. Nothing else: **no LICENSE, no tests, no CI, no releases, no git history, no docs**.
- Behavior: reads **standard input only** (no file arguments) and prints lines matching a Go regular expression (**RE2 syntax**: no backreferences/lookarounds).
- Usage: `grepl [-i] [-v] PATTERN < input`; exactly one PATTERN argument (else usage message, exit 2).
- Flags: `-i` case-insensitive (prepends `(?i)`), `-v` invert (print non-matching lines). Flags must precede PATTERN (Go `flag` stops at the first non-flag).
- Exit codes: **0** if any line printed, **1** if none, **2** on usage error or invalid pattern.
- Limitation (deep catch, optional): `bufio.Scanner` default buffer means lines longer than 64 KiB stop the scan silently (scanner error not checked).
- Build/install: `go build` (produces `grepl`), `go install .` from a clone; `go install github.com/example-org/grepl@latest` works only if the module is actually published at that path (unverified).

## Core points a strong README highlights

1. One-line: minimal grep-like filter for stdin using Go regex.
2. Usage with flags and a pipeline example; exit codes for scripting.
3. Build/install from source (Go 1.22+).
4. Honest scope: small; stdin only.

## Traps (judge explicitly)

- Inventing a license (MIT etc.) or a License section claiming one -> major. Correct handling: omit and flag to the requester.
- Inventing features: file arguments, recursive search, color output, context lines, `-n`, `-c`, etc. -> major each.
- Invented badges (CI, Go Report Card, coverage, release) -> major. A static Go-version badge is acceptable.
- Invented sections with fabricated content: roadmap, benchmarks, changelog, contributors, FAQ -> major (fabricated) or C penalty (empty boilerplate).
- Claiming PCRE/grep-compatible regex -> minor.
- Over-long README for a 40-line tool -> C penalty.
- "Professional" should not mean padding: a short, accurate, well-formatted README should win.

## Judge notes

- `main.go` and `go.mod` are all the evidence there is; Go may not be installed, so emulate behavior from the code when you cannot build it.
