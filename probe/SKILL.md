---
name: probe
description: Conducts an interview-style session that interrogates a plan or design until shared understanding is reached. Use when the user wants to stress-test, pressure-test, interrogate, or probe an idea — supports free-form sessions for raw idea-flushing and doc-aware sessions that anchor on a SCOPE.md input file and read or update CONTEXT.md and ADRs.
---

<what-to-do>

Interview the user relentlessly about every aspect of the plan until shared understanding is reached. Walk down each branch of the design tree, resolving dependencies between decisions one at a time. For each question, provide a recommended answer.

Ask one question at a time, waiting for an answer before continuing.

If a question can be answered by exploring the codebase, explore the codebase instead.

</what-to-do>

<session-setup>

## Step 1 — Pick a session type

Before any probing, ask the user:

> "Doc-aware session, or free-form session?"

- **Free-form** — raw idea-flushing. No file reads, no file writes. Skip directly to probing. Even if SCOPE.md or CONTEXT.md is present, ignore it.
- **Doc-aware** — anchor the session on existing project artifacts. Continue to step 2.

## Step 2 — Offer SCOPE.md (doc-aware only)

Check the working directory and repo root for `SCOPE.md`. If it exists:

> "I see SCOPE.md — want me to use it as the plan we probe against?"

If yes, read it and treat it as the spec under interrogation. **SCOPE.md is input-only — never modify it.** Refinements that emerge during the session land in CONTEXT.md, ADRs, or the conversation itself.

If no SCOPE.md exists, skip this step.

## Step 3 — Offer existing context (doc-aware only)

Look for `CONTEXT.md`, `CONTEXT-MAP.md`, and `docs/adr/*.md`. If any exist:

> "I see [list of files]. Want me to read them in so I can challenge the plan against your existing language and decisions?"

If yes, read them before probing begins.

</session-setup>

<doc-aware-behaviors>

These behaviors are active during probing in doc-aware mode. They do not apply in free-form mode.

### Challenge against the glossary

When the user uses a term that conflicts with `CONTEXT.md`, call it out immediately. "Your glossary defines 'cancellation' as X, but you seem to mean Y — which is it?"

### Sharpen fuzzy language

When the user uses vague or overloaded terms, propose a precise canonical term. "You're saying 'account' — do you mean the Customer or the User? Those are different things."

### Stress-test with concrete scenarios

When domain relationships are being discussed, invent scenarios that probe edge cases and force the user to be precise about the boundaries between concepts.

### Cross-reference with code

When the user states how something works, check whether the code agrees. Surface contradictions: "Your code cancels entire Orders, but you just said partial cancellation is possible — which is right?"

### Update CONTEXT.md inline

When a term is resolved, update `CONTEXT.md` right there. Don't batch — capture them as they happen. Use the format in [CONTEXT-FORMAT.md](./CONTEXT-FORMAT.md). Create the file lazily — only when the first term is resolved.

Don't couple `CONTEXT.md` to implementation details. Only include terms meaningful to domain experts.

### Offer ADRs sparingly

Only offer to create an ADR when all three are true:

1. **Hard to reverse** — the cost of changing your mind later is meaningful
2. **Surprising without context** — a future reader will wonder "why did they do it this way?"
3. **The result of a real trade-off** — there were genuine alternatives and you picked one for specific reasons

If any of the three is missing, skip the ADR. Use the format in [ADR-FORMAT.md](./ADR-FORMAT.md).

</doc-aware-behaviors>
