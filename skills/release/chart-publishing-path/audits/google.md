# Google Play Audit Guide (Expo / React Native)

You are auditing an Expo / React Native app for Google Play publishing readiness. Your output is a JSON-in-fenced-block of findings (schema in the dispatching skill prompt).

## What to read

Glob first, then `Read` for contents.

- `app.json` and/or `app.config.{js,ts}` — Expo configuration (REQUIRED)
- `eas.json` — EAS Build / Submit configuration (REQUIRED if present)
- `package.json` — dependency manifest
- `android/app/build.gradle` — native module-level gradle (only if `android/` exists)
- `android/app/src/main/AndroidManifest.xml` — native manifest (only if `android/` exists)
- `android/gradle.properties` — Android build properties (only if `android/` exists)
- Any `privacy-policy*` files at repo root

## How to interpret the Expo workflow

- **Managed workflow** (`android/` absent): `AndroidManifest.xml` is generated from `app.json` `android.permissions` + plugins at prebuild time.
- **Bare workflow** (`android/` present): native files are authoritative.
- Detect framework as `expo-managed`, `expo-bare`, or `bare-react-native` (same rules as Apple guide).

## Checklist

### shared.account.dev-program
- **Section:** 1. Account & Developer Program
- **Title:** Google Play Console account active (cross-platform — share ID with Apple guide)
- **Done if:** `eas.json` references a Google service account JSON path (`submit.production.android.serviceAccountKeyPath`) AND the file path is set (existence not always verifiable).
- **Pending if:** no service account reference.
- **Blocked default:** if no evidence either way.
- **Interview question:** "Is your Google Play Console account active and verified ($25 one-time fee paid, identity verified)?"

### google.account.tester-gate
- **Section:** 1. Account & Developer Program
- **Title:** 14-day / 12-tester closed testing gate (new Play accounts only)
- **Blocked default:** always `blocked`.
- **Interview question:** "Is your Play Console account new (registered after Nov 2023)? If yes, you must run a closed test with ≥12 testers for ≥14 days before promoting to production."

### google.account.tax-banking
- **Section:** 1. Account & Developer Program
- **Title:** Google Play merchant / tax & banking info
- **Blocked default:** always `blocked`.
- **Interview question:** "Have you set up a Google Play merchant account and added banking + tax info? (Required for paid apps or in-app purchases.)"

### google.identity.package-name
- **Section:** 2. App Identity & Versioning
- **Title:** Android package name set
- **Done if:** `app.json` `android.package` is set to a reverse-DNS string AND does not contain placeholder substrings (`example`, `acme`, `your-domain`).
- **Partial if:** placeholder substring present.
- **Pending if:** missing.

### google.identity.versioning
- **Section:** 2. App Identity & Versioning
- **Title:** Version + versionCode scheme
- **Done if:** `app.json` has both `version` AND `android.versionCode` (integer); OR EAS auto-increment configured.
- **Partial if:** version present but versionCode missing.
- **Pending if:** neither.
- **Interview question (if unknown):** "How are you bumping Android `versionCode` between submissions — manually, or via EAS auto-increment?"

### google.signing.keystore
- **Section:** 3. Build, Signing & EAS Submit
- **Title:** Android signing keystore
- **Done if:** `eas.json` has a `production` profile AND credentials are configured for Android (either EAS-managed or `gradle.properties` keystore references).
- **Pending if:** no `production` profile in `eas.json`.
- **Blocked default:** if EAS-managed and not directly verifiable.
- **Interview question (if unknown or blocked):** "Have you generated an Android signing keystore (via `eas credentials` or manually) and enrolled in Play App Signing?"

### google.signing.play-app-signing
- **Section:** 3. Build, Signing & EAS Submit
- **Title:** Play App Signing enrolled
- **Blocked default:** always `blocked`.
- **Interview question:** "Have you enrolled the app in Play App Signing in Play Console? (Mandatory for new apps since Aug 2021.)"

