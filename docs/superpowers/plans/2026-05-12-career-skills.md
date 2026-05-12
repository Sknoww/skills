# Career Skills Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship three new skills (`build-background`, `refine-template`, `align-resume`) under `skills/career/`, plus a canonical BACKGROUND schema and a small `page_count.py` helper for `align-resume`'s page-length enforcement.

**Architecture:** Skills are leaf folders containing `SKILL.md` (frontmatter + procedure markdown). Bundled assets live alongside each `SKILL.md`. The existing installer walks recursively for any `SKILL.md` — no installer changes. A canonical `BACKGROUND-template.md` lives in `skills/shared/templates/`; `build-background` ships a copy inside its folder.

**Tech Stack:** Markdown (skill files), Python 3 stdlib + `pypdf` (page_count helper), Pandoc + PDF engine (used at skill runtime, not implementation time), pytest (helper testing).

---

## File Structure

**Created:**
- `skills/shared/templates/BACKGROUND-template.md` — canonical schema, single source of truth
- `skills/career/build-background/SKILL.md`
- `skills/career/build-background/BACKGROUND-template.md` — copy of the canonical schema, bundled for install
- `skills/career/refine-template/SKILL.md`
- `skills/career/refine-template/default-style.css` — ATS-safe baseline stylesheet
- `skills/career/refine-template/default-resume.template.md` — markdown skeleton with placeholder markers
- `skills/career/align-resume/SKILL.md`
- `skills/career/align-resume/page_count.py` — counts pages of a PDF via pypdf
- `tests/test_page_count.py`
- `requirements-dev.txt` — declares pypdf for tests

**Modified:**
- `README.md` — add Career section under Skills

Each `SKILL.md` is documentation-style (Claude interprets it), so no automated tests for the markdown content. The Python helper gets full TDD. Existing skill files like `skills/discover/probe-product/SKILL.md` are the reference shape — frontmatter with `name:` + `description:`, `## Preconditions`, `## Procedure`, `## Rules`.

---

## Task 1: Add the canonical BACKGROUND schema

**Files:**
- Create: `skills/shared/templates/BACKGROUND-template.md`

- [ ] **Step 1: Write the BACKGROUND template file**

Create `skills/shared/templates/BACKGROUND-template.md` with the exact schema from the spec:

````markdown
# Background

<!--
Canonical BACKGROUND.md schema. Used by build-background, refine-template, and align-resume.
Sections appear in this fixed order. H2/H3 structure is stable so the skills can parse without ambiguity.
Gaps the user wants to fill later are marked with `<!-- TODO: ... -->` comments anywhere in the file.
-->

## Personal
Name: ...
Email: ...
Phone: ...
Location: ...
LinkedIn: ...
GitHub: ...
Site: ...
Headline: ...

## Career goals & targets
- Target roles: ...
- Target level(s): ...
- Industries in scope: ...
- Industries out of scope: ...
- Search trigger: ...

## Constraints & non-negotiables
- Comp floor: ...
- Location / remote: ...
- Deal-breakers: ...
- Travel: ...
- Work authorization: ...

## Experience
### <Company> — <Title>
Dates: <YYYY-MM> — <YYYY-MM | present>
Location: ...
Work mode: <on-site | hybrid | remote>
Scope: <team / company size and what they do>
Why joined: ...
Why left: ...
Tech: ...
Accomplishments:
- <metric-anchored bullet>
- ...
Notable projects:
- <name>: <one-line>
Skills developed: ...

## Projects
### <Project name>
Description: ...
Role: <solo | with team — what you owned>
Tech: ...
Outcome: ...
Link: ...
Motivation: ...

## Education
### <Institution> — <Degree>
Dates: ...
Major / minor: ...
GPA: <optional>
Honors: ...
Relevant coursework: ...

## Skills
- Languages: <name (proficiency)>, ...
- Frameworks: ...
- Tools / platforms: ...
- Domain expertise: ...
- Soft skills: ...

## Certifications
### <Name>
Issuer: ...
Date: ...
Expiry: ...
Credential ID: ...

## Story bank
### <Story title>
Situation: ...
Task: ...
Action: ...
Result: ...

## Awards, publications, talks, volunteer, languages, patents
### Awards
- ...
### Publications
- ...
### Talks
- ...
### Volunteer
- ...
### Languages
- <Language (proficiency)>
### Patents
- ...
````

- [ ] **Step 2: Commit**

```bash
git add skills/shared/templates/BACKGROUND-template.md
git commit -m "Add canonical BACKGROUND.md schema template"
```

---

## Task 2: Create build-background SKILL.md

**Files:**
- Create: `skills/career/build-background/SKILL.md`
- Create: `skills/career/build-background/BACKGROUND-template.md` (copy of shared template, bundled for install)

