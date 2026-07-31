# ATTREQ Agent Guide

## Project

AI-powered wardrobe management and outfit recommendation platform. Users upload clothing images (auto-tagged via LLM classifiers — Groq Llama 4 Scout is the live default), build a digitized wardrobe, receive daily outfit suggestions based on weather, wear history, and context. **Expo mobile app (`apps/mobile/`) is the primary React Native client**; a **native SwiftUI iOS client (`apps/ios/`)** reimplements the same product against the same backend under the Redesign v2 visual language; web app is legacy secondary.

## Docs Hierarchy

Read in this order when context needed:
1. `docs/README.md` — navigation guide
2. `docs/00-current-status/00-current-status.md` — current implementation truth
3. `docs/05-roadmap/00-roadmap-overview.md` — active launch roadmap (milestone files are self-contained and executable)
4. `docs/02-implementation/plan/06-frontend.md` — authoritative React Native plan
5. `docs/03-execution/tasks/mobile-tasks-v1.md` — active mobile checklist

Also: `docs/Pending.md` (known-gaps matrix), `docs/01-product/`, `docs/02-implementation/plan/` for product/planning context. Conflict rule: code wins over docs; `00-current-status/` wins over other docs.

## Monorepo Layout

```
apps/api/           FastAPI backend (Python) — src layout at src/attreq_api/
apps/mobile/        Expo + React Native primary client
apps/ios/           Native SwiftUI iOS client (Redesign v2, zero deps)
apps/web/           Next.js 15 secondary/legacy client
apps/landing/       Standalone Next.js landing page
infra/docker/       Docker Compose definitions (dev, local deps only, prod)
scripts/dev         Local developer helpers
scripts/test        Manual API and integration smoke tests
scripts/data        Test-image download helpers and shared fixture data
docs/               Canonical documentation
assets/design       Design assets
research/           Research and model work
```

## Commands

```bash
make compose-up          # Full API stack (PostgreSQL, Redis, Weaviate, API)
make compose-local-up    # DB/cache deps only (no API container)
make compose-down        # Stop full stack
make compose-logs        # Follow Docker logs
make dev-api             # API locally with hot-reload (port 8000)
make dev-mobile          # Expo dev server
make dev-web             # Next.js dev server
make dev-landing         # Landing page dev server
make test                # Backend pytest suite
make lint                # Ruff (backend) + next lint (web)
make format              # Ruff format backend
make migrate             # Alembic migrations to head
```

**Mobile** (run from `apps/mobile/`):
```bash
npm test                 # Jest test suite
npm run typecheck        # tsc --noEmit
npm run ios              # expo run:ios
npm run android          # expo run:android
npx jest src/test/login-screen.test.tsx  # single test
```

**Native iOS** (run from `apps/ios/`):
```bash
xcodebuild -project ATTREQ.xcodeproj -scheme ATTREQ \
  -destination 'platform=iOS Simulator,name=iPhone 17 Pro' build   # build
xcodebuild -project ATTREQ.xcodeproj -scheme ATTREQ \
  -destination 'platform=iOS Simulator,name=iPhone 17 Pro' test    # unit + UI tests
```

**Backend test with filter:**
```bash
cd apps/api && PYTHONPATH=src ../../.venv/bin/python -m pytest -k "test_name"
```

**Backend direct run:**
```bash
PYTHONPATH=src uvicorn attreq_api.main:app --reload
```

## Backend Architecture (apps/api/)

FastAPI + SQLAlchemy 2 async. Package root: `apps/api/src/attreq_api`.

```
src/attreq_api/
├── main.py                 # App factory + lifespan (DB/Redis/Weaviate startup)
├── api/v1/
│   ├── api.py              # Router aggregator
│   ├── deps.py             # Dependency injection (DB session, current user)
│   └── endpoints/          # auth, users, wardrobe, outfits, recommendations
├── config/
│   ├── settings.py         # Pydantic settings (loaded from .env)
│   ├── database.py         # asyncpg + SQLAlchemy engine/session
│   └── security.py         # JWT encode/decode, bcrypt hashing
├── models/                 # SQLAlchemy ORM models
├── schemas/                # Pydantic request/response schemas
├── crud/                   # Async CRUD operations
└── services/
    ├── ai/                 # Classifier factory + Groq/Gemini/Claude/OpenAI classifiers
    ├── cache/              # Redis client
    ├── recommendation/     # Outfit suggestion logic (Style DNA scoring integrated)
    ├── storage/            # File upload handling (originals/processed/thumbnails/style-dna)
    └── style_dna/          # Style DNA orchestrator, LLM prompts, scoring functions
```

Endpoints: `auth`, `users` (includes `onboarding/complete`), `wardrobe` (includes `items/bulk`), `outfits`, `recommendations`, `style-dna`.

Other paths: Alembic config at `apps/api/alembic.ini`, uploads at `apps/api/uploads`.

