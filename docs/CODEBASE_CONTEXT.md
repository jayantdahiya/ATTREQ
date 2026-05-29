# ATTREQ — Full Codebase Context

> Single-shot reference for an AI agent onboarding to this codebase. Covers product concept, architecture, stack, data flow, and key file locations.

---

## 1. What Is ATTREQ?

AI-powered wardrobe management and outfit recommendation platform. Core loop:

1. User photographs clothing items
2. AI classifies each item (category, color, pattern, season, occasion) and removes background
3. Items are stored in a digital wardrobe with vector embeddings
4. Every day, the system generates personalized outfit suggestions based on current weather, occasion context, wear history, and learned preferences
5. User wears an outfit → logs it → gives feedback → improves future suggestions

**Primary client:** iOS/Android mobile app (React Native + Expo).  
**Secondary client:** Web app (Next.js, legacy).  
**Standalone marketing:** Next.js landing page.

---

## 2. Monorepo Layout

```
Project Attreq/
├── apps/
│   ├── api/                   Python FastAPI backend
│   ├── mobile/                React Native / Expo primary client
│   ├── web/                   Next.js 15 legacy web client
│   └── landing/               Next.js 15 standalone marketing site
├── infra/
│   └── docker/
│       ├── compose.api.yml    Full dev stack (API + DB + Redis + Weaviate)
│       ├── compose.api.dev.yml Local deps only (no API container)
│       └── compose.api.prod.yml Production stack
├── scripts/
│   ├── dev/                   Local developer helpers
│   ├── test/                  Manual API/integration smoke tests
│   └── data/                  Test image fixtures and bulk download helpers
├── docs/                      Canonical documentation
├── research/                  Model/AI research
└── AGENTS.md                  Developer guide (authoritative)
```

---

## 3. Full Tech Stack

### Backend (`apps/api/`)

| Concern | Technology |
|---|---|
| Language | Python 3.11 |
| Framework | FastAPI (async) + Uvicorn |
| ORM | SQLAlchemy 2.0 async |
| DB driver | asyncpg |
| Database | PostgreSQL 15 |
| Migrations | Alembic |
| Vector DB | Weaviate 1.27 (`text2vec-transformers` module) |
| Embedding model | `sentence-transformers-all-MiniLM-L6-v2` (CPU, Docker service) |
| Cache | Redis 7 |
| Auth | JWT (HS256) via `python-jose` + bcrypt passwords via `passlib` |
| AI — primary classifier | Groq API → Llama 4 Scout (vision) |
| AI — batch classifier | Google Gemini API (dormant in prod pipeline) |
| Background removal | `rembg` library |
| Color/pattern fallback | Pillow + scikit-learn K-means |
| HTTP client | `httpx` (async) |
| Validation | Pydantic v2 + pydantic-settings |
| Linting | Ruff |

### Mobile (`apps/mobile/`)

| Concern | Technology |
|---|---|
| Framework | React Native 0.83.4 + Expo SDK 55 |
| Router | `expo-router` (file-based) |
| Server state | TanStack Query v5 |
| Client state | Zustand |
| HTTP | Axios (with JWT refresh interceptor) |
| Secure storage | `expo-secure-store` (refresh token) |
| Styling | NativeWind 4 (Tailwind for RN) |
| Fonts | Cormorant Garamond (display), DM Sans (body), IBM Plex Mono (labels) |
| Images | `expo-image`, `expo-image-picker` |
| Location | `expo-location` |
| Animations | `react-native-reanimated` |
| Forms | `react-hook-form` + `zod` |
| Dense lists | FlashList |
| Testing | Jest + Testing Library / React Native |
| Language | TypeScript |

### Web / Landing

| App | Stack |
|---|---|
| `apps/web` | Next.js 15 App Router, TypeScript |
| `apps/landing` | Next.js 15 App Router, Framer Motion, Lucide React, TypeScript |

---

## 4. Backend Architecture

### Package Layout

