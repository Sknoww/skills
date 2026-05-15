# Add a pre-probe Shape stage to the Probe Library

**Status:** accepted (2026-05-13)

The Probe Library starts at `probe-feature`, which assumes the user arrives with a defined feature. There was no place to *shape* a half-formed idea into something concrete enough to probe — leaving users to either (a) probe prematurely on a mushy idea and produce a weak PRD, or (b) leave the library and brainstorm elsewhere (e.g., `superpowers:brainstorming`) with no artifact handoff back in.

We add `shape-feature` as a monolithic skill in `skills/shape/`. It produces `docs/concepts/<slug>.md` (a **Concept doc**) with a `Status` field (`shaping | ready-to-probe | shelved`) and a `Framings` / `Chosen framing` pair that captures alternatives considered. `probe-feature` gains a step 0: if `docs/concepts/<slug>.md` exists with `Status: ready-to-probe`, it **promotes** the concept by moving it to `docs/features/<slug>/concept.md` and passing the path to each probe sub-skill, which then drafts answers from it (light, judgment-based mapping — no heavy section tables).

## Considered options

- **Wrap `superpowers:brainstorming`.** Rejected — it produces no library-native artifact, doesn't speak the library's vocabulary (slug / module / slice), and conducts brainstorming as a generic activity not bound to the probe → PRD → slice flow.
- **Extend `probe-product` with shaping questions.** Rejected — collapses two distinct activities (deciding *whether/what* to build vs. interviewing *about* a known feature). Probing assumes the feature is real; shaping decides if it should be.
- **Name the new skill `scope`.** Rejected — collides with the existing `## In scope` / `## Out of scope` vocabulary used throughout `probe-product.md` and the PRD template.
- **Place concept docs at `docs/features/<slug>/concept.md` from the start.** Rejected — forces a slug commitment before shaping is done, and creates phantom feature folders for concepts that get shelved. A separate `docs/concepts/` directory lets concepts live independently until they're promoted.
- **No `Status` gate; advisory only.** Rejected — `probe-feature` enforcing `Status: ready-to-probe` mirrors the library's existing phase-gate philosophy (`write-prd` refuses on unresolved Open questions). It also gives shelved concepts a real, recorded home.
- **Heavy explicit mapping tables in each probe SKILL.md.** Rejected — triples skill length and creates maintenance burden. Light, judgment-based drafting is sufficient given the concept doc's self-describing section names (`Problem (rough)`, `Beneficiary (rough)`, `Explicit no-gos`).
- **Make `probe-design` pre-fill from the concept doc.** Rejected — design questions (tone, motion, density, accessibility floor) have weak overlap with shape-stage content. `probe-design` reads the concept doc as background only.

## Consequences

- The library lifecycle gains an explicit upstream stage: `shape → discover → synthesize → plan → implement → integrate`.
- `docs/concepts/` becomes a first-class location in user projects, alongside `docs/features/` and `docs/adr/`.
- `probe-feature`, `probe-product`, and `probe-technical` each gain a small "Concept doc handling" section. `probe-design` gains a one-line note in its step 2 only.
- The Concept doc's `Framings` section preserves rejected alternatives as a permanent record inside the feature folder after promotion — useful when the feature is later revisited.
- Slug uniqueness now spans both `docs/concepts/` and `docs/features/`. Both `shape-feature` and `probe-feature` refuse to write to a colliding slug.
- The README's quick-start gains an optional zeroth step (`shape-feature`) before `probe-feature`.