**Cross-cutting flows** (span multiple modules — read these together):
- **Classification pipeline:** wardrobe upload endpoint → `workers/image_processor.py` / `workers/batch_image_processor.py` → `services/ai/classifier_factory.py` (provider chosen by `CLASSIFIER_PROVIDER`) → `services/ai/schema_mapper.py` (single choke point mapping every provider's output to `WardrobeItem` fields) → DB. Background removal (`rembg`) and thumbnails happen in the same worker pass.
- **Storage:** all image I/O goes through the `file_storage` singleton in `services/storage/file_handler.py` (local disk, `/uploads/...` URLs). Imported by the wardrobe endpoint, both workers, and `style_dna_service.py` — change storage behavior in one place, check all four call sites.
- **Recommendation scoring** (`services/recommendation/algorithm.py`): outfits are top×bottom pairs scored `color_harmony 0.4 + formality 0.4 + preference 0.2`; when the user has Style DNA, weights switch to `color 0.2 + formality 0.2 + style_dna 0.4 + behaviour 0.2`. Category slotting is currently substring-based on free-text categories (known gap — see roadmap M2).
- **Auth:** JWT access (15 min) + refresh (7 days) from `config/security.py`; mobile stores tokens in Expo SecureStore and refreshes via an Axios interceptor in `src/lib/api/`.

Required env vars (copy `apps/api/.env.example` → `apps/api/.env`):
- `DATABASE_URL` — postgresql+asyncpg connection string
- `SECRET_KEY` — JWT signing key
- `CLASSIFIER_PROVIDER` — `groq` (default) | `gemini` | `claude` | `openai`
- `GROQ_API_KEY` / `GEMINI_API_KEY` / `CLAUDE_API_KEY` / `OPENAI_API_KEY` — whichever provider is active
- `OPENWEATHER_API_KEY` — weather-based recommendations

## Mobile Architecture (apps/mobile/)

Expo 55, React Native 0.83, TypeScript, Expo Router (file-based routing).

```
app/
├── (auth)/                 # Unauthenticated: login, register
├── (onboarding)/           # First-run: upload-style → results → review-items
└── (protected)/
    ├── (tabs)/             # Tab navigation for authenticated users
    └── style-dna/          # Style DNA card (post-onboarding)
src/
├── components/             # Reusable UI (common/, ui/, attreq/)
├── features/               # Screen-level components per domain
│   ├── auth/
│   ├── wardrobe/
│   ├── outfits/
│   ├── recommendations/
│   ├── profile/
│   └── style-dna/          # StyleDnaCard, PhotoGrid, FoundItemsCard, ItemReviewCard, hooks
├── lib/
│   ├── api/                # Axios client + endpoint wrappers (style-dna.ts added)
│   ├── query/              # TanStack Query hooks + queryKeys
│   └── storage/            # Expo SecureStore (JWT tokens)
├── store/
│   └── auth-store.ts       # Zustand auth state
└── theme/                  # Colors, typography, design tokens
```

**Key patterns:**
- Route protection in `app/(protected)/_layout.tsx` — checks Zustand auth store
- Onboarding gate in `app/index.tsx` — routes new users (`onboarding_completed=false`) to `/(onboarding)/upload-style`
- Server state via TanStack Query in `src/lib/query/`; local UI state stays in components
- Styling: NativeWind (Tailwind for RN) — use `className` props, not StyleSheet
- Dense lists: FlashList over FlatList
- Path alias `@/` → `src/` (tsconfig.json + babel.config.js)

**Web frontend paths:** `apps/landing/src/app`, `apps/web/src/app`, `apps/web/src/components`, `apps/web/src/lib`, `apps/web/src/store`.

## Mobile Testing

Jest with custom env (`jest.react-native-env.js`). `jest.setup.ts` mocks all Expo native modules (reanimated, secure-store, vector-icons, image-picker, location). Tests live in `src/test/`. Expo modules auto-mocked; `@/` aliases work in tests.

## Native iOS Architecture (apps/ios/)

SwiftUI, iOS 17.0 target, Swift 6 (strict concurrency), **zero third-party dependencies**. Bundle id `com.attreq.ios`. Xcode project uses buildable folders (PBXFileSystemSynchronizedRootGroup) — new source files auto-join the target, no pbxproj edits needed. Three targets: `ATTREQ` (app), `ATTREQTests` (Swift Testing units, hermetic via mock URLProtocol), `ATTREQUITests` (XCUITest E2E against a live local backend, provisions its own accounts).

```
ATTREQ/
├── App/            AppSession (auth state machine), RootView (routing gate +
│                   audit routes), MainTabsView (tab shell owning view models)
├── Core/
│   ├── Networking/ APIClient (async/await), Endpoint (JSON/form/multipart),
│   │               AuthSession actor (Keychain tokens, single-flight
│   │               epoch-guarded 401 refresh), APIError
│   ├── Keychain/   KeychainStore (AfterFirstUnlockThisDeviceOnly)
│   ├── Location/   LocationProvider (CoreLocation async wrapper)
│   └── Models/     Codable mirrors of backend schemas
├── DesignSystem/   Theme (semantic colors, light+dark), Typography (bundled
│                   Cormorant Garamond / DM Sans / IBM Plex Mono), components
└── Features/       Auth, Wardrobe, StyleDna, Today, History, Profile
```

**Key patterns:**
- MVVM-lite: `@Observable` `@MainActor` view models over plain repository classes; view models owned by `MainTabsView` so tab state survives switches.
- Screens are pixel-faithful to `assets/design/ios-redesign-v2/` — the `.jsx` files are the spec, implemented in both light and dark themes.
- Login is OAuth2 form-urlencoded; refresh token is not rotated by the backend; JWT refresh is single-flight with an epoch guard in the `AuthSession` actor.
- Debug base URL is `http://localhost:8001/api/v1` (override with `ATTREQ_API_URL` launch env). Full backend setup, audit routes, and UI-test launch hooks are in `apps/ios/README.md`.
- Known deliberate divergences from RN (documented in `docs/06-ios-native/`): worn dates use local calendar day (RN uses UTC slice); `style_preferences` column is Style-DNA-owned; icons are fixed-metric SF Symbol approximations.

Goal file + per-milestone execution history: `docs/06-ios-native/00-goal.md` and `01`–`06-milestone-*.md`. iOS work lives on the `ios-native` branch.

## iOS Simulator Debugging

`computer-use` cannot reach Simulator.app (inside Xcode.app). Use CLI. The commands below target Expo Go; for the native app substitute process `ATTREQ` and bundle id `com.attreq.ios`:

```bash
xcrun simctl list devices | grep Booted           # check booted device
xcrun simctl io booted screenshot /tmp/sim_screen.png  # screenshot → Read /tmp/sim_screen.png
xcrun simctl listapps booted | grep -i "attreq\|expo"  # installed apps

# Stream Expo Go logs
xcrun simctl spawn booted log stream --predicate 'process == "Expo Go"' --level default
# Errors/warnings only
xcrun simctl spawn booted log stream --predicate 'process == "Expo Go"' --level default \
  | grep -E "ERROR|WARN|console|JS|exception|crash|fatal"

# Metro bundler
lsof -i :8081 -sTCP:LISTEN          # is Metro running?
curl -s http://localhost:8081/status  # → packager-status:running
curl -s http://localhost:8081/json    # lists JS debugger targets
```

**Note:** System logs privacy-redact JS console output. For JS-level logs use Metro terminal or React Native DevTools at `localhost:8081/debugger-frontend/...` (URL from `curl localhost:8081/json`).

## Compose Files

| File | Purpose |
|------|---------|
| `infra/docker/compose.api.yml` | Full dev stack (API + DB + Redis + Weaviate) |
| `infra/docker/compose.api.dev.yml` | Local deps only (DB + Redis) — pair with `make dev-api` |
| `infra/docker/compose.api.prod.yml` | Production stack |

## CI

GitHub Actions, path-scoped:
- `.github/workflows/backend-ci.yml` — on `apps/api/**` changes: Ruff, `alembic upgrade head` against a Postgres 15 service, pytest
- `.github/workflows/mobile-ci.yml` — on `apps/mobile/**` changes: `tsc --noEmit`, Jest
- `.github/workflows/ios-ci.yml` — on `apps/ios/**` changes: `xcodebuild` build + full test run on a macOS runner

Before pushing backend changes run `make lint && make test`; for mobile run `npm run typecheck && npm test` from `apps/mobile/`; for iOS run the `xcodebuild ... test` command above from `apps/ios/`. New Alembic migrations must chain from the current head or CI fails.

## Library Docs & Implementation Verification

Use `ctx7` CLI to fetch current docs when implementing against or verifying any library, SDK, API, or framework — even well-known ones. Training data may be stale.

```bash
# Step 1 — resolve library ID
npx ctx7@latest library <name> "<specific question>"

# Step 2 — fetch docs
npx ctx7@latest docs <libraryId> "<specific question>"

# Step 3 — if answer unsatisfactory, retry with live research
npx ctx7@latest docs <libraryId> "<specific question>" --research
```

**When to use:** implementing against a new SDK, verifying API shapes (request/response format, parameter names, method signatures), version migrations, debugging unexpected SDK behavior.

**Not needed for:** refactoring, business logic, code review, general Python/TS patterns.

## Bash Preferences

Prefer these over defaults; fall back silently if missing:

- **Search content:** `rg` over `grep`
- **Find files:** `fd` over `find`; never `find -exec` or `xargs` chains when `fd -x` or `rg -l | xargs` is clearer
- **AST/structural search:** `ast-grep` (`sg`) for TS/TSX refactors and pattern search
- **JSON:** `jq` for parsing/filtering/transformation
- **YAML/TOML:** `yq`
- **GitHub:** `gh` for PRs, issues, reviews, CI, releases — never scrape github.com directly
- **Benchmarking:** `hyperfine`
- **Circular deps:** `madge --circular`
- **Dead code:** `knip`
- **Duplication:** `jscpd`
- **Typecheck only:** `tsc --noEmit` (or `tsc -b --noEmit` in monorepos)
