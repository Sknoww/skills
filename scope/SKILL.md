---
name: scope
description: Conducts a brief scoping interview (5–10 questions) and produces a clean, probe-ready SCOPE.md. Use when starting a new project or a new feature and you need a tight, structured starting point before running the probe skill.
---

<what-to-do>

Conduct a short scoping interview that produces a single, clean SCOPE.md file. The output is consumed by the probe skill, so keep SCOPE.md tight — it's a seed, not a spec.

Ask one question at a time, waiting for the answer before continuing. Aim for 5–10 questions total. If a question can be answered by reading existing project files, read them instead of asking.

</what-to-do>

<session-setup>

## Step 1 — Read existing context silently

Read these if they exist. Do not ask permission, do not summarize them back:

- `CONTEXT.md` and `CONTEXT-MAP.md`
- `README.md`
- `docs/adr/*.md`

Use what you find to skip questions whose answers are already documented.

## Step 2 — Ask mode upfront

> "Is this a **new project** or a **new feature** in an existing codebase?"

This becomes the `Type` field in SCOPE.md and decides which conditional questions apply.

## Step 3 — Note any existing SCOPE.md

If `SCOPE.md` already exists in the working directory or repo root, do not act on it yet. Handle it during finalization.

</session-setup>

<question-set>

Ask one at a time. Skip any answered by existing context. Cap at 10 questions including the mode question.

### Always ask

1. **Goal** — "In one or two sentences: what are you building, and why does it need to exist?"
2. **In-scope** — "What's explicitly IN scope? Give me 3–5 bullets."
3. **Out-of-scope** — "What's explicitly OUT of scope — adjacent things you are deliberately not doing?"
4. **Constraints & assumptions** — "What constraints or assumptions does this rest on? Tech stack, deadlines, dependencies, anything load-bearing."
5. **Open questions** — "What open questions do you already know are unresolved? These seed the probe session."

### If new project

6. **Users** — "Who is this for? Be concrete — a role, a team, a product."
7. **Success picture** — "What does 'done and working' look like at a high level?"

### If new feature

6. **Where it lives** — "Which part of the existing codebase or system does this fit into?"
7. **Trigger** — "What's prompting this work now — a bug, a customer ask, a strategic shift?"

</question-set>

<finalization>

When the question set is complete:

1. Draft SCOPE.md using the format below.
2. Show the draft to the user for a final read.
3. Handle the file write per the rules below.

### Folding conditional answers

Weave conditional answers into the agreed sections rather than adding new headings:

- **Users / Trigger** → into the Goal paragraph (e.g. "...for {audience}", "...prompted by {trigger}").
- **Success picture** → into the Goal paragraph as a closing sentence.
- **Where it lives** → into Constraints & assumptions as a bullet.

### Writing the file

**No existing SCOPE.md** → write the new file directly.

**Existing SCOPE.md** → confirm with the user before any write:

> "There's an existing SCOPE.md. Two options:
> 1. **Overwrite** — replace it with the new draft.
> 2. **Archive then replace** — move the old one to `archive/SCOPE-{YYYY-MM-DD}.md`, then write the new SCOPE.md.
>
> Which?"

Do not write or move anything until the user picks. If archiving, create the `archive/` directory if it doesn't exist.

</finalization>

<scope-format>

```md
# Scope

**Type:** New project | New feature

## Goal

{One or two sentences. What and why. Weave in audience, trigger, or success picture if applicable.}

## In scope

- {Bullet}
- {Bullet}

## Out of scope

- {Bullet}
- {Bullet}

## Constraints & assumptions

- {Bullet}
- {Bullet}

## Open questions

- {Bullet}
- {Bullet}
```

Rules:

- Keep each section tight. Bullets, not paragraphs.
- Use the user's words, structured. Don't editorialize.
- Don't add sections beyond the five above. Probe will surface success criteria, stakeholders, and the rest.

</scope-format>
