# Milestone 5 — Distribution & Beta Launch

> **Goal:** A repeatable path from `main` to testers' phones: EAS builds, TestFlight + Google Play internal track, mobile crash reporting in Sentry, and a beta go/no-go process. Closes **TKT-009** (release & distribution baseline).
> **Depends on:** Milestone 4 (first tester build ships instrumented and test-covered). **Store paperwork should already be done** — Apple Developer enrollment and Play Console setup were kicked off during Milestone 1 (Play needs a 12-tester/14-day closed-testing soak before production access).
> **Status:** Not started

## Context (self-contained)

- Mobile app: Expo SDK 55 / React Native at `apps/mobile/` in an npm-workspaces monorepo. Config in `apps/mobile/app.json`. **No `eas.json` exists; no EAS `projectId` in `app.json`; `expo-dev-client` is not installed; no Sentry SDK in `apps/mobile/package.json`** (verified 2026-06-10).
- Backend Sentry already works (`SENTRY_DSN` in `apps/api`); mobile has zero crash reporting.
- Production API is live at `https://api.<domain>` (M1). Mobile reads the backend URL from `EXPO_PUBLIC_API_URL`.
- Manual smoke checklist exists from M4 (run it on both platforms before inviting testers).
- Mobile CI (`.github/workflows/mobile-ci.yml`): typecheck + jest. EAS builds are run manually via CLI, not CI (fine for solo dev).

## Decisions (pre-made)

- **Sentry lands first** (5.1 before any build) so the very first tester install reports crashes.
- **Three EAS profiles**: `development` (dev client, LAN API), `preview` (internal distribution, prod API — this is the tester build), `production` (store builds, auto-increment). Secrets/env via **EAS environment variables per profile**, not committed.
- Builds and submits run **manually via `eas` CLI** for now; CI-driven builds are post-launch work.

## Tasks

### 5.1 Mobile Sentry

1. `cd apps/mobile && npx expo install @sentry/react-native`.
2. Initialize in the root layout (`apps/mobile/app/_layout.tsx`): `Sentry.init({ dsn: process.env.EXPO_PUBLIC_SENTRY_DSN, enabled: !__DEV__ })` and wrap the root component per `@sentry/react-native` Expo docs; add the `@sentry/react-native/expo` plugin entry to `app.json` (org/project slugs).
3. Create a separate Sentry project for mobile (don't reuse the backend DSN); set `EXPO_PUBLIC_SENTRY_DSN` as an EAS env var on `preview` and `production` profiles only.
4. Source maps: configure the Sentry Expo plugin's upload (`SENTRY_AUTH_TOKEN` as EAS secret) so release builds symbolicate.

### 5.2 EAS setup

1. `cd apps/mobile && eas init` — links the project, writes `extra.eas.projectId` into `app.json`. Confirm `ios.bundleIdentifier` / `android.package` in `app.json` match what was registered in App Store Connect / Play Console (created during M1).
2. `npx expo install expo-dev-client` (needed for the `development` profile).
3. **New** `apps/mobile/eas.json`:

   ```jsonc
   {
     "cli": { "appVersionSource": "remote" },
     "build": {
       "development": {
         "developmentClient": true,
         "distribution": "internal",
         "env": { "EXPO_PUBLIC_API_URL": "http://<LAN-IP>:8000/api/v1" }
       },
       "preview": {
         "distribution": "internal",
         "env": { "EXPO_PUBLIC_API_URL": "https://api.<domain>/api/v1" }
       },
       "production": {
         "autoIncrement": true,
         "env": { "EXPO_PUBLIC_API_URL": "https://api.<domain>/api/v1" }
       }
     },
     "submit": { "production": {} }
   }
   ```

   (Sentry DSN + auth token via EAS env vars/secrets, not in this file.)
4. **Monorepo caveat**: the app lives in an npm workspace — verify EAS builds resolve dependencies from the workspace root (Metro config at `apps/mobile/metro.config.js` already handles dev; confirm the EAS build log installs at the repo root, and add `"build": { "...": { "node": ... } }`/`pnpm-style` workarounds only if the first build fails).
5. First builds: `eas build --profile preview --platform ios` and `--platform android`; install the Android `.apk`/internal build on a real device and run the M4 smoke checklist.

### 5.3 Store plumbing + release doc

1. **iOS**: App Store Connect app for the bundle ID → TestFlight → internal testing group (no review needed for internal) → `eas submit --profile production --platform ios` (or upload the preview build) → invite testers by email.
2. **Android**: Play Console → internal testing track → `eas submit --platform android` → tester email list / opt-in link. (The 12-tester/14-day closed-test soak for *production* access should already be running from M1 — internal track has no such gate.)
3. **New** `docs/mobile-release.md`: the full release runbook — profile/env matrix (which profile, which API URL, which Sentry project), build commands, submit commands, tester invite flow for both stores, versioning policy (`appVersionSource: remote`, autoIncrement on production), and the M4 smoke checklist as the pre-invite gate.

### 5.4 Beta launch

1. Seed **5–10 testers** across iOS and Android (mix of phone sizes/OS versions).
2. Before each invite wave: run the 10-step smoke checklist (M4) on both platforms against prod.
3. **Sentry release tagging**: confirm builds report the EAS build number/release so crashes map to builds.
4. Feedback channel: a single place (WhatsApp/Telegram group or Google Form) linked from the TestFlight/Play "What to test" notes.
5. **Go/no-go for widening the beta**: no P0 (crash-on-launch, data-loss, auth-lockout) Sentry issues across 48 h of tester use; smoke checklist passes on both platforms.

## Out of scope

- Public App Store / Play production release (separate decision after beta). CI-driven EAS builds. OTA updates (`expo-updates`) policy. Push-notification server infrastructure changes. Marketing/landing-page work.

## Exit criteria

- A **non-developer** installs from TestFlight (iOS) and Play internal track (Android), completes onboarding → Style DNA → upload → daily recommendation against the prod backend.
- A forced crash in a `preview` build appears in Sentry attributed to the correct release.
- `docs/mobile-release.md` exists; a second build/submit cycle takes < 1 hour of hands-on time following it.

## Verification

```bash
cd apps/mobile
npm run typecheck && npm test
eas build --profile preview --platform all      # both builds succeed
eas submit --platform ios                        # lands in TestFlight internal group
eas submit --platform android                    # lands in Play internal track
```

- Fresh tester account (not the developer's) completes the full smoke checklist from a store-distributed install on each platform.
- Trigger a deliberate crash (hidden dev gesture or test button in preview builds) → event in Sentry with correct release + sourcemapped stack.
- Pull a fresh clone, follow only `docs/mobile-release.md` → produces a submittable build.
