# Issue NNN: <imperative title>

## Slice type: vertical | skeleton

## Vertical slice

- **User-facing outcome:** <what a user can do after this issue ships, end-to-end>
- **Not a layer:** confirm this is not "all the schema" or "all the UI"

For `skeleton` issues, describe the scaffolding purpose instead and why it cannot be a vertical slice.

## Modules touched

- **<module-name>:** changes <internal | public surface> — <one-line rationale>

## Context manifest

- **Read:**
  - `path/to/file.ts` (~<N> tokens) — <why>
- **Write:**
  - `path/to/file.ts`
  - `path/to/file.test.ts`
- **Reference (by section, not full read):**
  - `docs/features/<slug>/design-brief.md` §<section>
  - `docs/features/<slug>/tech-spec.md` §<section>
  - `docs/design-system.md` §<section>
- **Do NOT read:**
  - <directories or paths irrelevant to this issue>
- **Estimated context:** <X> tokens (must be < 100,000)

## Tests

- **Test files (written first):**
  - `path/to/feature.test.ts` — <what it covers>
- **Test commands:**
  - `npm test path/to/feature.test.ts`
- **TDD note:** write failing tests first → implement to green → refactor
- **Waiver:** <only if waived — explicit justification, e.g., "skeleton issue, tests in 003" or "config-only change">

## UX slice

- **User moment:** <which moment from design-brief>
- **States to handle:** empty / loading / error / success — <which apply, what each looks like>
- **Design tokens:** <which tokens from design-system.md>
- **Interaction notes:** <key interactions>

## Acceptance

- **Functional:**
  - [ ] All tests in Tests section pass
  - [ ] <additional behavioral check>
- **Visual:** matches design-brief §<section>
  - [ ] <visual check>
- **Module boundary check:**
  - [ ] No imports cross declared module public surfaces inappropriately

## Execution log (filled by execute-issue)

- **Token budget actual:** <filled post-run>
- **Files changed:** <filled post-run>
- **Subagent type used:** <filled post-run>

## Review verdict (filled by verify-issue)

- **Code review:** PASS | FAIL | NEEDS_USER — <summary>
- **QA doc:** `docs/features/<slug>/qa/NNN-qa-review.md`

## GitHub (filled by publish-issues, optional)

- **Issue:** #<N>
- **URL:** <url>
- **Last synced:** <ISO date>
