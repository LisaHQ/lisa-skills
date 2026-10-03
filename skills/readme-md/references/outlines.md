# Outlines by kind

Pick the closest kind; combine two when the project spans them, such as a
library that ships a CLI. Bracketed sections are optional: include them only
when the evidence fills them.

## App or service

1. Title, pitch, [badges], [screenshot or short demo of the main screen]
2. Highlights: what users can do
3. Quick start: prerequisites with versions; get the code; configure (copy the
   example environment file, name the required variables); run with one
   command; where to open it (URL, port) and what you should see
4. Configuration: table of variable, required, default, and purpose
5. Development: test, lint, and build commands; [project layout as an
   annotated tree, two levels at most]
6. [Deployment: only what the repository automates or documents]
7. [Architecture: a paragraph or small diagram when several components talk]
8. [Troubleshooting: known problems with fixes]
9. Contributing, support, license

## Library or package

1. Title, pitch, [badges: version, CI, license]
2. Highlights
3. Install: the published name with the project's package manager, or
   from-source steps when it is not published
4. Quick example: 5–15 lines that run as written, with the result
5. Usage: two to four common tasks; key options with defaults
6. [API overview: main exports, one line each, linking the full reference]
7. Compatibility: runtime versions, environments, module formats, types
8. [Upgrading: breaking changes in the current major, linking the changelog]
9. Contributing, license

## CLI tool

1. Title, pitch, [demo: terminal recording or an example with output]
2. Highlights
3. Install: each supported channel; confirm with the version flag
4. Usage: a synopsis line; three to five task-based examples (goal, command,
   output)
5. Options: table of the main flags from `--help`, linking the full help
6. [Configuration: environment variables, config files, and precedence]
7. [Exit codes: when scripts depend on them]
8. Contributing, license

## Monorepo root

1. Title, pitch for the whole system
2. [Architecture: how the parts connect, with ports]
3. Repository map: table of path, what it is, and a link to its README
4. Quick start for the whole system: prerequisites; one command to run
   everything
5. Common tasks: workspace-level commands
6. [Conventions: where new code goes, how to add a package]
7. Contributing, license

## Subfolder or package in a larger repository

1. Title (folder or package name) and purpose; where it fits, linking the
   root README
2. [Status (stable, experimental, deprecated) and owners, when stated]
3. Usage from the rest of the repository: import path or commands, and the
   directory to run them from
4. Key files: a short annotated list
5. Testing this part

Link up to the root README instead of repeating it.

## Dataset

1. Title and description: what was measured or collected, where, when, and
   by whom
2. Key facts: coverage (ISO 8601 dates, places), size (files, rows), version,
   and the pitfalls that would skew results, such as missing-value codes,
   time zones, units, and corrections already applied
3. Files: table or tree of file, contents, format, and rows or size
4. Data dictionary: table of column, type, unit, meaning, allowed values, and
   missing-value codes
5. Methods: source and provenance, collection, processing (scripts that
   derive files and their rules), quality flags, known limitations and biases
6. Usage: a loading snippet that handles the pitfalls
7. License or terms, citation, contact

## Document or material collection

Training and course material, design assets, reports, and research material.

1. Title, purpose, and audience
2. Contents: table in the order of use: item, what it is, format, when to use
   it
3. How to use: recommended path, prerequisites, time needed when stated
4. Conventions: naming, versions and dates, where updates go
5. Access and rights: license, usage restrictions, confidentiality
6. Contact or help

Describe files you cannot open by name, type, and size only, and list their
contents as unknowns.

## Template or starter

1. Title, pitch: what a new project gets
2. Create a project: the exact command or "Use this template" flow
3. Customize: checklist of names, settings, and files to change
4. Included tooling: scripts and what each does
5. Next steps, license
