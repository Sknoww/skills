# Probe-Feature Skill Library Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the 12-skill probe-feature skill library described in `docs/superpowers/specs/2026-05-10-probe-feature-skill-library-design.md`.

**Architecture:** A flat-installable Claude Code skill library. Source repo organizes skills under category folders (`flow/`, `discover/`, `synthesize/`, `plan/`, `implement/`, `integrate/`, `shared/`); install scripts copy each leaf skill folder (containing `SKILL.md`) into `~/.claude/skills/`. Skills produce/consume markdown artifacts under `docs/features/<slug>/` in the user's project. The keystone skill (`slice-issues`) enforces a 100k token cap per issue using a bundled Python heuristic.

**Tech Stack:** Markdown for skill content and templates; Python 3 (stdlib only) for the token estimator; PowerShell + Bash for install scripts; `gh` CLI for GitHub integration.

**Working directory:** `C:\Users\hsfro\code\claude\temp_skills` (Windows). Cross-platform paths use forward slashes inside skill content; install scripts are environment-specific.

**SKILL.md format (used in many tasks below):**
```
---
name: <skill-name>
description: <one-line capability>. Use when <specific triggers>.
---

<body — procedure, preconditions, etc.>
```

---

## Task 1: Bootstrap repo (git, gitignore, copy spec)

**Files:**
- Create: `.gitignore`
- Move: `docs/superpowers/specs/2026-05-10-probe-feature-skill-library-design.md` (already exists, will be included in first commit)

- [ ] **Step 1: Initialize git repo**

Run:
```
git init
```
Expected: `Initialized empty Git repository in C:/Users/hsfro/code/claude/temp_skills/.git/`

- [ ] **Step 2: Create `.gitignore`**

Create `.gitignore` with:
```
# Local scratch
scratch/
*.local.md

# OS junk
.DS_Store
Thumbs.db

# Python
__pycache__/
*.pyc
.pytest_cache/
.venv/

# Editor
.vscode/
.idea/

# Test artifacts
test-output/
```

- [ ] **Step 3: Verify spec exists**

Run:
```
ls docs/superpowers/specs/2026-05-10-probe-feature-skill-library-design.md
```
Expected: file listed (already created during brainstorming).

- [ ] **Step 4: Initial commit**

```
git add .gitignore docs/superpowers/specs/2026-05-10-probe-feature-skill-library-design.md
git commit -m "chore: bootstrap repo with approved design spec"
```

---

## Task 2: README skeleton

**Files:**
- Create: `README.md`

- [ ] **Step 1: Create README.md skeleton**

Content:
```markdown
# Probe-Feature Skill Library

A Claude Code skill library for PRD-driven feature development. Takes a feature from rough idea through probe → PRD/design-brief/tech-spec → vertical-slice issues → per-issue execution with separate-agent review.

**Status:** Implementation in progress. See `docs/superpowers/specs/` for the approved design and `docs/superpowers/plans/` for the build plan.

## Quick start (after install)

```
> probe-feature           # interactive — produces docs/features/<slug>/ bundle
> slice-issues            # produces issues/NNN-*.md and SEQUENCE.md
> execute-issue 001-...   # loop per issue
> verify-issue 001-...    # after each execute
> publish-issues          # optional — syncs to GitHub
```

## Install

See install instructions below (filled in at Task 18).
```

- [ ] **Step 2: Commit**

```
git add README.md
git commit -m "docs: add README skeleton"
```

---

## Task 3: Token estimator script (TDD)

**Files:**
- Create: `scripts/estimate_tokens.py`
- Create: `tests/test_estimate_tokens.py`

This is the only real code in the project; it gets full TDD.

- [ ] **Step 1: Create test directory and write failing tests**

Create `tests/test_estimate_tokens.py`:
```python
import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "estimate_tokens.py"


def run_estimator(args):
    result = subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        capture_output=True, text=True
    )
    return result.stdout, result.stderr, result.returncode


def test_empty_file_zero_tokens(tmp_path):
    f = tmp_path / "empty.py"
    f.write_text("")
    out, _, code = run_estimator([str(f)])
    assert code == 0
    assert "\t0\n" in out or out.strip().endswith("\t0")
    assert "TOTAL\t0" in out


def test_code_file_uses_3_5_divisor(tmp_path):
    # 350 chars / 3.5 = 100 tokens
    f = tmp_path / "code.ts"
    f.write_text("x" * 350)
    out, _, code = run_estimator([str(f)])
    assert code == 0
    assert "\t100" in out
    assert "TOTAL\t100" in out


def test_markdown_uses_4_divisor(tmp_path):
    # 400 chars / 4.0 = 100 tokens
    f = tmp_path / "doc.md"
    f.write_text("x" * 400)
    out, _, code = run_estimator([str(f)])
    assert code == 0
    assert "\t100" in out
    assert "TOTAL\t100" in out


def test_multiple_files_with_total(tmp_path):
    f1 = tmp_path / "a.ts"
    f1.write_text("x" * 350)  # 100
    f2 = tmp_path / "b.md"
    f2.write_text("x" * 400)  # 100
    out, _, code = run_estimator([str(f1), str(f2)])
    assert code == 0
    assert "TOTAL\t200" in out


def test_unknown_extension_uses_prose_divisor(tmp_path):
    # Files without a known code extension treat as prose (divisor 4.0)
    f = tmp_path / "data.txt"
    f.write_text("x" * 400)
    out, _, code = run_estimator([str(f)])
    assert code == 0
    assert "\t100" in out


def test_nonexistent_file_errors(tmp_path):
    out, err, code = run_estimator([str(tmp_path / "nope.py")])
    assert code != 0
    assert "nope.py" in err or "nope.py" in out
```

- [ ] **Step 2: Run tests, confirm they fail**

