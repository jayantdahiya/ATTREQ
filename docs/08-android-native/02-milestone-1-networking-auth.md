# A1 — Networking Core, Types & Auth

> **Milestone file for A1.** Self-contained; read with `00-goal.md`. Node order: `ios-reader → rn-implementer → verifier → screenshot-auditor`.
> **Status:** ✅ COMPLETE — all four nodes passed. `tsc` + Jest **5/5**; **Maestro auth E2E green** (register → login → onboarding gate → home → sign out → re-login vs the live 8001 backend); Login + register wizard render faithfully in light + dark. Dev DB recreated from empty (requester-approved) to clear an inconsistent Alembic state. Maestro asserts post-navigation screens by `testID` (`onboarding-screen`/`home-screen`) — RN Fabric text on those screens wasn't reliably readable by Maestro, though visible.

## Goal (A1 gate)

Register → login → logout work against the local API; 401-refresh unit-tested; Maestro auth flow green; screens match iOS in both themes.

## ios-reader spec (sources)

- Flow: `apps/ios/App/AppSession.swift` (register = register → login → best-effort `PUT /users/me` + `PATCH /users/me/location` → `GET /users/me`; login; logout; bootstrap; routing states loading/loggedOut/authenticated) and `Features/Auth/Register/RegisterViewModel.swift` (3-step validation, 8 style keywords, device-location vs manual city).
- Visual: `assets/design/ios-redesign-v2/attreq-auth.jsx` — Login (divider + ATTREQ wordmark + card) and 3 register artboards with the circular-back StepNav + dot indicators + `NN/NN` counter.
- Contracts: `apps/api` schemas — `POST /auth/register` returns **User only** (no tokens); `POST /auth/login` is form-urlencoded → `{access_token, refresh_token, user}`; password policy 8–72 chars + upper/lower/digit. Backend dev port is **8001** (not 8000).

## rn-implementer — what shipped

- **Logic layer** (ported from `_legacy`, near-verbatim): `lib/api/{client,session,auth,users,errors}.ts`, `lib/query/query-client.ts`, `lib/storage/secure-store.ts` (via `expo-secure-store`), `lib/utils/env.ts` (fixed to port **8001**), `lib/location/location.ts` (`expo-location` permission + reverse-geocode). `store/auth-store.ts` gained `login()` + `register()` orchestration mirroring iOS AppSession.
- **Types:** regenerated `lib/api/types.ts` (auth + user subset) against backend schemas; grown per later milestone.
- **Screens:** `LoginScreen` (artboard 01), `RegisterScreen` (3-step wizard, artboards 02–04, device-location + manual city), `HomePlaceholderScreen` + `OnboardingPlaceholderScreen` (A1 stubs — real tabs/onboarding are A2–A5), all from the design system. `StepNav` upgraded to the canonical auth artboard style.
- **Root gate:** `navigation/RootNavigator.tsx` — loading → auth → onboarding → home, reading the auth store + cached `/users/me`.
- **App wiring:** `QueryClientProvider` + `ThemeProvider` + bootstrap-on-mount.

## Deliberate divergences (A1) — pivoted off Expo (requester-approved)

`expo-modules-core` was abandoned for A1 after **six sequential integration failures** in this bare-RN-0.83 bridgeless monorepo (Gradle version catalog → react-native-screens codegen version conflict → babel-preset-expo/Jest conflict → Metro `.virtual-metro-entry` → entry alignment → opaque bridgeless `MessageQueue` runtime crash). A1 reverted to the **proven A0 baseline** (which built + ran flawlessly):

- **Secure storage → `@react-native-async-storage/async-storage`** (maintained, New-Architecture, no Expo) for the refresh token. **Not encrypted** — acceptable for the dev build; upgrade to hardware-backed storage (e.g. react-native-keychain) before any distribution milestone.
- **Device location deferred** — was `expo-location`; `requestDeviceLocation()` now throws a friendly "enter your city" and the register wizard's **manual-city** path covers A1. A New-Arch community geolocation module lands in a later milestone.
- **JS-only navigation** (a lightweight screen switch) instead of React Navigation: `react-native-screens`' codegen emits `UnionTypeAnnotation` event props this env's RN 0.83 codegen (0.83.4) rejects. React Navigation + native-stack reintroduced once that conflict is resolved. `react-native-screens` + `react-native-gesture-handler` uninstalled.
- **Config reverted to A0:** `@react-native/babel-preset`, `@react-native/metro-config` (monorepo watch/resolve), plain `AppRegistry` entry, non-Expo `MainApplication`/`MainActivity`, A0 `settings.gradle`. Kept explicit AGP `8.12.0` / Kotlin `2.1.20` on the root buildscript + body-level RN-gradle-plugin `includeBuild` (monorepo requirement).
- "Forgot password" is inert (no backend endpoint), matching iOS.

## Verification

- `verifier` static: `tsc --noEmit` → 0; Jest → **5/5** (`component-gallery` ×2, `auth-session` ×3 incl. 401→refresh→retry, refresh-fail→sign-out, login-endpoint-skips-refresh).
- `verifier` build + Maestro: native `installDebug` on `emulator-5554`; `.maestro/auth-flow.yaml` (register → onboarding → home → sign out → re-login) against the 8001 backend. **(completing)**
- `screenshot-auditor`: Login + register wizard in light + dark vs `attreq-auth.jsx`. **(completing)**
