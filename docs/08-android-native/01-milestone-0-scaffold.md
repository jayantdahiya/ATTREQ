# A0 — Scaffold & Design System

> **Milestone file for A0.** Self-contained; read with `00-goal.md`. Graph node order: `ios-reader → rn-implementer → verifier → screenshot-auditor`.
> **Status:** ✅ COMPLETE — all four nodes passed. Gallery renders every design-system piece in light + dark on `emulator-5554`; `tsc --noEmit` + Jest green; app boots (`Running "ATTREQ" … fabric:true`). One screenshot-auditor finding (status-bar overlap) fixed via top safe-area inset, then re-audited clean.

## Goal (A0 gate)

Component gallery screen renders every design-system piece in both themes on an Android emulator; `tsc --noEmit` + Jest green; app boots.

## Toolchain provisioned (local)

Zulu JDK 17, Android SDK Platform 35, Build-Tools 36.0.0, AVD `attreq_pixel` (Google APIs arm64-v8a) on `emulator-5554`, Maestro 2.7, watchman. Env is **not** inherited by non-login shells — source `scratchpad/android-env.sh` (`JAVA_HOME`, `ANDROID_HOME`, PATH) in build/emulator commands.

## ios-reader spec (sources)

- Tokens: `assets/design/ios-redesign-v2/attreq-shared.jsx` (`ATTREQ_C` / `ATTREQ_DARK_C`), cross-checked against `apps/ios/DesignSystem/Theme/Theme.swift`.
- Typography: `apps/ios/DesignSystem/Theme/Typography.swift` — Cormorant Garamond (Regular/Medium/SemiBold + italics), DM Sans (Light/Regular/Medium/SemiBold), IBM Plex Mono (Regular/Medium).
- Gallery layout mirrors `apps/ios/DesignSystem/Gallery/ComponentGalleryView.swift` (header + 9 sections + floating tab bar).

## rn-implementer — what shipped

- **Scaffold-in-place:** bare RN 0.83.4 (React 19.2, New Architecture + Hermes) replaced the Expo scaffold in `apps/mobile/`. Old Expo UI + logic quarantined to `apps/mobile/_legacy/` (port source for A1). `applicationId = com.attreq.mobile` (namespace `com.attreq`).
- **Config:** `babel.config.js` (module-resolver `@/`→`src`, `react-native-worklets/plugin` last), `metro.config.js`, `tsconfig.json` (`extends @react-native/typescript-config`, `@/*` paths, excludes `_legacy`), `jest.config.js` (preset `react-native`, ignores `_legacy`), `jest.setup.ts` (safe-area-context stub), `app.json`, `react-native.config.js` (fonts).
- **Monorepo Gradle fix:** `apps/mobile` is an npm **workspace** → RN deps hoist to repo-root `node_modules`. `settings.gradle` + `app/build.gradle` resolve `@react-native/gradle-plugin`, `react-native`, `@react-native/codegen` via `node require.resolve` instead of fixed `../node_modules` paths.
- **Design system** (`src/design-system/`): `theme/theme.ts` (light+dark tokens, garment gradients, card shadow, tab-bar surface), `theme/ThemeProvider.tsx` (`useColorScheme`-driven, `forceScheme` override), `theme/typography.ts` (`display`/`body`/`mono`). Components: `MonoLabel`, `BodyText`, `Card`, `Chip`, `Pill`, `PrimaryButton`, `UnderlineInput`, `GarmentPlaceholder` (svg gradient — no expo-linear-gradient at A0), `TabBar` (floating pill), `StepNav`. `icons/AttreqIcon.tsx` — all 16 feather icons in `react-native-svg`. `gallery/ComponentGallery.tsx` — 9 sections + tab bar overlay.
- **Fonts:** 12 static OFL `.ttf`s (from `@expo-google-fonts` static instances since google/fonts serves variable fonts) in `assets/fonts/`, linked into Android via `npx react-native-asset`.
- **CI:** `.github/workflows/mobile-ci.yml` updated for bare RN — JS job (`tsc --noEmit` + Jest) + Android `assembleDebug` job (JDK 17 + setup-android).

## Deliberate divergences (Android)

- Floating tab bar uses a **semi-opaque surface**, not a live blur (no cheap system-wide blur on Android) — approximation, per goal doc.
- `expo-modules-core` + Expo native modules deferred to the point of first use (A1); A0's gallery needs only `react-native` + `react-native-svg` + `react-native-safe-area-context`.

## Verification

- `verifier` static: `tsc --noEmit` → exit 0; Jest → `src/test/component-gallery.test.tsx` 2/2 pass (light + dark render).
- `verifier` build + `screenshot-auditor`: Android `installDebug` on `emulator-5554`, launch, capture light + dark, compare to iOS gallery reference. **(completing)**
