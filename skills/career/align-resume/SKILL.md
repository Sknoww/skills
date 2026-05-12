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
- **Exists:** Ask: "Revise existing, or start fresh?".
  - On **start fresh**, move it to `./<slug>.<YYYYMMDD-HHMMSS>.bak/` and re-create.
  - On **revise**: re-use the existing `job-description.md` (skip Step 2's JD parsing). Load the existing `resume.md` as the prior selection — pass it through to Step 5 so the material selection prefers the prior choices unless JD context has shifted. In Step 7, show a per-section diff against the prior `resume.md` so the user sees what changed.
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

If running in revise mode (Step 3), start from the prior `resume.md`'s selections and only re-rank if the JD parse in Step 2 surfaces new requirements not addressed by the prior version.

Read the full `<hub>/BACKGROUND.md` and `<hub>/template/resume.template.md` and `<hub>/template/template-notes.md`. Determine target page length from `template-notes.md`.

For each section of the template, pick the most relevant material:
- **Experience** — which roles to include, and within each, which bullets. Story-bank entries are an alternate source when an experience bullet is a weak JD match. Rank bullets by JD relevance (keyword overlap + recency + seniority match); selection order is the ranking order.
- **Projects** — kept or cut depending on length target and relevance.
- **Skills** — reorder to surface JD keywords first. **Never add a skill that is not in BACKGROUND.md.**
- **Education / Certifications / Extras** — filter to relevant.

Maintain a ranked-bullet list in memory: a list of (role, bullet-index, bullet-text, JD-relevance-score) tuples, ordered by score descending. Step 8's page-trimming reuses this list — removing bullets from the bottom (lowest score) first.

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

If revising, show a per-section diff against the prior resume.md (sections added/removed/reworded).
```

Ask: "Accept, request specific changes, or ask for a different selection?". Iterate until the user approves.

### 8. Render + write

Write the approved files:
- `./<slug>/resume.md` — the locked markdown source.
- `./<slug>/job-description.md` — the JD (already written in step 3).

Render via Pandoc:
```bash
pandoc ./<slug>/resume.md -o ./<slug>/resume.pdf --pdf-engine=<detected-pdf-engine> --css <hub>/template/style.css
pandoc ./<slug>/resume.md -o ./<slug>/resume.docx --reference-doc <hub>/template/reference.docx
```

`<detected-pdf-engine>` is the engine identified in Preconditions (one of `wkhtmltopdf`, `weasyprint`, `pdflatex`). The `--css` flag is honored only for HTML-based engines (`wkhtmltopdf`, `weasyprint`); pdflatex users will see unstyled output unless they also customize a LaTeX template (out of scope).

**Page-target enforcement:**

If the target recorded in template-notes.md is "flexible", skip this entire enforcement block.

1. Read target page count from `<hub>/template/template-notes.md`.
2. Run `python ~/.claude/skills/align-resume/page_count.py ./<slug>/resume.pdf` to get the rendered page count. (`page_count.py` is bundled in the same folder as this SKILL.md; after the repo installer runs, the install location is `~/.claude/skills/align-resume/page_count.py`. If the skill is invoked from the source repo directly, substitute the source path.)
3. If over target:
   - Trim the lowest-ranked bullet from the relevance ordering produced in step 5.
   - Re-render PDF + DOCX.
   - Re-count pages.
   - Repeat up to 3 attempts. (Attempt 1 = first trim-and-rerender. The initial render before any trimming is not counted.)
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
- If `template-notes.md` records "flexible" as the page target, skip page-count enforcement in Step 8.
- If `<hub>/template/` is missing pieces, error early with a pointer to `refine-template`.