- [ ] **Step 1: Create the skill directory and bundle the template**

```bash
mkdir -p skills/career/build-background
cp skills/shared/templates/BACKGROUND-template.md skills/career/build-background/BACKGROUND-template.md
```

- [ ] **Step 2: Write SKILL.md**

Create `skills/career/build-background/SKILL.md` with frontmatter and procedure. Use this exact content:

````markdown
---
name: build-background
description: Interactive interview that captures the user's full career history, projects, skills, and achievements into a canonical BACKGROUND.md in the career hub. Optionally seeded by an existing resume. Re-run to update specific sections. Use when starting career-skill setup or when career history needs revising.
---

# build-background

Conduct an interactive career interview and write the result to `<career-hub>/BACKGROUND.md` following the canonical schema in `BACKGROUND-template.md` (bundled in this skill folder). One question at a time. If an existing resume is provided, extract what you can and dig deeper rather than re-asking.

## Preconditions

None — this is the entry point of the career-skill flow.

## Procedure

### 1. First-run hub setup

If `~/.claude/career/config.yml` is missing:
- Ask: "Where should your career hub live? (Default: `~/career/`)"
- Create the chosen directory if it does not exist.
- Write `~/.claude/career/config.yml`:

  ```yaml
  hub: <user-chosen-path>
  created: <YYYY-MM-DD>
  ```

Read the config to determine `<hub>` for the rest of the run.

### 2. Detect existing BACKGROUND.md

Check for `<hub>/BACKGROUND.md`.

- **Present:** Ask: "Full re-interview, or update specific sections?"
  - On **full re-interview**: back up the existing file as `<hub>/BACKGROUND.<YYYYMMDD-HHMMSS>.md.bak`, then proceed to step 3.
  - On **section update**: read the existing file silently, then jump to step 4 — interview only the sections the user names. Rewrite those sections in place; preserve the others.
- **Missing:** proceed to step 3.

### 3. Optional resume ingestion

Ask: "Do you have an existing resume to seed from? (Path to PDF/DOCX/MD/TXT, or skip.)"

If a path is provided:
- Stash a copy at `<hub>/.imported-resume.<ext>` (overwriting any prior import). This is read by `refine-template` later.
- Read the file:
  - PDF / MD / TXT — read directly via the Read tool.
  - DOCX — convert to markdown via `pandoc input.docx -t markdown`; if pandoc is unavailable, fall back to `unzip -p input.docx word/document.xml` and parse plaintext from the XML.
- Extract what can be inferred for each schema section.
- Present a summary per section, one section at a time: "Here's what I pulled for Experience — accurate? Anything to correct?". User confirms or corrects before moving on.
- These extracted values seed the interview. Skip questions whose answers were extracted and confirmed; spend questions digging deeper (metrics, why-you-left, story-grade detail).

### 4. Interview each section (one question at a time)

Read the canonical schema from `BACKGROUND-template.md` (bundled in this skill folder) to know section order and structure.

For each section, ask focused questions. Sections in order:

- **Personal** — name, email, phone, location, LinkedIn, GitHub, personal site, professional headline.
- **Career goals & targets** — target roles, target level(s), industries in scope, industries excluded, what's prompting the search now.
- **Constraints & non-negotiables** — comp floor, location/remote requirements, deal-breakers, travel willingness, work-authorization status if relevant.
- **Experience** — loop most-recent-first. Per role: company, title, dates, location, work mode, team/company scope, why-joined, why-left, top 3–5 accomplishments (push for metrics), tech stack, notable projects within the role, skills developed.
- **Projects** — loop most-recent-first. Per project: name, description, role, tech, outcome, link, motivation.
- **Education** — per institution: degree, major/minor, dates, optional GPA, honors, relevant coursework. Bootcamps and certificate programs count.
- **Skills** — languages with proficiency, frameworks, tools/platforms, domain expertise, soft skills (only ones the user would actually list).
- **Certifications** — per cert: name, issuer, date, expiry, credential ID.
- **Story bank (STAR)** — push for 5–10 strong stories. Per story: title, Situation, Task, Action, Result (with metrics).
- **Awards, publications, talks, volunteer, languages, patents** — ask "any of these apply?" first; only probe the relevant ones.

### 5. Write BACKGROUND.md

Assemble answers into `<hub>/BACKGROUND.md` using the exact section order and H2/H3 structure from `BACKGROUND-template.md`. Use `<!-- TODO: ... -->` markers anywhere the user wanted to come back to a gap.

### 6. Report

Print:
> "Wrote `<hub>/BACKGROUND.md`. Captured: <N> roles, <M> projects, <K> stories. TODOs to revisit: <count>. Next: run `refine-template` to lock in your resume template."

## Rules

