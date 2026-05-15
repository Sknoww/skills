---
name: chart-publishing-path
description: Audits an Expo / React Native app and produces (or idempotently updates) docs/publishing-roadmap.md — a single checklist showing what stands between the project and shipping to the Apple App Store and/or Google Play. Re-run any time; developer notes are preserved across runs.
---

# chart-publishing-path

Produces and maintains `docs/publishing-roadmap.md`: a living checklist of everything between "code mostly working" and "app live in the stores." Tuned for Expo / React Native (managed + bare workflows).

The skill produces the roadmap; it does not do the publishing work.

## Preconditions

1. Working directory must contain at least one of:
   - `app.json`
   - `app.config.js` or `app.config.ts`
   - `package.json` whose `dependencies` includes `expo` or `react-native`

   If none are present, refuse:
   > "`chart-publishing-path` is tuned for Expo / React Native projects. I don't see `app.json`, `app.config.*`, or a `package.json` with `expo` / `react-native`. Re-run from your app project root."

2. `docs/` must exist or be creatable. Create it if absent.

3. Git repo is a soft precondition — used only for the dirty-file safety check in step 8.

## Procedure

### 1. Detect prior state

Check if `docs/publishing-roadmap.md` exists.

- **Exists** → "update" mode. Parse it to in-memory state (step 2).
- **Does not exist** → "scaffold" mode. Start with empty state.

### 2. Parse existing roadmap (update mode only)

Run:

```
python <this-skill-folder>/roadmap_merge.py parse docs/publishing-roadmap.md > /tmp/roadmap_state.json
```

The script emits JSON of items, headers, dev notes, and history log.

### 3. Ask the platform question

Ask the developer:

> "Apple App Store, Google Play, or both?"

Defaults:
- In update mode: default to whatever the existing roadmap's `**Platforms:**` line covers.
- In scaffold mode: if `app.json` declares only an `ios` block (no `android`), frame as confirmation for "Apple only"; if only `android`, frame as "Google only"; otherwise default "Both."

### 4. Detect framework + collect header metadata

From `app.json` / `app.config.*`:
- App name (`expo.name` or `name`).
- Bundle ID (`expo.ios.bundleIdentifier`), package name (`expo.android.package`). Prefer the one matching the platforms in scope.
- Framework string. Detect:
  - `expo-managed` if `expo` in dependencies AND `ios/` does not exist.
  - `expo-bare` if `expo` in dependencies AND `ios/` exists.
  - `bare-react-native` if no `expo` dependency AND `ios/` exists.
  - Then format as e.g., `"Expo SDK 52 / React Native 0.76 (managed)"`.

### 5. Dispatch audits in parallel

In a SINGLE message, fire the in-scope subagents using the `Agent` tool. The two audits run concurrently:

**Apple audit** (`subagent_type: general-purpose`):

```
You are an Apple App Store publishing-readiness auditor for an Expo /
React Native app.

Project root: <absolute path>

Read the audit guide at <absolute path to this skill folder>/audits/apple.md
in full, then audit the project against every checklist item in the guide.

Output: a JSON fenced code block at the end of your reply, with this shape:

{
  "platform": "apple",
  "framework_detected": "<expo-managed | expo-bare | bare-react-native>",
  "expo_sdk_version": "<string or null>",
  "items": [
    {
      "id": "<from-guide>",
      "section": <1-10>,
      "title": "<from-guide>",
      "platform_tag": "Apple | Both",
      "status": "done | partial | pending | blocked | unknown | not-applicable",
      "evidence": "<short prose with file:line refs>",
      "interview_question": "<from-guide if status=unknown or blocked>",
      "next_action": "<one-line developer next step>"
    }
  ]
}

Rules:
- Read-only. Do not write files. Do not run builds.
- Glob first to confirm what exists, then Read for contents.
- Apply each item's criteria from the guide exactly.
- For shared cross-platform items (id prefix `shared.`), set platform_tag to "Both".
```

**Google audit** has the same prompt structure with `audits/google.md` and `platform: "google"`.

If only one platform is in scope, dispatch only that subagent.

### 6. Collect findings + interview the gaps

After both subagents return:

1. Extract the JSON fenced block from each subagent's reply.
2. Combine items into a single findings list. For items appearing in both (id prefix `shared.`), reconcile by taking the more conservative status (e.g., if Apple says `done` and Google says `pending`, use `pending` because the shared item only counts as done when both platforms agree).
3. Build `findings.json`:

```
{
  "audit_date": "<today YYYY-MM-DD>",
  "platforms_audited": ["apple", "google"],
  "framework_detected": "<detected>",
  "items": [<combined items list, drop interview_question key>]
}
```

4. For every item with `status: "unknown"` or `status: "blocked"`, ask the developer the item's `interview_question` ONE AT A TIME. Skip questions whose answer is already in the existing roadmap (item exists with status `done` or has a dev note covering this question — see merge rules for "Skip questions whose answer is in the existing roadmap" in the design spec).

   For each answer, update the item's `status` and `evidence`:
   - "Yes, done" → `status: "done"`, evidence: "_user confirmed: <answer>_"
   - "No, not yet" → `status: "pending"` or `blocked`, evidence: "_user reported not done as of <date>_"
   - "N/A for this project" → `status: "not-applicable"`

5. Write the finalized findings to `findings.json`.

### 7. Merge

Run:

```
python <this-skill-folder>/roadmap_merge.py merge /tmp/roadmap_state.json findings.json > /tmp/merged_state.json
```

(In scaffold mode, pass an empty state JSON: `echo '{"header":{},"items":[],"history":[]}' > /tmp/roadmap_state.json` first.)

### 8. Git-dirty safety check (update mode only)

If `docs/publishing-roadmap.md` already exists AND the working directory is a git repo, run:

```
git status --porcelain docs/publishing-roadmap.md
```

If output is non-empty (file has uncommitted changes), pause and ask:

> "`docs/publishing-roadmap.md` has uncommitted manual edits. The merge rules preserve `> _Dev note_` blockquotes but not freeform edits elsewhere. Commit your edits first, or proceed and risk losing them?"

Do not proceed without explicit confirmation.

### 9. Build metadata + render

Build `metadata.json` (in `/tmp/`):

```
{
  "generated_date": "<today YYYY-MM-DD>",
  "platforms": [<from step 3, formatted as 'Apple App Store' / 'Google Play'>],
  "app_name": "<from step 4>",
  "bundle_id": "<from step 4>",
  "framework": "<from step 4>",
  "last_audit_date": "<today YYYY-MM-DD>",
  "template_path": "<absolute path to this skill folder>/templates/roadmap.md"
}
```

Then render:

```
python <this-skill-folder>/roadmap_merge.py render /tmp/merged_state.json /tmp/metadata.json > docs/publishing-roadmap.md
```

### 10. Print summary

Output a short message to the developer:

> Roadmap updated at `docs/publishing-roadmap.md`.
>
> - ✅ Done: N
> - 🟡 In progress: N
> - ⬜ Pending: N
> - 🚧 Blocked on you: N
> - ⚠️ Needs re-check: N
>
> Re-run `chart-publishing-path` any time after making progress to refresh.

## Edge cases

- **Subagent returns malformed JSON.** Retry the dispatch ONCE with a tighter prompt that includes the prior malformed output. If still malformed, fall back to walking the developer through the audit guide manually, asking each item's interview question.
- **Audit guide file missing.** Hard error: "`audits/apple.md` not found. Re-run `install.ps1` / `install.sh` to refresh skills."
- **Project has only `app.json` `ios` block (no `android`).** Default Q3 to "Apple only."
- **Working directory is not a git repo.** Skip step 8 silently.
- **`app.config.ts` only (no `app.json`).** The subagent reads it as TypeScript source via `Read`. It does NOT execute the config. Dynamic config values become `unknown` findings → interview questions.

## Not supported in v1

- Multi-app monorepos with multiple `app.json` files.
- Native-only iOS or Android projects without an Expo / RN bridge.
- Auto-fixing audit findings.

## Files in this skill

- `audits/apple.md`, `audits/google.md` — the audit guides handed to the subagents.
- `templates/roadmap.md` — scaffold-mode template.
- `roadmap_merge.py` — Python helper for parse / merge / render. Mirrors the source-of-truth at `scripts/roadmap_merge.py` in the skill-library repo.