```
apps/api/
├── src/attreq_api/
│   ├── main.py                     App factory + lifespan hooks
│   ├── api/v1/
│   │   ├── api.py                  Router aggregator
│   │   ├── deps.py                 DI: DB session, current user
│   │   └── endpoints/
│   │       ├── auth.py
│   │       ├── users.py
│   │       ├── wardrobe.py
│   │       ├── outfits.py
│   │       └── recommendations.py
│   ├── config/
│   │   ├── settings.py             Pydantic settings (from .env)
│   │   ├── database.py             asyncpg + SQLAlchemy engine/session
│   │   └── security.py             JWT encode/decode, bcrypt
│   ├── models/                     SQLAlchemy ORM models
│   ├── schemas/                    Pydantic request/response schemas
│   ├── crud/                       Async CRUD operations
│   ├── workers/
│   │   ├── image_processor.py      Single-image background task
│   │   └── batch_image_processor.py Batch upload processor
│   ├── services/
│   │   ├── ai/
│   │   │   ├── groq_classifier.py  Llama 4 Scout vision classifier
│   │   │   ├── gemini_classifier.py Gemini batch classifier (dormant)
│   │   │   ├── embeddings.py       Weaviate client + vector ops
│   │   │   └── background_removal.py rembg wrapper
│   │   ├── cache/
│   │   │   └── redis_client.py     Redis wrapper
│   │   ├── recommendation/
│   │   │   └── algorithm.py        Outfit scoring + selection logic
│   │   └── storage/
│   │       └── file_storage.py     Local disk storage, thumbnail generation
│   └── integrations/
│       └── external/
│           └── weather_api.py      OpenWeatherMap API client
├── alembic/                        Migration files
├── alembic.ini
└── .env.example
```

### API Routes Summary

```
POST   /api/v1/auth/register
POST   /api/v1/auth/login
POST   /api/v1/auth/refresh
POST   /api/v1/auth/logout

GET    /api/v1/users/me
PUT    /api/v1/users/me
PUT    /api/v1/users/me/location

POST   /api/v1/wardrobe/upload            (multipart, single image)
POST   /api/v1/wardrobe/batch-upload      (multipart, multiple images)
GET    /api/v1/wardrobe/items
GET    /api/v1/wardrobe/items/{id}
PUT    /api/v1/wardrobe/items/{id}
DELETE /api/v1/wardrobe/items/{id}

POST   /api/v1/outfits/
GET    /api/v1/outfits/
GET    /api/v1/outfits/{id}
POST   /api/v1/outfits/{id}/wear
POST   /api/v1/outfits/{id}/feedback
DELETE /api/v1/outfits/{id}

GET    /api/v1/recommendations/daily      ?lat=&lon=&occasion=
DELETE /api/v1/recommendations/cache

GET    /health
```

---

## 5. Database Schema

### `users`
```
id                UUID PK
email             VARCHAR UNIQUE
password_hash     VARCHAR
full_name         VARCHAR
location          VARCHAR
saved_latitude    FLOAT
saved_longitude   FLOAT
saved_city        VARCHAR
is_active         BOOLEAN
is_verified       BOOLEAN
created_at        TIMESTAMP
updated_at        TIMESTAMP
last_login        TIMESTAMP
oauth_provider    VARCHAR (Phase 2, not wired)
oauth_id          VARCHAR (Phase 2, not wired)
style_preferences TEXT (JSON)
```

### `wardrobe_items`
```
id                    UUID PK
user_id               UUID FK → users (CASCADE DELETE)
original_image_url    VARCHAR
processed_image_url   VARCHAR (background removed)
thumbnail_url         VARCHAR (300px)
category              VARCHAR   (e.g. "t-shirt", "jeans")
color_primary         VARCHAR
color_secondary       VARCHAR
pattern               VARCHAR   (e.g. "solid", "striped")
season                ARRAY[VARCHAR]   (e.g. ["spring","summer"])
occasion              ARRAY[VARCHAR]   (e.g. ["casual","business"])
detection_confidence  FLOAT
classification_source VARCHAR   ("ai" | "fallback")
processing_status     VARCHAR   ("pending"|"processing"|"completed"|"failed")
wear_count            INTEGER
last_worn             DATE
created_at            TIMESTAMP
updated_at            TIMESTAMP
```