- One question at a time. Never batch.
- Experience and Projects: always most-recent-first.
- Push back once on a vague answer ("can you quantify that?", "what was the impact?"); if still vague, capture as a `<!-- TODO: ... -->` and move on.
- Push hard for quantification on accomplishments and story-bank entries — numbers, percent changes, before/after.
- Never fabricate. If extracted-from-resume info is uncertain, confirm with the user before writing.
- On section-update mode, read the existing file silently first; don't re-ask answered questions.
- The bundled `BACKGROUND-template.md` is the canonical structure — match it exactly when writing the output file.
````

- [ ] **Step 3: Verify the skill directory layout**

Run:
```bash
ls skills/career/build-background/
```
Expected output: `BACKGROUND-template.md` and `SKILL.md` both present.

- [ ] **Step 4: Verify frontmatter parses**

Run:
```bash
python -c "import yaml; doc = open('skills/career/build-background/SKILL.md').read().split('---')[1]; print(yaml.safe_load(doc))"
```
Expected: prints a dict with `name: build-background` and the description string. If yaml is not installed: `pip install pyyaml`.

- [ ] **Step 5: Commit**

```bash
git add skills/career/build-background/
git commit -m "Add build-background skill"
```

---

## Task 3: Add refine-template bundled defaults

**Files:**
- Create: `skills/career/refine-template/default-style.css`
- Create: `skills/career/refine-template/default-resume.template.md`

- [ ] **Step 1: Create the skill directory**

```bash
mkdir -p skills/career/refine-template
```

- [ ] **Step 2: Write the default stylesheet**

Create `skills/career/refine-template/default-style.css`:

```css
/* Default ATS-safe resume style. Single column, Helvetica/Arial,
   clear hierarchy. Modify in refine-template to taste. */

@page {
  size: letter;
  margin: 0.6in 0.7in;
}

body {
  font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
  font-size: 10.5pt;
  line-height: 1.35;
  color: #1a1a1a;
  max-width: none;
}

h1 {
  font-size: 18pt;
  margin: 0 0 0.1em 0;
}

h2 {
  font-size: 11pt;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  border-bottom: 1px solid #999;
  margin: 1em 0 0.4em 0;
  padding-bottom: 2px;
}

h3 {
  font-size: 11pt;
  margin: 0.6em 0 0.1em 0;
}

p {
  margin: 0.1em 0;
}

ul {
  margin: 0.2em 0 0.5em 1.2em;
  padding: 0;
}

li {
  margin: 0.15em 0;
}

a {
  color: #1a1a1a;
  text-decoration: none;
}
```

- [ ] **Step 3: Write the default template skeleton**

Create `skills/career/refine-template/default-resume.template.md`:

````markdown
<!--
Default resume structural skeleton. Used by refine-template as the starting point when the user did not import an existing resume. Placeholders are markers, not a templating-engine syntax — align-resume reads BACKGROUND.md and fills them in based on selected material.
-->

# {{Name}}

{{Email}} · {{Phone}} · {{Location}}
{{LinkedIn}} · {{GitHub}} · {{Site}}

## Summary

{{One-line headline or short summary derived from Career goals & targets}}

## Experience

### {{Company}} — {{Title}}
{{Dates}} · {{Location}}

- {{Accomplishment bullet; preserve metrics verbatim from BACKGROUND.md}}
- {{...}}

<!-- Repeat per role from BACKGROUND.md Experience, most-recent first, filtered by JD relevance and length target -->

## Projects

- **{{Project name}}** — {{description}} ([link]({{link}}))

<!-- Repeat per project, filtered by relevance; may be cut entirely if one-page target is tight -->

## Education

### {{Institution}} — {{Degree}}
{{Dates}} · {{Honors if any}}

<!-- Repeat per institution -->

## Skills

- **Languages:** {{language list, ordered by JD relevance}}
- **Frameworks:** {{frameworks list}}
- **Tools:** {{tools list}}

## Certifications

- {{Name}} — {{Issuer}} ({{Date}})

<!-- Repeat per cert; filter to relevant -->
````

- [ ] **Step 4: Commit**

```bash
git add skills/career/refine-template/default-style.css skills/career/refine-template/default-resume.template.md
git commit -m "Add refine-template starter assets (CSS + markdown skeleton)"
```

---

## Task 4: Create refine-template SKILL.md

**Files:**
- Create: `skills/career/refine-template/SKILL.md`

- [ ] **Step 1: Write SKILL.md**

Create `skills/career/refine-template/SKILL.md`:

````markdown
---
name: refine-template
description: Critiques the user's existing resume format against modern industry best practices and ATS requirements, iterates with the user on structure and visuals, and locks in a reusable resume template (markdown skeleton + CSS + reference.docx) in the career hub. Use after build-background, or anytime the template needs revising.
---

# refine-template

