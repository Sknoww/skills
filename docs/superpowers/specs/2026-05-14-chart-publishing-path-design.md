# `chart-publishing-path` skill — design

**Date:** 2026-05-14
**Status:** Draft, awaiting plan
**Library stage:** `skills/release/` (new stage)
**Output artifact:** `docs/publishing-roadmap.md` (one per app project, lives at `docs/` root)

## Goal

Help a developer working on an Expo / React Native app understand exactly what stands between "code mostly working" and "app live in the Apple App Store and/or Google Play." The skill produces and maintains a single roadmap file — a living checklist scoped to the app's actual state, refreshed by re-invoking the skill.

The skill produces a map; it does not do the work. It will not run `eas submit`, fill in App Store Connect forms, or generate marketing assets. Its value is keeping the developer's attention on the right unfinished thing.

## Non-goals

- Multi-app monorepos with multiple `app.json` files.
- Native-only iOS or Android projects without an Expo / RN bridge.
- Auto-fixing audit findings.
- ASO keyword research, marketing/launch comms, A/B testing setup, post-launch optimisation.

## Shape at a glance

- **Skill:** `chart-publishing-path`
- **Lifecycle:** idempotent — first run scaffolds, subsequent runs merge new audit findings into the existing roadmap while preserving developer notes.
- **Information gathering:** audit-first via two parallel `general-purpose` subagents (one Apple, one Google), then interview the developer for whatever the audit cannot determine. Matches the established pattern in `probe-technical`.
- **Output structure:** single file, organised by concern, items tagged `[Apple]` / `[Google]` / `[Both]`. Items the audit proves don't apply are dropped, not listed-and-marked-N/A.
- **Scope:** Expo / React Native only — both managed and bare workflows. Other frameworks are out of scope for v1.

## Architecture

### Flow (single run)

```
1. Preconditions check
   └─ Working dir looks like an Expo/RN app (app.json,
      app.config.{js,ts}, or package.json with expo/react-native dep).
      Refuse cleanly if not.

2. Detect prior state
   └─ Does docs/publishing-roadmap.md exist?
       No  → "scaffold" mode
       Yes → "update" mode (parse existing roadmap)

3. One question to the developer:
   "Apple App Store, Google Play, or both?"
   └─ In update mode, default to whatever the existing roadmap covers.
   └─ If app.json has only ios or only android block, frame as confirmation.

4. Dispatch audits in parallel (single message, multiple Agent tool uses).
   └─ Apple audit subagent (if Apple in scope), given audits/apple.md
   └─ Google audit subagent (if Google in scope), given audits/google.md
   Each returns a JSON-in-fenced-block of findings.

5. Reconcile + interview the gaps.
   └─ For each finding marked "unknown" or "blocked", ask the developer
      one at a time using the item's `interview_question`.
   └─ Skip questions whose answer is already in the existing roadmap and
      hasn't been contradicted by the new audit (e.g., the prior run
      converted a "blocked" item to ✅ via a dev note — don't re-ask).

6. Write/update docs/publishing-roadmap.md
   └─ Scaffold mode: write fresh from template.
   └─ Update mode: merge per rules below; preserve dev notes; append to
      the history log.

7. Print a short summary
   └─ "N done, M pending, K blocked on you, J net new since last run."
```

### Skill folder layout

```
skills/release/chart-publishing-path/
├── SKILL.md
├── audits/
│   ├── apple.md       ← Apple audit guide (read by Apple subagent)
│   └── google.md      ← Google audit guide (read by Google subagent)
└── templates/
    └── roadmap.md     ← Skeleton used in scaffold mode
```

The audit guides are the durable expertise of the skill — they live in their own files because (a) they are likely to be updated independently when Apple/Google requirements change, and (b) keeping them out of `SKILL.md` keeps the skill's procedural document focused on flow rather than content.

### Subagent contract

Each subagent is `subagent_type: "general-purpose"` and is given a prompt of roughly this shape (Apple version):

