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

### 1.5. Promote concept if present

Check whether `docs/concepts/<slug>.md` exists.

- **If it does not exist:** proceed without a concept doc. The user came in raw; that's allowed.
- **If it exists**, read it and inspect the `Status:` field:
  - `Status: ready-to-probe` — **promote** the concept: move `docs/concepts/<slug>.md` to `docs/features/<slug>/concept.md` (create `docs/features/<slug>/` first if needed). After the move, the concept no longer lives in `docs/concepts/`. Report:
    > "Promoted `docs/concepts/<slug>.md` → `docs/features/<slug>/concept.md`."
    Then pass the concept path (`docs/features/<slug>/concept.md`) to each sub-skill below.
  - `Status: shaping` — refuse:
    > "Concept at `docs/concepts/<slug>.md` has Status `shaping`. Re-run `shape-feature` on this slug and set Status to `ready-to-probe` before probing."
    Stop.
  - `Status: shelved` — refuse:
    > "Concept at `docs/concepts/<slug>.md` has Status `shelved`. Either edit the file to flip Status to `ready-to-probe` first, or pick a different slug."
    Stop.
  - Missing or unrecognized Status — refuse:
    > "Concept at `docs/concepts/<slug>.md` has no recognizable `Status:` field. Re-run `shape-feature` to fix it."
    Stop.

### 2. Run the three probes (sequentially in this session — they can't be truly parallel because they share the user)

For each:
- Invoke the sub-skill (`probe-product`, then `probe-design`, then `probe-technical`).
- Pass the slug through. If a concept was promoted in step 1.5, also pass the concept path (`docs/features/<slug>/concept.md`).
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
- Promotion is one-way: once `docs/concepts/<slug>.md` is moved into `docs/features/<slug>/concept.md`, do not write back to `docs/concepts/`. Revisions to the concept after promotion happen in-place in the feature folder.

(END probe-feature)
