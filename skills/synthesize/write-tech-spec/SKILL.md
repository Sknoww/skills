---
name: write-tech-spec
description: Translates probe-technical + PRD into a tech spec at docs/features/<slug>/tech-spec.md. Always writes the Module map section (slice-issues depends on it); other sections are conditional on tech-spec depth signal from probe-technical. Use after the PRD is written.
---

# write-tech-spec

Synthesize `probe-technical.md` and `prd.md` into a tech spec. The **Module map section is always written**, even for trivial features — slice-issues depends on it. Other sections are written only when the feature warrants them.

## Preconditions (HARD)

Both must exist at `docs/features/<slug>/`:
- `prd.md`
- `probe-technical.md`

If missing, abort with a pointer to the upstream skill.

## Procedure

### 1. Resolve slug

The slug may be the first argument (e.g. `/write-tech-spec dark-mode-toggle`). Ask for it only if not provided.

### 2. Read inputs

- `docs/features/<slug>/prd.md`
- `docs/features/<slug>/probe-technical.md`

Note the `Tech spec depth signal` from probe-technical: `full` or `module-map-only`.

### 3. Always write Module map

For each existing module touched + each new module, write:
- **Module name**
- **Responsibility** (one sentence)
- **Public surface** (exports — types, functions, components)
- **Internal-only files** (must not be imported from outside)
- **Allowed dependencies** (which other modules it may import from)

Pull from probe-technical Modules touched + Modules new.

### 4. Conditional sections (only if depth signal is `full`)

- **Architecture deltas** — structural changes
- **Data model deltas** — schemas, migrations
- **API deltas** — endpoints, contracts
- **Open technical questions** — items the user has explicitly marked "in flight"

If depth signal is `module-map-only`, write each conditional section with a single line: `No <category> changes — additive within existing modules.`

### 5. Write

Write `docs/features/<slug>/tech-spec.md`.

### 6. Report

> "Wrote `docs/features/<slug>/tech-spec.md` (depth: <full | module-map-only>).
>
> Next — run: `/slice-issues <slug>`"

## Rules

- Module map section is NEVER skipped, even for trivial features.
- A module's public surface should be small and named — avoid "anything in this folder."
- If probe-technical's Verification findings show mismatches, surface them in Module map as comments, not silently.
