# Apple App Store Audit Guide (Expo / React Native)

You are auditing an Expo / React Native app for Apple App Store publishing readiness. Your output is a JSON-in-fenced-block of findings (schema in the dispatching skill prompt).

## What to read

Glob first to confirm what exists, then `Read` for contents.

- `app.json` and/or `app.config.{js,ts}` — Expo configuration (REQUIRED to read)
- `eas.json` — EAS Build / Submit configuration (REQUIRED if present)
- `package.json` — dependency manifest (look for plugins that imply permissions: `expo-camera`, `expo-location`, `expo-notifications`, etc.)
- `ios/<App>/Info.plist` — native plist, only if `ios/` exists (bare workflow)
- `ios/<App>.xcodeproj/project.pbxproj` — native project, only if `ios/` exists
- Any `privacy-policy*` files at repo root (for evidence of hosted privacy policy)

## How to interpret the Expo workflow

- **Managed workflow** (`ios/` absent): `Info.plist` is generated from `app.json` `ios.infoPlist` at prebuild time. Native capabilities (Sign in with Apple, Push, etc.) declared via plugins in `app.json` `plugins`.
- **Bare workflow** (`ios/` present): native files are authoritative. `app.json` may or may not be in sync — when in doubt, prefer the native source for `Info.plist` keys.
- Detect framework as `expo-managed` (Expo dep present, no `ios/`), `expo-bare` (Expo dep present, `ios/` present), or `bare-react-native` (no Expo dep, `ios/` present).

## Checklist

### shared.account.dev-program
- **Section:** 1. Account & Developer Program
- **Title:** Apple Developer Program enrollment active
- **Done if:** `eas.json` references an Apple team ID (e.g., `submit.production.ios.appleTeamId`) AND the team ID format looks valid (10-char alphanumeric).
- **Pending if:** no team ID anywhere in the project.
- **Blocked default:** if no evidence either way, treat as `blocked` — only the developer can confirm enrollment status.
- **Interview question (if unknown or blocked):** "Is your Apple Developer Program membership active (paid and current)? Your team ID, if you know it?"

### apple.account.tax-banking
- **Section:** 1. Account & Developer Program
- **Title:** Tax & banking info in App Store Connect
- **Done if:** never derivable from code alone.
- **Blocked default:** always `blocked`.
- **Interview question:** "Have you completed Tax & Banking in App Store Connect → Agreements? (Required before any paid app or in-app purchase revenue.)"

### apple.identity.bundle-id
- **Section:** 2. App Identity & Versioning
- **Title:** iOS bundle identifier set
- **Done if:** `app.json` `ios.bundleIdentifier` is set to a reverse-DNS string (e.g., `com.acme.app`), OR (bare workflow) the Xcode project's PRODUCT_BUNDLE_IDENTIFIER is set.
- **Partial if:** value present but contains placeholder substrings like `example`, `acme`, `your-domain`.
- **Pending if:** missing entirely.

### apple.identity.versioning
- **Section:** 2. App Identity & Versioning
- **Title:** Version + build number scheme
- **Done if:** `app.json` has both `version` (semver) AND `ios.buildNumber` (integer or build-stamp); OR EAS auto-increment is configured in `eas.json` (e.g., `build.production.autoIncrement: true`).
- **Partial if:** version present but build number missing.
- **Pending if:** neither present.
- **Interview question (if unknown):** "How are you bumping iOS build numbers between submissions — manually in `app.json`, or via EAS auto-increment?"