```
python -m pytest tests/test_estimate_tokens.py -v
```
Expected: all 6 tests FAIL with FileNotFoundError or similar (script doesn't exist yet).

- [ ] **Step 3: Implement `scripts/estimate_tokens.py`**

Create `scripts/estimate_tokens.py`:
```python
#!/usr/bin/env python3
"""Estimate token counts for a list of files.

Heuristic: chars / 3.5 for code, chars / 4.0 for prose/markdown.
Bundled with slice-issues for the 100k context budget gate.

Usage: python estimate_tokens.py path1 path2 ...
Output (tab-separated, one line per file plus TOTAL):
    path<TAB>estimate
    ...
    TOTAL<TAB>sum
Exit code 0 on success, 1 if any path could not be read.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

CODE_EXTS = {
    ".py", ".pyi",
    ".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs",
    ".go",
    ".rs",
    ".java", ".kt", ".kts",
    ".swift",
    ".cpp", ".cc", ".cxx", ".c", ".h", ".hpp",
    ".cs",
    ".rb",
    ".php",
    ".scala",
    ".sh", ".bash", ".zsh", ".fish",
    ".ps1",
    ".sql",
    ".lua",
    ".dart",
    ".vue", ".svelte",
}


def estimate(path: Path) -> int:
    text = path.read_text(encoding="utf-8", errors="replace")
    divisor = 3.5 if path.suffix.lower() in CODE_EXTS else 4.0
    return int(len(text) / divisor)


def main(argv: list[str]) -> int:
    if not argv:
        print("usage: estimate_tokens.py path1 [path2 ...]", file=sys.stderr)
        return 2

    errors: list[str] = []
    total = 0
    lines: list[str] = []
    for raw in argv:
        path = Path(raw)
        if not path.exists() or not path.is_file():
            errors.append(f"missing: {raw}")
            continue
        try:
            n = estimate(path)
        except OSError as exc:
            errors.append(f"read failed: {raw}: {exc}")
            continue
        total += n
        lines.append(f"{raw}\t{n}")

    print("\n".join(lines))
    print(f"TOTAL\t{total}")

    if errors:
        for err in errors:
            print(err, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
```

- [ ] **Step 4: Run tests, confirm they pass**

```
python -m pytest tests/test_estimate_tokens.py -v
```
Expected: all 6 tests PASS.

- [ ] **Step 5: Commit**

```
git add scripts/estimate_tokens.py tests/test_estimate_tokens.py
git commit -m "feat: add estimate_tokens.py heuristic with tests"
```

---

## Task 4: Shared templates

**Files:**
- Create: `skills/shared/templates/PRD-template.md`
- Create: `skills/shared/templates/DESIGN-BRIEF-template.md`
- Create: `skills/shared/templates/TECH-SPEC-template.md`
- Create: `skills/shared/templates/ISSUE-template.md`
- Create: `skills/shared/templates/DESIGN-SYSTEM-template.md`

These are canonical reference copies. Each write-* skill bundles its own copy (Tasks 8–10). probe-design bundles the design-system template (Task 6). slice-issues bundles the issue template (Task 12).

- [ ] **Step 1: Create `skills/shared/templates/PRD-template.md`**

```markdown
# PRD — <feature name>

## Problem

<1-3 sentences describing the user pain or business gap this addresses.>

## Users & JTBD

- **Primary user:** <role / segment>
- **Job to be done:** When <situation>, I want <motivation>, so I can <outcome>.

## Goals

- <measurable outcome>
- <measurable outcome>

## Non-goals

- <explicit out-of-scope item>
- <explicit out-of-scope item>

## User stories

- As a <user>, I can <action>, so that <outcome>.

## Success metrics

- <metric>: <baseline> → <target>

## Open questions

<Only items still in flight at PRD time. Unresolved items go BACK to probe-product, not into this section as TBDs.>
```

- [ ] **Step 2: Create `skills/shared/templates/DESIGN-BRIEF-template.md`**

```markdown
# Design Brief — <feature name>

## Tone & references

- **Feels like:** <reference products — "Linear, not Jira">
- **Tone words:** <e.g., precise, calm, expert>

## Key user moments

1. **<moment name>** — <what the user sees and feels>
2. <moment>

## Screen-by-screen states

### <screen name>

- **Empty:** <description; design tokens used>
- **Loading:** <description>
- **Error:** <description>
- **Success:** <description>

## Design tokens used

- <token name from docs/design-system.md §<section>>

## Microcopy direction

- <voice notes — concise, conversational, etc.>

## Motion

- <timing, easing, what animates and why>
```

- [ ] **Step 3: Create `skills/shared/templates/TECH-SPEC-template.md`**

```markdown
# Tech Spec — <feature name>

## Module map

ALWAYS WRITTEN — `slice-issues` depends on this.

- **<module-name>**
  - Responsibility: <one sentence>
  - Public surface: <exported types / functions / components>
  - Internal-only files: <files that must not be imported from outside>
  - Allowed dependencies: <other modules this may import from>

## Architecture deltas

<Only if the feature warrants. Otherwise: "No structural changes — additive within existing modules.">

## Data model deltas

<Only if applicable. Migration notes included.>

## API deltas

<Only if applicable. Endpoint contracts, request/response shapes.>

## Open technical questions

<Only items still in flight. Unresolved items go back to probe-technical.>
```

- [ ] **Step 4: Create `skills/shared/templates/ISSUE-template.md`**

```markdown
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
```

- [ ] **Step 5: Create `skills/shared/templates/DESIGN-SYSTEM-template.md`**

```markdown
# Design System

A starter scaffold. Fill in the values that reflect this project's actual design language. Skills reference sections of this file by header.

## Tokens

### Color
- Primary: <hex or CSS var>
- Background: <hex or CSS var>
- Surface: <hex or CSS var>
- Text-primary / Text-secondary: <hex or CSS var>
- Border: <hex or CSS var>
- Success / Warning / Error: <hex or CSS var>

### Typography
- Font family: <stack>
- Scale: 12 / 14 / 16 / 18 / 24 / 32

### Spacing
- Scale: 4 / 8 / 12 / 16 / 24 / 32 / 48

### Radius
- none / sm / md / lg / full

### Shadow
- <levels>

## Components

- Button, Input, Card, Modal, Toast — link to component file or describe defaults

## Patterns

- **States** (empty / loading / error / success): global conventions
- **Motion:** timing/easing defaults
- **Density:** compact vs comfortable

## Accessibility floor

- WCAG <AA / AAA>
- Focus styles, contrast minimums, keyboard nav patterns
```

- [ ] **Step 6: Verify all 5 template files exist**

Run (PowerShell):
```
Get-ChildItem skills/shared/templates/
```
Expected output includes all 5 files.

- [ ] **Step 7: Commit**

```
git add skills/shared/templates/
git commit -m "feat: add canonical templates (PRD, design-brief, tech-spec, issue, design-system)"
```

---

## Task 5: probe-product/SKILL.md

**Files:**
- Create: `skills/discover/probe-product/SKILL.md`

- [ ] **Step 1: Create the SKILL.md**

```markdown
---
name: probe-product
description: Conducts an interactive product discovery interview for a new feature — JTBD, primary user, success metrics, in-scope/out-of-scope, business trigger. Use when starting the discovery phase for a new feature, before writing the PRD.
---

# probe-product

Conduct an interactive product-discovery interview and write the results to `docs/features/<slug>/probe-product.md`. One question at a time. If a question can be answered by reading existing project docs, read them instead of asking.

## Preconditions

None — this is the entry point of the discover phase.

## Procedure

### 1. Identify the feature

Ask:
> "What is the feature name? (Short slug, lowercase-hyphenated, e.g. `dark-mode-toggle`.)"

Then ask:
> "Short human-readable name? (e.g. 'Dark mode toggle')"

Create `docs/features/<slug>/` if it does not exist.

### 2. Read existing context silently

Read these if they exist; do not ask permission, do not summarize back:
- `CONTEXT.md`, `CONTEXT-MAP.md`
- `README.md`
- `docs/adr/*.md`

Use what you find to skip questions whose answers are already documented.

### 3. Interview — ask one at a time

Ask each question only if not already answered by existing context. Wait for the answer before moving on.

1. **Trigger** — "What's prompting this work now? Bug, customer ask, strategic shift, internal pain?"
2. **Problem** — "In 1–3 sentences: what user pain or business gap does this address?"
3. **Primary user** — "Who is the primary user? Be concrete — a role, segment, or persona."
4. **JTBD** — "Complete the sentence: When <situation>, I want <motivation>, so I can <outcome>."
5. **In-scope** — "What's explicitly IN scope? Three to five bullets."
6. **Out-of-scope** — "What's explicitly OUT of scope — adjacent things you're deliberately not doing?"
7. **Success metrics** — "How will we know this worked? Each metric: name + baseline + target."
8. **Stakeholders** — "Anyone else involved or affected? Brief — names/roles/why."
9. **Open questions** — "What unresolved product questions do you already know about? These seed the next steps."

### 4. Write the artifact

Write `docs/features/<slug>/probe-product.md` with this structure:

```markdown
# Probe — Product: <name> (<slug>)

**Date:** <YYYY-MM-DD>
**Trigger:** <answer>

## Problem
<answer>

## Primary user
<answer>

## JTBD
When <situation>, I want <motivation>, so I can <outcome>.

## In scope
- <bullet>

## Out of scope
- <bullet>

## Success metrics
- <metric>: <baseline> → <target>

## Stakeholders
- <name/role/why>

## Open questions
- <bullet>
```

### 5. Report

After writing, print:
> "Wrote `docs/features/<slug>/probe-product.md`. Next: run `probe-design` or `probe-technical` (parallel) — both must be done before `write-prd`."

## Rules

- One question at a time. Never batch.
- If the user gives a vague answer, push back once with a sharpening prompt; if still vague, capture as an Open question.
- Never fabricate answers — if the user can't answer, list it as an Open question.
- The Open questions section is the handoff back to the user for follow-up.
```

- [ ] **Step 2: Verify file structure**

Run:
```
Select-String -Path skills/discover/probe-product/SKILL.md -Pattern "^---$|^name:|^description:" | Select-Object -First 4
```
Expected: matches `---`, `name: probe-product`, `description: ...`, `---`.

- [ ] **Step 3: Commit**

```
git add skills/discover/probe-product/SKILL.md
git commit -m "feat: add probe-product skill"
```

---

## Task 6: probe-design/SKILL.md + bundled design-system template

**Files:**
- Create: `skills/discover/probe-design/SKILL.md`
- Create: `skills/discover/probe-design/DESIGN-SYSTEM-template.md`

- [ ] **Step 1: Create the bundled DESIGN-SYSTEM-template.md**

Copy the content from `skills/shared/templates/DESIGN-SYSTEM-template.md` (created in Task 4 Step 5) verbatim into `skills/discover/probe-design/DESIGN-SYSTEM-template.md`. This is a deliberate co-copy so the skill folder is self-contained at install time.

- [ ] **Step 2: Create the SKILL.md**

```markdown
---
name: probe-design
description: Conducts an interactive UX/design discovery interview for a new feature — tone, references, key user moments, accessibility floor, density, motion, error/empty/loading states. Scaffolds docs/design-system.md from template if missing. Use when probing the design dimension of a feature.
---

# probe-design

Conduct an interactive design-discovery interview and write the results to `docs/features/<slug>/probe-design.md`. One question at a time. Parallel to `probe-product` and `probe-technical` — none blocks the others.

## Preconditions

None.

## Procedure

### 1. Identify the feature

If invoked standalone, ask:
> "What is the feature slug? (lowercase-hyphenated)"

If invoked via `probe-feature`, the slug is passed in.

### 2. Check for `docs/design-system.md`

If `docs/design-system.md` does NOT exist:
> "No `docs/design-system.md` found. I can scaffold one from a template — you fill in the actual tokens/values for this project. Scaffold now? (y/n)"

If yes, copy the bundled `DESIGN-SYSTEM-template.md` (in this skill folder) to `docs/design-system.md`. Then prompt:
> "Scaffold written to `docs/design-system.md`. Open it and fill in your project's actual tokens before continuing? (y/n)"

If the user wants to fill it in first, end the skill here and tell them to re-invoke once done. Otherwise continue with the template as the current source of truth.

### 3. Interview — ask one at a time

1. **Emotional tone** — "What should this feel like? Give me 3 adjectives (e.g., calm / precise / confident)."
2. **Reference products** — "Name 1–3 products this should feel like — and one it should NOT feel like."
3. **Key user moments** — "What are the 2–4 key moments in this feature? Each: when it happens and the desired feeling."
4. **Information density** — "Comfortable, balanced, or compact? When in doubt: which way do we err?"
5. **Motion philosophy** — "How much motion? Minimal / restrained / expressive. What animates and why?"
6. **State philosophy** — "How do empty / loading / error states feel? Same vibe as success or distinct?"
7. **Accessibility floor** — "WCAG AA, AAA, or other floor? Any specific concerns (color-vision, motion-sensitive, screen-reader)?"
8. **Microcopy voice** — "Voice and tone for microcopy: terse, conversational, technical, playful?"
9. **Open design questions** — "What design questions do you already know are unresolved?"

### 4. Write the artifact

Write `docs/features/<slug>/probe-design.md`:

```markdown
# Probe — Design: <name> (<slug>)

**Date:** <YYYY-MM-DD>

## Tone
- Adjectives: <three>
- Reference products (yes): <list>
- Reference products (no): <list>

## Key user moments
1. <moment> — <feeling/intent>
2. ...

## Density
<answer>

## Motion
<answer>

## States philosophy
<answer>

## Accessibility floor
<answer>

## Microcopy voice
<answer>

## Open design questions
- <bullet>
```

### 5. Report

After writing, print:
> "Wrote `docs/features/<slug>/probe-design.md`. Design system: `docs/design-system.md`. Next: `probe-product` / `probe-technical` (if not yet run), then `write-prd` + `write-design-brief`."

## Rules

- One question at a time.
- If `docs/design-system.md` exists and is already populated, do NOT overwrite — reference its sections in `probe-design.md` where relevant.
- Never invent design references the user didn't supply.
```

- [ ] **Step 3: Verify both files exist**

Run:
```
Get-ChildItem skills/discover/probe-design/
```
Expected: `SKILL.md`, `DESIGN-SYSTEM-template.md`.

- [ ] **Step 4: Commit**

```
git add skills/discover/probe-design/
git commit -m "feat: add probe-design skill with bundled design-system template"
```

---

## Task 7: probe-technical/SKILL.md

**Files:**
- Create: `skills/discover/probe-technical/SKILL.md`

- [ ] **Step 1: Create the SKILL.md**

```markdown
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

Write `docs/features/<slug>/probe-technical.md`:

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
```

- [ ] **Step 2: Commit**

```
git add skills/discover/probe-technical/SKILL.md
git commit -m "feat: add probe-technical skill"
```

---

## Task 8: write-prd + bundled template

**Files:**
- Create: `skills/synthesize/write-prd/SKILL.md`
- Create: `skills/synthesize/write-prd/PRD-template.md`

- [ ] **Step 1: Create the bundled PRD-template.md**

Copy the content from `skills/shared/templates/PRD-template.md` (Task 4 Step 1) verbatim into `skills/synthesize/write-prd/PRD-template.md`.

- [ ] **Step 2: Create the SKILL.md**

```markdown
---
name: write-prd
description: Synthesizes probe-product + probe-design + probe-technical into a complete PRD at docs/features/<slug>/prd.md. Refuses to run with unresolved items — they must go back to the relevant probe first. Use after all three probe-* skills have run for a feature.
---

# write-prd

Synthesize the three probe outputs into a concrete, complete PRD. No "TBD" sections allowed.

## Preconditions (HARD)

All three of these must exist at `docs/features/<slug>/`:
- `probe-product.md`
- `probe-design.md`
- `probe-technical.md`

If any are missing, abort with:
> "Cannot write PRD — missing `<file>`. Run `probe-<name>` first."

## Procedure

### 1. Resolve slug

Ask for slug if not provided. Confirm all three probe files exist.

### 2. Read all three probes

Read fully. Identify any items in the "Open questions" sections of each.

### 3. Gate on unresolved items

If ANY probe has open questions in the "Open questions" section, abort with:

> "Cannot synthesize PRD — unresolved items in <probe-name>.md:
> - <each open question>
>
> Re-run the relevant probe-* skill to resolve, then re-invoke write-prd."

### 4. Synthesize PRD

Read the bundled `PRD-template.md`. Fill in each section by drawing from the probes:
- **Problem** ← probe-product Problem + Trigger
- **Users & JTBD** ← probe-product Primary user + JTBD
- **Goals** ← probe-product Success metrics + In scope (as outcomes, not features)
- **Non-goals** ← probe-product Out of scope
- **User stories** ← derived from JTBD + key user moments from probe-design (1 story per moment)
- **Success metrics** ← probe-product Success metrics verbatim
- **Open questions** ← ONLY items the user has explicitly marked "in flight" — distinct from probe Open questions (those gated). If empty, write "None at PRD write time."

### 5. Write

Write `docs/features/<slug>/prd.md`.

### 6. Report

> "Wrote `docs/features/<slug>/prd.md`. Next: `write-design-brief` and `write-tech-spec`."

## Rules

- Refuse "TBD" — if you don't know, abort and send the user back to probes.
- Use the user's wording wherever possible. Don't paraphrase the JTBD.
- Don't invent metrics, goals, or stories not derivable from the probes.
```

- [ ] **Step 3: Verify**

```
Get-ChildItem skills/synthesize/write-prd/
```
Expected: `SKILL.md`, `PRD-template.md`.

- [ ] **Step 4: Commit**

```
git add skills/synthesize/write-prd/
git commit -m "feat: add write-prd skill with bundled PRD template"
```

---

## Task 9: write-design-brief + bundled template

**Files:**
- Create: `skills/synthesize/write-design-brief/SKILL.md`
- Create: `skills/synthesize/write-design-brief/DESIGN-BRIEF-template.md`

- [ ] **Step 1: Create the bundled DESIGN-BRIEF-template.md**

Copy the content from `skills/shared/templates/DESIGN-BRIEF-template.md` (Task 4 Step 2) verbatim into `skills/synthesize/write-design-brief/DESIGN-BRIEF-template.md`.

- [ ] **Step 2: Create the SKILL.md**

```markdown
---
name: write-design-brief
description: Translates probe-design + PRD into an actionable design brief with screen-by-screen states, design tokens, and motion specs at docs/features/<slug>/design-brief.md. Use after the PRD is written.
---

# write-design-brief

Synthesize `probe-design.md` and `prd.md` into a design brief that issues can reference by section in their UX slices.

## Preconditions (HARD)

Both must exist at `docs/features/<slug>/`:
- `prd.md`
- `probe-design.md`

`docs/design-system.md` must exist (scaffolded by `probe-design` if needed).

If any are missing, abort with a pointer to the upstream skill.

## Procedure

### 1. Read inputs

- `docs/features/<slug>/prd.md`
- `docs/features/<slug>/probe-design.md`
- `docs/design-system.md`

### 2. Fill the brief

Read the bundled `DESIGN-BRIEF-template.md`. Fill each section:
- **Tone & references** ← probe-design Tone section
- **Key user moments** ← probe-design moments, with each fleshed out into a screen-level description
- **Screen-by-screen states** ← for each moment, write empty/loading/error/success entries. Pull state philosophy from probe-design.
- **Design tokens used** ← cross-reference `docs/design-system.md` and list sections referenced
- **Microcopy direction** ← probe-design Microcopy voice
- **Motion** ← probe-design Motion philosophy

### 3. Write

Write `docs/features/<slug>/design-brief.md`.

### 4. Report

> "Wrote `docs/features/<slug>/design-brief.md`. Next: `write-tech-spec`, then `slice-issues`."

## Rules

- Section headers must be stable — issues will reference them by name (e.g., "design-brief.md §Screen-by-screen states > signup").
- Reference design tokens by their section in `docs/design-system.md` — don't inline tokens.
- Each key moment must have explicit empty / loading / error / success states. If a state doesn't apply, say so explicitly ("N/A — never empty in this flow").
```

- [ ] **Step 3: Commit**

```
git add skills/synthesize/write-design-brief/
git commit -m "feat: add write-design-brief skill with bundled template"
```

---

## Task 10: write-tech-spec + bundled template

**Files:**
- Create: `skills/synthesize/write-tech-spec/SKILL.md`
- Create: `skills/synthesize/write-tech-spec/TECH-SPEC-template.md`

- [ ] **Step 1: Create the bundled TECH-SPEC-template.md**

Copy the content from `skills/shared/templates/TECH-SPEC-template.md` (Task 4 Step 3) verbatim into `skills/synthesize/write-tech-spec/TECH-SPEC-template.md`.

- [ ] **Step 2: Create the SKILL.md**

```markdown
---
name: write-tech-spec
description: Translates probe-technical + PRD into a tech spec at docs/features/<slug>/tech-spec.md. Always writes the Module map section (slice-issues depends on it); other sections are conditional on tech-spec depth signal from probe-technical. Use after the PRD is written.
---

# write-tech-spec

Synthesize `probe-technical.md` and `prd.md` into a tech spec. The **Module map section is always written**, even for trivial features — slice-issues depends on it. Other sections are written only when the feature warrants them.

## Preconditions (HARD)

Both must exist at `docs/features/<slug>/`:
- `prd.md`
- `probe-technical.md`

If missing, abort with a pointer to the upstream skill.

## Procedure

### 1. Read inputs

- `docs/features/<slug>/prd.md`
- `docs/features/<slug>/probe-technical.md`

Note the `Tech spec depth signal` from probe-technical: `full` or `module-map-only`.

### 2. Always write Module map

For each existing module touched + each new module, write:
- **Module name**
- **Responsibility** (one sentence)
- **Public surface** (exports — types, functions, components)
- **Internal-only files** (must not be imported from outside)
- **Allowed dependencies** (which other modules it may import from)

Pull from probe-technical Modules touched + Modules new.

### 3. Conditional sections (only if depth signal is `full`)

- **Architecture deltas** — structural changes
- **Data model deltas** — schemas, migrations
- **API deltas** — endpoints, contracts
- **Open technical questions** — items the user has explicitly marked "in flight"

If depth signal is `module-map-only`, write each conditional section with a single line: `No <category> changes — additive within existing modules.`

### 4. Write

Write `docs/features/<slug>/tech-spec.md`.

### 5. Report

> "Wrote `docs/features/<slug>/tech-spec.md` (depth: <full | module-map-only>). Next: `slice-issues`."

## Rules

- Module map section is NEVER skipped, even for trivial features.
- A module's public surface should be small and named — avoid "anything in this folder."
- If probe-technical's Verification findings show mismatches, surface them in Module map as comments, not silently.
```

- [ ] **Step 3: Commit**

```
git add skills/synthesize/write-tech-spec/
git commit -m "feat: add write-tech-spec skill with bundled template"
```

---

## Task 11: probe-feature/SKILL.md (orchestrator)

**Files:**
- Create: `skills/flow/probe-feature/SKILL.md`

- [ ] **Step 1: Create the SKILL.md**

```markdown
---
name: probe-feature
description: Thin orchestrator that runs probe-product, probe-design, probe-technical for a new feature, then write-prd, write-design-brief, and write-tech-spec. The friendly front door — composes sub-skills, contains no probing logic of its own. Use when starting work on a new feature.
---

# probe-feature

Thin orchestrator. Composes the six discover + synthesize sub-skills for a new feature. Does NOT contain probing logic of its own — if probing behavior needs to change, fix the sub-skill.

## Preconditions

None. Working directory should be the user's project repo.

## Procedure

### 1. Get the feature identity

Ask:
> "Feature name? (Short human label, e.g. 'Dark mode toggle')"

Then:
> "Slug? (lowercase-hyphenated, e.g. 'dark-mode-toggle')"

Create `docs/features/<slug>/` if it does not exist.

### 2. Run the three probes (sequentially in this session — they can't be truly parallel because they share the user)

For each:
- Invoke the sub-skill (`probe-product`, then `probe-design`, then `probe-technical`).
- Pass the slug through.
- After each, confirm the artifact was written before continuing.

### 3. Gate check

After all three probes:
- Read each probe's Open questions section.
- If any have unresolved items, surface them as a single list:
  > "Unresolved items remain. Address these by re-running the relevant probe-* skill, then re-invoke probe-feature (or write-prd / write-design-brief / write-tech-spec directly).
  >
  > <list of open questions per probe>"
- Stop. Do not proceed to synthesis.

### 4. Run synthesis

In order:
- `write-prd`
- `write-design-brief`
- `write-tech-spec` (depth follows probe-technical's signal)

### 5. Report

> "Feature probe complete. Bundle at `docs/features/<slug>/`:
> - probe-product.md
> - probe-design.md
> - probe-technical.md
> - prd.md
> - design-brief.md
> - tech-spec.md (depth: <full | module-map-only>)
>
> Next: `slice-issues` to break this into vertical-slice issues."

## Rules

- This skill is intentionally thin. It does NOT ask its own questions — every question comes from a sub-skill.
- Do NOT skip probes even if you "already know" the answers — the artifacts are downstream dependencies.
- Do NOT proceed to synthesis if probes have unresolved Open questions.
```

- [ ] **Step 2: Commit**

```
git add skills/flow/probe-feature/SKILL.md
git commit -m "feat: add probe-feature orchestrator skill"
```

---

## Task 12: slice-issues (the keystone) + bundled assets

**Files:**
- Create: `skills/plan/slice-issues/SKILL.md`
- Create: `skills/plan/slice-issues/ISSUE-TEMPLATE.md`
- Create: `skills/plan/slice-issues/estimate_tokens.py`

- [ ] **Step 1: Copy estimate_tokens.py into slice-issues folder**

Copy `scripts/estimate_tokens.py` (Task 3) verbatim into `skills/plan/slice-issues/estimate_tokens.py`. This deliberate duplicate is so the skill folder is self-contained at install time.

- [ ] **Step 2: Copy ISSUE-TEMPLATE.md into slice-issues folder**

Copy `skills/shared/templates/ISSUE-template.md` (Task 4 Step 4) verbatim into `skills/plan/slice-issues/ISSUE-TEMPLATE.md`.

- [ ] **Step 3: Create the SKILL.md**

```markdown
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
```

- [ ] **Step 4: Verify**

```
Get-ChildItem skills/plan/slice-issues/
```
Expected: `SKILL.md`, `ISSUE-TEMPLATE.md`, `estimate_tokens.py`.

- [ ] **Step 5: Verify the bundled script still runs**

```
python skills/plan/slice-issues/estimate_tokens.py skills/plan/slice-issues/SKILL.md
```
Expected: a line `skills/plan/slice-issues/SKILL.md<TAB><N>` and `TOTAL<TAB><N>`, exit 0.

- [ ] **Step 6: Commit**

```
git add skills/plan/slice-issues/
git commit -m "feat: add slice-issues keystone skill with bundled template and token estimator"
```

---

## Task 13: sequence-issues/SKILL.md

**Files:**
- Create: `skills/plan/sequence-issues/SKILL.md`

- [ ] **Step 1: Create the SKILL.md**

```markdown
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
```

- [ ] **Step 2: Commit**

```
git add skills/plan/sequence-issues/SKILL.md
git commit -m "feat: add sequence-issues skill"
```

---

## Task 14: execute-issue/SKILL.md

**Files:**
- Create: `skills/implement/execute-issue/SKILL.md`

- [ ] **Step 1: Create the SKILL.md**

```markdown
---
name: execute-issue
description: Executes a single issue by dispatching a Claude Code subagent with the issue's Context manifest as the starting prompt. Prompts the user for subagent type (default general-purpose). Records actual files read and token usage back into the issue. Use to implement an issue from a feature's issues/ folder.
---

# execute-issue

Dispatch a subagent to implement one issue, isolated to the context the issue declared. Update the issue's Execution log with results.

## Preconditions (HARD)

The target issue file must:
- Exist
- Have a filled Context manifest (Read / Write / Estimated context)
- Have an EMPTY Execution log section

If Execution log is already filled, ask:
> "Issue <NNN> has already been executed. Options: (1) re-run (overwrite log), (2) skip, (3) abort. Which?"

## Procedure

### 1. Resolve target issue

Argument: a path or NNN. Resolve to `docs/features/<slug>/issues/NNN-<slug>.md`. Read the full issue.

### 2. Prompt for subagent type

Ask:
> "Which subagent type for this issue? Options:
> - general-purpose (default, broad capability)
> - Frontend Developer
> - Backend Architect
> - Senior Developer
> - Other (specify)
>
> Press Enter for general-purpose."

Capture the choice.

### 3. Build the subagent prompt

Compose the prompt from the issue's:
- Vertical slice section (user-facing outcome)
- Modules touched
- Context manifest (Read / Write / Reference / Do NOT read / Estimated context)
- Tests section (TDD discipline reminder)
- UX slice
- Acceptance

Prefix with:
> "You are executing issue <NNN> for feature <slug>. Read ONLY the files in your Context manifest's Read list. Do NOT browse the codebase beyond what's listed. Follow TDD: write the failing tests in your Write list FIRST, then implement, then refactor.
>
> If the `superpowers:test-driven-development` skill is available, invoke it.
>
> When done, report:
> - Files changed (with paths)
> - Files actually read (for token-actual measurement)
> - Test command(s) run and result
> - Any deviations from the manifest and why
> - Status: DONE / BLOCKED / NEEDS_USER"

### 4. Dispatch via Agent tool

Use the Agent tool with the chosen `subagent_type`. Pass the composed prompt as the agent task. Wait for the result.

### 5. Measure actual context

From the subagent's report of files actually read, locate the bundled token estimator (after install, all skills are flat siblings at `~/.claude/skills/`):
```
python ~/.claude/skills/slice-issues/estimate_tokens.py <each-file>
```
Capture the total.

If the script isn't found at that path (e.g., the user installed in a non-standard location), skip the actual-token measurement and record `Token budget actual: unmeasured` with a note in the Execution log.

### 6. Update Execution log

Append to the issue's `## Execution log (filled by execute-issue)` section:
- **Token budget actual:** <N>
- **Files changed:** <list>
- **Subagent type used:** <chosen>
- **Date:** <YYYY-MM-DD>

### 7. Report

> "Issue <NNN> executed. Status: <DONE | BLOCKED | NEEDS_USER>. Token actual: <N> (estimated was <M>). Next: `verify-issue <NNN>`."

## Rules

- Always dispatch a subagent — don't implement inline. The whole point is isolated context.
- Do NOT modify the issue's other sections (Vertical slice, Modules, Context manifest, etc.) — only the Execution log.
- If the subagent reports it had to read files outside the Read list, capture this in the Execution log so slice-issues' heuristics can be tuned later.
- If status is BLOCKED, surface why — usually a missing dependency on another issue.
```

- [ ] **Step 2: Commit**

```
git add skills/implement/execute-issue/SKILL.md
git commit -m "feat: add execute-issue skill"
```

---

## Task 15: verify-issue/SKILL.md

**Files:**
- Create: `skills/implement/verify-issue/SKILL.md`

- [ ] **Step 1: Create the SKILL.md**

```markdown
---
name: verify-issue
description: Reviews an executed issue using a separate subagent (default code-reviewer) to avoid context bias. Writes a step-by-step QA doc for vertical-slice issues. Use after execute-issue completes for an issue.
---

# verify-issue

Dispatch a DIFFERENT subagent to review the executed issue against its Acceptance + module boundaries. Always emit a QA doc for vertical slices; skip for skeleton issues.

## Preconditions (HARD)

The target issue file must:
- Exist
- Have a FILLED Execution log section (executed by execute-issue)
- Have an EMPTY Review verdict section (otherwise prompt: re-review / skip / abort)

The subagent used for this review MUST be different from the subagent_type recorded in the Execution log. This is the whole point — avoid context bias.

## Procedure

### 1. Resolve target issue

Argument: a path or NNN. Resolve to `docs/features/<slug>/issues/NNN-<slug>.md`. Read the full issue.

### 2. Prompt for review subagent type

Default: `code-reviewer` (general code review focus). Ask:
> "Which subagent type for review? Default: code-reviewer. Override?"

Reject if the user chooses the same type used for execution (per Execution log).

### 3. Build the review prompt

Compose:
> "You are reviewing issue <NNN> for feature <slug>. The issue was executed by a different subagent.
>
> Read:
> - The issue file: <path>
> - The diff of the Write files declared in the issue (or just read the current state of each)
> - The design-brief sections referenced in the UX slice
> - The tech-spec Module map section relevant to the Modules touched
>
> Check:
> 1. Functional acceptance — do the declared tests exist and pass?
> 2. Visual acceptance — does the implementation match the referenced design-brief sections?
> 3. Module boundary — do any imports cross module public surfaces inappropriately per tech-spec?
> 4. Tests-first discipline — were tests written first per the Tests section, or written after? (Best-effort check via git history or test content.)
>
> Report:
> - Per-check status: PASS / FAIL / NEEDS_USER (the last for visual checks you cannot verify)
> - Overall verdict: PASS / FAIL / NEEDS_USER
> - Summary: one paragraph"

### 4. Dispatch via Agent tool

Use the Agent tool with the chosen review `subagent_type`. Wait for the result.

### 5. Conditional QA doc

If `Slice type: vertical`:

Write `docs/features/<slug>/qa/NNN-qa-review.md`:

```markdown
# QA Review — Issue NNN: <title>

**Date:** <YYYY-MM-DD>
**Review verdict:** <PASS | FAIL | NEEDS_USER>

## Manual verification steps

### Functional
1. <concrete step the user runs to verify the functional acceptance>
2. <step>

Expected outcome at end: <user-visible state matching the Vertical slice section>.

### Visual
For each visual acceptance check in the issue:
- **<check>** — Open <screen / page / component>. Compare against `docs/features/<slug>/design-brief.md` §<section>. Look for: <specific cues — spacing, color, motion>.

### Edge cases
Pulled from the issue's States section:
- **Empty state:** <how to trigger, what to look for>
- **Loading state:** <how to trigger>
- **Error state:** <how to trigger, what's the right error UX>
- **Success state:** <verified above in Functional>

## Reviewer's notes
<paste the review subagent's per-check observations>
```

If `Slice type: skeleton`: skip the QA doc.

### 6. Append to issue's Review verdict section

```markdown
## Review verdict (filled by verify-issue)
- **Code review:** <verdict> — <summary>
- **Reviewer subagent type:** <chosen>
- **QA doc:** docs/features/<slug>/qa/NNN-qa-review.md (or "N/A — skeleton issue")
- **Date:** <YYYY-MM-DD>
```

### 7. Report

> "Issue <NNN> review: <verdict>. <QA doc path or 'no QA doc — skeleton issue'>. Next: <fix-and-re-verify | execute-issue NNN+1>."

## Rules

- Reviewer subagent MUST differ from the executing subagent. Refuse to dispatch otherwise.
- Vertical slices ALWAYS get a QA doc.
- Skeleton issues NEVER get a QA doc (verdict-only).
- The review subagent reads design-brief by section reference, never the whole file.
- Do not auto-close GitHub issues even on PASS — that's a user action (see publish-issues).
```

- [ ] **Step 2: Commit**

```
git add skills/implement/verify-issue/SKILL.md
git commit -m "feat: add verify-issue skill"
```

---

## Task 16: publish-issues/SKILL.md

**Files:**
- Create: `skills/integrate/publish-issues/SKILL.md`

- [ ] **Step 1: Create the SKILL.md**

```markdown
---
name: publish-issues
description: Creates or updates GitHub issues from a feature's local issue files using the gh CLI. Idempotent — detects existing GitHub block in local issues and updates rather than duplicating. Optional in the main flow. Use to sync local issues to a GitHub repository.
---

# publish-issues

Push local issues to GitHub. Idempotent. Does NOT auto-close on verify-pass.

## Preconditions (HARD)

- `gh` CLI must be installed and authenticated (`gh auth status` succeeds).
- Current working directory must be a git repo with a GitHub remote (`gh repo view` succeeds).
- At least one `docs/features/<slug>/issues/NNN-*.md` must exist.

If any check fails, abort with the specific message (e.g., "gh CLI not authenticated — run `gh auth login`").

## Procedure

### 1. Resolve slug + verify gh

Ask for slug if not provided. Run:
```
gh auth status
gh repo view --json nameWithOwner
```
Both must succeed.

### 2. Optional label

Ask:
> "Apply a feature label to all synced issues? (Recommended: `feature:<slug>`.) Press Enter to use default, type to override, or '-' to skip."

### 3. For each local issue file (sorted by NNN)

a. Read the issue file. Extract:
   - Title (the `# Issue NNN: <title>` line)
   - Body (the entire file content minus the GitHub block)
   - Existing GitHub block (if present)

b. **If the issue has a `## GitHub` block with a populated `Issue: #N`:**
   - Update the existing GitHub issue body:
     ```
     gh issue edit <N> --body-file <temp-file-with-body>
     ```
   - If a label was provided and not yet applied:
     ```
     gh issue edit <N> --add-label feature:<slug>
     ```

c. **Else (no GitHub block yet):**
   - Create the issue:
     ```
     gh issue create --title "Issue NNN: <title>" --body-file <temp-file-with-body> [--label feature:<slug>]
     ```
   - Capture the issue number and URL from `gh`'s output.
   - Append/replace the `## GitHub` block at the end of the local issue file:
     ```
     ## GitHub
     - **Issue:** #<N>
     - **URL:** <url>
     - **Last synced:** <YYYY-MM-DD>
     ```

d. Update the `Last synced` field to today in both cases.

### 4. Report

> "Synced <N> issues to <owner/repo>. <created> created, <updated> updated. Label: <label or none>."

## Rules

- Idempotent: re-running pushes only changes (body diffs), never duplicates.
- Never auto-close issues. Verify-pass does not imply ship-ready.
- If the local issue title changes, update GitHub too.
- If a local issue has no GitHub block and is at `Slice type: skeleton`, still publish — skeleton issues are real work, just not user-facing.
- Sanitize the body: strip any leading whitespace before the `#` heading line so GitHub renders it as a header. The local format already meets this, but worth a guard.
```

- [ ] **Step 2: Commit**

```
git add skills/integrate/publish-issues/SKILL.md
git commit -m "feat: add publish-issues skill for GitHub sync"
```

---

## Task 17: install scripts

**Files:**
- Create: `install.ps1`
- Create: `install.sh`

- [ ] **Step 1: Create `install.ps1`**

```powershell
<#
.SYNOPSIS
Installs the probe-feature skill library into ~/.claude/skills/.

.DESCRIPTION
Walks skills/ for any folder containing a SKILL.md and copies each leaf folder to
~/.claude/skills/<leaf-name>/. On collision, prompts overwrite / skip / archive.
Offers to archive prototype skills (probe, scope, grill-me) on first run.

.PARAMETER DryRun
If set, prints what would happen without copying anything.

.PARAMETER Force
If set, overwrites collisions without prompting.

.EXAMPLE
.\install.ps1
.\install.ps1 -DryRun
#>
[CmdletBinding()]
param(
    [switch]$DryRun,
    [switch]$Force
)

$ErrorActionPreference = 'Stop'

$repoRoot   = Split-Path -Parent $MyInvocation.MyCommand.Path
$skillsRoot = Join-Path $repoRoot 'skills'
$destRoot   = Join-Path $HOME '.claude\skills'
$archiveRoot = Join-Path $destRoot '.archive'

if (-not (Test-Path $skillsRoot)) {
    throw "skills/ folder not found at $skillsRoot"
}

if (-not (Test-Path $destRoot)) {
    if ($DryRun) {
        Write-Host "[dry-run] would create $destRoot"
    } else {
        New-Item -ItemType Directory -Path $destRoot -Force | Out-Null
    }
}

# Find leaf skill folders (any folder containing SKILL.md, excluding shared/templates).
$leafSkills = Get-ChildItem -Path $skillsRoot -Recurse -Filter 'SKILL.md' -File |
    Where-Object { $_.Directory.FullName -notlike '*shared\templates*' } |
    ForEach-Object { $_.Directory }

Write-Host "Found $($leafSkills.Count) skill folders to install."

# Offer to archive prototype skills on first encounter.
$prototypes = @('probe', 'scope', 'grill-me')
$existingPrototypes = $prototypes | Where-Object { Test-Path (Join-Path $destRoot $_) }
if ($existingPrototypes.Count -gt 0) {
    Write-Host "Found existing prototype skills: $($existingPrototypes -join ', ')"
    if (-not $Force) {
        $answer = Read-Host "Archive these (move to .archive/) before installing the new library? (y/N)"
    } else {
        $answer = 'y'
    }
    if ($answer -eq 'y') {
        if (-not (Test-Path $archiveRoot)) {
            if (-not $DryRun) { New-Item -ItemType Directory -Path $archiveRoot -Force | Out-Null }
        }
        foreach ($p in $existingPrototypes) {
            $src = Join-Path $destRoot $p
            $stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
            $dst = Join-Path $archiveRoot "$p-$stamp"
            if ($DryRun) {
                Write-Host "[dry-run] would archive $src -> $dst"
            } else {
                Move-Item -Path $src -Destination $dst
                Write-Host "Archived $p -> .archive/$p-$stamp"
            }
        }
    }
}

# Install each leaf.
$installed = 0; $skipped = 0; $overwritten = 0
foreach ($leaf in $leafSkills) {
    $name = $leaf.Name
    $dst = Join-Path $destRoot $name

    if (Test-Path $dst) {
        if ($Force) {
            $action = 'overwrite'
        } else {
            $action = Read-Host "Skill '$name' already exists. (o)verwrite / (s)kip / (a)rchive-then-overwrite?"
        }
        switch ($action) {
            'o' {
                if ($DryRun) { Write-Host "[dry-run] would overwrite $dst" }
                else { Remove-Item -Recurse -Force $dst; Copy-Item -Recurse $leaf.FullName $dst; $overwritten++ }
            }
            'overwrite' {
                if ($DryRun) { Write-Host "[dry-run] would overwrite $dst" }
                else { Remove-Item -Recurse -Force $dst; Copy-Item -Recurse $leaf.FullName $dst; $overwritten++ }
            }
            'a' {
                $stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
                $archDst = Join-Path $archiveRoot "$name-$stamp"
                if (-not (Test-Path $archiveRoot)) {
                    if (-not $DryRun) { New-Item -ItemType Directory -Path $archiveRoot -Force | Out-Null }
                }
                if ($DryRun) {
                    Write-Host "[dry-run] would archive existing $dst -> $archDst, then install"
                } else {
                    Move-Item -Path $dst -Destination $archDst
                    Copy-Item -Recurse $leaf.FullName $dst
                    $overwritten++
                }
            }
            default {
                Write-Host "Skipped $name"; $skipped++
            }
        }
    } else {
        if ($DryRun) { Write-Host "[dry-run] would install $name -> $dst" }
        else { Copy-Item -Recurse $leaf.FullName $dst; $installed++ }
    }
}

Write-Host ""
Write-Host "Summary: $installed installed, $overwritten overwritten/archived, $skipped skipped."
```

- [ ] **Step 2: Create `install.sh`**

```bash
#!/usr/bin/env bash
# Installs the probe-feature skill library into ~/.claude/skills/.
# Walks skills/ for SKILL.md files and copies each containing folder to
# ~/.claude/skills/<leaf-name>/.

set -euo pipefail

DRY_RUN=0
FORCE=0
while [[ $# -gt 0 ]]; do
    case "$1" in
        --dry-run) DRY_RUN=1 ;;
        --force) FORCE=1 ;;
        *) echo "unknown arg: $1" >&2; exit 2 ;;
    esac
    shift
done

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILLS_ROOT="$REPO_ROOT/skills"
DEST_ROOT="$HOME/.claude/skills"
ARCHIVE_ROOT="$DEST_ROOT/.archive"

[[ -d "$SKILLS_ROOT" ]] || { echo "skills/ folder not found at $SKILLS_ROOT" >&2; exit 1; }

run() {
    if [[ $DRY_RUN -eq 1 ]]; then echo "[dry-run] $*"; else eval "$*"; fi
}

run "mkdir -p '$DEST_ROOT'"

# Collect leaf skill folders, excluding shared/templates.
mapfile -t LEAVES < <(find "$SKILLS_ROOT" -name 'SKILL.md' -type f | while read -r f; do
    d="$(dirname "$f")"
    [[ "$d" == *"shared/templates"* ]] && continue
    echo "$d"
done)

echo "Found ${#LEAVES[@]} skill folders to install."

# Offer to archive prototypes on first run.
PROTOTYPES=(probe scope grill-me)
EXISTING=()
for p in "${PROTOTYPES[@]}"; do
    [[ -d "$DEST_ROOT/$p" ]] && EXISTING+=("$p")
done
if [[ ${#EXISTING[@]} -gt 0 ]]; then
    echo "Found existing prototype skills: ${EXISTING[*]}"
    if [[ $FORCE -eq 1 ]]; then ans=y; else read -r -p "Archive these before installing the new library? (y/N) " ans; fi
    if [[ "$ans" == "y" || "$ans" == "Y" ]]; then
        run "mkdir -p '$ARCHIVE_ROOT'"
        for p in "${EXISTING[@]}"; do
            stamp="$(date +%Y%m%d-%H%M%S)"
            run "mv '$DEST_ROOT/$p' '$ARCHIVE_ROOT/$p-$stamp'"
            echo "Archived $p -> .archive/$p-$stamp"
        done
    fi
fi

installed=0; skipped=0; overwritten=0
for leaf in "${LEAVES[@]}"; do
    name="$(basename "$leaf")"
    dst="$DEST_ROOT/$name"

    if [[ -d "$dst" ]]; then
        if [[ $FORCE -eq 1 ]]; then action=o; else
            read -r -p "Skill '$name' already exists. (o)verwrite / (s)kip / (a)rchive-then-overwrite? " action
        fi
        case "$action" in
            o)
                run "rm -rf '$dst'"
                run "cp -r '$leaf' '$dst'"
                overwritten=$((overwritten+1))
                ;;
            a)
                stamp="$(date +%Y%m%d-%H%M%S)"
                run "mkdir -p '$ARCHIVE_ROOT'"
                run "mv '$dst' '$ARCHIVE_ROOT/$name-$stamp'"
                run "cp -r '$leaf' '$dst'"
                overwritten=$((overwritten+1))
                ;;
            *)
                echo "Skipped $name"; skipped=$((skipped+1))
                ;;
        esac
    else
        run "cp -r '$leaf' '$dst'"
        installed=$((installed+1))
    fi
done

echo
echo "Summary: $installed installed, $overwritten overwritten/archived, $skipped skipped."
```

- [ ] **Step 3: Make install.sh executable**

```
git update-index --chmod=+x install.sh 2>$null
```
(On Windows the bit doesn't matter for execution; this line ensures git tracks the executable bit for non-Windows users when they clone.)

- [ ] **Step 4: Dry-run the PowerShell installer to verify it discovers all 12 skills**

```
.\install.ps1 -DryRun
```
Expected: prints `Found 12 skill folders to install.` and per-skill messages.

- [ ] **Step 5: Commit**

```
git add install.ps1 install.sh
git commit -m "feat: add install scripts for PowerShell and Bash"
```

---

## Task 18: Full README

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Overwrite README.md with full content**

```markdown
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

The installer copies each leaf skill folder into `~/.claude/skills/`. Re-running is idempotent (it'll prompt before overwriting). On first run, it offers to archive existing prototype skills (`probe`, `scope`, `grill-me`) to `~/.claude/skills/.archive/`.

## Quick start

Three-command happy path:

```
> probe-feature           # interactive — produces docs/features/<slug>/ bundle
> slice-issues            # produces issues/NNN-*.md and SEQUENCE.md
> execute-issue 001-...   # loop per issue
> verify-issue 001-...    # after each execute
> publish-issues          # optional — syncs to GitHub
```

## Skills

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
- `slice-issues` — the keystone. Vertical slices, 100k token cap, required Tests sections, Do-NOT-read lists.
- `sequence-issues` — topological order with parallelizable groups.

### Implement
- `execute-issue` — dispatches a subagent for one issue.
- `verify-issue` — dispatches a *different* subagent to review; emits a QA doc for vertical slices.

### Integrate
- `publish-issues` — syncs local issues to GitHub via `gh`. Idempotent. Optional.

## Artifact layout in your project

```
docs/features/<feature-slug>/
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

`docs/design-system.md` lives at the project root (one per project, not per feature).

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
```

- [ ] **Step 2: Commit**

```
git add README.md
git commit -m "docs: full README with install + usage"
```

---

## Task 19: End-to-end dry run

**Files:** none changed; this task validates the library against a real feature.

- [ ] **Step 1: Install the library locally**

```
.\install.ps1 -Force
```
Expected: 12 skills installed under `~/.claude/skills/`.

- [ ] **Step 2: Pick a small real feature in a real project**

Choose any existing project repo on the user's machine where a small feature can be planned (does NOT have to be implemented as part of this validation). Example: "add a dark mode toggle to the settings page" in some existing app.

- [ ] **Step 3: Run probe-feature**

In a fresh Claude Code session inside the chosen project:
```
> probe-feature
```
Walk through the three probes. Expected: `docs/features/<slug>/probe-product.md`, `probe-design.md`, `probe-technical.md`, `prd.md`, `design-brief.md`, `tech-spec.md` all written.

Verify by listing:
```
ls docs/features/<slug>/
```
Expected: 6 files.

- [ ] **Step 4: Run slice-issues**

```
> slice-issues
```
Expected: `docs/features/<slug>/issues/NNN-*.md` files written. Inspect at least one:
- Has all required sections (Slice type, Vertical slice, Modules touched, Context manifest, Tests, UX slice, Acceptance, Execution log placeholder, Review verdict placeholder).
- Estimated context < 100k.
- Tests section is populated (not waived without justification).
- "Do NOT read" section is populated.

- [ ] **Step 5: Run sequence-issues**

```
> sequence-issues
```
Expected: `docs/features/<slug>/issues/SEQUENCE.md` written with layered build order.

- [ ] **Step 6: Run execute-issue on issue 001 (in throwaway mode)**

```
> execute-issue 001-...
```
When prompted for subagent type, pick general-purpose. Allow the subagent to do its work. Expected: issue file's Execution log section is filled with token-actual, files changed, subagent type.

If you don't want to actually commit code from the subagent's work, run this in a worktree or a scratch branch:
```
git worktree add ../<project>-dryrun
cd ../<project>-dryrun
> execute-issue 001-...
```

- [ ] **Step 7: Run verify-issue 001**

```
> verify-issue 001-...
```
Pick a DIFFERENT subagent type (e.g., code-reviewer). Expected:
- For a vertical-slice issue: `docs/features/<slug>/qa/001-qa-review.md` written with manual verification steps.
- For a skeleton issue: no QA doc, verdict-only.
- Review verdict appended to the issue file.

- [ ] **Step 8: Capture dry-run findings**

Create `docs/superpowers/dry-runs/2026-05-10-dry-run.md` in this repo with:
- Feature used + slug
- Any rough edges encountered
- Per-skill notes (worked, almost-worked, blocked)
- Token estimate accuracy (estimated vs actual for executed issue)

If significant rough edges are found, file them as follow-up tasks in a new plan.

- [ ] **Step 9: Commit the dry-run notes**

```
git add docs/superpowers/dry-runs/2026-05-10-dry-run.md
git commit -m "docs: capture initial dry-run findings"
```

- [ ] **Step 10: Tag the v0.1 milestone**

```
git tag v0.1-mvp
```

---

## Self-review notes (for the engineer executing this plan)

- **Spec coverage:** Every section of `docs/superpowers/specs/2026-05-10-probe-feature-skill-library-design.md` maps to at least one task above. 12 skills = Tasks 5–7, 8–10, 11, 12–13, 14–15, 16. Token estimator = Task 3. Templates = Task 4. Install = Task 17. README = Tasks 2, 18. Dry-run = Task 19.
- **No placeholders:** All SKILL.md content is shown inline. The dry-run task explicitly notes that "any slug" / "any project" is acceptable — those aren't placeholders, those are runtime parameters.
- **Type consistency:** Section names used by skills are stable across files: `## Vertical slice`, `## Slice type`, `## Context manifest`, `## Tests`, `## UX slice`, `## Acceptance`, `## Execution log (filled by execute-issue)`, `## Review verdict (filled by verify-issue)`, `## GitHub (filled by publish-issues, optional)`. Verify-issue and execute-issue reference these by name.
- **Estimate-vs-actual loop:** execute-issue computes token-actual; over time this informs slice-issues heuristics. Currently the heuristic is fixed (3.5/4.0 divisors); deliberate v1 simplification.
- **One thing to watch during execution:** the bundled `estimate_tokens.py` exists in both `scripts/` and `skills/plan/slice-issues/`. They must stay in sync. If the heuristic is tuned later, update both copies (or refactor to import).
