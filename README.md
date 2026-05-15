# Probe-Feature Skill Library

A Claude Code skill library for PRD-driven feature development. Takes a feature from rough idea through probe → PRD/design-brief/tech-spec → vertical-slice issues → per-issue execution with separate-agent review.

Inspired by Matt Pocock's probe → PRD → issues → implement flow. Three additions:
1. **Parallel design probing** — UX is a first-class discovery input.
2. **Token budget discipline** at the issue-slicing layer (100k cap per issue, 120k stability envelope).
3. **Phase gates via skill preconditions** — skills refuse to run if upstream artifacts are missing.

## Install

```powershell
# Windows
.\install.ps1
```

```bash
# macOS / Linux
./install.sh
```

The installer copies each leaf skill folder into `~/.claude/skills/`. Re-running is idempotent. On the first collision it asks once whether to overwrite-all / skip-all / archive-all / decide-each. Non-interactive equivalents: `--overwrite` (alias `--force`), `--skip`, `--archive` (PowerShell: `-Overwrite`/`-Skip`/`-Archive`); these are mutually exclusive and compose with `--dry-run`/`-DryRun`. On first run it also offers to archive existing prototype skills (`probe`, `scope`, `grill-me`) to `~/.claude/skills/.archive/`.

## Quick start

Happy path:

```
> shape-feature           # optional — half-formed ideas only. Produces docs/concepts/<slug>.md
> probe-feature           # interactive — produces docs/features/<slug>/ bundle (auto-promotes a ready-to-probe concept)
> slice-issues            # produces issues/NNN-*.md and SEQUENCE.md
> execute-issue <slug>/001-...   # loop per issue (slug-qualified — avoids cross-feature NNN collisions)
> verify-issue  <slug>/001-...   # after each execute
> publish-issues          # optional — syncs to GitHub
```

Skip `shape-feature` if you already know what you're building.

## Skills

### Shape (optional, pre-probe)
- `shape-feature` — interview that turns a rough idea into a concept doc (`docs/concepts/<slug>.md`) with Framings, a Chosen framing, Appetite, and a Status gate (`shaping` / `ready-to-probe` / `shelved`). `probe-feature` auto-promotes any `ready-to-probe` concept into `docs/features/<slug>/concept.md`.

### Orchestrator
- `probe-feature` — runs the discovery + synthesis phases end-to-end for a new feature.

### Discover (parallel)
- `probe-product` — JTBD, users, success metrics, scope.
- `probe-design` — tone, references, key moments, a11y, density, motion, states. Scaffolds `docs/design-system.md`.
- `probe-technical` — modules, integrations, constraints. Audits the codebase against claims.

### Synthesize
- `write-prd` — refuses to run with unresolved probe items.
- `write-design-brief` — screen-by-screen states, tokens, motion.
- `write-tech-spec` — always writes Module map; full sections only when warranted.

### Plan
- `slice-issues` — the keystone. Vertical slices, 100k token cap, required Tests sections, Do-NOT-read lists. Also seeds `docs/features/<slug>/issues/STATUS.md`, a per-feature progress tracker that `execute-issue`/`verify-issue` tick off and that drives the literal "Next — run:" command at every handoff.
- `sequence-issues` — topological order with parallelizable groups.

### Implement
- `execute-issue` — dispatches a subagent for one issue.
- `verify-issue` — dispatches a *different* subagent to review; emits a QA doc for vertical slices.

### Integrate
- `publish-issues` — syncs local issues to GitHub via `gh`. Idempotent. Optional.

### Release
- `chart-publishing-path` — audits an Expo / React Native project and produces (or idempotently updates) `docs/publishing-roadmap.md`, a single checklist tracking everything between code and store-live status for the Apple App Store and Google Play. Re-run any time; developer notes are preserved across runs.

### Career
- `build-background` — interview-driven capture of career history, projects, skills, story-bank, and goals into `<career-hub>/BACKGROUND.md`. First run picks the career-hub location.
- `refine-template` — critiques resume format against modern best practices + ATS, iterates with the user, locks in a reusable template (markdown skeleton + CSS + reference.docx) in the career hub.
- `align-resume` — generates an ATS-aware tailored resume from a job description: selects and lightly rewords material from BACKGROUND.md, renders MD/PDF/DOCX into a per-job subfolder in CWD, enforces page-length target.

## Artifact layout in your project

```
docs/concepts/
└── <slug>.md                 # shaped concepts (shaping | ready-to-probe | shelved). Removed once promoted.

docs/features/<feature-slug>/
├── concept.md                # only present if this feature was promoted from a shaped concept
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

```
docs/publishing-roadmap.md  # project-wide release/publishing checklist; produced by chart-publishing-path
```

Slugs are unique across both `docs/concepts/` and `docs/features/`. `docs/design-system.md` lives at the project root (one per project, not per feature).

## Career artifact layout

Career hub (single source of truth, location set by `build-background` on first run, recorded in `~/.claude/career/config.yml`):

```
<career-hub>/
├── BACKGROUND.md
└── template/
    ├── resume.template.md
    ├── style.css
    ├── reference.docx
    └── template-notes.md
```

Per-job folder (in the directory `align-resume` is invoked from):

```
<cwd>/<job-slug>/
├── job-description.md
├── resume.md
├── resume.pdf
├── resume.docx
└── tailoring-notes.md
```

## Philosophy

- **Vertical slices** — every issue is end-to-end user-facing functionality.
- **Modules with public surfaces** — code organized into modules; cross-module imports only via declared public surface.
- **Sequence is dependency-driven**, not preference-driven.
- **PRDs are concrete and complete** — no "TBD" sections.
- **TDD is default** — every issue has a Tests section; waivers require explicit justification.
- **Composed tools** — sub-skills are individually invokable; `probe-feature` is a thin orchestrator.

## Design + plan docs

- Design: `docs/superpowers/specs/2026-05-10-probe-feature-skill-library-design.md`
- Plan: `docs/superpowers/plans/2026-05-10-probe-feature-skill-library.md`
- Design: `docs/superpowers/specs/2026-05-14-chart-publishing-path-design.md`
- Plan: `docs/superpowers/plans/2026-05-14-chart-publishing-path.md`