Critique the user's resume format, iterate with the user, and lock in a reusable template at `<career-hub>/template/`. Industry-aware defaults are inferred from BACKGROUND.md. Page-length target is a hard constraint downstream `align-resume` will enforce.

## Preconditions

- `~/.claude/career/config.yml` exists. If missing, exit with: `"Career hub config not found. Run build-background first."`
- `<hub>/BACKGROUND.md` exists. If missing, exit with: `"BACKGROUND.md not found at <hub>. Run build-background first."`
- `pandoc` is on PATH. If missing, exit with: `"Pandoc not found. Install via 'winget install JohnMacFarlane.Pandoc' (Windows), 'brew install pandoc' (macOS), or 'apt install pandoc' (Linux)."`
- A PDF engine is available (try `wkhtmltopdf`, `weasyprint`, `pdflatex` in that order). If none, exit with: `"No PDF engine found. Install one: 'pip install weasyprint' OR 'winget install wkhtmltopdf' OR install a LaTeX distribution."`

## Procedure

### 1. Detect existing template

Check for `<hub>/template/`.
- **Populated:** Ask: "Revise existing template, or start over?" On **start over**, move the directory to `<hub>/template.<YYYYMMDD-HHMMSS>.bak/`. On **revise**, load the existing files as the starting point.
- **Missing:** create the directory and proceed.

### 2. Determine industry context

Read `<hub>/BACKGROUND.md` silently — specifically the `## Career goals & targets` and `## Experience` sections. Infer primary industry from target roles and recent experience (software engineering, design, product, finance, academic, sales, etc.).

Confirm: "I'm assuming `<industry>` as the primary target. Correct?" If the user overrides, use their answer.

The industry choice drives section ordering, length norms, and style register.

### 3. Establish target length

Ask: "Target length — one page, two pages, or flexible?" Suggest a default:
- Tech, ≤10 years experience: one page.
- Senior leadership: two pages OK.
- Academic / medical / research: multi-page CV.
- Otherwise: one page.

If the user picks one-page but BACKGROUND.md's Experience spans many roles or years, warn: "Heads up — your background spans <N> roles across <Y> years; one page will require aggressive prioritization. Still go for one?"

Record the chosen length — it gets stored in `template-notes.md` at step 8.

### 4. Establish the structural starting point

Check for `<hub>/.imported-resume.<ext>`.
- **Exists:** read it (PDF/MD/TXT directly; DOCX via `pandoc <file> -t markdown`). Extract section order and naming as the starting structural template.
- **Missing:** copy `default-resume.template.md` (bundled in this skill folder) to `<hub>/template/resume.template.md`.

### 5. Establish the visual starting point

- Copy `default-style.css` (bundled in this skill folder) to `<hub>/template/style.css`.
- Generate a starter reference.docx via Pandoc:
  ```bash
  pandoc --print-default-data-file reference.docx > <hub>/template/reference.docx
  ```

Render a sample PDF + DOCX to a temp scratch dir:
- Populate the template by reading selected highlights from BACKGROUND.md (Personal, top 1–2 roles, top 3 skills, top 2 projects, education, top certs).
- Render: `pandoc <scratch>/resume.md -o <scratch>/resume.pdf --css <hub>/template/style.css` and `pandoc <scratch>/resume.md -o <scratch>/resume.docx --reference-doc <hub>/template/reference.docx`.

Show the user paths to the sample PDF and DOCX. Ask them to open and view before proceeding.

### 6. Critique pass

Write a critique of the current state covering modern best practices and ATS pitfalls. Categories:

- Section order and naming.
- Length vs target (over/under by how much, where to cut).
- Bullet length and density (ATS prefers 1–2 line bullets).
- Action verbs and active voice.
- Quantification of accomplishments.
- White space and rhythm.
- Fonts (typeface, sizes, hierarchy).
- Column count (single-column required for ATS unless explicitly overridden by the user).
- Graphics / icons / photos (ATS-hostile).
- Header / footer text (ATS frequently skips it).
- File naming conventions.
- Industry-specific length norms.

Identify 5–10 prioritized issues with concrete suggested fixes.

### 7. Iterate with user

Present **one issue at a time**:
> "Issue 1 of N: <description>. Suggested fix: <fix>. Apply, skip, or modify?"

After each accepted change, re-render the sample PDF + DOCX so the user can see the effect concretely.

If the user proposes a change that hurts ATS safety (two-column layout, graphics in header, etc.), warn them once and require explicit confirmation before applying.

Continue until the user signs off on the template as a whole.

### 8. Lock in the template

