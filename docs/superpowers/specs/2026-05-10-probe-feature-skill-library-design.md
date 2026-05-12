# Probe-Feature Skill Library — Design

**Status:** Approved 2026-05-10
**Scope:** v1 — new features in existing codebases. Greenfield/project bootstrap is out of scope.

## Goal

A composable Claude Code skill library that takes a feature from rough idea → PRD + design brief (+ optional tech spec) → vertical-slice issues with enforced token discipline → per-issue implementation with separate-agent review. Inspired by Matt Pocock's probe → PRD → issues → implement flow, with three explicit additions:

1. **Parallel design probing** — UX is a first-class discovery input alongside product and technical, not bolted on at the end.
2. **Token budget discipline** at the issue-slicing layer (100k per-issue cap inside a 120k stability envelope).
3. **Phase gates via skill preconditions** — skills refuse to run if upstream artifacts are missing.

## Philosophy

- **Vertical slices** — every issue is end-to-end user-facing functionality. No layer-only issues ("all the schema," "all the UI").
- **Modules with public surfaces** — code organized into modules; cross-module imports only via declared public surface; internals stay internal.
- **Sequence is dependency-driven**, not preference-driven.
- **PRDs are concrete and complete** — no "TBD" sections. Unresolved questions stay in probe outputs.
- **TDD is default** — every issue has a Tests section. Waivers require explicit justification.
- **Composed tools, with a friendly front door** — Unix philosophy. Sub-skills are individually invokable; `probe-feature` is a thin orchestrator for the common case.

## Architecture overview

**Three-command happy path:**
```
probe-feature  →  slice-issues  →  execute-issue (loop)
```

`verify-issue` runs after each `execute-issue`. `publish-issues` syncs to GitHub on demand. Sub-skills (probe-*, write-*) are available for surgical use (e.g., backfilling UX rigor on a feature that already has a PRD).

**Artifact home:** `docs/features/<slug>/` per feature, in the user's project repo:
```
docs/features/<slug>/
├── probe-product.md
├── probe-design.md
├── probe-technical.md
├── prd.md
├── design-brief.md
├── tech-spec.md
├── issues/
│   ├── NNN-<slug>.md
│   └── SEQUENCE.md
└── qa/
    └── NNN-qa-review.md
```

## Skill inventory (12 skills)

### Orchestrator
**`probe-feature`** — Thin orchestrator. Invokes probe-product, probe-design, probe-technical in sequence (interactive, with the user). Then hands outputs to write-prd, write-design-brief, write-tech-spec. Decides whether tech-spec is full-depth or module-map-only based on signals from probe-technical (new modules? new data model? new integrations?). SKILL.md is short — it composes, it does not contain probing logic.

### Discover (sub-skills, parallel)
| Skill | Preconditions | Reads | Writes |
|---|---|---|---|
| `probe-product` | none | existing project docs | `probe-product.md` |
| `probe-design` | none | `docs/design-system.md` if present | `probe-design.md`; scaffolds `docs/design-system.md` from template if missing |
| `probe-technical` | none | source tree | `probe-technical.md` |

### Synthesize (sub-skills)
| Skill | Preconditions | Writes |
|---|---|---|
| `write-prd` | all three probe-*.md | `prd.md` (no "TBD" sections; unresolved items go back to probe-product) |
| `write-design-brief` | `prd.md`, `probe-design.md` | `design-brief.md` |
| `write-tech-spec` | `prd.md`, `probe-technical.md` | `tech-spec.md` — always includes **Module map section** (slice-issues depends on it); full-depth sections only when warranted |

### Plan
| Skill | Preconditions | Writes |
|---|---|---|
| `slice-issues` | `prd.md`, `design-brief.md`, `tech-spec.md` | `issues/NNN-*.md` — the keystone, see below |
| `sequence-issues` | `issues/NNN-*.md` exist | `issues/SEQUENCE.md` — dependency-ordered build order, identifies parallelizable groups |

### Implement
| Skill | Preconditions | Behavior |
|---|---|---|
| `execute-issue` | target issue file exists with filled Context manifest | Prompts user for subagent type (default general-purpose). Dispatches via Agent tool. Subagent works from manifest only. Reports back; issue's Execution log filled. |
| `verify-issue` | target issue's Execution log filled | Spawns a **different** subagent (default code-reviewer) to review against acceptance + module boundaries. Writes `qa/NNN-qa-review.md` for vertical slices (skipped for skeleton issues). Appends verdict to issue file. |

