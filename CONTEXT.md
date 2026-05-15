# Probe Library

A composable Claude Code skill library for PRD-driven feature development: rough idea → shaped concept → discovery probes → PRD/design-brief/tech-spec → vertical-slice issues → per-issue execution with separate-agent review.

## Language

**Probe Library**:
The name of this skill collection. Distinct from "the superpowers plugin" and from any single skill within it.
_Avoid_: probe-feature library (that's one orchestrator inside the library, not the library itself)

**Feature**:
A unit of work with a slug, a `docs/features/<slug>/` bundle, and a path through probe → synthesize → slice → execute. Promoted from a Concept once it's ready to be probed.
_Avoid_: idea (use Concept), epic (no equivalent here)

**Concept**:
A pre-feature idea being shaped — not yet committed to as a Feature. Lives in `docs/concepts/<slug>.md` while being shaped or shelved. Promoted into a Feature by `probe-feature`.
_Avoid_: idea, pitch, brief (when referring to the artifact, say "concept doc")

**Slug**:
A lowercase-hyphenated identifier that names a Concept or a Feature (e.g., `dark-mode-toggle`). Same slug travels from Concept → Feature on promotion.
_Avoid_: id, name, handle

**Shape**:
The verb for the pre-probe stage — taking a rough Concept and giving it enough definition to be ready for `probe-feature`. Borrows from Shape Up methodology. Performed by the `shape-feature` skill, output is a Concept doc.
_Avoid_: brainstorm (associated with `superpowers:brainstorming`), scope (collides with In/Out of scope sections), ideate

**Probe**:
The verb for the discovery stage — gathering structured product/design/technical information for a known Feature. Performed by `probe-*` skills. Probing assumes the Feature is real; Shaping decides whether it should be.
_Avoid_: discover (used as a folder name only; `probe` is the verb)

**Promotion**:
The act of moving a shaped Concept from `docs/concepts/<slug>.md` into a real Feature folder at `docs/features/<slug>/concept.md`. Performed at the start of `probe-feature`. After promotion, the concept doc no longer lives in `docs/concepts/`.
_Avoid_: migration, import

**Framing**:
An alternative shape the same Concept could take — e.g., a lightweight version, an ambitious version, a different-audience version. A Concept holds 1–3 Framings during shaping.
_Avoid_: variant, option, alternative (use only in body text, not as the section heading)

**Chosen framing**:
The single Framing the user commits to before Promotion. Rejected Framings stay in the Concept doc as a record of "we considered this and picked otherwise."
_Avoid_: winner, pick, selected

**Status**:
A field on every Concept with one of three values: `shaping` (actively being worked on), `ready-to-probe` (gate passed, eligible for Promotion), `shelved` (decided not to pursue, kept as a record). `probe-feature` refuses to Promote a Concept whose Status is not `ready-to-probe`.
_Avoid_: state (collides with UI states), phase

**Appetite**:
A rough sizing field on a Concept — one of `small`, `medium`, `large` (mapped to time, e.g. ~1–2 weeks, ~3–4 weeks, >1 month). Non-binding: no downstream skill enforces it. Used as a converging force during shaping (kills oversized Framings) and as a later reference signal ("we said this was small, why is it 8 weeks?"). Borrowed from Shape Up.
_Avoid_: estimate (estimates are per-issue, set later), size (overloaded), budget

## Relationships

- A **Concept** is shaped by `shape-feature` and lives in `docs/concepts/<slug>.md`.
- A **Concept** is promoted into a **Feature** by `probe-feature`, which moves the concept doc into `docs/features/<slug>/concept.md`.
- A **Feature** has exactly one originating **Concept** (preserved as `concept.md` after promotion).
- A **Slug** is unique across both `docs/concepts/` and `docs/features/`. `shape-feature` and `probe-feature` both refuse to write if the slug collides.
- Not every **Concept** becomes a **Feature** — shelved concepts stay in `docs/concepts/` as a record of "we thought about this."

## Flagged ambiguities

- "Scope" was proposed as the new skill name but was rejected: `probe-product.md` already has dedicated `## In scope` / `## Out of scope` sections, so "scope" the skill would collide with "scope" the boundary-setting concept. Resolved: the skill is `shape-feature`; "scope" remains the boundary concept only.
- "Brainstorming" was rejected as a name because it's strongly associated with the external `superpowers:brainstorming` skill, which the user does not want to depend on. Resolved: the verb is "shape," not "brainstorm."