### `outfits`
```
id                UUID PK
user_id           UUID FK → users (CASCADE DELETE)
top_item_id       UUID FK → wardrobe_items (SET NULL)
bottom_item_id    UUID FK → wardrobe_items (SET NULL)
accessory_ids     ARRAY[UUID]
worn_date         DATE
feedback_score    INTEGER  (-1 = disliked, 0 = neutral, 1 = liked)
weather_context   JSON
occasion_context  VARCHAR
created_at        TIMESTAMP
updated_at        TIMESTAMP
```

### Weaviate Collection: `ClothingItem`
Vector-indexed properties: `itemId`, `userId`, `category`, `colorPrimary`, `colorSecondary`, `pattern`, `season[]`, `occasion[]`, `description`. Embedding via `text2vec-transformers` (MiniLM-L6-v2).

---

## 6. Key Data Flows

### Image Upload & AI Processing Pipeline

```
Mobile                          Backend (FastAPI)
------                          -----------------
Upload image (multipart)
  POST /wardrobe/upload    →    FileStorageService.save_upload_file()
                                  → saved: uploads/originals/{userId}_{uuid}.ext
                                wardrobe_crud.create() → DB record, status="pending"
                                ↓ FastAPI BackgroundTask fires:
                                  1. status → "processing"
                                  2. BackgroundRemovalService.remove_background() [rembg]
                                       → uploads/processed/
                                  3. FileStorageService.generate_thumbnail() [Pillow, 300px]
                                       → uploads/thumbnails/
                                  4. ClothingDetectionService.detect_clothing()
                                       → if GROQ_API_KEY: GroqClassifierService
                                            (Llama 4 Scout vision, httpx POST to api.groq.com)
                                       → else: fallback K-means color + std-dev pattern detect
                                  5. WeaviateEmbeddingsService.add_item()
                                       → vector indexed in Weaviate
                                  6. wardrobe_crud.update() → all attributes, status="completed"
```

Batch upload: same pipeline, up to 5 items processed sequentially per batch.

### Recommendation Pipeline

```
GET /recommendations/daily?lat=&lon=&occasion=
  1. Redis cache check: key = daily_suggestions:{userId}:{date}:{occasion}
       → cache hit → return immediately (24h TTL)
  2. Resolve location: provided lat/lon OR user.saved_lat/lon
  3. WeatherAPIService.get_current_weather() → OpenWeatherMap (1h Redis cache)
  4. generate_daily_outfits():
     a. Fetch all WardrobeItems (status="completed") for user
     b. filter_items_by_weather():
          >25°C → summer items
          <15°C → winter items
          else  → spring/autumn items
     c. filter_items_by_occasion(): match item.occasion array to requested occasion
     d. get_recently_worn_items(): outfits in last 14 days
     e. get_user_preference_weights(): analyze outfits with feedback_score=1
     f. Score every bottom × top combination not recently worn:
          color_harmony_score    (complementary/neutral/clash rules)
          formality_score        (category-based formality tiers)
          preference_bonus       (from liked colors)
          total = 0.4×color + 0.4×formality + 0.2×preference
          + random accessory if available
     g. Sort by score, deduplicate (no item reused across suggestions)
  5. Cache results in Redis (24h TTL)
  6. Return DailySuggestionsResponse
```

### Auth Flow (Mobile ↔ Backend)

```
Login:
  POST /auth/login (form-urlencoded: username + password)
  → access_token (JWT, 15min) + refresh_token (JWT, 7 days)
  → access_token: stored in Zustand store (in-memory)
  → refresh_token: stored in expo-secure-store (encrypted device storage)

Request cycle:
  Axios interceptor: adds Bearer token to every request header

Token expiry (401):
  Axios response interceptor:
    → POST /auth/refresh with refresh_token
    → new access_token → retry original request

App bootstrap:
  getRefreshToken() from expo-secure-store
  if present → authApi.refresh() → set access_token in Zustand
  then authApi.getCurrentUser() → cached in TanStack Query
```

---

## 7. Mobile App Architecture