Write the final files to `<hub>/template/`:
- `resume.template.md` — the locked structural skeleton (after iteration).
- `style.css` — the locked PDF stylesheet.
- `reference.docx` — the locked DOCX styling reference.
- `template-notes.md` — a decisions log with the following structure:

  ```markdown
  # Template notes

  **Date locked:** <YYYY-MM-DD>
  **Industry:** <inferred industry, with any user override>
  **Target page length:** <one | two | flexible>

  ## Section order
  <ordered list of H2 sections in resume.template.md>

  ## ATS choices
  - Column count: <single | two — note any override>
  - Graphics: <none | <description if any>>
  - Header/footer text: <none | <description>>

  ## Notable iteration decisions
  - <decision>: <rationale>
  ```

### 9. Report

Print a summary of decisions locked in, then:
> "Template locked at `<hub>/template/`. Run `align-resume <jd-path>` to generate a tailored resume."

## Rules

- Check Pandoc + PDF engine **before** starting the interview — fail fast.
- One critique issue at a time.
- Re-render the sample after each accepted change.
- Never override ATS-safety choices for visual flair without explicit user confirmation.
- Industry inference is a soft default; the user can override at any point.
- The target page length recorded here is a hard constraint for `align-resume`.
````

- [ ] **Step 2: Verify frontmatter parses**

Run:
```bash
python -c "import yaml; doc = open('skills/career/refine-template/SKILL.md').read().split('---')[1]; print(yaml.safe_load(doc))"
```
Expected: prints a dict with `name: refine-template` and the description string.

- [ ] **Step 3: Commit**

```bash
git add skills/career/refine-template/SKILL.md
git commit -m "Add refine-template skill"
```

---

## Task 5: Add page_count.py with TDD

**Files:**
- Create: `requirements-dev.txt`
- Create: `skills/career/align-resume/page_count.py`
- Create: `tests/test_page_count.py`

- [ ] **Step 1: Declare the test-time dependency**

Create `requirements-dev.txt`:
```
pypdf>=4.0
pytest>=8.0
pyyaml>=6.0
```

Install for local testing:
```bash
pip install -r requirements-dev.txt
```

- [ ] **Step 2: Write the failing test**

Create the skill directory first:
```bash
mkdir -p skills/career/align-resume
```

Create `tests/test_page_count.py`:

```python
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parent.parent / "skills" / "career" / "align-resume" / "page_count.py"


def run_script(args):
    result = subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        capture_output=True, text=True
    )
    return result.stdout, result.stderr, result.returncode


def make_pdf(path, pages):
    from pypdf import PdfWriter
    writer = PdfWriter()
    for _ in range(pages):
        writer.add_blank_page(width=612, height=792)
    with open(path, "wb") as f:
        writer.write(f)


def test_one_page_pdf(tmp_path):
    pdf = tmp_path / "one.pdf"
    make_pdf(pdf, 1)
    out, err, code = run_script([str(pdf)])
    assert code == 0, err
    assert out.strip() == "1"


def test_three_page_pdf(tmp_path):
    pdf = tmp_path / "three.pdf"
    make_pdf(pdf, 3)
    out, err, code = run_script([str(pdf)])
    assert code == 0, err
    assert out.strip() == "3"


def test_missing_file_errors(tmp_path):
    out, err, code = run_script([str(tmp_path / "nope.pdf")])
    assert code != 0
    assert "nope.pdf" in (out + err)


def test_no_args_prints_usage():
    out, err, code = run_script([])
    assert code != 0
    assert "usage" in (out + err).lower()
```

- [ ] **Step 3: Run the test and verify it fails**

Run:
```bash
pytest tests/test_page_count.py -v
```
Expected: tests fail (script does not exist yet). Error message references the missing `page_count.py`.

- [ ] **Step 4: Implement the script**

Create `skills/career/align-resume/page_count.py`:

```python
#!/usr/bin/env python3
"""Count pages in a PDF file.

Usage: python page_count.py <path.pdf>
Prints page count to stdout. Exits 0 on success, 1 on read failure, 2 on usage error.

Requires: pypdf (`pip install pypdf`).
"""
from __future__ import annotations

import sys
from pathlib import Path


def page_count(path: Path) -> int:
    from pypdf import PdfReader
    return len(PdfReader(str(path)).pages)


def main(argv: list[str]) -> int:
    if len(argv) != 1:
        print("usage: page_count.py <path.pdf>", file=sys.stderr)
        return 2
    path = Path(argv[0])
    if not path.exists() or not path.is_file():
        print(f"missing: {argv[0]}", file=sys.stderr)
        return 1
    try:
        print(page_count(path))
    except Exception as exc:
        print(f"error: {argv[0]}: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
```

- [ ] **Step 5: Run the test and verify it passes**

Run:
```bash
pytest tests/test_page_count.py -v
```
Expected: all four tests pass.

- [ ] **Step 6: Commit**

```bash
git add requirements-dev.txt skills/career/align-resume/page_count.py tests/test_page_count.py
git commit -m "Add page_count.py helper with pypdf"
```