### apple.signing.distribution-cert
- **Section:** 3. Build, Signing & EAS Submit
- **Title:** iOS distribution certificate available
- **Done if:** `eas.json` has a `production` profile with `distribution: "store"` AND credentials are resolved (running `eas credentials` would show a cert exists — the audit can't verify this directly, only that the configuration is set up for it).
- **Pending if:** no `production` profile in `eas.json`, or `distribution` is not set to `"store"`.
- **Blocked default:** if `eas.json` looks correct but the audit can't see EAS-managed credentials.
- **Interview question (if unknown or blocked):** "Have you generated an iOS distribution certificate (via `eas credentials` or manually in App Store Connect)?"

### apple.signing.provisioning-profile
- **Section:** 3. Build, Signing & EAS Submit
- **Title:** iOS App Store provisioning profile
- **Done if:** same evidence as distribution cert — `eas.json` production profile with `distribution: "store"`.
- **Blocked default:** if EAS-managed credentials are likely but not verifiable.
- **Interview question:** "Is the iOS App Store provisioning profile generated and linked to your bundle ID?"

### apple.signing.asc-api-key
- **Section:** 3. Build, Signing & EAS Submit
- **Title:** App Store Connect API key configured
- **Done if:** `eas.json` `submit.production.ios` has `ascApiKeyPath` set OR EAS-managed key is referenced.
- **Pending if:** `submit.production.ios` is missing or has no API key reference.
- **Interview question (if unknown):** "Have you uploaded an App Store Connect API key for `eas submit` to use?"

### apple.metadata.app-icon
- **Section:** 4. Store Listing & Metadata
- **Title:** App icon (1024×1024 PNG, no transparency)
- **Done if:** `app.json` `icon` field points to a file that exists in the repo. (The audit confirms existence but not dimensions; flag for visual inspection.)
- **Partial if:** `icon` field set but file does not exist.
- **Pending if:** no `icon` field.

### apple.metadata.screenshots
- **Section:** 4. Store Listing & Metadata
- **Title:** App Store screenshots (6.7", 6.5", 5.5" iPhone)
- **Done if:** never derivable from code (screenshots live in App Store Connect, not the repo).
- **Blocked default:** always `blocked`.
- **Interview question:** "Do you have App Store screenshots for the required device sizes (6.7", 6.5", 5.5" iPhone — and iPad if you support tablet)?"

### apple.metadata.copy
- **Section:** 4. Store Listing & Metadata
- **Title:** App Store listing copy (name, subtitle, description, keywords, category)
- **Blocked default:** always `blocked`.
- **Interview question:** "Is your App Store listing copy (app name, subtitle, description, keywords, category) drafted?"

### apple.privacy.policy-url
- **Section:** 5. Privacy & Data Handling
- **Title:** Privacy policy URL hosted
- **Done if:** a privacy policy URL is referenced anywhere in repo (`app.json`, `app.config.*`, README.md) AND the URL is well-formed (https, not a placeholder).
- **Pending if:** no privacy policy URL detected anywhere.
- **Interview question (if unknown):** "What is your privacy policy URL? It must be a stable HTTPS URL accessible without login."

### apple.privacy.nutrition-labels
- **Section:** 5. Privacy & Data Handling
- **Title:** App Privacy "nutrition labels" filled in App Store Connect
- **Blocked default:** always `blocked`.
- **Interview question:** "Have you filled out the App Privacy section in App Store Connect (which data your app collects, links to identity, used for tracking)?"

### apple.privacy.att-prompt
- **Section:** 5. Privacy & Data Handling
- **Title:** App Tracking Transparency prompt (if IDFA used)
- **Done if:** ATT-related dependency or plugin is present (`expo-tracking-transparency`, native ATT code in `ios/`) AND `NSUserTrackingUsageDescription` is set in `app.json` `ios.infoPlist`.
- **Partial if:** ATT dependency present but no usage description, or usage description present but no plugin.
- **Pending if:** uses ad/analytics SDK that may use IDFA (`react-native-firebase` with analytics, AppsFlyer, Adjust, Branch) but no ATT setup detected.
- **Not-applicable if:** no IDFA-consuming SDK detected.
- **Interview question (if unknown):** "Does your app use the advertising identifier (IDFA) for tracking, analytics, or attribution? If yes, is the ATT prompt wired up?"

### apple.permissions.usage-descriptions
- **Section:** 6. Permissions & Capabilities
- **Title:** iOS usage descriptions for every requested permission
- **Done if:** for every Expo permission plugin in `package.json` (e.g., `expo-camera`, `expo-location`, `expo-media-library`, `expo-contacts`, `expo-microphone`, `expo-notifications` with iOS specifics), the corresponding `NS*UsageDescription` is set in `app.json` `ios.infoPlist`. List every match and every gap.
- **Partial if:** some descriptions set, others missing.
- **Pending if:** permission plugins detected but no usage descriptions found.

### apple.permissions.push-notifications
- **Section:** 6. Permissions & Capabilities
- **Title:** Push notifications wired (APNs)
- **Done if:** `expo-notifications` plugin in `app.json` `plugins` AND `app.json` `ios.entitlements` has `aps-environment` OR Expo manages this automatically via the plugin.
- **Pending if:** `expo-notifications` installed but no plugin registration.
- **Not-applicable if:** no `expo-notifications` dependency.
- **Interview question (if blocked):** "Have you uploaded an APNs key or .p8 to EAS / App Store Connect?"

### apple.permissions.deep-links
- **Section:** 6. Permissions & Capabilities
- **Title:** Universal links / deep links configured
- **Done if:** `app.json` `ios.associatedDomains` is set AND the domain has an `apple-app-site-association` file (not verifiable by the audit — flag for human check).
- **Pending if:** deep linking SDK present (`expo-router`, `react-native-deep-linking`) but no `associatedDomains` configured.
- **Not-applicable if:** no deep-linking dependency detected.

### apple.permissions.sign-in-with-apple
- **Section:** 6. Permissions & Capabilities
- **Title:** Sign in with Apple (if third-party auth used)
- **Done if:** `expo-apple-authentication` in dependencies AND third-party auth SDK detected.
- **Pending if:** third-party auth SDK detected (`@react-native-google-signin/google-signin`, `react-native-fbsdk-next`, Firebase Auth with social providers) but no Sign in with Apple.
- **Not-applicable if:** no third-party social login detected.
- **Interview question (if unknown):** "Are you using any third-party social login (Google, Facebook, etc.)? If yes, Apple requires Sign in with Apple as an option."

### apple.compliance.export-encryption
- **Section:** 7. Compliance & Content
- **Title:** Export compliance encryption flag
- **Done if:** `app.json` `ios.infoPlist.ITSAppUsesNonExemptEncryption` is set to a boolean.
- **Pending if:** key absent.
- **Interview question (if unknown):** "Does your app use any non-standard encryption? (If you only use HTTPS / standard iOS crypto APIs, set `ITSAppUsesNonExemptEncryption: false`.)"

### apple.compliance.age-rating
- **Section:** 7. Compliance & Content
- **Title:** App Store age rating questionnaire
- **Blocked default:** always `blocked`.
- **Interview question:** "Have you completed the App Store age rating questionnaire in App Store Connect?"

### apple.quality.accessibility
- **Section:** 8. Quality & Pre-Submission Testing
- **Title:** Accessibility pass (VoiceOver, contrast, touch targets)
- **Done if:** never derivable conclusively. Audit can grep for `accessibilityLabel`, `accessibilityRole`, `accessibilityHint` usage in `app/`, `src/`, or `components/` and report coverage as a hint.
- **Pending if:** no `accessibility*` props found in the JSX/TSX source.
- **Blocked default:** flag for human review regardless of code evidence.
- **Interview question:** "Have you done a VoiceOver pass on your app's main flows? Touch targets ≥44pt, text scales with Dynamic Type, contrast meets WCAG AA?"

### apple.quality.testflight
- **Section:** 8. Quality & Pre-Submission Testing
- **Title:** TestFlight setup
- **Blocked default:** always `blocked`.
- **Interview question:** "Have you set up an internal TestFlight group and tested at least one build through it?"

### apple.submission.reviewer-credentials
- **Section:** 9. Submission & Review Prep
- **Title:** Demo account credentials for App Review
- **Done if:** never derivable from code.
- **Blocked default:** `blocked` if any auth dependency is detected (`expo-auth-session`, `firebase/auth`, `next-auth`, any login screen detected); `not-applicable` if no auth.
- **Interview question:** "Does your app require login? If yes, do you have demo account credentials ready to provide to App Review?"

### apple.submission.reviewer-notes
- **Section:** 9. Submission & Review Prep
- **Title:** Reviewer notes / demo video
- **Blocked default:** always `blocked`.
- **Interview question:** "Are reviewer notes drafted (what the app does, how to demo it, anything non-obvious to a reviewer)?"

### apple.postlaunch.crash-reporting
- **Section:** 10. Post-Launch Monitoring
- **Title:** Crash reporting integrated
- **Done if:** Sentry, Bugsnag, Firebase Crashlytics, or similar SDK detected in `package.json` AND initialized in app entry (e.g., `app/_layout.tsx`, `App.tsx`).
- **Partial if:** SDK installed but no initialization detected.
- **Pending if:** no crash reporter detected.

### apple.postlaunch.phased-release
- **Section:** 10. Post-Launch Monitoring
- **Title:** Phased release plan
- **Blocked default:** always `blocked`.
- **Interview question:** "Will you use App Store Connect's phased release (7-day staged rollout) for the production launch?"

### apple.postlaunch.ota-strategy
- **Section:** 10. Post-Launch Monitoring
- **Title:** OTA update strategy (`expo-updates`)
- **Done if:** `expo-updates` in dependencies AND `app.json` has `runtimeVersion` set AND `updates.url` is configured (or `eas update` channels are referenced in `eas.json`).
- **Partial if:** `expo-updates` installed but `runtimeVersion` not set.
- **Not-applicable if:** no `expo-updates` dependency.
- **Interview question (if unknown):** "Are you using EAS Update? If yes, what's your `runtimeVersion` policy (sdkVersion, appVersion, or custom)?"
