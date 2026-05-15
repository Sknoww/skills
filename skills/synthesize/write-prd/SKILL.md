---
name: write-prd
description: Synthesizes probe-product + probe-design + probe-technical into a complete PRD at docs/features/<slug>/prd.md. Refuses to run with unresolved items — they must go back to the relevant probe first. Use after all three probe-* skills have run for a feature.
---

# write-prd

Synthesize the three probe outputs into a concrete, complete PRD. No "TBD" sections allowed.

## Preconditions (HARD)

All three of these must exist at `docs/features/<slug>/`:
- `probe-product.md`
- `probe-design.md`
- `probe-technical.md`

If any are missing, abort with:
> "Cannot write PRD — missing `<file>`. Run `probe-<name>` first."

## Procedure

### 1. Resolve slug

The slug may be the first argument (e.g. `/write-prd dark-mode-toggle`). Ask for it only if not provided. Confirm all three probe files exist.

### 2. Read all three probes

Read fully. Identify any items in the "Open questions" sections of each.

### 3. Gate on unresolved items

If ANY probe has open questions in the "Open questions" section, abort with:

> "Cannot synthesize PRD — unresolved items in <probe-name>.md:
> - <each open question>
>
> Re-run the relevant probe-* skill to resolve, then re-invoke write-prd."

### 4. Synthesize PRD

Read the bundled `PRD-template.md`. Fill in each section by drawing from the probes:
- **Problem** ← probe-product Problem + Trigger
- **Users & JTBD** ← probe-product Primary user + JTBD
- **Goals** ← probe-product Success metrics + In scope (as outcomes, not features)
- **Non-goals** ← probe-product Out of scope
- **User stories** ← derived from JTBD + key user moments from probe-design (1 story per moment)
- **Success metrics** ← probe-product Success metrics verbatim
- **Open questions** ← ONLY items the user has explicitly marked "in flight" — distinct from probe Open questions (those gated). If empty, write "None at PRD write time."

### 5. Write

Write `docs/features/<slug>/prd.md`.

### 6. Report

> "Wrote `docs/features/<slug>/prd.md`.
>
> Next — run both: `/write-design-brief <slug>` and `/write-tech-spec <slug>`"

## Rules

- Refuse "TBD" — if you don't know, abort and send the user back to probes.
- Use the user's wording wherever possible. Don't paraphrase the JTBD.
- Don't invent metrics, goals, or stories not derivable from the probes.