### google.signing.service-account
- **Section:** 3. Build, Signing & EAS Submit
- **Title:** Google Play service account JSON for `eas submit`
- **Done if:** `eas.json` `submit.production.android.serviceAccountKeyPath` is set AND points to a non-placeholder filename.
- **Pending if:** key not configured.
- **Interview question (if unknown):** "Have you created a Google Play service account JSON with the right scopes (publish releases) and provided its path to `eas submit`?"

### google.metadata.app-icon
- **Section:** 4. Store Listing & Metadata
- **Title:** App icon + adaptive icon
- **Done if:** `app.json` `icon` exists AND `app.json` `android.adaptiveIcon.foregroundImage` exists AND both files exist.
- **Partial if:** one but not the other.
- **Pending if:** neither.

### google.metadata.feature-graphic
- **Section:** 4. Store Listing & Metadata
- **Title:** Feature graphic (1024×500 PNG/JPG)
- **Blocked default:** always `blocked` (uploaded directly to Play Console, not the repo).
- **Interview question:** "Is your Play Store feature graphic (1024×500) prepared?"

### google.metadata.screenshots
- **Section:** 4. Store Listing & Metadata
- **Title:** Phone + tablet screenshots
- **Blocked default:** always `blocked`.
- **Interview question:** "Do you have phone screenshots (≥2 required) and tablet screenshots (7" and 10" recommended if you support tablets) prepared?"

### google.metadata.copy
- **Section:** 4. Store Listing & Metadata
- **Title:** Play Store listing copy (title ≤30 chars, short ≤80, full ≤4000)
- **Blocked default:** always `blocked`.
- **Interview question:** "Is your Play Store listing copy drafted (title ≤30 chars, short description ≤80 chars, full description ≤4000 chars, category chosen)?"

### google.privacy.policy-url
- **Section:** 5. Privacy & Data Handling
- **Title:** Privacy policy URL (cross-platform — share ID `shared.privacy.policy-url` if also using Apple)
- **Done if:** privacy policy URL referenced in repo and well-formed (HTTPS, no placeholder).
- **Pending if:** none detected.
- **Interview question (if unknown):** "What is your privacy policy URL?"

### google.privacy.data-safety
- **Section:** 5. Privacy & Data Handling
- **Title:** Data Safety form filled in Play Console
- **Blocked default:** always `blocked`.
- **Interview question:** "Have you filled out the Data Safety form in Play Console (what data your app collects, how it's used, encryption in transit)?"

### google.permissions.declared
- **Section:** 6. Permissions & Capabilities
- **Title:** Android permissions declared and justified
- **Done if:** for every Expo permission plugin in `package.json`, the corresponding Android permission is in `app.json` `android.permissions` array (or generated by the plugin).
- **Partial if:** some declared, others missing.
- **Pending if:** plugins detected but no `android.permissions` configured.

### google.permissions.sensitive
- **Section:** 6. Permissions & Capabilities
- **Title:** Sensitive permissions (foreground service, background location, accessibility, SMS, call log) have declared use cases
- **Done if:** no sensitive permissions detected in `app.json` `android.permissions`.
- **Blocked if:** sensitive permission detected (`ACCESS_BACKGROUND_LOCATION`, `BIND_ACCESSIBILITY_SERVICE`, `READ_SMS`, `READ_CALL_LOG`, `FOREGROUND_SERVICE_*`, `MANAGE_EXTERNAL_STORAGE`, `QUERY_ALL_PACKAGES`).
- **Interview question (if blocked):** "Your app declares sensitive permission(s). Have you prepared the use-case justification + demo video required by Play Console for these permissions?"

### google.permissions.push-notifications
- **Section:** 6. Permissions & Capabilities
- **Title:** Push notifications wired (FCM)
- **Done if:** `expo-notifications` in dependencies AND `google-services.json` file present at the expected path AND `app.json` `android.googleServicesFile` references it.
- **Partial if:** plugin present but `google-services.json` missing.
- **Not-applicable if:** no `expo-notifications` dependency.
- **Interview question (if blocked):** "Have you created a Firebase project and downloaded `google-services.json`?"