### Route Tree (Expo Router, file-based)

```
app/
  index.tsx                    Auth check redirect
  _layout.tsx                  Root: QueryClientProvider, SafeAreaProvider, auth bootstrap
  (auth)/
    _layout.tsx                Stack navigator
    login.tsx                  → LoginScreen
    register.tsx               → RegisterScreen
  (protected)/
    _layout.tsx                Auth guard (unauthenticated → /login)
    (tabs)/
      _layout.tsx              Bottom tab bar (4 tabs)
      index.tsx                → DashboardScreen (daily outfit suggestions)
      wardrobe.tsx             → WardrobeScreen (closet grid + upload)
      history.tsx              → HistoryScreen (outfit diary, grouped by date)
      profile.tsx              → ProfileScreen (user info, location, notifications, sign out)
```

### Feature Modules (`src/features/`)

| Feature | File | Description |
|---|---|---|
| Dashboard | `recommendations/dashboard-screen.tsx` | Weather strip, outfit cards, wear/feedback actions, location request |
| Wardrobe | `wardrobe/wardrobe-screen.tsx` | 2-column masonry grid, camera/library picker, upload |
| History | `outfits/history-screen.tsx` | Outfit diary grouped by date, feedback labels |
| Profile | `profile/profile-screen.tsx` | User card, location update, daily reminder (8AM weekday via `expo-notifications`), sign out |

### API Layer (`src/lib/api/`)

```
client.ts         Axios instance; request interceptor adds Bearer token;
                  response interceptor handles 401 → refresh → retry
auth.ts           register, login, refresh, logout, getCurrentUser
wardrobe.ts       listItems, uploadItem (multipart), getItem
recommendations.ts getDailySuggestions
outfits.ts        createFromSuggestion, markAsWorn, submitFeedback, listOutfits
users.ts          updateLocation
types.ts          Shared TypeScript types for all API response shapes
```

### State Architecture

- **Server state:** TanStack Query hooks in `src/lib/query/` — all API data lives here
- **Auth state:** Zustand store in `src/store/auth-store.ts` — holds access_token and user identity
- **UI state:** Local component state only; no global UI store

### Design System (`src/components/attreq/editorial.tsx`)

Custom editorial component library. Key components:

| Component | Purpose |
|---|---|
| `AppSurface` | Dark/light themed container |
| `EditorialHeader` | Full-bleed header with title/subtitle |
| `EditorialCard` | Bordered content card |
| `GarmentTile` | Clothing item tile with gradient placeholder |
| `MonoLabel` | IBM Plex Mono label text |
| `WeatherStrip` | Current weather display bar |
| `StatusPill` | Processing status indicator |
| `IconCircle` | Circular icon wrapper |

Theme via `useThemeColors()` (defaults dark). Colors in `src/theme/colors.ts`. Path alias: `@/` → `src/`.

---

## 8. Infrastructure & Configuration

### Docker Services (full dev stack)

| Service | Image | Port | Purpose |
|---|---|---|---|
| `postgres` | postgres:15-alpine | 5432 | Primary database |
| `redis` | redis:7-alpine | 6379 | Caching layer |
| `weaviate` | semitechnologies/weaviate:1.27.0 | 8080 | Vector database |
| `t2v-transformers` | semitechnologies/transformers-inference-api | — | MiniLM-L6-v2 embedding model |
| `backend` | (local build) | 8000 | FastAPI app; runs `alembic upgrade head` then uvicorn on startup |

### Required Environment Variables

```bash
# Backend (.env at apps/api/.env)
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/attreq
SECRET_KEY=                       # min 32 chars, JWT signing
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=15
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7
GROQ_API_KEY=                     # primary AI classifier (Llama 4 Scout vision)
GEMINI_API_KEY=                   # batch classifier (dormant in prod pipeline)
OPENWEATHER_API_KEY=              # weather for recommendations
REDIS_HOST=redis
REDIS_PORT=6379
WEAVIATE_HOST=weaviate
WEAVIATE_PORT=8080
GOOGLE_CLIENT_ID=                 # Phase 2 OAuth (not wired yet)
GOOGLE_CLIENT_SECRET=             # Phase 2 OAuth (not wired yet)

# Mobile (apps/mobile/.env)
EXPO_PUBLIC_API_URL=http://<host>:8000
```

