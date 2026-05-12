# Career Skills (`build-background` / `refine-template` / `align-resume`) — Design

**Status:** Approved 2026-05-12
**Scope:** Three new skills under `skills/career/` for capturing career background once and generating job-tailored resumes per application. Standalone from the probe-feature flow.

## Goal

A three-skill flow that lets the user:

1. Capture their full career history, projects, skills, and achievements **once** into a canonical `BACKGROUND.md` (`build-background`).
2. Critique and lock in a **reusable resume template** — structural + visual — that respects modern best practices, ATS constraints, and a target page length (`refine-template`).
3. Generate an ATS-aware, **job-tailored resume per application** with MD/PDF/DOCX artifacts (`align-resume`).

The skills run independently with preconditions guarding the flow (no orchestrator). Once set up, the steady-state cost per job application is one `align-resume` invocation.

## Philosophy

- **Single source of truth.** Career facts live in one `BACKGROUND.md` outside any project directory. Tailored resumes are derivations, never inputs to other resumes.
- **Truthfulness over keyword density.** Skills never fabricate skills, tools, scope, or metrics. Gaps between a JD and BACKGROUND.md are surfaced, not papered over.
- **ATS-first defaults.** Single-column layouts, text-based content, no graphics/icons/photos in headers, no header/footer text. Visual flair only with explicit user override.
- **Hard page targets.** Length is set in `refine-template` and enforced by render-and-count in `align-resume`, not heuristic estimation.
- **Phase gates via preconditions.** Each skill refuses to run if upstream artifacts are missing, with a clear pointer to the prior skill.
- **Composed skills, no orchestrator.** Three independent entry points the user invokes by name. Matches how the probe-* skills compose in this repo.

## Architecture overview

**Happy path:**
```
build-background   →   refine-template   →   align-resume <jd>   (re-run per application)
```

**Two storage locations:**
- **Career hub** — long-lived, single source of truth. User-chosen path, recorded once in a config file. Holds `BACKGROUND.md` and the locked template.
- **Per-job folder in CWD** — created by `align-resume` each time. Holds the JD plus tailored resume artifacts.

**Career-hub config:** `~/.claude/career/config.yml`
```yaml
hub: C:\Users\hsfro\career
created: 2026-05-12
```
Created by `build-background` on first run. Both other skills read it; if missing they error with "run `build-background` first."

**Career-hub layout:**
```
<hub>/
├── BACKGROUND.md
├── .imported-resume.<ext>      ← optional, stashed if user provided one to build-background
└── template/
    ├── resume.template.md      ← structural skeleton with placeholders
    ├── style.css               ← Pandoc CSS for PDF rendering
    ├── reference.docx          ← Pandoc reference doc for DOCX styling
    └── template-notes.md       ← decisions log: industry, page-target, ATS choices
```

**Per-job layout** (`align-resume` invoked in any directory):
```
<cwd>/<job-slug>/
├── job-description.md
├── resume.md
├── resume.pdf
├── resume.docx
└── tailoring-notes.md          ← what was selected, what was reworded, what was missing
```

## External dependencies

| Tool | Required by | Behavior if missing |
|---|---|---|
| **Pandoc** | `refine-template`, `align-resume` | Skill exits at start with install hints (`winget install JohnMacFarlane.Pandoc` / `brew install pandoc` / `apt install pandoc`). |
| **PDF engine** (LaTeX, wkhtmltopdf, or weasyprint) | `refine-template`, `align-resume` | Skill auto-detects available engine. If none, exits with install hints. |

`build-background` has no hard external dependencies — it operates on text.

## BACKGROUND.md schema

Strict H2 sections in fixed order. Each has a stable H3 sub-structure so consumers can parse without ambiguity.

```markdown
# Background

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
```

Gaps the user wants to fill later are marked with `<!-- TODO: ... -->` markers anywhere in the file.

## Skill 1 — `build-background`

**Description:** "Interactive interview that captures the user's full career history, projects, skills, and achievements into a canonical BACKGROUND.md in the career hub. Optionally seeded by an existing resume. Re-run to update specific sections. Use when starting career-skill setup or when career history needs revising."

**Preconditions:** None — entry point.

**Procedure:**

1. **First-run hub setup.** If `~/.claude/career/config.yml` is missing: ask user for hub path (default `~/career/`); create the directory and config.

2. **Detect existing BACKGROUND.md.**
   - If present: ask **full re-interview** or **update specific sections**. On full re-interview, back up the existing file as `BACKGROUND.<timestamp>.md.bak` before overwriting. On section update, read the file silently and interview only the chosen sections.
   - If missing: proceed to new flow.

3. **Optional resume ingestion** (new flow, or if user opts to re-seed during update):
   - Ask for path; skip if none provided.
   - Stash a copy at `<hub>/.imported-resume.<ext>` for `refine-template` to use later.
   - Read it: PDF/MD/TXT directly via the Read tool; DOCX via Pandoc-to-MD if available, else unzip+parse fallback.
   - Extract what can be inferred per section. Present a summary chunk per section: "Here's what I pulled for Experience — accurate?". User confirms or corrects.
   - Extracted answers seed the interview; the skill skips re-asking and focuses on **digging deeper** (metrics, context, why-you-left, story-grade detail).

