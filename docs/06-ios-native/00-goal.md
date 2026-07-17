# Native iOS App (Swift) — Goal & Execution Plan

> **Status:** ✅ COMPLETE (M0–M5 shipped, 2026-07-15 → 2026-07-17). Native SwiftUI app on branch `ios-native` at `apps/ios/`. See the completion summary at the bottom of this file.
> **Audience:** Any LLM or developer executing a milestone. Read this file + the single milestone file you are executing. Milestone files (`01-…` onward) are written when a milestone starts and must be self-contained.
> **Relationship to other docs:** This is a separate track from the beta-launch roadmap in `docs/05-roadmap/` (which targets the React Native client). Nothing here modifies `apps/mobile/` or the backend.

## Goal

Build a **fully native iOS app in Swift** that delivers all features of the existing ATTREQ mobile app (`apps/mobile/`, Expo + React Native) against the same FastAPI backend — but with the **new visual design from the Redesign v2 handoff** (`assets/design/ios-redesign-v2/`), implemented pixel-faithfully in both **light and dark themes**.

**Done means:** a user can pick up the native app and complete every flow the RN app supports today — register (3-step), login, complete Style DNA onboarding, browse and upload wardrobe items, get daily weather-aware outfit recommendations, log worn outfits, view history, manage their profile — and every screen matches the Redesign v2 artboards in both themes, verified running on the iOS Simulator.

## Three sources of truth

| Concern | Source of truth |
|---|---|
| **Visual design** (layout, colors, type, components) | `assets/design/ios-redesign-v2/ATTREQ Redesign v2.html` + the jsx files it imports (see "Design source" below) |
| **Behavior & flows** (what each screen does, edge cases) | RN client `apps/mobile/` — reference implementation |
| **API contracts** (endpoints, shapes) | FastAPI backend `apps/api/src/attreq_api/` — wins over the RN client when they disagree |

Where the design and the RN app conflict on *flow* (e.g., registration), **the design wins** — its flows map cleanly onto existing endpoints (mappings below). Where the design omits a screen the RN app has, build it in the design's visual language using the shared design-system components.

## Ground rules

- **New code lives in `apps/ios/`.** Do not touch `apps/mobile/ios/` — that is the React Native shell, not this project.
- **No backend changes.** Every design flow must be implemented against existing endpoints; divergences get noted in the milestone file, not "fixed" server-side.
- **Match the design, don't reinterpret it.** The handoff jsx files spell out exact colors, font sizes, spacing, radii. Read them directly; don't design from screenshots. Static mock content in the design (names, "24 pieces", "87% match") is placeholder — bind real data.
- **The RN app keeps working.** CI for `apps/mobile/**` and `apps/api/**` stays green; this track adds its own CI, it never edits theirs.

## Design source: Redesign v2 handoff

Location: `assets/design/ios-redesign-v2/` (imported from the Claude Design handoff bundle; original zip at repo root can be deleted once this doc lands).

**Primary file:** `ATTREQ Redesign v2.html` — read it in full, then the files it imports, in this order:

1. `attreq-shared.jsx` — **the design system**: light/dark token sets, fonts, 16 SVG icons, and micro-components (status bar, tab bar, screen shell, mono-label, body text, underline input, card, chip, pill, garment placeholder, button). Port this first; every screen composes from it.
2. `attreq-auth.jsx` — Login + 3-step registration (Account → Style → Location) + step-progress nav.
3. `attreq-app.jsx` — Dashboard (weather strip, recommendation card), Wardrobe, History, Profile.
4. `attreq-onboarding.jsx` — Style DNA photo-upload screen.

Ignore `design-canvas.jsx`, `ios-frame.jsx`, `tweaks-panel.jsx` (canvas tooling), and `ATTREQ Redesign.html` / `attreq-screens.jsx` / `attreq-main.jsx` (superseded v1 iteration). Screenshots in `screenshots/` are quick orientation only — the jsx is the spec.

### Design tokens (from `attreq-shared.jsx`)

| Token | Light | Dark |
|---|---|---|
| `bg` | `#F5F2EE` | `#181512` |
| `surface` | `#FFFFFF` | `#231F1B` |
| `text` / `deep` | `#1C1917` | `#EDE9E3` |
| `t2` (secondary) | `#78716C` | `#9A9088` |
| `t3` (tertiary) | `#A8A29E` | `#6E6862` |
| `accent` (camel) | `#9B7B5A` | `#BA9272` |
| `clay` (destructive/skip) | `#BF5C45` | `#D4705A` |
| `moss` (positive/worn) | `#5A8A6A` | `#72AA86` |
| borders | `rgba(28,25,23,0.08/0.05)` | `rgba(237,233,227,0.08/0.05)` |

