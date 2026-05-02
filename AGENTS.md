# ATTREQ Agent Guide

## Project

AI-powered wardrobe management and outfit recommendation platform. Users upload clothing images (auto-tagged via Gemini), build a digitized wardrobe, receive daily outfit suggestions based on weather, wear history, and context. **Mobile app is primary client**; web app is legacy secondary.

## Docs Hierarchy

Read in this order when context needed:
1. `docs/README.md` — navigation guide
2. `docs/00-current-status/00-current-status.md` — current implementation truth
3. `docs/02-implementation/plan/06-frontend.md` — authoritative React Native plan
4. `docs/03-execution/tasks/mobile-tasks-v1.md` — active mobile checklist

Also: `docs/01-product/`, `docs/02-implementation/plan/` for product/planning context.

## Monorepo Layout

```
apps/api/           FastAPI backend (Python) — src layout at src/attreq_api/
apps/mobile/        Expo + React Native primary client
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
    ├── ai/                 # Gemini API integration, embeddings, Weaviate
    ├── cache/              # Redis client
    ├── recommendation/     # Outfit suggestion logic
    └── storage/            # File upload handling
```

Other paths: Alembic config at `apps/api/alembic.ini`, uploads at `apps/api/uploads`.

Required env vars (copy `apps/api/.env.example` → `apps/api/.env`):
- `DATABASE_URL` — postgresql+asyncpg connection string
- `SECRET_KEY` — JWT signing key
- `GEMINI_API_KEY` — clothing attribute extraction
- `OPENWEATHER_API_KEY` — weather-based recommendations

## Mobile Architecture (apps/mobile/)

Expo 55, React Native 0.83, TypeScript, Expo Router (file-based routing).

```
app/
├── (auth)/                 # Unauthenticated: login, register
└── (protected)/(tabs)/     # Tab navigation for authenticated users
src/
├── components/             # Reusable UI (common/, ui/, attreq/)
├── features/               # Screen-level components per domain
│   ├── auth/
│   ├── wardrobe/
│   ├── outfits/
│   ├── recommendations/
│   └── profile/
├── lib/
│   ├── api/                # Axios client + endpoint wrappers
│   ├── query/              # TanStack Query hooks
│   └── storage/            # Expo SecureStore (JWT tokens)
├── store/
│   └── auth-store.ts       # Zustand auth state
└── theme/                  # Colors, typography, design tokens
```

**Key patterns:**
- Route protection in `app/(protected)/_layout.tsx` — checks Zustand auth store
- Server state via TanStack Query in `src/lib/query/`; local UI state stays in components
- Styling: NativeWind (Tailwind for RN) — use `className` props, not StyleSheet
- Dense lists: FlashList over FlatList
- Path alias `@/` → `src/` (tsconfig.json + babel.config.js)

**Web frontend paths:** `apps/landing/src/app`, `apps/web/src/app`, `apps/web/src/components`, `apps/web/src/lib`, `apps/web/src/store`.

## Mobile Testing

Jest with custom env (`jest.react-native-env.js`). `jest.setup.ts` mocks all Expo native modules (reanimated, secure-store, vector-icons, image-picker, location). Tests live in `src/test/`. Expo modules auto-mocked; `@/` aliases work in tests.

## iOS Simulator Debugging

`computer-use` cannot reach Simulator.app (inside Xcode.app). Use CLI:

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
