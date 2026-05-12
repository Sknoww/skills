---
name: probe-technical
description: Conducts an interactive technical discovery interview for a new feature — modules touched, integration points, perf/security constraints, data model changes — and audits the existing codebase against claims via Grep/Glob/Read. Use when probing the technical dimension of a feature.
---

# probe-technical

Conduct an interactive technical-discovery interview and write the results to `docs/features/<slug>/probe-technical.md`. One question at a time, with codebase verification.

## Preconditions

None. Working directory should be the project repo.

## Procedure

### 1. Identify the feature

If invoked standalone, ask for the slug. If invoked via `probe-feature`, the slug is passed in.

### 2. Skim the codebase silently

- `Glob` for project markers: `package.json`, `pyproject.toml`, `go.mod`, `Cargo.toml`, etc.
- Identify the language(s) and primary frameworks.
- Look for an existing module/package structure (e.g., `src/modules/*`, `apps/*`, `packages/*`, `lib/*`).

Do not summarize back unless asked — this is internal context.

### 3. Interview — ask one at a time

1. **Modules touched (existing)** — "Which existing modules / packages / areas of the codebase will this feature touch?" Cross-reference with the skim. If the user names something that doesn't exist, surface it.
2. **New modules needed** — "Will this require any new modules? Each one: name, responsibility, public surface."
3. **Integration points** — "External services, internal APIs, libraries, or systems this integrates with?"
4. **Data model deltas** — "Any new tables, columns, indexes, migrations? Any changes to existing models?"
5. **API deltas** — "Any new endpoints or changes to existing endpoint contracts?"
6. **Constraints** — "Perf, security, compliance, browser/runtime support — anything load-bearing?"
7. **Dependencies (new)** — "Any new third-party dependencies? If yes: which and why?"
8. **Tech-spec depth signal** — Decide internally: are there new modules / data model deltas / API deltas / new dependencies? If yes, recommend `tech-spec.md` at full depth. Otherwise, module-map-only is sufficient.
9. **Open technical questions** — "Unresolved technical questions you already know about?"

### 4. Verify claims against code

For each claim:
- "We'll touch module X" → confirm X exists. If not, surface as Open question.
- "We need to change endpoint Y" → grep for Y. If not found, surface.

Capture verification findings inline.

### 5. Write the artifact

Write `docs/features/<slug>/probe-technical.md` with a structure including: Tech spec depth signal, Modules touched (existing) with verification refs, Modules new, Integration points, Data model deltas, API deltas, Constraints, New dependencies, Verification findings, Open technical questions.

Example artifact structure (use a fenced code block in your SKILL.md):

```markdown
# Probe — Technical: <name> (<slug>)

**Date:** <YYYY-MM-DD>
**Tech spec depth signal:** full | module-map-only

## Modules touched (existing)
- <module>: <how it changes> — verified at <path>: <line ref or note>

## Modules new
- <name>: <responsibility> — public surface: <list>

## Integration points
- <list>

## Data model deltas
- <list, or "none">

## API deltas
- <list, or "none">

## Constraints
- <list>

## New dependencies
- <list, or "none">

## Verification findings
- <any mismatches between user claims and code>

## Open technical questions
- <bullet>
```

### 6. Report

> "Wrote `docs/features/<slug>/probe-technical.md`. Tech spec depth signal: <full | module-map-only>. Next: `write-prd` (after all three probes complete), then `write-tech-spec`."

## Rules

- One question at a time.
- Always verify user's module/file claims against actual code via Glob/Grep.
- Never fabricate code findings — if you didn't read it, don't claim it.
