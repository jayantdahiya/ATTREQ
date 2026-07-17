# ATTREQ — Native iOS App

Native SwiftUI client for ATTREQ (AI wardrobe management), implementing the Redesign v2 visual language. Built against the same FastAPI backend as the other clients. See `docs/06-ios-native/00-goal.md` for the goal file and per-milestone docs (M0–M5) for execution history, verified states, and known divergences.

## Requirements

- Xcode 26+, iOS 17.0 deployment target, Swift 6 (strict concurrency)
- Zero third-party dependencies
- Local backend for full functionality (see below)

## Build & test

```bash
cd apps/ios
xcodebuild -project ATTREQ.xcodeproj -scheme ATTREQ \
  -destination 'platform=iOS Simulator,name=iPhone 17 Pro' build   # or: test
```

Unit tests (`ATTREQTests`, Swift Testing) are hermetic (mock URLProtocol). UI tests (`ATTREQUITests`, XCUITest) run E2E against a live local backend and provision their own accounts via the API.

## Local backend

```bash
# Deps (ports 5433/6380 to avoid collisions; compose project name matters):
docker compose -p attreq-dev -f infra/docker/compose.api.dev.yml \
  -f <override with 5433:5432 / 6380:6379 port maps> up -d
# API:
cd apps/api && PYTHONPATH=src ../../.venv/bin/python -m uvicorn attreq_api.main:app --port 8001
```

The app's Debug base URL is `http://localhost:8001/api/v1` (override with the `ATTREQ_API_URL` launch environment). Optional backend keys: `GROQ_API_KEY` (clothing classification / Style DNA extraction), `OPENWEATHER_API_KEY` (real weather; a default-weather fallback exists). Without them the app runs in documented degraded modes.

## Architecture

```
ATTREQ/
├── App/            AppSession (auth state machine), RootView (routing gate +
│                   audit routes), MainTabsView (tab shell), AppConfig
├── Core/
│   ├── Networking/ APIClient (async/await), Endpoint (JSON/form/multipart),
│   │               AuthSession actor (Keychain tokens, single-flight
│   │               epoch-guarded 401 refresh), APIError
│   ├── Keychain/   KeychainStore (ThisDeviceOnly)
│   ├── Location/   LocationProvider (CoreLocation async wrapper)
│   └── Models/     Codable mirrors of the backend schemas
├── DesignSystem/   Theme (semantic colors, light+dark), Typography (bundled
│                   Cormorant Garamond / DM Sans / IBM Plex Mono), components
│                   (cards, chips, pills, inputs, tab bar, …), gallery
└── Features/       Auth, Wardrobe (+PhotoInput), StyleDna (onboarding,
                    profile, correction), Today, History, Profile
```

Patterns: MVVM-lite — `@Observable` `@MainActor` view models over plain repository classes; view models owned by `MainTabsView` so tab state survives switches; screens are pixel-faithful to `assets/design/ios-redesign-v2/` (the jsx files are the spec).

## Audit routes (design verification)

Launch arguments jump straight to a screen (used for screenshot audits and by docs):

```
xcrun simctl launch booted com.attreq.ios -gallery              # design-system gallery
xcrun simctl launch booted com.attreq.ios -screen <name>
# names: register-account | register-style | register-location | wardrobe |
#        style-dna-upload | style-dna | today | history | profile
```

UI-test hooks (test builds only, all opt-in by launch argument): `-reset-auth` (clean keychain), `-uitest-autopick-photo` / `-uitest-autopick-photos` (bypass PHPicker with synthetic JPEGs — the system picker doesn't accept synthesized taps).

## CI

`.github/workflows/ios-ci.yml` — path-scoped to `apps/ios/**`: build + full test run on a macOS runner.