---

## Task 6: Create align-resume SKILL.md

**Files:**
- Create: `skills/career/align-resume/SKILL.md`

- [ ] **Step 1: Write SKILL.md**

Create `skills/career/align-resume/SKILL.md`:

````markdown
---
name: align-resume
description: Generates an ATS-aware, job-tailored resume from a job description by selecting and lightly rewording material from BACKGROUND.md, using the locked template. Outputs MD/PDF/DOCX into a per-job subfolder in CWD. Run per application.
---

# align-resume

Generate a tailored resume for one job application. Read the JD, select the most relevant material from BACKGROUND.md, lightly reword for keyword alignment without fabricating, render to MD + PDF + DOCX in a per-job folder in CWD, enforce the target page length.

## Preconditions

- `~/.claude/career/config.yml` exists. If missing, exit with: `"Career hub config not found. Run build-background first."`
- `<hub>/BACKGROUND.md` exists. If missing, exit with: `"BACKGROUND.md not found at <hub>. Run build-background first."`
- `<hub>/template/` is populated with `resume.template.md`, `style.css`, `reference.docx`, and `template-notes.md`. If missing or incomplete, exit with: `"Template not found at <hub>/template/. Run refine-template first."`
- `pandoc` is on PATH and a PDF engine is available (try `wkhtmltopdf`, `weasyprint`, `pdflatex`). If either is missing, exit with the install hints from `refine-template`.
- `python -c "import pypdf"` succeeds. If not, exit with: `"pypdf not installed. Run 'pip install pypdf' to enable page-length enforcement."`

## Procedure

### 1. Locate inputs

Read `~/.claude/career/config.yml` to get `<hub>`. Verify BACKGROUND.md, template files, and tooling.

Ask: "Path to the job description (PDF/DOCX/MD/TXT), or paste the JD text now."

### 2. Parse the JD

Read or save the input as `job-description.md` (after determining the job slug in step 3).
- PDF / MD / TXT: read directly.
- DOCX: convert via `pandoc <file> -t markdown`.

Extract: company name, role title, hard requirements, nice-to-haves, tech/tools keywords, seniority signals, comp/location if posted.

Echo the parse back as one paragraph: "Parsed: `<company>` hiring for `<title>`. Hard reqs: `<list>`. Tech: `<list>`. Seniority: `<signal>`. Looks right?". Wait for user confirmation.

### 3. Determine job slug + folder

Default slug: `<company-slug>-<role-slug>` (lowercase, hyphenated). Confirm with user: "Folder name: `./<slug>/` — sound right?".

Check whether `./<slug>/` already exists.
- **Exists:** Ask: "Revise existing, or start fresh?". On **start fresh**, move it to `./<slug>.<YYYYMMDD-HHMMSS>.bak/`. On **revise**, load existing `resume.md` as the starting draft.
- **Missing:** create it.

Save the JD (either as-read or converted to MD) as `./<slug>/job-description.md`.

### 4. Constraint check (soft gate)

Read `<hub>/BACKGROUND.md` silently — specifically the `## Career goals & targets` and `## Constraints & non-negotiables` sections.

Check the JD against the user's stated constraints. If anything violates:
- Industry excluded?
- Comp below floor (if comp is posted)?
- Location mismatch (if location is posted)?
- Other deal-breakers?

Surface each violation as a warning: "Heads up — `<violation>`. Continue?". The user can proceed; this is not a hard block.

### 5. Material selection

Read the full `<hub>/BACKGROUND.md` and `<hub>/template/resume.template.md` and `<hub>/template/template-notes.md`. Determine target page length from `template-notes.md`.

For each section of the template, pick the most relevant material:
- **Experience** — which roles to include, and within each, which bullets. Story-bank entries are an alternate source when an experience bullet is a weak JD match. Rank bullets by JD relevance (keyword overlap + recency + seniority match); selection order is the ranking order.
- **Projects** — kept or cut depending on length target and relevance.
- **Skills** — reorder to surface JD keywords first. **Never add a skill that is not in BACKGROUND.md.**
- **Education / Certifications / Extras** — filter to relevant.

Track the relevance ranking — `align-resume` reuses it during page-trimming in step 8.

### 6. Light rewording

For each selected bullet, lightly reword to surface JD keywords. Use active voice, past tense, action verbs. **Preserve all metrics, numbers, and named technologies verbatim** from BACKGROUND.md.

**Hard rule:** never invent skills, tools, scope, or metrics. If the JD asks for something not in BACKGROUND.md, do not add it.

### 7. Preview + user review (the gate)

Render an in-memory `resume.md` (do not write to disk yet). Present a structured preview to the user:

```
Selected roles:
  - <Company> — <Title>: <N> bullets selected (out of <M> in BACKGROUND.md)
    - bullet 1 (reworded)
    - ...

Selected projects:
  - <Project name>

Reworded bullets (before → after):
  - <original> → <reworded>
  - ...

Gaps surfaced (JD requires, BACKGROUND.md does not list):
  - <requirement> — not added; consider updating BACKGROUND.md

Constraint warnings:
  - <warning if any>
```

Ask: "Accept, request specific changes, or ask for a different selection?". Iterate until the user approves.

### 8. Render + write

Write the approved files:
- `./<slug>/resume.md` — the locked markdown source.
- `./<slug>/job-description.md` — the JD (already written in step 3).

Render via Pandoc:
```bash
pandoc ./<slug>/resume.md -o ./<slug>/resume.pdf --css <hub>/template/style.css
pandoc ./<slug>/resume.md -o ./<slug>/resume.docx --reference-doc <hub>/template/reference.docx
```

**Page-target enforcement:**
1. Read target page count from `<hub>/template/template-notes.md`.
2. Run `python <skill-folder>/page_count.py ./<slug>/resume.pdf` to get the rendered page count.
3. If over target:
   - Trim the lowest-ranked bullet from the relevance ordering produced in step 5.
   - Re-render PDF + DOCX.
   - Re-count pages.
   - Repeat up to 3 attempts.
4. If still over after 3 attempts, tell the user: "Resume still <N> pages after 3 trims. Accept overflow or prune manually?". On accept, leave as-is. On prune, return to step 7 with current selection.

Iterations happen silently; the user is only re-engaged on cap failure.

Write `./<slug>/tailoring-notes.md`:

```markdown
# Tailoring notes — <slug>

**Date:** <YYYY-MM-DD>
**Target page length:** <one | two | flexible>
**Rendered page count:** <N>

## Selected from BACKGROUND.md
- Experience: <list of roles + bullet counts>
- Projects: <list>
- Skills surfaced: <list, JD-relevant>
- Certifications: <list>

## Rewording log
- <original> → <reworded>

## Gaps surfaced
- <JD requirement absent from BACKGROUND.md>

## Constraint warnings
- <if any>
```

### 9. Report

Print:
> "Wrote `./<slug>/`: `resume.md`, `resume.pdf` (<N> pages), `resume.docx`, `job-description.md`, `tailoring-notes.md`. Gaps that surfaced: <count>. Suggested next: review the PDF before submitting."

## Rules

- Never fabricate skills, tools, scope, metrics, or accomplishments.
- Preserve all numbers and named technologies verbatim from BACKGROUND.md.
- Selection > rewriting; reword only for keyword alignment or tightness.
- Hard requirements absent from BACKGROUND.md are surfaced, not papered over.
- Target page length is enforced via `page_count.py` render-and-count, not heuristic.
- If `<hub>/template/` is missing pieces, error early with a pointer to `refine-template`.
````

- [ ] **Step 2: Verify frontmatter parses**

Run:
```bash
python -c "import yaml; doc = open('skills/career/align-resume/SKILL.md').read().split('---')[1]; print(yaml.safe_load(doc))"
```
Expected: prints a dict with `name: align-resume` and the description.

- [ ] **Step 3: Verify the skill directory layout**

Run:
```bash
ls skills/career/align-resume/
```
Expected: `SKILL.md` and `page_count.py` both present.

- [ ] **Step 4: Commit**

```bash
git add skills/career/align-resume/SKILL.md
git commit -m "Add align-resume skill"
```

---

## Task 7: Update README.md

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Read current README**

Run:
```bash
cat README.md
```
Note the structure: it has a `## Skills` section with subsections per category (Orchestrator, Discover, Synthesize, Plan, Implement, Integrate).

- [ ] **Step 2: Add a Career subsection**

Use the Edit tool to add a new `### Career` block under the `## Skills` heading, after the `### Integrate` block. Insert this exact block:

```markdown
### Career
- `build-background` — interview-driven capture of career history, projects, skills, story-bank, and goals into `<career-hub>/BACKGROUND.md`. First run picks the career-hub location.
- `refine-template` — critiques resume format against modern best practices + ATS, iterates with the user, locks in a reusable template (markdown skeleton + CSS + reference.docx) in the career hub.
- `align-resume` — generates an ATS-aware tailored resume from a job description: selects and lightly rewords material from BACKGROUND.md, renders MD/PDF/DOCX into a per-job subfolder in CWD, enforces page-length target.
```

- [ ] **Step 3: Add a Career artifact-layout note**

After the existing artifact-layout block (under `## Artifact layout in your project`), add this new block:

```markdown
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
```

- [ ] **Step 4: Commit**

```bash
git add README.md
git commit -m "Document career skills in README"
```

---

## Task 8: Smoke-test the installer

**Files:** none modified — verification only.

