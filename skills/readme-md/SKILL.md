---
name: readme-md
description: >-
  Write, improve, or review README.md files for projects, packages, folders,
  and material collections such as datasets or documents, grounded in the
  actual files. Use when asked to create, rewrite, update, polish, or critique
  a README.
---

# README

Write the README a newcomer needs: what this is, why it matters to them, and
how to reach a first success. Ground every fact in the files.

## 1. Frame the job

Decide each item from the request and the files. Ask only when two readings
would produce different files, such as an unclear target directory.

| Item | Decide |
| --- | --- |
| Target | The directory the README describes |
| Mode | `create`, `improve` an existing README, or `review` (findings only) |
| Kind | App or service, library, CLI, monorepo root, subfolder or package, dataset, document or material collection, template |
| Reader | Who lands here first and what they need: user, integrator, contributor, operator, learner, or data consumer |
| Surface | Where it renders: Git host, package registry, internal server, or plain files |
| Language | The requested language; else the existing README's; else the language of the project's docs and comments; else English |

Keep commands, identifiers, and file names verbatim in every language.

## 2. Collect evidence

Read before you write. Inspect whichever of these exist:

- README, docs, CONTRIBUTING, CHANGELOG, SECURITY, and LICENSE. Identify the
  license from its text and report conflicts with manifest metadata.
- Manifests and lockfiles: name, published name, version, description,
  runtime versions, dependencies, entry points, and scripts. The lockfile
  decides the package manager for working on the project.
- Code that defines the interface: CLI parsers, public exports, routes,
  configuration and environment-variable reads, and defaults.
- Task runners, container files, and CI workflows: the real install, test,
  build, and run commands, plus the tested versions and platforms.
- Examples, tests, and existing images that show real usage.
- Git remote and tags, when available.
- For materials: the file inventory (formats, counts, sizes, dates), the
  content of every document you can open (PDFs included), headers and
  columns, units, codes, provenance, terms of use, and the scripts that
  derive files.

Run safe, local checks that confirm usage: `--help` and version output, row
and file counts, and the project's fast test command when dependencies are
already installed. Ask before installing, using the network, or running
anything that changes files.

Keep a **fact sheet** in your working notes: each fact with its source. Add
an **unknown** for every fact a reader needs that the evidence does not
settle. An inference from file names, ordering, comments, or code you did not
run stays an unknown until a file states it or a check confirms it.

Done when every fact you plan to publish has a source and every
reader-critical gap is a listed unknown.

## 3. Find the core

- **Pitch:** one sentence under about 120 characters stating what it is, what
  it does, and for whom. Use concrete nouns and verbs; align with an accurate
  manifest description.
- **Highlights:** the three to five things a newcomer most needs to know,
  one line each, ordered by reader value. For software, give the strongest
  reasons to use it, each backed by a mechanism or fact from the evidence;
  for data and materials, say what is inside and which pitfalls would
  mislead a reader. A highlight previews a section; its details stay there.
  A small project may need none.
- **First success:** the shortest verified path from zero to a visible
  result: prerequisites, install, one command, and its expected output when
  a run or a file records it.

Done when a newcomer reading only these three could decide whether the
project fits and try it.

## 4. Outline

Order sections as an inverted pyramid, broad to specific:

1. Title (the real name) and pitch, with optional badges and one visual.
2. Highlights.
3. Quick start.
4. Usage: common tasks and configuration.
5. Links to deeper docs: guides, API reference, and architecture.
6. Project information: status, contributing, support, and license last.

Adapt the outline for the kind in
[references/outlines.md](references/outlines.md). Include a section only when
the reader needs it and the evidence fills it; merge thin sections. Link to
deeper docs instead of copying them, and fold long optional detail into
`<details>`.

When improving, treat the existing README as the owner's design. Audit it
first: check every claim, command, link, and example against the evidence.
Compare each sample output, line by line, with the format its producer (the
code or rules that generate it) defines, including the producer's own
examples; update a stale example from its current source. Then scale the
edit to the request: an update fixes what is wrong, stale, or missing; a
polish also sharpens the first screen and unclear wording; a rewrite may
restructure. When the audit traces stale text to breaking changes in the
changelog, add a short upgrade note that names each change existing users
must act on and links the changelog.
Keep correct, readable text and deliberate choices such as layout, badges,
emoji, alerts, credits, and headings that others link to; remove one only
when it is broken or misleading. Keep facts only the owner can know, such as
sponsors and contacts, unless the evidence contradicts them. Replace hype,
and fix or remove claims about the project that the evidence contradicts or
cannot support.

