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
