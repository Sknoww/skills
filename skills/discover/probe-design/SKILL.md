---
name: probe-design
description: Conducts an interactive UX/design discovery interview for a new feature — tone, references, key user moments, accessibility floor, density, motion, error/empty/loading states. Scaffolds docs/design-system.md from template if missing. Use when probing the design dimension of a feature.
---

# probe-design

Conduct an interactive design-discovery interview and write the results to `docs/features/<slug>/probe-design.md`. One question at a time. Parallel to `probe-product` and `probe-technical` — none blocks the others.

## Preconditions

None.

## Procedure

### 1. Identify the feature

If invoked standalone, ask:
> "What is the feature slug? (lowercase-hyphenated)"

If invoked via `probe-feature`, the slug is passed in.

### 2. Check for `docs/design-system.md`

If `docs/design-system.md` does NOT exist:
> "No `docs/design-system.md` found. I can scaffold one from a template — you fill in the actual tokens/values for this project. Scaffold now? (y/n)"

If yes, copy the bundled `DESIGN-SYSTEM-template.md` (in this skill folder) to `docs/design-system.md`. Then prompt:
> "Scaffold written to `docs/design-system.md`. Open it and fill in your project's actual tokens before continuing? (y/n)"

If the user wants to fill it in first, end the skill here and tell them to re-invoke once done. Otherwise continue with the template as the current source of truth.

### 3. Interview — ask one at a time

1. **Emotional tone** — "What should this feel like? Give me 3 adjectives (e.g., calm / precise / confident)."
2. **Reference products** — "Name 1–3 products this should feel like — and one it should NOT feel like."
3. **Key user moments** — "What are the 2–4 key moments in this feature? Each: when it happens and the desired feeling."
4. **Information density** — "Comfortable, balanced, or compact? When in doubt: which way do we err?"
5. **Motion philosophy** — "How much motion? Minimal / restrained / expressive. What animates and why?"
6. **State philosophy** — "How do empty / loading / error states feel? Same vibe as success or distinct?"
7. **Accessibility floor** — "WCAG AA, AAA, or other floor? Any specific concerns (color-vision, motion-sensitive, screen-reader)?"
8. **Microcopy voice** — "Voice and tone for microcopy: terse, conversational, technical, playful?"
9. **Open design questions** — "What design questions do you already know are unresolved?"

### 4. Write the artifact

Write `docs/features/<slug>/probe-design.md` with this structure:

```markdown
# Probe — Design: <name> (<slug>)

**Date:** <YYYY-MM-DD>

## Tone
- Adjectives: <three>
- Reference products (yes): <list>
- Reference products (no): <list>

## Key user moments
1. <moment> — <feeling/intent>
2. ...

## Density
<answer>

## Motion
<answer>

## States philosophy
<answer>

## Accessibility floor
<answer>

## Microcopy voice
<answer>

## Open design questions
- <bullet>
```

### 5. Report

After writing, print:
> "Wrote `docs/features/<slug>/probe-design.md`. Design system: `docs/design-system.md`. Next: `probe-product` / `probe-technical` (if not yet run), then `write-prd` + `write-design-brief`."

## Rules

- One question at a time.
- If `docs/design-system.md` exists and is already populated, do NOT overwrite — reference its sections in `probe-design.md` where relevant.
- Never invent design references the user didn't supply.
