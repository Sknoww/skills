---
name: probe-feature
description: Thin orchestrator that runs probe-product, probe-design, probe-technical for a new feature, then write-prd, write-design-brief, and write-tech-spec. The friendly front door — composes sub-skills, contains no probing logic of its own. Use when starting work on a new feature.
---

# probe-feature

Thin orchestrator. Composes the six discover + synthesize sub-skills for a new feature. Does NOT contain probing logic of its own — if probing behavior needs to change, fix the sub-skill.

## Preconditions

None. Working directory should be the user's project repo.

## Procedure

### 1. Get the feature identity

Ask:
> "Feature name? (Short human label, e.g. 'Dark mode toggle')"

Then:
> "Slug? (lowercase-hyphenated, e.g. 'dark-mode-toggle')"

Create `docs/features/<slug>/` if it does not exist.

### 2. Run the three probes (sequentially in this session — they can't be truly parallel because they share the user)

For each:
- Invoke the sub-skill (`probe-product`, then `probe-design`, then `probe-technical`).
- Pass the slug through.
- After each, confirm the artifact was written before continuing.

### 3. Gate check

After all three probes:
- Read each probe's Open questions section.
- If any have unresolved items, surface them as a single list:
  > "Unresolved items remain. Address these by re-running the relevant probe-* skill, then re-invoke probe-feature (or write-prd / write-design-brief / write-tech-spec directly).
  >
  > <list of open questions per probe>"
- Stop. Do not proceed to synthesis.

### 4. Run synthesis

In order:
- `write-prd`
- `write-design-brief`
- `write-tech-spec` (depth follows probe-technical's signal)

### 5. Report

> "Feature probe complete. Bundle at `docs/features/<slug>/`:
> - probe-product.md
> - probe-design.md
> - probe-technical.md
> - prd.md
> - design-brief.md
> - tech-spec.md (depth: <full | module-map-only>)
>
> Next: `slice-issues` to break this into vertical-slice issues."

## Rules

- This skill is intentionally thin. It does NOT ask its own questions — every question comes from a sub-skill.
- Do NOT skip probes even if you "already know" the answers — the artifacts are downstream dependencies.
- Do NOT proceed to synthesis if probes have unresolved Open questions.

(END probe-feature)
