---
name: sequence-issues
description: Builds a dependency-ordered build sequence for a feature's issues, identifying which issues can run in parallel. Reads docs/features/<slug>/issues/*.md and writes SEQUENCE.md. Use after slice-issues, or to re-sequence after scope changes.
---

# sequence-issues

Build a topological build order from the issues' module dependencies and shared-file overlaps. Identify parallelizable groups.

## Preconditions (HARD)

At least one `docs/features/<slug>/issues/NNN-*.md` file must exist.

If none exist, abort with:
> "No issues found at `docs/features/<slug>/issues/`. Run `slice-issues` first."

## Procedure

### 1. Resolve slug + read all issues

Read every `NNN-*.md` in `docs/features/<slug>/issues/`. Extract from each:
- Issue number + title
- Slice type
- Modules touched (with internal/public surface annotation)
- Read list (paths)
- Write list (paths)

### 2. Build the dependency graph

Edge from A → B (A must complete before B) if EITHER:
- B's Read list includes a file in A's Write list (B depends on what A creates/modifies).
- A is a `Slice type: skeleton` issue and B is a vertical slice that touches a module A scaffolds.

Modules-touched alone do NOT create dependencies — multiple vertical slices may touch the same module independently if they don't share files.

### 3. Detect cycles

If a cycle is detected, abort with:
> "Dependency cycle detected among issues: <list>. Re-slice or merge these issues — they cannot be sequenced as-is."

### 4. Topological sort + parallelization

Layer the issues by topological depth:
- Layer 0: issues with no inbound edges (start here)
- Layer N: issues whose dependencies are all in layers 0..N-1

Within a layer, issues can run in parallel.

### 5. Write SEQUENCE.md

Write `docs/features/<slug>/issues/SEQUENCE.md`:

```markdown
# Build Sequence — <feature name> (<slug>)

**Generated:** <YYYY-MM-DD>

## Build order

### Layer 0 (start here — parallelizable)
- 001 — <title>
- 003 — <title>

### Layer 1 (after Layer 0 complete — parallelizable)
- 002 — <title>

### Layer 2 (after Layer 1 complete)
- 004 — <title>

## Dependency rationale

- 002 depends on 001: writes to `<path>` consumed by 002 Read.
- 004 depends on 002: ...

## Re-sequencing

Re-run `sequence-issues` whenever issues are added, removed, or re-scoped.
```

### 6. Report

> "Wrote `docs/features/<slug>/issues/SEQUENCE.md`. <N> layers, max parallelism <M>. Next: `execute-issue 001-...` to begin."

## Rules

- The graph is built from declared Read/Write files, not from inferred behavior. If an issue depends on another but doesn't read its outputs, the issue spec is wrong.
- Skeleton issues are always upstream of the vertical slices they enable.
- A re-sequence does NOT modify issue files; only SEQUENCE.md is rewritten.

(END sequence-issues)
