---
name: shape-feature
description: Pre-probe shaping skill — takes a rough idea and gives it enough definition (problem, beneficiary, framings, appetite, no-gos) to be ready for probe-feature. Writes docs/concepts/<slug>.md with a Status field (shaping | ready-to-probe | shelved). Use when the idea is still half-formed and you're not yet sure whether/what to build.
---

# shape-feature

Take a half-formed idea and shape it until it's ready to probe. One question at a time. Output: `docs/concepts/<slug>.md`.

Shaping is distinct from probing. Shaping decides *whether and what* to build. Probing assumes the feature is real and gathers structured detail for the PRD. If the user already knows what they're building, skip this skill and go straight to `probe-feature`.

## Preconditions

None. Working directory should be the user's project repo.

## Procedure

### 1. Get the concept identity

Ask:
> "Short human-readable name for this idea? (e.g. 'Dark mode toggle')"

Then:
> "Slug? (lowercase-hyphenated, e.g. 'dark-mode-toggle')"

Check for collisions:
- If `docs/concepts/<slug>.md` exists → refuse:
  > "A concept already exists at `docs/concepts/<slug>.md`. Pick a different slug, or re-invoke `shape-feature` on the existing one to revise it."
  Then ask whether the user wants to revise the existing concept (read it and continue) or pick a new slug.
- If `docs/features/<slug>/` exists → refuse with no override:
  > "A feature folder already exists at `docs/features/<slug>/`. Slugs are unique across both concepts and features. Pick a different slug."

Create `docs/concepts/` if it does not exist.

### 2. Read existing context silently

Read these if they exist; do not ask permission, do not summarize back:
- `CONTEXT.md`, `CONTEXT-MAP.md`
- `README.md`
- `docs/adr/*.md`
- Any existing `docs/concepts/*.md` (to learn the project's shaping voice and avoid duplicating prior concepts)

Use what you find to skip questions whose answers are already documented, and to flag near-duplicate concepts.

### 3. Interview — ask one at a time

Ask each question only if not already answered by existing context. Wait for the answer before moving on. If the user gives a vague answer, push back once with a sharpening prompt; if still vague, capture as an Open question.

1. **Trigger** — "What's prompting this now? Bug, customer ask, strategic shift, internal pain?"
2. **Problem (rough)** — "In 1–3 sentences: what user pain or business gap does this address? Rough is fine — we'll sharpen in probe-product."
3. **Beneficiary (rough)** — "Who benefits? Be concrete — a role, segment, or persona. Doesn't have to be the final 'primary user' framing yet."
4. **Framings** — "Let's consider 1–3 different shapes this idea could take. I'll propose a few and you can react, add your own, or rule any out.
   - A **lightweight** version: the smallest thing that delivers any value.
   - An **ambitious** version: what this looks like with no constraints.
   - A **different-audience** version: who else might benefit if we re-targeted it.
   
   Which of these resonate? Add or modify."
   
   Capture each Framing the user keeps. Aim for 1–3 total.
5. **Chosen framing** — "Pick one as the chosen framing — the one you'd actually want to probe. *Why* this one over the others?" Capture both the pick and the reasoning. Rejected framings stay in the doc as a record.
6. **Appetite** — "Rough sizing for the chosen framing: small (~1–2 weeks), medium (~3–4 weeks), or large (>1 month)? Non-binding — it's a converging force, not an estimate."
   - If the appetite feels off versus the chosen framing's scope, push back once: "That framing feels bigger/smaller than <appetite> — want to resize it, pick a lighter framing, or keep the mismatch?"
7. **Explicit no-gos** — "What's explicitly NOT being attempted in this shape? Things adjacent that you want on the record as out-of-bounds."
8. **Open questions** — "What unresolved shaping questions do you already know about? These seed probe-product or further shaping."

### 4. Decide Status

Ask:
> "Status for this concept?
> - `ready-to-probe` — gate passed; probe-feature will promote it.
> - `shaping` — needs more thinking; come back to it later.
> - `shelved` — decided not to pursue; keep as a record."

If the user picks `ready-to-probe` but there are unresolved Open questions, push back once:
> "Open questions remain: <list>. Are these OK to carry into probing, or should the status be `shaping` until they're resolved?"

### 5. Write the artifact

Write `docs/concepts/<slug>.md` with this structure:

```markdown
# Concept: <name> (<slug>)

**Status:** <shaping | ready-to-probe | shelved>
**Date:** <YYYY-MM-DD>
**Trigger:** <answer>
**Appetite:** <small | medium | large>

## Problem (rough)
<answer>

## Beneficiary (rough)
<answer>

## Framings
- **<framing label 1>** — <description>
- **<framing label 2>** — <description>
- ...

## Chosen framing
**<label>** — <description>

*Why this one:* <reasoning>

## Explicit no-gos
- <bullet>

## Open questions
- <bullet>
```

If the user is revising an existing concept doc, preserve any Framings the user didn't explicitly remove (rejected framings are a permanent record), and update Status / Chosen framing / Open questions as needed.

### 6. Report

Based on the Status the user chose, print one of:

- **ready-to-probe:**
  > "Wrote `docs/concepts/<slug>.md` (Status: ready-to-probe).
  >
  > Next — run: `/probe-feature <slug>` (it promotes this concept into `docs/features/<slug>/concept.md` on entry)."
- **shaping:**
  > "Wrote `docs/concepts/<slug>.md` (Status: shaping). Re-invoke `shape-feature` on this slug when you have more clarity, or move directly to `probe-feature` once you flip Status to `ready-to-probe`."
- **shelved:**
  > "Wrote `docs/concepts/<slug>.md` (Status: shelved). Kept as a record; `probe-feature` will refuse to promote it."

## Rules

- One question at a time. Never batch.
- Slugs are unique across `docs/concepts/` and `docs/features/`. Refuse collisions.
- Always capture **rejected framings** in the artifact — they're the audit trail of "we considered this and picked otherwise."
- Never fabricate framings the user didn't engage with. If the user rejects all proposed framings without supplying their own, capture as an Open question and set Status to `shaping`.
- Never promote a concept yourself — promotion is `probe-feature`'s job.
- If `docs/concepts/<slug>.md` already exists and the user wants to revise, read it first and treat unchanged sections as still-valid.

(END shape-feature)
