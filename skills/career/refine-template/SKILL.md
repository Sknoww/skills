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

Read `~/.claude/career/config.yml` to determine `<hub>` for all subsequent steps.

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
- **Exists:** read it (PDF/MD/TXT directly; DOCX via `pandoc <file> -t markdown`). Extract section order and naming as the starting structural template. Write the extracted structure to `<hub>/template/resume.template.md` as the starting draft.
- **Missing:** copy `default-resume.template.md` (bundled in this skill folder) to `<hub>/template/resume.template.md`.

### 5. Establish the visual starting point

- Copy `default-style.css` (bundled in this skill folder) to `<hub>/template/style.css`.
- Generate a starter reference.docx via Pandoc:
  ```bash
  pandoc --print-default-data-file reference.docx > <hub>/template/reference.docx
  ```

Render a sample PDF + DOCX to `./.scratch/` (a folder in the **current working directory** — the directory the user invoked Claude from, not the career hub and not the OS temp dir). Create `./.scratch/` if it does not exist. Never use `/tmp`, `$TMPDIR`, `%TEMP%`, or any path outside CWD for scratch output.

- Populate the template by reading selected highlights from BACKGROUND.md (Personal, top 1–2 roles, top 3 skills, top 2 projects, education, top certs). **Substitute every `{{...}}` placeholder with the corresponding value from BACKGROUND.md.** Remove any `<!-- Repeat per ... -->` HTML comments before rendering — repeat the surrounding block once per source entry (e.g., one `### <Company> — <Title>` block per role from BACKGROUND.md Experience). Write the populated source to `./.scratch/resume.md`.
- Render:
  - `pandoc ./.scratch/resume.md -o ./.scratch/resume.pdf --pdf-engine=<detected-pdf-engine> --css <hub>/template/style.css`
  - `pandoc ./.scratch/resume.md -o ./.scratch/resume.docx --reference-doc <hub>/template/reference.docx`

  `<detected-pdf-engine>` is the engine identified in Preconditions (one of `wkhtmltopdf`, `weasyprint`, `pdflatex`). The `--css` flag is honored only for HTML-based engines (`wkhtmltopdf`, `weasyprint`); pdflatex users will see unstyled output unless they also customize a LaTeX template (out of scope).

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

After each accepted change, re-render the sample PDF + DOCX so the user can see the effect concretely (use the same two Pandoc commands from Step 5, writing into `./.scratch/` in CWD: `pandoc ./.scratch/resume.md -o ./.scratch/resume.pdf --pdf-engine=<detected-pdf-engine> --css <hub>/template/style.css` and `pandoc ./.scratch/resume.md -o ./.scratch/resume.docx --reference-doc <hub>/template/reference.docx`).

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
- **Scratch output stays in CWD.** All transient sample renders (PDF/DOCX/MD generated during iteration) must be written to `./.scratch/` — a folder inside the user's current working directory (the directory Claude was launched from). Do **not** write to `/tmp`, `$TMPDIR`, `%TEMP%`, `tempfile.mkdtemp()`, or any other path outside CWD. The only files allowed outside CWD are the locked template files at `<hub>/template/` (per the design) and reads from `<hub>/BACKGROUND.md`.