4. **Interview each section** (one question at a time, sections in schema order):
   - **Personal** — name, email, phone, location, LinkedIn, GitHub, site, headline.
   - **Career goals & targets** — target roles/levels, industries in/out, search trigger.
   - **Constraints & non-negotiables** — comp floor, location/remote, deal-breakers, travel, work-auth.
   - **Experience** — per role, most-recent-first: company, title, dates, location, work mode, team/company scope, why joined, why left, top 3–5 accomplishments **with metrics**, tech stack, notable projects within the role, skills developed. The skill aggressively pushes for quantification.
   - **Projects** — name, description, role if collaborative, tech, outcome, link, motivation.
   - **Education** — per institution: degree, major/minor, dates, optional GPA, honors, relevant coursework. Bootcamps count.
   - **Skills** — languages w/ proficiency, frameworks, tools/platforms, domain expertise, soft skills.
   - **Certifications** — name, issuer, date, expiry, credential ID.
   - **Story bank (STAR)** — push for 5–10 strong stories with metrics.
   - **Extras** — awards / publications / talks / volunteer / languages / patents. Skill asks "any of these apply?" and only probes the relevant ones.

5. **Write `BACKGROUND.md`** to the career hub using the canonical schema. Use `<!-- TODO: ... -->` markers for gaps.

6. **Report** — summary, TODO count, next step: "Run `refine-template` to lock in your resume template."

**Rules:**
- One question at a time. Never batch.
- Experience and Projects: most-recent-first.
- Push back **once** on vague answers; if still vague, capture as a TODO marker.
- Push hard for quantification on accomplishments and story-bank entries.
- Never fabricate. If extracted-from-resume info is uncertain, confirm before writing.
- On update mode, read existing file silently first; don't re-ask answered questions.

## Skill 2 — `refine-template`

**Description:** "Critiques the user's existing resume format against modern industry best practices and ATS requirements, iterates with the user on structure and visuals, and locks in a reusable resume template (structural + CSS + reference.docx) in the career hub. Use after build-background, or anytime the template needs revising."

**Preconditions:**
- Career hub config exists (errors otherwise with "run `build-background` first").
- `<hub>/BACKGROUND.md` exists.
- Pandoc + PDF engine available (errors with install hints if not).

**Procedure:**

1. **Detect existing template.**
   - If `<hub>/template/` is populated: ask **revise existing** or **start over**. On start-over, back up as `template.<timestamp>.bak/`.
   - If missing: new flow.

2. **Determine industry context.** Read BACKGROUND's `Career goals & targets` and `Experience` silently; infer primary industry (software engineering, design, finance, academic, sales, etc.). Confirm assumption with user. Drives section ordering, length norms, and style register.

3. **Establish target length.** Ask: one page, two pages, or flexible. Suggest a default based on industry + years of experience (tech ≤10 yrs → one page; academic/medical → multi-page CV; senior leadership → two pages OK). If the user picks one-pager but their Experience spans many roles/years, warn upfront and re-confirm. Store the choice in `template-notes.md`.

4. **Establish the structural starting point.**
   - If `<hub>/.imported-resume.<ext>` exists: extract section order and naming as the starting point.
   - Else: use the industry-default structural template baked into the skill.
   - Generate `<hub>/template/resume.template.md` — a skeleton with placeholders (`{{personal.name}}`, `{{experience[].bullets}}`, etc.).

5. **Establish the visual starting point.** Generate starter `style.css` and `reference.docx` from the industry default. Render a sample resume to a temp scratch dir (populate template with selected highlights from BACKGROUND.md, render to PDF + DOCX via Pandoc).

6. **Critique pass.** Skill writes a critique covering modern best practices + ATS pitfalls. Categories:
   - Section order and naming.
   - Length vs target (over/under, where to cut).
   - Bullet length and density.
   - Action verbs and active voice.
   - Quantification of accomplishments.
   - White space and rhythm.
   - Fonts (typeface, sizes, hierarchy).
   - Column count (single-column required for ATS unless overridden).
   - Graphics/icons/photos (ATS-hostile).
   - Header/footer text (ATS often skips).
   - File naming conventions.
   - Industry-specific length norms.

   Present 5–10 prioritized issues with concrete suggested fixes.

7. **Iterate with user.** One issue at a time: "Issue #1: [description]. Suggested fix: [fix]. Apply, skip, or modify?". After each accepted change, re-render the sample so the user sees the effect. Continue until sign-off.

8. **Lock in the template.** Write final `<hub>/template/resume.template.md`, `style.css`, `reference.docx`, and `template-notes.md` (decisions log including industry assumption, page target, ATS choices).

9. **Report** — summary of locked decisions; next step: "Run `align-resume <jd-path>`."

**Rules:**
- One critique issue at a time.
- Re-render the sample after each accepted change.
- Never override ATS-safety choices for visual flair without explicit user confirmation (warn first on two-column, graphics, etc.).
- Check Pandoc + PDF engine **before** starting the interview.
- Industry inference is a soft default; user can override at any point.
- Target page length is a hard constraint for downstream `align-resume`.