### Integrate
| Skill | Preconditions | Behavior |
|---|---|---|
| `publish-issues` | `issues/NNN-*.md` exist; `gh` CLI available; current dir is a GitHub repo | Creates/updates GitHub issues via `gh`. Idempotent — detects `## GitHub` block in local issue and updates rather than duplicates. Does not auto-close on verify-pass. |

### Shared
`skills/shared/templates/` — `PRD-template.md`, `DESIGN-BRIEF-template.md`, `TECH-SPEC-template.md`, `ISSUE-template.md`, `DESIGN-SYSTEM-template.md`. Used by the write-* skills (bundled into each skill folder at install) and by probe-design (which scaffolds the design system).

## Issue template (the keystone artifact)

```markdown
# Issue NNN: <imperative title>

## Slice type: vertical | skeleton

## Vertical slice
- User-facing outcome: <what a user can do after this issue ships, end-to-end>
- Not a layer: confirm this is not "all the schema" or "all the UI"

## Modules touched
- <module-name>: changes <internal | public surface> — <one-line rationale>

## Context manifest
- Read:
  - path/to/file.ts (~<N> tokens) — <why>
- Write:
  - path/to/file.ts
  - path/to/file.test.ts
- Reference (by section, not full read):
  - docs/features/<slug>/design-brief.md §<section>
  - docs/features/<slug>/tech-spec.md §<section>
  - docs/design-system.md §<section>
- Do NOT read:
  - <directories or paths that are irrelevant — pre-empts exploratory reading>
- Estimated context: <X> tokens (must be < 100,000)

## Tests
- Test files (written first):
  - path/to/feature.test.ts — <what it covers>
- Test commands:
  - `npm test path/to/feature.test.ts`
- TDD note: write failing tests first → implement to green → refactor
- Waiver: <only if waived — explicit justification>

## UX slice
- User moment: <which moment from design-brief>
- States to handle: empty / loading / error / success — <which apply, what each looks like>
- Design tokens: <which tokens from design-system.md>
- Interaction notes: <key interactions>

## Acceptance
- Functional:
  - [ ] All tests in Tests section pass
  - [ ] <additional behavioral check>
- Visual: matches design-brief §<section>
  - [ ] <visual check>
- Module boundary check:
  - [ ] No imports cross declared module public surfaces inappropriately

## Execution log (filled by execute-issue)
- Token budget actual: <filled post-run>
- Files changed: <filled post-run>
- Subagent type used: <filled post-run>

## Review verdict (filled by verify-issue)
- Code review: PASS | FAIL | NEEDS_USER — <summary>
- QA doc: docs/features/<slug>/qa/NNN-qa-review.md

## GitHub (filled by publish-issues, optional)
- Issue: #<N>
- URL: <url>
- Last synced: <ISO date>
```

## Token budget & splitting algorithm

### Per-issue cap
**100,000 tokens** estimated context, inside a **120,000 token stability envelope** (room for subagent reasoning + tool results). No exceptions without explicit user override.

### Estimator (`estimate_tokens.py`)
Pure Python, no deps. Char count ÷ 3.5 for code files, ÷ 4.0 for markdown/prose. Bundled inside `slice-issues/`. CLI: `python estimate_tokens.py path1 path2 ...` → per-file estimates + total.

### Splitting procedure (slice-issues when an issue exceeds 100k)
1. Identify the largest contributing files.
2. Can the issue split into two **independent vertical slices**? Each must ship a user-visible thing.
3. If yes: split, re-estimate, ensure each < 100k.
4. If no, in order of preference:
   a. **Reduce reads** — replace full-file reads with section references where possible.
   b. **Extract a setup issue** — pull scaffolding/refactor work into a preceding issue.
   c. **Escalate** — surface to user, get explicit "proceed anyway" override.

### Slice-type guardrails
- > 20% skeleton issues triggers a "this looks layer-driven, not slice-driven — reconsider" warning.
- Skeleton issues skip QA doc generation (verify-issue emits verdict only).

## Runtime flow

### `execute-issue` procedure
1. Precondition check on target issue file.
2. Prompt user for subagent type (default general-purpose).
3. Build subagent starting prompt from Context manifest + UX slice + Acceptance + "Do NOT read" list.
4. Dispatch via Agent tool with chosen subagent_type.
5. Subagent works, returns files changed + summary + any deviations + actual files read.
6. Estimate actual tokens via `estimate_tokens.py` on files actually read.
7. Update issue's Execution log section.
8. Report status (DONE / BLOCKED / NEEDS_USER) + next step (`verify-issue NNN`).