```
You are an Apple App Store publishing-readiness auditor for an Expo /
React Native app.

Job: audit the codebase at <absolute project path> against the checklist
in skills/release/chart-publishing-path/audits/apple.md and return a
structured JSON-in-fenced-block of findings.

Scope: read only. Do not write files. Do not run builds.

Procedure:
1. Read the audit guide in full.
2. Read every file the guide tells you to inspect (app.json, app.config.*,
   eas.json, package.json, ios/ if present, Info.plist if present, etc.).
   Glob first to confirm what exists, then Read for contents.
3. For each checklist item in the guide, classify as:
     "done"           — code/config clearly satisfies the item
     "partial"        — some evidence but incomplete
     "pending"        — no evidence, but inferable that it applies
     "blocked"        — requires human action the codebase can't supply
     "unknown"        — audit can't determine; flag for interview
     "not-applicable" — explicitly doesn't apply
4. Return findings as a fenced JSON block at the end of your reply.

Findings schema:
{
  "platform": "apple",
  "framework_detected": "expo-managed | expo-bare | bare-react-native",
  "expo_sdk_version": "<string>" or null,
  "items": [
    {
      "id": "apple.signing.distribution-cert",
      "section": "Build, Signing & EAS Submit",
      "title": "iOS distribution certificate",
      "status": "done | partial | pending | blocked | unknown | not-applicable",
      "evidence": "file:line references or short prose",
      "interview_question": "asked only if status=unknown",
      "next_action": "what the developer needs to do, in one line"
    }
  ]
}
```

The Google subagent has the identical shape with `audits/google.md` and `platform: "google"`.

**Why JSON-in-a-fenced-block at the end:**
- Easy for the orchestrator to extract (locate the JSON fence, parse).
- The subagent can still write prose above the JSON for its own reasoning trail; the orchestrator ignores it.
- Keeps the orchestrator stateless w.r.t. the subagent's internal reasoning process.

### Audit guide structure (`audits/apple.md`, `audits/google.md`)

Each guide contains three sections:

1. **What to read.** Explicit list of files / globs the subagent must inspect.
2. **How to interpret the Expo workflow.** Calls out the difference between managed (no `ios/`, no `Info.plist`; truth lives in `app.json` `ios.infoPlist`) and bare (`ios/` and `Info.plist` present and authoritative).
3. **Checklist items.** One entry per item, each with:
   - **Done if:** criteria the audit can confirm from code/config.
   - **Partial if:** criteria for partial evidence.
   - **Pending if:** what "not done but applies" looks like.
   - **Interview question (if unknown or blocked):** the question to ask if the audit cannot determine status.

Example item:

```markdown
### apple.signing.distribution-cert
- Done if: eas.json production profile has credentials resolved, OR ios/
  has a valid embedded provisioning profile referencing a distribution
  identity.
- Partial if: profile exists but app ID mismatches bundle identifier.
- Pending if: no signing config found.
- Interview question (if unknown or blocked): "Have you generated an iOS distribution
  certificate (via `eas credentials` or manually in App Store Connect)?"
```

## The roadmap file

### Skeleton

```markdown
# Publishing Roadmap

> Generated by `chart-publishing-path` on YYYY-MM-DD. Re-run the skill any
> time to refresh. Free-text notes you write under any item are preserved
> across re-runs.

**Platforms:** Apple App Store, Google Play
**App:** <name> (`<bundle id>`)
**Framework:** Expo SDK X / React Native Y (managed | bare)
**Last audit:** YYYY-MM-DD

## Summary

- ✅ Done: N
- 🟡 In progress: N
- ⬜ Pending: N
- 🚧 Blocked on you: N
- ⚠️ Needs re-check: N

---

## 1. Account & Developer Program
- ✅ [Both] ... <!-- id: shared.account.dev-program -->
- ⬜ [Apple] ... <!-- id: apple.account.tax-banking -->
- 🚧 [Google] ... <!-- id: google.account.tester-gate -->

## 2. App Identity & Versioning
## 3. Build, Signing & EAS Submit
## 4. Store Listing & Metadata
## 5. Privacy & Data Handling
## 6. Permissions & Capabilities
## 7. Compliance & Content
## 8. Quality & Pre-Submission Testing
## 9. Submission & Review Prep
## 10. Post-Launch Monitoring

---

## Notes & history

- YYYY-MM-DD — Initial scaffold (Expo X, RN Y).
- _(future re-runs append entries here)_
```

### Symbol legend