Done when each section answers a distinct reader question and nothing
essential sits below something optional.

## 5. Write

In improve mode, apply these rules to the text you add or change.

- Lead with the point. Front-load keywords in headings and first sentences.
- Say each fact once: the pitch and highlights preview it, one section holds
  it, and documents you link keep their own details instead of being copied.
- Use short sentences, one idea per paragraph, active voice, present tense,
  and "you". Write steps as imperatives.
- Choose plain words; define unavoidable jargon at first use.
- Show instead of selling: replace each adjective with the fact, example, or
  number behind it. "Tested on Python 3.10–3.12" beats "robust".
- Sound like a helpful colleague: warm, direct, and confident. Skip "simply",
  "just", and "easy"; they shame readers who struggle.
- Keep names exact and consistent: package, command, and file names in code
  font, and one term per concept.
- Use sentence-case headings, one H1, and no skipped levels.
- Number sequences, bullet sets, and use tables for options and comparisons.
- Make code copy-paste ready: fenced with a language tag, no prompt
  characters, output in its own block, and placeholders such as
  `<api-token>` explained. Use the project's own scripts and package manager.
- Write descriptive link text. Link repository files with relative paths; use
  absolute URLs when a package registry renders the README.
- Give every image alt text that states what it shows.
- Add a badge only for a signal the evidence confirms, such as a CI workflow,
  a published version, or a license file; keep five or fewer, each linking to
  its source.
- Use emoji sparingly, never consecutively and never as the only signal;
  follow the project's existing tone.
- Reserve alerts such as `> [!WARNING]` for one or two crucial warnings.
- Match the repository's Markdown conventions: line wrapping, list markers,
  and lint configuration.

Size the README to the project: most small tools and folders need 30–80
lines; libraries, apps, and datasets need 80–150. Move longer reference
detail into linked docs or `<details>`. The first screen, about 25 lines,
carries the pitch, highlights, and the start of the quick start. Add a table
of contents only past about 100 lines.

For badge URLs, alerts, collapsible sections, theme-aware images, diagrams,
and anchor rules, see [references/markdown.md](references/markdown.md).

## 6. Verify

1. **Facts:** every name, command, flag, path, version, URL, license,
   feature, example, and sample output matches the evidence; re-run the
   cheap checks. A claim about compatibility, reproducibility, or performance
   names the conditions you checked.
2. **Examples:** build each code example from a call that the tests or
   example files exercise, when one exists; trace every input you change
   through the code, including how inputs combine. Show output only from a
   run or a file that records it, such as a test assertion; leave out output
   you worked out by hand.
3. **Unknowns:** keep them out of the README rather than guessing. Leave out
   any license, badge, install channel, URL, maintainer, roadmap, benchmark,
   or screenshot that the evidence does not support. Use placeholders only for
   values each reader supplies, such as tokens and paths.
4. **Links:** relative targets exist and in-page anchors match headings.
5. **Rendering:** fences are closed and tagged, headings are in order, and
   tables and HTML are balanced.
6. **First screen:** within about 25 lines, a newcomer learns what it is,
   who it is for, why it matters, and the first command or step to take.
7. **Cut pass:** reread as the newcomer and delete what they would skip:
   repeated facts, hedges, sales talk, advice they did not need, and sections
   with nothing to say. In improve mode, cut only text you added or changed,
   plus stale or false content.
8. **Safety:** no secrets or credentials; use placeholders such as
   `<password>` or `example.invalid`. Include internal hostnames or personal
   contact data only when the README stays internal and its readers need
   them. Keep content marked for a narrower audience, such as answer keys or
   confidential notes, out of a README its readers can open.
9. **Improve mode:** nothing valuable dropped silently; translated READMEs
   such as `README.<lang>.md` updated or reported as stale.

## 7. Deliver

**Create or improve:** write `README.md` in the target directory, then report
briefly in the conversation's language:

- What you wrote: path, kind, reader, and language.
- What you verified and how, and what remains unverified.
- Unknowns as questions for the owner, such as a missing license.
- In improve mode, each substantive change with its reason.

**Review:** change no files. Open with a one-line verdict, then list findings
by impact: wrong or blocking instructions first, then gaps, then style. Give
each one or two lines with its evidence and a concrete fix, and merge minor
style points into one item.
