# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Project Is

ATTREQ is an AI-powered wardrobe management and outfit recommendation platform. Users upload clothing images (auto-tagged via Google Gemini), build a digitized wardrobe, and receive daily outfit suggestions based on weather, wear history, and context. The **mobile app is the primary client**; the web app is a legacy secondary client.

## Monorepo Layout

```
apps/api/           FastAPI backend (Python) — src layout at src/attreq_api/
apps/mobile/        Expo + React Native primary client
apps/web/           Next.js 15 secondary/legacy client
apps/landing/       Standalone Next.js landing page
infra/docker/       Docker Compose definitions (dev, local deps only, prod)
scripts/            Dev helpers, smoke tests, fixture data
docs/               Canonical documentation (read docs/README.md first)
```

## Documentation Hierarchy

When context is needed, read in this order:
1. `docs/README.md` — navigation guide
2. `docs/00-current-status/00-current-status.md` — current implementation truth
3. `docs/02-implementation/plan/06-frontend.md` — authoritative React Native plan
4. `docs/03-execution/tasks/mobile-tasks-v1.md` — active mobile checklist

## Commands

All root commands delegate to the Makefile:

```bash
make compose-up          # Start full API stack (PostgreSQL, Redis, Weaviate, API)
make compose-local-up    # Start DB/cache dependencies only (no API container)
make compose-down        # Stop full stack
make compose-logs        # Follow Docker logs

make dev-api             # Run API locally with hot-reload (port 8000)
make dev-mobile          # Start Expo dev server
make dev-web             # Start Next.js dev server

make test                # Run backend pytest suite
make lint                # Ruff (backend) + next lint (web)
make format              # Ruff format backend
make migrate             # Run Alembic migrations to head
```

**Mobile-specific commands** (run from `apps/mobile/`):
```bash
npm test                 # Jest test suite
npm run typecheck        # tsc --noEmit
npm run ios              # expo run:ios
npm run android          # expo run:android
```

**Run a single mobile test:**
```bash
cd apps/mobile && npx jest src/test/login-screen.test.tsx
```

**Run backend tests with filter:**
```bash
cd apps/api && PYTHONPATH=src ../../.venv/bin/python -m pytest -k "test_name"
```

## Backend Architecture (apps/api/)

FastAPI + SQLAlchemy 2 async stack:

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

Required environment variables (copy `apps/api/.env.example` → `apps/api/.env`):
- `DATABASE_URL` — postgresql+asyncpg connection string
- `SECRET_KEY` — JWT signing key
- `GEMINI_API_KEY` — clothing attribute extraction
- `OPENWEATHER_API_KEY` — weather-based recommendations

## Mobile Architecture (apps/mobile/)

Expo 55, React Native 0.83, TypeScript, Expo Router (file-based routing):

```
app/                        # Expo Router routes
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
- Route protection is handled in `app/(protected)/_layout.tsx` — checks Zustand auth store
- Server state via TanStack Query hooks in `src/lib/query/`; local UI state stays in components
- Styling uses NativeWind (Tailwind for RN) — use `className` props, not StyleSheet
- Dense lists use FlashList instead of FlatList for performance
- Path alias `@/` resolves to `src/` (configured in tsconfig.json and babel.config.js)

## Mobile Testing Setup

Jest is configured with a custom environment (`jest.react-native-env.js`). `jest.setup.ts` mocks all Expo native modules (reanimated, secure-store, vector-icons, image-picker, location). Tests live in `src/test/`.

When writing mobile tests: Expo modules are auto-mocked — import from `@/` aliases works in tests.

## Compose File Mapping

| File | Purpose |
|------|---------|
| `infra/docker/compose.api.yml` | Full dev stack (API + DB + Redis + Weaviate) |
| `infra/docker/compose.api.dev.yml` | Local deps only (DB + Redis) — use when running API via `make dev-api` |
| `infra/docker/compose.api.prod.yml` | Production stack |


### Bash commands

Prefer these over defaults when available. Fall back silently if missing.

- **Search content:** `rg` over `grep`
- **Find files:** `fd` over `find`
- **Never** use `find -exec` or `xargs` chains when `fd -x` or `rg -l | xargs` would be clearer. Prefer readable pipelines.
- **Structural/AST search:** `ast-grep` (`sg`) for refactors and pattern-based code search, especially in TS/TSX
- **JSON:** `jq` for any parsing, filtering, or transformation in pipelines
- **YAML/TOML:** `yq`
- **GitHub operations:** `gh` for PRs, issues, reviews, CI status, and releases. Do not scrape github.com or hit the REST API directly when `gh` can do it.
- **Benchmarking:** `hyperfine` when comparing command performance
- **Circular deps (JS/TS):** `madge --circular`
- **Dead code (JS/TS):** `knip`
- **Duplication (JS/TS):** `jscpd`
- **Typecheck only:** `tsc --noEmit` (or `tsc -b --noEmit` in monorepos)