### File Storage

Local disk at `apps/api/uploads/`, three subdirectories:

```
uploads/
  originals/     Raw user-uploaded images
  processed/     Background-removed images (rembg)
  thumbnails/    300px thumbnails (Pillow)
```

Served as static files via FastAPI: `GET /uploads/{path}`.

### Common Dev Commands

```bash
make compose-up          # Full API stack
make compose-local-up    # DB/cache only (pair with make dev-api for hot reload)
make compose-down
make dev-api             # FastAPI with hot reload on port 8000
make dev-mobile          # Expo dev server
make migrate             # Alembic upgrade head
make test                # pytest suite
make lint                # Ruff + next lint
```

---

## 9. Key File Index

| File | Purpose |
|---|---|
| `apps/api/src/attreq_api/main.py` | FastAPI app factory, lifespan (DB/Redis/Weaviate startup) |
| `apps/api/src/attreq_api/api/v1/api.py` | Router aggregator |
| `apps/api/src/attreq_api/api/v1/deps.py` | DI: DB session + current user resolver |
| `apps/api/src/attreq_api/config/settings.py` | All env var config (Pydantic) |
| `apps/api/src/attreq_api/config/security.py` | JWT + bcrypt |
| `apps/api/src/attreq_api/models/` | SQLAlchemy ORM models |
| `apps/api/src/attreq_api/schemas/` | Pydantic request/response shapes |
| `apps/api/src/attreq_api/crud/` | Async CRUD operations |
| `apps/api/src/attreq_api/workers/image_processor.py` | Single-image processing background task |
| `apps/api/src/attreq_api/workers/batch_image_processor.py` | Batch processing |
| `apps/api/src/attreq_api/services/ai/groq_classifier.py` | Groq/Llama vision classifier |
| `apps/api/src/attreq_api/services/ai/gemini_classifier.py` | Gemini batch classifier |
| `apps/api/src/attreq_api/services/ai/embeddings.py` | Weaviate client + vector ops |
| `apps/api/src/attreq_api/services/ai/background_removal.py` | rembg wrapper |
| `apps/api/src/attreq_api/services/recommendation/algorithm.py` | Outfit scoring and selection |
| `apps/api/src/attreq_api/services/cache/redis_client.py` | Redis wrapper |
| `apps/api/src/attreq_api/integrations/external/weather_api.py` | OpenWeatherMap client |
| `apps/api/.env.example` | Env var template |
| `apps/api/alembic.ini` | Alembic config |
| `apps/mobile/app/` | Expo Router route files |
| `apps/mobile/src/features/` | Screen-level feature components |
| `apps/mobile/src/lib/api/client.ts` | Axios instance with auth interceptors |
| `apps/mobile/src/lib/api/types.ts` | Shared TypeScript API types |
| `apps/mobile/src/lib/query/` | TanStack Query hooks |
| `apps/mobile/src/store/auth-store.ts` | Zustand auth state |
| `apps/mobile/src/components/attreq/editorial.tsx` | Custom UI component library |
| `apps/mobile/src/theme/colors.ts` | Design system color tokens |
| `infra/docker/compose.api.yml` | Full dev docker-compose |
| `AGENTS.md` | Developer guide (commands, architecture reference) |
| `docs/` | Canonical product and implementation documentation |

---

## 10. Current Status Snapshot (as of 2026-05-02)

- Mobile app is primary client, actively developed
- Backend fully functional: auth, wardrobe CRUD, AI classification, recommendations
- Groq (Llama 4 Scout) is live classifier; Gemini exists but is dormant in the upload pipeline
- Weaviate vector DB integrated for semantic item search (embeddings in place)
- Web app (`apps/web`) is legacy secondary client
- Google OAuth (Phase 2) env vars exist but are not wired in code
- File storage is local disk (not cloud storage) — suitable for dev, would need swap for prod scale
- Daily reminders via `expo-notifications` implemented in profile screen