### google.permissions.deep-links
- **Section:** 6. Permissions & Capabilities
- **Title:** App Links configured
- **Done if:** `app.json` `android.intentFilters` includes an `autoVerify: true` filter for the app's domain AND the domain has an `assetlinks.json` file (not verifiable by audit — flag for human check).
- **Pending if:** deep-linking dependency present but no intent filters.
- **Not-applicable if:** no deep-linking dependency.

### google.compliance.target-sdk
- **Section:** 7. Compliance & Content
- **Title:** Target SDK version meets Play Store policy
- **Done if:** `app.json` `android.compileSdkVersion` and/or `targetSdkVersion` (or Expo SDK default) is ≥34 (Android 14, current floor for new apps as of 2025).
- **Partial if:** present but below the current Play Store floor.
- **Pending if:** unable to determine from configuration.
- **Interview question (if unknown):** "What Expo SDK version are you on? (Affects the default `targetSdkVersion` Expo prebuild uses.)"

### google.compliance.content-rating
- **Section:** 7. Compliance & Content
- **Title:** IARC content rating questionnaire
- **Blocked default:** always `blocked`.
- **Interview question:** "Have you completed the IARC content rating questionnaire in Play Console?"

### google.quality.accessibility
- **Section:** 8. Quality & Pre-Submission Testing
- **Title:** Accessibility pass (TalkBack, contrast, touch targets)
- **Done if:** never derivable conclusively. Audit reports `accessibilityLabel` coverage as a hint.
- **Blocked default:** flag for human review.
- **Interview question:** "Have you done a TalkBack pass on your app's main flows? Touch targets ≥48dp, contrast meets WCAG AA?"

### google.quality.large-screen
- **Section:** 8. Quality & Pre-Submission Testing
- **Title:** Large-screen / foldable support
- **Done if:** `app.json` `android.resizeableActivity: true` AND no `screenOrientation: portrait` lock.
- **Partial if:** resizeable but portrait-locked.
- **Pending if:** orientation-locked or no large-screen config.

### google.quality.testing-track
- **Section:** 8. Quality & Pre-Submission Testing
- **Title:** Closed/open testing track exercised before production
- **Blocked default:** always `blocked`.
- **Interview question:** "Have you run the build through Play Console's internal or closed testing track before promoting to production?"

### google.submission.reviewer-credentials
- **Section:** 9. Submission & Review Prep
- **Title:** Demo account credentials for Play Review
- **Blocked default:** `blocked` if any auth dependency detected; `not-applicable` if no auth.
- **Interview question:** "Does your app require login? If yes, do you have demo credentials for the Play Review team?"

### google.postlaunch.crash-reporting
- **Section:** 10. Post-Launch Monitoring
- **Title:** Crash reporting integrated (cross-platform; share ID with Apple)
- **Done if:** crash reporter SDK in `package.json` AND initialized in app entry.
- **Partial if:** installed but not initialized.
- **Pending if:** no crash reporter.

### google.postlaunch.staged-rollout
- **Section:** 10. Post-Launch Monitoring
- **Title:** Staged rollout plan
- **Blocked default:** always `blocked`.
- **Interview question:** "Will you use Play Console's staged rollout (% rollout) for the production launch?"

### google.postlaunch.ota-strategy
- **Section:** 10. Post-Launch Monitoring
- **Title:** OTA update strategy (cross-platform — same as Apple)
- **Done if:** `expo-updates` in dependencies AND `runtimeVersion` set AND update channels configured.
- **Partial if:** installed but not configured.
- **Not-applicable if:** no `expo-updates`.
- **Interview question (if unknown):** "Are you using EAS Update? What's your `runtimeVersion` policy?"
