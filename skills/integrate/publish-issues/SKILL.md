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

(END publish-issues)
