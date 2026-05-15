---
name: write-design-brief
description: Translates probe-design + PRD into an actionable design brief with screen-by-screen states, design tokens, and motion specs at docs/features/<slug>/design-brief.md. Use after the PRD is written.
---

# write-design-brief

Synthesize `probe-design.md` and `prd.md` into a design brief that issues can reference by section in their UX slices.

## Preconditions (HARD)

Both must exist at `docs/features/<slug>/`:
- `prd.md`
- `probe-design.md`

`docs/design-system.md` must exist (scaffolded by `probe-design` if needed).

If any are missing, abort with a pointer to the upstream skill.

## Procedure

### 1. Resolve slug

The slug may be the first argument (e.g. `/write-design-brief dark-mode-toggle`). Ask for it only if not provided.

### 2. Read inputs

- `docs/features/<slug>/prd.md`
- `docs/features/<slug>/probe-design.md`
- `docs/design-system.md`

### 3. Fill the brief

Read the bundled `DESIGN-BRIEF-template.md`. Fill each section:
- **Tone & references** ← probe-design Tone section
- **Key user moments** ← probe-design moments, with each fleshed out into a screen-level description
- **Screen-by-screen states** ← for each moment, write empty/loading/error/success entries. Pull state philosophy from probe-design.
- **Design tokens used** ← cross-reference `docs/design-system.md` and list sections referenced
- **Microcopy direction** ← probe-design Microcopy voice
- **Motion** ← probe-design Motion philosophy

### 4. Write

Write `docs/features/<slug>/design-brief.md`.

### 5. Report

> "Wrote `docs/features/<slug>/design-brief.md`.
>
> Next — run: `/write-tech-spec <slug>`"

## Rules

- Section headers must be stable — issues will reference them by name (e.g., "design-brief.md §Screen-by-screen states > signup").
- Reference design tokens by their section in `docs/design-system.md` — don't inline tokens.
- Each key moment must have explicit empty / loading / error / success states. If a state doesn't apply, say so explicitly ("N/A — never empty in this flow").
