# ATTREQ — Missing Links & Open Problems

> Comprehensive reference covering all unresolved gaps across Architecture, Backend, Infrastructure, and Operations. Compiled from codebase analysis as of 2026-05-02.

***

## 1. Architectural Missing Links

### 1.1 Local Disk File Storage in Production

All uploaded images are written to `apps/api/uploads/` on the local filesystem, organised into three subdirectories: `originals/`, `processed/`, and `thumbnails/`. This works for a single-developer local setup but is fundamentally broken as a production architecture for three reasons:

- **Horizontal scaling is impossible.** If two API containers are running behind a load balancer, a file written by Container A is invisible to Container B.
- **No durability.** A container restart, volume unmount, or infrastructure migration wipes all user images permanently.
- **No CDN or access control.** Images are served as raw FastAPI static files via `GET /uploads/{path}`, meaning no signed URLs, no expiry, no geo-distribution, and no protection against direct enumeration.

**What needs to happen:** Replace `FileStorageService` with a cloud blob storage backend (AWS S3, GCS, or Cloudflare R2). The service interface already exists in `apps/api/src/attreq_api/services/storage/file_storage.py`, so this is a contained swap. Presigned URLs should replace the current direct static-file serving pattern.

***

### ~~1.2 Gemini Classifier is Dead Code in Production~~ ✅ RESOLVED (2026-05-02)

`gemini_classifier.py` deleted. The file was never imported anywhere and referenced non-existent settings fields — it would have crashed at instantiation. `GEMINI_API_KEY` removed from `.env.example`. Live classifier remains Groq (Llama 4 Scout) via `clothing_detection.py`.

***

### 1.3 No Outfit Completeness — Shoes, Outerwear, Layers

The `outfits` database table only models `top_item_id` and `bottom_item_id` as first-class foreign keys. The `accessory_ids` field is an unscored UUID array that accessories are randomly appended to, not matched into. There is no slot for footwear, outerwear (jackets, coats), or layering pieces.

This is a significant product gap because:
- A user in a cold-weather context receiving a recommendation with no coat suggestion is receiving an incomplete, unusable outfit.
- The scoring algorithm (`0.4 × color_harmony + 0.4 × formality + 0.2 × preference`) runs only on top/bottom pairs — accessories don't influence or get influenced by the score.
- Shoes are arguably the hardest piece to coordinate and the one users most want help with.

**What needs to happen:** The `outfits` schema needs `footwear_item_id`, `outerwear_item_id`, and the scoring algorithm needs to incorporate these slots. The `wardrobe_items` category taxonomy needs to cleanly distinguish these types.

***

### 1.4 Google OAuth is a Ghost Feature

The `users` table has `oauth_provider` and `oauth_id` columns. The `.env.example` documents `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET`. The `settings.py` likely loads these. But there is zero wired code — no OAuth endpoint, no redirect handler, no token exchange. Any user flow that attempts "Sign in with Google" would receive a 404 or silent failure.

**What needs to happen:** Either implement it end-to-end (auth endpoint + mobile deep-link callback) or strip the dead columns and env vars until Phase 2 is actually planned. Ghost features confuse new contributors and create false product impressions.

***

### 1.5 Clothing Category Normalization

The `category` field on `wardrobe_items` is a free-text `VARCHAR`. The AI classifier produces natural language labels ("t-shirt", "tshirt", "Tee Shirt", "short sleeve top"). There is no canonicalization layer, enum validation, or controlled vocabulary enforcement anywhere in the pipeline.

This is not a cosmetic issue — it breaks:
- **Filtering**: `filter_items_by_occasion()` and `filter_items_by_weather()` in `algorithm.py` rely on matching category strings.
- **Formality scoring**: The scoring algorithm uses "category-based formality tiers", which only works if categories are consistent strings.
- **UI grouping**: The wardrobe grid groups items by category — a user could see "t-shirt" and "Tshirt" as two separate categories.

**What needs to happen:** Define a controlled vocabulary enum (e.g. `tops.tshirt`, `tops.shirt`, `bottoms.jeans`), normalize AI classifier output through a mapping layer, and add a Pydantic validator that rejects or corrects unknown categories.

***

## 2. Backend Missing Links

### ~~2.1 Incomplete Alembic Migration Coverage~~ ✅ RESOLVED (2026-05-02)

Migration `c4e5f6a7b8c9` added — creates `wardrobe_items` and `outfits` tables with all indexes and foreign keys. Previously, migration `b1c2d3e4f5a6` (add `classification_source`) pointed directly to the location-fields migration, meaning `alembic upgrade head` on a fresh database would crash trying to ALTER a non-existent `wardrobe_items` table. Chain is now correct:

```
5a522e143506 (users) → 3a686a89c4c2 (user location) → c4e5f6a7b8c9 (wardrobe_items + outfits) → b1c2d3e4f5a6 (classification_source)
```

`alembic check` is also now a step in the backend CI workflow, so future drift is caught automatically on every PR.

***

### 2.2 Unstable Backend ↔ Mobile Contract

The auth contract (login response shape, refresh token request format), the recommendation-card-to-outfit materialization mapping, and the location update inputs are all noted as ambiguous between backend and mobile client. This means the mobile app's Axios interceptors and TanStack Query hooks may be making assumptions the backend doesn't honour.

**What needs to happen:** Write an explicit API contract document (or OpenAPI annotation) for: login/refresh response shapes, the exact flow for converting a recommendation into a persisted outfit via `POST /outfits/`, and the lat/lon precision and fallback expectations.

***

### 2.3 Placeholder Geocoding

Location handling uses a stub — there is no real geocoding provider wired in. The recommendation endpoint accepts `?lat=&lon=` but if a user hasn't set their location and the mobile app fails to get GPS permission, there is no fallback geocoding from city name or IP address.