| Symbol | Meaning |
|---|---|
| ✅ | Done (verified by audit) |
| 🟡 | In progress (audit shows partial, or dev marked it) |
| ⬜ | Pending |
| 🚧 | Blocked on you (requires human action the audit can't perform) |
| ⚠️ | Re-check (audit contradicts a prior note or status) |

### Categories (sections 1–10)

1. **Account & Developer Program** — Apple Developer enrollment, Google Play Console account, tax & banking, account holder identity, legal entity (DUNS for orgs on Apple), the 14-day/12-tester gate for new Play accounts.
2. **App Identity & Versioning** — bundle identifier reserved, Android package name registered, version + build number scheme, semantic version policy.
3. **Build, Signing & EAS Submit** — iOS distribution cert + provisioning profile (or EAS-managed), Android keystore + Play App Signing, App Store Connect API key, Google Play service account JSON, `eas.json` production profile configured, `eas submit` config.
4. **Store Listing & Metadata** — app name, subtitle (iOS), short + full description, keywords (iOS), category, age rating, app icon (all required sizes), screenshots (per required device class), preview/promo video, localizations.
5. **Privacy & Data Handling** — privacy policy URL hosted, App Privacy "nutrition labels" filled (iOS), Data Safety form filled (Google), App Tracking Transparency prompt if using IDFA, GDPR/CCPA stance, COPPA/age compliance if applicable.
6. **Permissions & Capabilities** — `NS*UsageDescription` strings for every iOS permission used, Android runtime permissions declared + justified, push notifications (APNs + FCM) wired, deep / universal / app links, Sign in with Apple if third-party auth used (mandatory on iOS), background modes.
7. **Compliance & Content** — export compliance (encryption usage flag), IARC content rating (Google), App Store age rating answers, restricted APIs (background location, accessibility services, etc.), in-app purchase rules (digital goods must use platform IAP), trademark/IP review.
8. **Quality & Pre-Submission Testing** — crash-free session baseline, graceful network failure & offline behavior, accessibility (VoiceOver/TalkBack labels, contrast, touch target sizes), dark mode + dynamic type (iOS), tablet/iPad layout, large-screen/foldable (Android), localization, TestFlight setup, Play internal/closed/open testing track.
9. **Submission & Review Prep** — demo account credentials for reviewer (if app requires login), reviewer notes / demo video, audit against common rejection patterns (login walls, placeholder content, broken links, undocumented features).
10. **Post-Launch Monitoring** — crash reporting (Sentry / Crashlytics) integrated, App Store Connect / Play Console analytics access provisioned, staged/phased rollout plan, OTA-update strategy (`expo-updates` channels + `runtimeVersion` policy).

### Two structural details

- **`> _Dev note (DATE):_` blockquotes** under any item are preserved verbatim across re-runs. They are how the developer adds context without it getting clobbered. The skill never edits these.
- **Notes & history** at the bottom is an append-only log: each re-run appends a single line summarising what changed. It is never rewritten.

## Idempotent re-run behaviour

### Stable item IDs

Every checklist item has a stable ID. IDs follow the convention `<platform>.<section-slug>.<item-slug>`, where:

- `<platform>` is one of `apple`, `google`, or `shared` (cross-platform items).
- `<section-slug>` matches the section the item lives in (e.g., `signing`, `account`, `metadata`).
- `<item-slug>` is a stable lowercase-hyphenated identifier for the specific item.

Examples: `apple.signing.distribution-cert`, `google.account.tester-gate`, `shared.account.dev-program`.

IDs are written into the roadmap as HTML comments next to each item:

```markdown
- ✅ [Both] Developer accounts active. <!-- id: shared.account.dev-program -->
```

HTML comments render invisibly in most markdown viewers; the skill uses them to match audit findings back to existing items on re-run.

### Merge rules

| Existing roadmap state | New audit finding | Resulting state |
|---|---|---|
| Item missing | Audit returns it | Add item, ordered by section |
| Item exists, status unchanged | Same status | Unchanged. Do not rewrite. |
| Item exists, status improved (⬜ → 🟡 → ✅) | Better status from audit | Update status icon. Preserve dev notes. |
| Item exists, status regressed (✅ → ⬜) | Audit no longer sees evidence | Mark ⚠️ Re-check, keep old status in `evidence` line as strikethrough, preserve dev notes. |
| Item exists with dev note that contradicts audit | Audit contradicts | Mark ⚠️ Re-check, append audit finding, keep dev note intact. |
| Item exists, audit returns `not-applicable` | Audit determines item doesn't apply | Move to "Notes & history" as "no longer applicable on YYYY-MM-DD". Don't delete outright. |
| Item missing from new audit (guide updated, item removed) | Item not in current audit guide | Move to "Notes & history" as "removed from audit guide on YYYY-MM-DD". |

### Always preserved across re-runs

- `> _Dev note (DATE):_` blockquotes under any item.
- The "Notes & history" log at the bottom (only appended to).
- The "Platforms" line at the top — unless the developer changes scope at invocation time, in which case the skill prompts before flipping it.

### Always overwritten on re-run

- The `**Last audit:**` timestamp.
- The Summary counts at the top.
- The audit-derived `evidence:` portion of each item.

### Re-run procedure (step 6 of the flow above)

```
6a. Parse existing roadmap → in-memory map of {item_id: ItemState}.
6b. For each new audit finding, look up by id and apply the merge rule.
6c. For each item in the map but NOT in the new findings, apply
    "missing from new audit" rule.
6d. Write the file fresh from template, item by item, in canonical
    section/order, injecting preserved dev notes verbatim.
6e. Append a single line to "Notes & history":
    "YYYY-MM-DD — Re-run. +2 done, +1 pending, 1 re-check flagged."
```

The skill writes the file fresh rather than diff-patching in place — much simpler. Idempotency comes from determinism: same inputs → same output bytes.

### Git-dirty safety check

Before overwriting an existing roadmap, the skill runs `git status --porcelain docs/publishing-roadmap.md`. If the file has uncommitted manual edits outside `Dev note` blockquotes, it pauses and asks:

> "`docs/publishing-roadmap.md` has uncommitted manual edits. The merge rules preserve `> _Dev note_` blockquotes but not freeform edits elsewhere. Commit your edits first, or proceed and risk losing them?"

If the working directory is not a git repo, this check is skipped silently.

## Preconditions

1. **Working directory is an Expo / RN project root.** Detected by `app.json`, `app.config.{js,ts}`, or `package.json` with `expo` or `react-native` in `dependencies`. If none of these exist, refuse:

   > "`chart-publishing-path` is tuned for Expo / React Native projects. I don't see `app.json`, `app.config.*`, or a `package.json` with `expo` / `react-native`. Re-run from your app project root, or invoke `write-a-skill` if you want to adapt this skill for another stack."

2. **`docs/` exists or is creatable.** If not, the skill creates `docs/` (matches existing library behaviour).

3. **Git repo (soft).** If not in a git repo, the git-dirty safety check is skipped silently; otherwise it runs.

## Edge cases

- **Managed-only Expo project (no `ios/` or `android/` dirs).** Audit guides explicitly handle this: if `ios/` is absent, the audit treats `app.json` `ios.infoPlist` / `ios.entitlements` as the source of truth instead of a native `Info.plist`. Same for Android.
- **`app.config.ts` instead of `app.json`.** The subagent reads it as TypeScript source via `Read`. It does not execute the config. If the config heavily uses dynamic values from environment variables, some findings will land as `unknown` and become interview questions.
- **Apple-only or Google-only project.** Q3 (the platforms question) defaults sensibly: if `app.json` has only an `ios` block (no `android`), default to "Apple only" with the question framed as confirmation, not open choice.
- **First run vs. nth run with no roadmap file.** Indistinguishable — both go through scaffold mode.
- **Existing roadmap was generated by an older version of the audit guide.** Items whose IDs no longer appear in the current guide get moved to "Notes & history" per the merge rules. New items from the updated guide get added.
- **Subagent returns malformed JSON.** The orchestrator retries the dispatch once with a tighter prompt that includes the prior malformed output. If still malformed, falls back to interviewing the developer directly with the checklist.
- **Audit guide markdown file is missing or unreadable.** Hard error: "`audits/apple.md` not found in skill bundle. Re-run `install.ps1` / `install.sh` to refresh skills." The audit guide is load-bearing; don't limp along without it.

## Open items

None. All shaping decisions made during brainstorm:

- Lifecycle: idempotent (scaffold + update).
- File layout: single file, sections by concern, items tagged per platform.
- Information gathering: audit-first, interview the gaps; parallel Apple/Google subagents.
- Decomposition: single skill, internal subagents (not decomposed into multiple skills).
- Naming: `chart-publishing-path` under new `skills/release/` stage.
- Output: `docs/publishing-roadmap.md` at project doc root.
- Framework scope: Expo / React Native only.
- Conflict resolution: ⚠️ Re-check flag, audit wins, dev note preserved.

## Next step

Hand off to `superpowers:writing-plans` to produce an implementation plan for the skill (SKILL.md procedure, the two audit guides, the template, the merge logic, and tests).
