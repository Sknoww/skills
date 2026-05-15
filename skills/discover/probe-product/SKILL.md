---
name: probe-product
description: Conducts an interactive product discovery interview for a new feature — JTBD, primary user, success metrics, in-scope/out-of-scope, business trigger. Use when starting the discovery phase for a new feature, before writing the PRD.
---

# probe-product

Conduct an interactive product-discovery interview and write the results to `docs/features/<slug>/probe-product.md`. One question at a time. If a question can be answered by reading existing project docs, read them instead of asking.

## Preconditions

None — this is the entry point of the discover phase.

## Procedure

### 1. Identify the feature

Ask:
> "What is the feature name? (Short slug, lowercase-hyphenated, e.g. `dark-mode-toggle`.)"

Then ask:
> "Short human-readable name? (e.g. 'Dark mode toggle')"

Create `docs/features/<slug>/` if it does not exist.

### 2. Read existing context silently

Read these if they exist; do not ask permission, do not summarize back:
- `CONTEXT.md`, `CONTEXT-MAP.md`
- `README.md`
- `docs/adr/*.md`

Use what you find to skip questions whose answers are already documented.

### 2.5. Concept doc handling

If `docs/features/<slug>/concept.md` exists (i.e. this feature was promoted from a shaped Concept), read it and use it to draft starting answers — light, judgment-based mapping, never copy verbatim:

- `Problem (rough)` → seed for the **Problem** answer.
- `Beneficiary (rough)` → seed for the **Primary user** answer.
- `Chosen framing` → orientation for **JTBD** and **In scope**.
- `Explicit no-gos` → seed for the **Out of scope** answer.
- `Open questions` from the concept → carry into this probe's **Open questions** unless they're now resolved.

When you ask each interview question below, lead with the drafted starting answer (if any) and ask the user to confirm or correct it rather than asking cold. Example:
> "From the concept, the primary user looks like <X>. Confirm or sharpen?"

If no `concept.md` exists, proceed normally with the interview below.

### 3. Interview — ask one at a time

Ask each question only if not already answered by existing context. Wait for the answer before moving on.

1. **Trigger** — "What's prompting this work now? Bug, customer ask, strategic shift, internal pain?"
2. **Problem** — "In 1–3 sentences: what user pain or business gap does this address?"
3. **Primary user** — "Who is the primary user? Be concrete — a role, segment, or persona."
4. **JTBD** — "Complete the sentence: When <situation>, I want <motivation>, so I can <outcome>."
5. **In-scope** — "What's explicitly IN scope? Three to five bullets."
6. **Out-of-scope** — "What's explicitly OUT of scope — adjacent things you're deliberately not doing?"
7. **Success metrics** — "How will we know this worked? Each metric: name + baseline + target."
8. **Stakeholders** — "Anyone else involved or affected? Brief — names/roles/why."
9. **Open questions** — "What unresolved product questions do you already know about? These seed the next steps."

### 4. Write the artifact

Write `docs/features/<slug>/probe-product.md` with this structure:

```markdown
# Probe — Product: <name> (<slug>)

**Date:** <YYYY-MM-DD>
**Trigger:** <answer>

## Problem
<answer>

## Primary user
<answer>

## JTBD
When <situation>, I want <motivation>, so I can <outcome>.

## In scope
- <bullet>

## Out of scope
- <bullet>

## Success metrics
- <metric>: <baseline> → <target>

## Stakeholders
- <name/role/why>

## Open questions
- <bullet>
```

### 5. Report

After writing, print:
> "Wrote `docs/features/<slug>/probe-product.md`. Next: run `probe-design` or `probe-technical` (parallel) — both must be done before `write-prd`."

## Rules

- One question at a time. Never batch.
- If the user gives a vague answer, push back once with a sharpening prompt; if still vague, capture as an Open question.
- Never fabricate answers — if the user can't answer, list it as an Open question.
- The Open questions section is the handoff back to the user for follow-up.
