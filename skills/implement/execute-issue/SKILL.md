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

(END execute-issue)
