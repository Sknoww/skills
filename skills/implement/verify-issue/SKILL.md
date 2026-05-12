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

(END verify-issue)