- [ ] **Step 1: Run install in dry-run mode**

Run from the repo root:
```powershell
.\install.ps1 -DryRun
```

Expected: output lists the three new skills (`build-background`, `refine-template`, `align-resume`) as detected leaf skill folders. No errors. Existing skills are also listed (they get re-detected).

- [ ] **Step 2: Confirm skill counts**

The installer prints "Found N skill folders to install." Before this change the repo had 12 leaf skills (per the spec for the probe-feature library). After this change: 12 + 3 = 15.

Verify: `Found 15 skill folders to install.` (or higher if other skills exist).

- [ ] **Step 3: Run tests to confirm everything still passes**

Run:
```bash
pytest -v
```
Expected: existing `test_estimate_tokens.py` tests + new `test_page_count.py` tests all pass. No failures.

- [ ] **Step 4: Final verification — frontmatter on all three new skills**

Run:
```bash
python -c "
import yaml, pathlib
for p in ['skills/career/build-background/SKILL.md', 'skills/career/refine-template/SKILL.md', 'skills/career/align-resume/SKILL.md']:
    fm = pathlib.Path(p).read_text().split('---')[1]
    d = yaml.safe_load(fm)
    assert 'name' in d and 'description' in d, p
    assert d['name'] == pathlib.Path(p).parent.name, f'name mismatch in {p}'
    print(p, 'OK')
"
```
Expected: three "OK" lines, one per skill. Any assertion failure means frontmatter is wrong.

- [ ] **Step 5: Final commit** (only if any tweaks were needed during smoke test)

If smoke test surfaced anything, fix it and commit. Otherwise skip.

---

## Self-Review

**Spec coverage check:**
- ✅ Career-hub config setup — Task 2 step 2 (build-background SKILL.md procedure §1).
- ✅ BACKGROUND.md canonical schema — Task 1, referenced in Tasks 2/4/6.
- ✅ Hybrid markdown with strict H2/H3 headings — schema in Task 1.
- ✅ Existing-resume ingestion (PDF/DOCX/MD/TXT, optional) — build-background SKILL.md §3.
- ✅ Section-update mode for re-runs — build-background SKILL.md §2.
- ✅ Per-section interview with quantification pressure — build-background SKILL.md §4 + Rules.
- ✅ Career-hub layout (BACKGROUND.md + template/) — established by build-background + refine-template.
- ✅ refine-template critique + iterate flow — Task 4 SKILL.md §§6–7.
- ✅ Target-page-length captured in template-notes.md — refine-template SKILL.md §3 + §8.
- ✅ Visual + structural template both produced — refine-template SKILL.md §§4–5 + §8.
- ✅ Industry-default starter (one universal, not multiple) — Task 3 bundled assets + refine-template §§4–5.
- ✅ Pandoc + PDF engine preconditions with install hints — refine-template + align-resume preconditions.
- ✅ Per-job folder in CWD — align-resume SKILL.md §3 + §8.
- ✅ MD/PDF/DOCX outputs via Pandoc — align-resume SKILL.md §8.
- ✅ Selection > rewording with metric preservation — align-resume SKILL.md §§5–6 + Rules.
- ✅ Preview + user gate before rendering — align-resume SKILL.md §7.
- ✅ Gaps surfaced, not fabricated — align-resume SKILL.md §7 + Rules.
- ✅ Page-target enforcement via render-and-count, 3-attempt cap, silent iterations — align-resume SKILL.md §8.
- ✅ "Lowest-priority" trimming = reverse of step-5 relevance ranking — align-resume SKILL.md §§5+8.
- ✅ tailoring-notes.md per job — align-resume SKILL.md §8.
- ✅ Installer needs no changes — confirmed in Task 8 smoke test.
- ✅ README documents the new skills — Task 7.

**Placeholder scan:** No "TBD", "TODO" (in plan steps), "implement later", or vague handwaving. All file paths are concrete. All code blocks are complete.

**Type / signature consistency:**
- `page_count.py` API: takes one positional arg, prints integer, exit 0/1/2 — consistent across test (Task 5 step 2) and implementation (Task 5 step 4) and align-resume invocation (Task 6 §8).
- Career hub config schema (`hub:` + `created:`) consistent across build-background, refine-template, align-resume.
- `template-notes.md` structure defined in refine-template §8; align-resume §8 reads `target page count` from it — consistent.
- Section headings of BACKGROUND.md are the same across the canonical schema (Task 1), build-background's writer (Task 2), refine-template's reader (Task 4), align-resume's reader (Task 6).

---

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-05-12-career-skills.md`. Two execution options:

**1. Subagent-Driven (recommended)** — Dispatch a fresh subagent per task, review between tasks, fast iteration.

**2. Inline Execution** — Execute tasks in this session using executing-plans, batch execution with checkpoints.

Which approach?