Plus `accentSoft`/`claySoft`/`mossSoft` tinted backgrounds and 5 garment-placeholder gradients per theme. Implement as **asset-catalog semantic colors** (light/dark variants) so the system appearance switch drives theming.

**Typography:** Cormorant Garamond (display serif — headlines, italic accents), DM Sans (body/UI), IBM Plex Mono (uppercase micro-labels, 1.6px letter-spacing). All three are OFL-licensed Google Fonts — bundle them in the app; do not substitute SF Pro/New York.

**Signature components** (build once in `DesignSystem`, reuse everywhere): floating pill tab bar (TODAY / WARDROBE / HISTORY / PROFILE, blur background, bottom-inset 20), 20pt-radius cards with soft shadow, underline text inputs with mono uppercase labels, selectable chips, status pills (muted/gold/moss/clay), full-width pill buttons, serif-italic headline pattern ("Good morning, *Natasha.*"), step-progress nav for wizards.

## Scope: screens & flow mappings

### Screen inventory

| # | Design artboard | Feature (RN behavioral reference) | API mapping |
|---|---|---|---|
| 01 | Login | `(auth)/login` | `POST /auth/login` |
| 02 | Register: Account | `(auth)/register` (now step 1 of 3) | validate locally; submit at step 3 |
| 03 | Register: Style | *(new step — was RN's style_preferences field)* | style keywords + occasions → `style_preferences` |
| 04 | Register: Location | *(new step — was RN profile's location edit)* | `POST /auth/register` then `PATCH /users/me/location` (device location via CoreLocation, or manual city) |
| 05 | Dashboard ("Today") | `(tabs)/index` dashboard | `GET /recommendations/daily`; Wear → `POST /outfits`; Skip/♥/✕ per RN feedback semantics |
| 06 | Wardrobe | `(tabs)/wardrobe` | `GET /wardrobe/items`; Camera/Library tiles → `POST /wardrobe/upload`; category filter chips; processing-status polling |
| 07 | History | `(tabs)/history` | `GET /outfits`, grouped by date, status pills (Worn/Loved/Skipped from `feedback_score`) |
| 08 | Profile | `(tabs)/profile` | `GET/PUT /users/me`, `PATCH /users/me/location`, Style DNA row → screen 10, Sign out → `POST /auth/logout` |
| 09 | Style DNA Upload | `(onboarding)/upload-style` | photo grid (3–8), `POST /users/style-dna` upload, "Skip for now" honors onboarding gate |
| 10 | *(not in handoff)* Style DNA results & profile | `(onboarding)/results`, `style-dna/profile` | `GET/PATCH /users/style-dna`, regenerate, photo delete — **compose in design language** |
| 11 | *(not in handoff)* Review detected items | `(onboarding)/review-items` | `POST /wardrobe/items/bulk` — **compose in design language** |

Every screen ships in **both light and dark** (system-driven), as specified by the handoff's dark artboards.

### Flow changes the design introduces (vs RN app)

- **Registration is a 3-step wizard** (Account → Style → Location) instead of one screen. All data lands on existing endpoints; no new API needed.
- **Dashboard recommendation card** adds Skip / Wear / love / dismiss affordances and a "pull down to weave new looks" refresh hint — map to the RN app's existing recommendation feedback semantics; where the RN app has no equivalent action, the milestone file defines the mapping (or marks it non-functional UI) before implementation.
- **Profile "Daily reminder" toggle** implies local notifications — implement as a local-only `UNUserNotificationCenter` daily reminder (no backend); can be stubbed UI-first and wired in M5.
- **"Forgot password"** appears in the design but has no backend endpoint — render it disabled/hidden until the backend supports it; note in M1.

### Cross-cutting behaviors to replicate (unchanged from RN app)

- **Auth lifecycle:** JWT access (15 min) + refresh (7 days); transparent refresh on 401 with retry; logout clears Keychain and resets navigation (RN reference: `src/lib/api/client.ts`, `session.ts`, `auth-store.ts`).
- **Onboarding gate:** same routing rules as `app/index.tsx` — `onboarding_completed == false` → Style DNA onboarding.
- **Wardrobe processing status:** uploads are `pending` → poll until `completed`/`failed`, with per-item status.
- **Weather & location:** CoreLocation permission flow; persisted via `PATCH /users/me/location`; recommendations consume weather.
- **Photo input:** PhotosUI picker + camera (the Wardrobe design shows both tiles explicitly); multipart uploads.

### API surface (all under `/api/v1`, unchanged)

```
POST   /auth/register            POST   /auth/login              POST /auth/logout
GET    /users/me                 PUT    /users/me                PATCH /users/me/location
POST   /users/onboarding/complete
GET    /users/style-dna          PATCH  /users/style-dna
POST   /users/style-dna/regenerate       DELETE /users/style-dna/photos/…
GET    /wardrobe/items           POST   /wardrobe/upload         POST /wardrobe/items/bulk
GET    /recommendations/daily
GET    /outfits                  POST   /outfits
```

Swift `Codable` models mirror `apps/mobile/src/lib/api/types.ts` (`User`, `AuthResponse`, `WardrobeItem`, `OutfitSuggestion`, `StyleDna`, etc.).

### Out of scope

Remote push notifications, Android, App Store/TestFlight submission (belongs to `05-roadmap` distribution milestone), new features beyond the design + RN parity, backend changes.

## Technical decisions (locked unless revisited explicitly)

| Decision | Choice | Rationale |
|---|---|---|
| UI framework | **SwiftUI** (100%; UIKit only via representable wrappers if unavoidable) | Modern default; the design's declarative screens map 1:1 |
| Min deployment target | **iOS 17.0** | Enables `@Observable`, modern SwiftUI APIs, wide device coverage |
| Language mode | **Swift 6** with strict concurrency | Catch data races at compile time from day one |
| Architecture | **MVVM-lite**: `@Observable` view models + feature folders, no heavyweight framework (no TCA) | Matches the app's feature-based layout; lowest ceremony |
| Theming | Asset-catalog **semantic colors** with light/dark variants + a `Theme` namespace mirroring the handoff token names (`bg`, `surface`, `t2`, `accent`, `clay`, `moss`…) | Handoff defines both palettes; system appearance drives the switch for free |
| Fonts | **Bundle Cormorant Garamond, DM Sans, IBM Plex Mono** (OFL); expose via `Font` extensions (`.attreqDisplay`, `.attreqBody`, `.attreqMono`) | Design's identity depends on these faces; no system-font substitution |
| Networking | **URLSession** + async/await + `Codable`; actor-based `AuthSession` for token refresh | Replaces Axios + interceptor; no third-party HTTP dependency |
| Token storage | **Keychain** (small internal wrapper) | Replaces Expo SecureStore |
| Server-state caching | Lightweight repository layer with in-memory cache per feature | Replaces TanStack Query; add sophistication only if a milestone proves the need |
| Image loading | **`AsyncImage` + configured `URLCache`** to start; adopt Nuke only if list scrolling measurably suffers | Minimize dependencies |
| Dependencies | Swift Package Manager only; default is **zero third-party packages** — each addition must be justified in a milestone file | Keep the build simple and auditable |
| Icons | Recreate the handoff's 16 stroke icons as SF Symbols where a near-exact match exists, else bundle the SVG paths as custom symbols | 1.5pt-stroke icon language is part of the design |
| Testing | **Swift Testing** (`@Test`) for units; **XCUITest** for the auth → onboarding → dashboard smoke flow | Modern test stack in Xcode 26 |
| Lint/format | **SwiftLint + SwiftFormat**, wired into CI | Standard Swift hygiene |
| Project format | Plain `.xcodeproj` with **buildable folders** (synchronized groups) | Xcode 26 folder sync avoids pbxproj churn; no XcodeGen/Tuist needed at this size |
| CI | New `.github/workflows/ios-ci.yml`, path-scoped to `apps/ios/**`: build + test on macOS runner | Mirrors the repo's path-scoped CI pattern |

Toolchain verified on this machine: Xcode 26.6, Swift 6.3, iOS 26.5 simulators (iPhone 17 Pro available and bootable).

## Milestones

Each milestone gets its own self-contained file in this directory when it starts. Every milestone ends **runnable on the simulator, in light and dark**, with its flows demonstrable end-to-end against the local backend (`make dev-api` or `make compose-up`).

| # | Milestone | Delivers | Exit criteria |
|---|---|---|---|
| M0 | **Scaffold & design system** | `apps/ios/ATTREQ.xcodeproj`; bundled fonts; semantic color assets (light+dark); `DesignSystem` components ported from `attreq-shared.jsx` (tab bar, card, input, chip, pill, button, mono-label, garment placeholder, icons); SwiftLint/SwiftFormat; `ios-ci.yml` | Component gallery screen renders every design-system piece in both themes on the simulator; CI green |
| M1 | **Networking core & auth** | API client, Codable models, Keychain, actor-based token refresh; Login (artboard 01) + 3-step registration wizard (02–04) incl. CoreLocation/city capture; root routing gate | Register via wizard + login + logout work against local API; 401-refresh unit-tested; screens match artboards in both themes |
| M2 | **Wardrobe** | Wardrobe screen (06): category chips, camera/library upload tiles, two-column grid, processing-status polling; bulk-add plumbing | Upload a photo → see it classified and displayed per the design |
| M3 | **Onboarding & Style DNA** | Style DNA upload (09), results + review-items + Style DNA profile (10–11, composed in design language); onboarding gate incl. "Skip for now" | Fresh account completes full onboarding → lands on tabs; Style DNA card renders |
| M4 | **Today & outfits** | Dashboard (05): greeting header, weather strip, recommendation card with Wear/Skip/feedback actions, pull-to-refresh; History (07) with date groups and status pills | Daily suggestions render with weather; wearing an outfit appears in History |
| M5 | **Profile, polish & design audit** | Profile (08) incl. stats, Style DNA row, preferences, local daily-reminder notification, sign out; error/empty/loading states everywhere; XCUITest smoke flow; screen-by-screen audit vs design artboards (light + dark) | Side-by-side simulator screenshots match the v2 artboards for every screen in both themes; full test suite green |

Order rationale: wardrobe (M2) before onboarding (M3) because review-items reuses wardrobe item cards and the bulk-add API.

## Verification approach (every milestone)

1. `xcodebuild build test` for the scheme (also what CI runs).
2. Boot the app on the iPhone 17 Pro simulator (`xcrun simctl`); drive the milestone's flows manually against the local backend.
3. Screenshot evidence in **both appearances**: `xcrun simctl io booted screenshot` with the simulator toggled light/dark (`xcrun simctl ui booted appearance dark`); compare against the design jsx specs (dimensions/colors/spacing are in the source — the artboards are 390×844, i.e., exactly the iPhone-13/14-class point grid).
4. RN app and backend test suites remain untouched and green.

## Completion summary (2026-07-17)

All six milestones shipped on branch `ios-native`, committed per milestone (M0…M5). The app builds and runs on the iPhone 17 Pro simulator; **117 unit tests + 4 end-to-end XCUITest flows** pass against the live local backend, and every screen was screenshot-audited in light and dark against the Redesign v2 artboards (audit table in `06-milestone-5-profile-polish.md`).

**Exit criteria (from "Done means") — all met:**
- Register (3-step wizard), login, logout, transparent 401 refresh, Keychain persistence — E2E tested (`AuthFlowUITests`).
- Style DNA onboarding (upload → results → review → complete) incl. skip and keyless-degraded paths — E2E tested (`OnboardingFlowUITests`); Style DNA profile view + correction UI shipped.
- Wardrobe browse + camera/library upload + processing-status polling — E2E tested (`WardrobeFlowUITests`).
- Daily weather-aware recommendations + Wear/Skip/feedback; worn outfits appear in History grouped by local day — E2E tested (`TodayFlowUITests`).
- Profile with live stats, location editing, daily-reminder local notification, Style DNA entry, sign out.
- Every screen matches the artboards in both themes (design audit).

**Architecture:** SwiftUI, iOS 17, Swift 6 strict concurrency, MVVM-lite (`@Observable` VMs + repositories), URLSession + actor-based `AuthSession`, Keychain, bundled fonts + semantic color assets, **zero third-party dependencies**. Path-scoped `ios-ci.yml` builds + tests on macOS. `apps/mobile/` and the backend were never modified.

**Known gaps / deliberate divergences (all documented in milestone docs):**
- Backend `PUT /users/me` ignores `style_preferences` (the column is DNA-owned) — chip-preference edits are device-local only. Backend-side change needed for server persistence; out of scope (no backend changes).
- Clothing classification (`GROQ_API_KEY`) and real weather (`OPENWEATHER_API_KEY`) require keys in `apps/api/.env`; without them the app runs in verified degraded modes (uploads still land; default weather; onboarding skips).
- Category taxonomy is free-text/substring-slotted on the backend (tracked in `docs/05-roadmap/` M2); iOS filters/recommendation-pairing mirror that.
- Worn dates use the **local** calendar day (RN uses a UTC slice) — deliberate diary semantics.
- Per-photo Style DNA delete is "remove all" (backend has no per-photo endpoint); "Forgot password" is inert (no backend endpoint).
- Icons are fixed-metric SF Symbol approximations of the handoff's feather set.

**Not in scope (never was):** remote push notifications, Android, App Store/TestFlight distribution (belongs to `docs/05-roadmap/` M5).