### `verify-issue` procedure
1. Precondition check: Execution log filled.
2. Spawn **different** subagent (default `code-reviewer`).
3. Review subagent reads issue file + diff of declared Write files + referenced design-brief sections. Checks acceptance, module boundaries, that tests exist and pass.
4. Review subagent reports PASS / FAIL / NEEDS_USER.
5. If `Slice type: vertical`: write `qa/NNN-qa-review.md` — step-by-step manual verification for the user (functional steps, visual checks with design-brief refs, edge cases from States section).
6. If `Slice type: skeleton`: skip QA doc.
7. Append verdict to issue's Review verdict section.
8. Report verdict + QA doc path to main session.

### TDD threading
- `slice-issues`: refuses to slice issues without Tests section. Waivers require justification text.
- `execute-issue`: subagent prompt explicitly instructs test-first. Instructs subagent to invoke `superpowers:test-driven-development` if available.
- `verify-issue`: review subagent checks tests exist and pass.

## Repo layout (source — `C:\Users\hsfro\code\claude\temp_skills\`)

```
.
├── README.md
├── install.ps1
├── install.sh
├── docs/superpowers/specs/2026-05-10-probe-feature-skill-library-design.md
└── skills/
    ├── flow/probe-feature/SKILL.md
    ├── discover/
    │   ├── probe-product/SKILL.md
    │   ├── probe-design/
    │   │   ├── SKILL.md
    │   │   └── DESIGN-SYSTEM-template.md
    │   └── probe-technical/SKILL.md
    ├── synthesize/
    │   ├── write-prd/
    │   │   ├── SKILL.md
    │   │   └── PRD-template.md
    │   ├── write-design-brief/
    │   │   ├── SKILL.md
    │   │   └── DESIGN-BRIEF-template.md
    │   └── write-tech-spec/
    │       ├── SKILL.md
    │       └── TECH-SPEC-template.md
    ├── plan/
    │   ├── slice-issues/
    │   │   ├── SKILL.md
    │   │   ├── ISSUE-TEMPLATE.md
    │   │   └── estimate_tokens.py
    │   └── sequence-issues/SKILL.md
    ├── implement/
    │   ├── execute-issue/SKILL.md
    │   └── verify-issue/SKILL.md
    ├── integrate/
    │   └── publish-issues/SKILL.md
    └── shared/templates/    # canonical copies for reference
        ├── PRD-template.md
        ├── DESIGN-BRIEF-template.md
        ├── TECH-SPEC-template.md
        ├── ISSUE-template.md
        └── DESIGN-SYSTEM-template.md
```

## Install & migration

### `install.ps1` / `install.sh`
1. Walk `skills/` for any folder containing `SKILL.md`.
2. Copy each leaf folder to `~/.claude/skills/<leaf-name>/`. Source repo's category folders (`flow/`, `discover/`, etc.) are not preserved at install — only the leaf folder name matters for skill discovery.
3. On collision, prompt: overwrite / skip / archive-then-overwrite (archive to `~/.claude/skills/.archive/<name>-<timestamp>/`).
4. On first run, offer to archive prototype skills (`probe`, `scope`, `grill-me`) which this library replaces.
5. Idempotent: re-runnable to refresh.

### Project setup (user runs in their feature repo)
```
cd <project>
# In Claude Code:
> probe-feature           # interactive — produces docs/features/<slug>/ bundle
> slice-issues            # produces issues/NNN-*.md and SEQUENCE.md
> publish-issues          # optional — syncs to GitHub
> execute-issue 001-...
> verify-issue 001-...
# loop execute/verify per issue
```

## Out of scope for v1

- Greenfield/foundation skills (`probe-project`, `slice-foundation`). Tracked as future work.
- Cross-project skill sharing beyond `~/.claude/skills/` (no package registry, no MCP server).
- Automated metric collection / dashboards on token budget accuracy.
- Auto-closing GitHub issues on verify-pass (deliberately kept manual).
- Linear / Jira / Notion adapters. `integrate/` folder structure leaves room.

## Success criteria

1. Running the three-command happy path on a real feature in a real project produces issues that each fit comfortably in a Claude Code subagent context window.
2. UX details appear in every issue's UX slice section without manual re-injection.
3. Skipping a phase fails fast with a clear error pointing to the missing artifact.
4. Sub-skills can be invoked individually for surgical use cases (backfilling, re-slicing, refreshing).
5. Tests appear in every issue. TDD waivers are rare and justified.