**What needs to happen:** Integrate a real geocoding provider (Google Maps Geocoding API or Mapbox) and define a clear fallback chain: GPS coordinates → saved lat/lon → city-name geocoding → graceful error state.

***

## 3. Infrastructure & Ops Missing Links

### 3.1 No Mobile Release / Distribution Pipeline

There are no EAS build profiles, no internal distribution configuration, and no documented path from local development to TestFlight or Google Play internal testing. This means the mobile app exists as code that cannot currently reach real users through any reproducible process.

**What needs to happen:**
- Define EAS build profiles: `development`, `preview` (internal distribution), `production`.
- Document the environment variable and secret injection strategy for each profile.
- Set up an `eas.json` at `apps/mobile/eas.json`.
- Document the TestFlight and Play Store internal track submission process.

***

### ~~3.2 No CI/CD Pipeline~~ ✅ RESOLVED (2026-05-02)

GitHub Actions workflows added:

- `.github/workflows/backend-ci.yml` — runs on PRs touching `apps/api/`. Sets up Python 3.11 with a real Postgres service container, runs ruff lint, `alembic upgrade head`, `alembic check`, and pytest.
- `.github/workflows/mobile-ci.yml` — runs on PRs touching `apps/mobile/`. Sets up Node 20, installs from root workspace, runs `tsc --noEmit` and jest.

EAS build trigger on merge to `main` remains optional/future.

***

### 3.3 No Error Tracking or Monitoring ⚠️ PARTIALLY RESOLVED (2026-05-02)

**Done (backend):** `sentry-sdk[fastapi]>=2.0.0` added to requirements. `SENTRY_DSN` setting added to `settings.py` and `.env.example`. Sentry initialised in `main.py` guarded by `if settings.sentry_dsn` — no-ops in dev, activates when env var is set. Background tasks capture automatically once SDK is initialised.

**Still needed:**
- Add `@sentry/react-native` to the mobile app and initialise it in `apps/mobile/src/` entry point.
- Add `SENTRY_DSN` to the mobile build environment (EAS secrets or `.env`).

***

### 3.4 Weaviate Has No Backup Strategy ⚠️ PARTIALLY RESOLVED (2026-05-02)

**Done:** `backup-filesystem` module enabled in `infra/docker/compose.api.yml`. `BACKUP_FILESYSTEM_PATH` set to `/var/lib/weaviate/backups`. Dedicated `weaviate_backups` Docker volume mounted. Backup API now available at `POST /v1/backups/filesystem`.

**Still needed:**
- Schedule periodic backup jobs (cron or `docker exec` script calling the backup API).
- Document the restore procedure (`POST /v1/backups/filesystem/{backup_id}/restore`).
- Consider `backup-s3` module as alternative for off-host durability.

***

### 3.5 Production Compose is Undocumented

`infra/docker/compose.api.prod.yml` exists but there are no deployment docs, no secrets management strategy, no reverse proxy configuration (nginx/Caddy), and no SSL/TLS setup described anywhere. "Production" currently means running the same Docker stack on a server, which is not a hardened deployment.

**What needs to happen:**
- Write `docs/deployment.md` covering: server requirements, secrets injection (Docker secrets or env file), reverse proxy setup with SSL termination, and health check configuration.
- Define a secrets management approach (Doppler, AWS Secrets Manager, or `.env` with strict access controls).

***

## 4. Product Roadmap Items Without Implementation Plans

These are features mentioned in product vision docs that have no tickets, no schema design, and no implementation stubs:

| Feature | Current State | What's Needed |
|---|---|---|
| Style DNA / preference learning | ✅ Implemented (2026-05-02) — dual-purpose LLM extraction, synthesis, 40% scoring weight, behaviour weights updated from feedback | — |
| Advanced onboarding | ✅ Implemented (2026-05-02) — `(onboarding)/` route group, upload → results → review flow, wardrobe seeded from seed photos | — |
| Shopping / affiliate integration | Not mentioned anywhere in code | Partner API research, affiliate link model, UI surface |
| Social / sharing features | Explicitly out of scope for current version | Future ticket definition |
| Broader outfit history analytics | Basic history screen exists | Trends view, wear frequency charts, cost-per-wear tracking |

***

## 5. Summary Priority Matrix

| Gap | Impact | Effort | Priority | Status |
|---|---|---|---|---|
| Cloud file storage | 🔴 Critical | Medium | P0 | Open |
| Alembic migration coverage | 🔴 Critical | Low | P0 | ✅ Done |
| Clothing category normalization | 🔴 Critical | Medium | P0 | Open |
| Backend ↔ mobile contract | 🟠 High | Low | P0 | Open |
| Mobile release pipeline (EAS) | 🟠 High | Medium | P0 | Open |
| Error tracking (Sentry) | 🟠 High | Low | P1 | ⚠️ Backend only |
| CI/CD pipeline | 🟠 High | Medium | P1 | ✅ Done |
| Geocoding (real provider) | 🟡 Medium | Low | P1 | Open |
| Outfit completeness (shoes, outerwear) | 🟡 Medium | High | P2 | Open |
| Weaviate backup strategy | 🟡 Medium | Low | P1 | ⚠️ Module enabled, scheduling pending |
| Google OAuth implementation | 🟡 Medium | High | P2 | Open |
| Dead Gemini classifier cleanup | 🟢 Low | Low | P2 | ✅ Done |
| Production deployment docs | 🟠 High | Low | P1 | Open |
| Style DNA / preference learning | 🟡 Medium | Very High | P3 | ✅ Done |
| Onboarding flow | 🟡 Medium | Medium | P2 | ✅ Done |
