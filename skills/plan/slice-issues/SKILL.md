---
name: slice-issues
description: Breaks a feature into vertical-slice issues with token-budgeted context manifests (100k cap), required Tests sections, UX slices, and acceptance criteria. The keystone skill of the probe-feature library. Use when ready to break a feature into actionable work items after the PRD, design brief, and tech spec are written.
---

# slice-issues

The keystone. Reads a feature's PRD + design brief + tech spec, produces vertical-slice issues at `docs/features/<slug>/issues/NNN-<slug>.md` with hard token-budget enforcement.

## Preconditions (HARD)

All three must exist at `docs/features/<slug>/`:
- `prd.md`
- `design-brief.md`
- `tech-spec.md`

`docs/design-system.md` must exist.

The bundled `ISSUE-TEMPLATE.md` and `estimate_tokens.py` must be in this skill's folder.

If any are missing, abort with a pointer to the upstream skill.

## Hard rules (non-negotiable)

1. **Every issue is a vertical slice** — ships an end-to-end user-facing outcome. NOT "all the schema," NOT "all the UI." If something genuinely can't be a vertical slice (true scaffolding), mark `Slice type: skeleton` and justify.
2. **100,000 token cap** on estimated context per issue. No exceptions without explicit user override (see Splitting procedure).
3. **Every issue declares a Tests section** with at least one test file in the Write list. Waivers require explicit justification text — no implicit waivers.
4. **Every issue declares a `Do NOT read` section** with at least one path/directory — prevents exploratory reading by the subagent.
5. **Skeleton-issue cap:** if more than 20% of issues for this feature are `Slice type: skeleton`, warn and ask the user to reconsider before writing.

## Procedure

### 1. Resolve slug + read inputs

Ask for slug if not provided. Read `prd.md`, `design-brief.md`, `tech-spec.md`. Note the Module map section in tech-spec — this is the boundary catalog issues must respect.

### 2. Draft candidate vertical slices

From PRD user stories + design-brief key moments, identify the minimum set of end-to-end outcomes. Each candidate should be:
- A user-facing thing a user can do after this issue ships
- Independent (or nearly so) of other issues

Layer-shaped items ("set up DB," "add routes," "build the form") are NOT candidates — they must either be folded into a vertical slice or extracted as a pre-requisite `Slice type: skeleton` issue.

### 3. For each candidate, draft an issue

Use the bundled `ISSUE-TEMPLATE.md`. Fill EVERY section. For the Context manifest:
- **Read** — minimal set of files the subagent must read. Each with a one-line `why`. Token estimates filled by `estimate_tokens.py` in Step 4.
- **Write** — files the subagent will create or modify. ALWAYS include at least one test file (or a waiver in the Tests section).
- **Reference (by section)** — design-brief and tech-spec sections by header, NOT full-file reads. Use this to keep context small.
- **Do NOT read** — directories or paths irrelevant to this issue.

### 4. Estimate context per issue

For each draft issue's Read list, run:
```
python <this skill folder>/estimate_tokens.py <read-path-1> <read-path-2> ...
```
Capture the per-file estimates into the issue's Read list and the TOTAL into Estimated context.

### 5. Enforce 100k cap

For any issue where Estimated context ≥ 100,000:

Apply the splitting procedure in order. Stop at the first option that gets the issue under 100k.

1. **Split into independent vertical slices.** Can the user-facing outcome be cleaved into two smaller user-facing outcomes (e.g., "happy path" + "error handling")? Each must independently ship something a user can do. If yes, split.
2. **Reduce reads.** Replace a full-file read with a section reference where possible (e.g., reference `tech-spec.md §<section>` instead of reading the whole spec).
3. **Extract a setup issue.** Pull a refactor or scaffold step into its own preceding `Slice type: skeleton` issue.
4. **Escalate to user.** Surface that the slice can't be enforced; ask whether to proceed with explicit override. If override granted, mark in the issue: `## Override: 100k cap waived — <user-supplied reason>`.

### 6. Number and name issues

Number sequentially `001`, `002`, etc. Slugify the title for the filename: `001-<imperative-slug>.md`.

### 7. Skeleton-issue cap check

Count issues with `Slice type: skeleton`. If they exceed 20% of total issues, halt and ask:
> "This plan has <N>/<total> skeleton issues (<percent>%). That suggests layer-driven slicing, not vertical-slice. Reconsider? (y / proceed-anyway)"

### 8. Write all issues

Write each to `docs/features/<slug>/issues/NNN-<slug>.md`.

### 9. Report

> "Wrote <N> issues to `docs/features/<slug>/issues/`. <count vertical / count skeleton>. Token budget summary: <min>k / <median>k / <max>k. Next: `sequence-issues` to build the dependency order."

## Rules

- Refuse to slice without all three preconditions (prd, design-brief, tech-spec).
- 100k cap is non-negotiable without explicit override.
- Test files MUST appear in Write list; waivers require justification text in the Tests section.
- Module boundary check in Acceptance is always present — issues must respect the tech-spec Module map.
- Don't fabricate file paths — only include paths in Read/Write that you've verified exist (for Read) or that follow the tech-spec Module map (for Write).