## Skill 3 — `align-resume`

**Description:** "Generates an ATS-aware, job-tailored resume from a job description by selecting and lightly rewording material from BACKGROUND.md, using the locked template. Outputs MD/PDF/DOCX into a per-job subfolder in CWD. Run per application."

**Preconditions:**
- Career hub config exists; `BACKGROUND.md` exists; `template/` is populated. Each missing piece errors with a pointer to the prior skill.
- Pandoc + PDF engine available (checked up front, errors with install hints if absent).

**Procedure:**

1. **Locate inputs.** Read career hub config; verify BACKGROUND.md + template + tooling. Ask for job description: file path (PDF/MD/TXT/DOCX) or pasted text.

2. **Parse the JD.** Read or save the input. Extract: company, role title, hard requirements, nice-to-haves, tech/tools keywords, seniority signals, comp/location if posted. Echo the parse back to the user for confirmation in one paragraph.

3. **Determine job slug + folder.** Default `<company-slug>-<role-slug>`; confirm with user. If `./<job-slug>/` already exists, ask **revise existing** or **start fresh** (back up old as `./<job-slug>.<timestamp>.bak/`).

4. **Constraint check (soft gate).** Read `Career goals & targets` + `Constraints & non-negotiables` from BACKGROUND.md silently. If the JD violates anything (industry excluded, comp below floor, location mismatch), surface it as a warning. Not a hard block.

5. **Material selection.** For each template section, pick the most relevant material from BACKGROUND.md:
   - Experience: which roles, which bullets per role (story bank as alternate bullet fodder when an experience bullet is a weak JD match).
   - Projects: kept or cut depending on length target.
   - Skills: reordered to surface JD keywords first; never add skills not in BACKGROUND.md.
   - Education / Certs / Extras: filter to relevant.
   - Respects the page-length target from `template-notes.md`.

6. **Light rewording.** Reword selected bullets to surface JD keywords. Active voice, past tense, action verbs. **Preserve all metrics and numbers verbatim.** Never invent skills, tools, scope, or metrics that aren't in BACKGROUND.md.

7. **Preview + user review (the gate).** Render `resume.md` and show the user a structured preview:
   - Selected roles/bullets/projects.
   - Reworded bullets shown as `before → after` diffs.
   - **Gaps surfaced:** JD requirements not present in BACKGROUND.md are called out, not silently added.
   - Constraint warnings if any.

   User accepts, requests targeted changes, or asks for a different selection. Iterate to approval.

8. **Render + write.**
   - Write `resume.md` and `job-description.md` to `./<job-slug>/`.
   - Pandoc → `resume.pdf` and `resume.docx`.
   - **Page-target enforcement:** if rendered PDF exceeds target page count, trim (lowest-priority bullets first) and re-render. Cap at 3 attempts; if still over, surface to user with options (accept overflow or prune manually).
   - Write `tailoring-notes.md` — what was selected, what was reworded, what was missing.

9. **Report.** Paths to all outputs. Any BACKGROUND.md TODOs the JD surfaced as worth filling in. Suggested next: review the PDF before submitting.

**Rules:**
- Never fabricate skills, tools, scope, metrics, or accomplishments.
- Preserve all numbers verbatim.
- Selection > rewriting; reword only for keyword alignment or tightness.
- Hard requirements absent from BACKGROUND.md are surfaced, not papered over.
- Target page length is enforced via render-and-count.

## Repo additions

```
skills/career/
├── build-background/SKILL.md
├── refine-template/SKILL.md
└── align-resume/SKILL.md

skills/shared/templates/
└── BACKGROUND-template.md          ← canonical BACKGROUND.md schema
```

The existing `install.ps1` / `install.sh` already walks recursively for any `SKILL.md`, so no installer changes are needed — these are picked up automatically.

## Out of scope

- **Cover-letter generation.** Could be a future `align-cover-letter` skill consuming the same BACKGROUND.md + JD.
- **Application tracking** (status, interview notes, follow-ups). Per-job folders could grow to support this later but v1 stays generation-only.
- **LinkedIn / online-profile alignment.** Same data could feed it; out of scope here.
- **Auto-submit** to job boards or ATS systems.
- **Interview prep tooling.** Story bank is captured, but using it for mock interviews is a separate skill.
- **Multi-language resumes.** Single-language only in v1.

## Success criteria

1. Running `build-background` on a user with an existing resume produces a complete `BACKGROUND.md` in one sitting, with quantified accomplishments and a story bank that exceeds what was in the original resume.
2. `refine-template` produces a template that respects the user's chosen page length and passes a basic ATS-friendliness check (single column, no graphics, plain headings, text-based).
3. `align-resume` on a JD produces a tailored resume that (a) fits the page target, (b) surfaces JD-required skills missing from BACKGROUND.md rather than fabricating them, and (c) preserves all metrics from BACKGROUND.md verbatim.
4. Skipping a phase fails fast with a clear error pointing to the missing artifact.
5. A user who has run setup once can produce a tailored resume for a new JD in a single `align-resume` invocation.
