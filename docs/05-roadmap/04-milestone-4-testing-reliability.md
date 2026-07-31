# Milestone 4 — Testing & Reliability Hardening

> **Goal:** Automated confidence on the flows beta testers will exercise, plus recoverability for the single-VPS stack: real mobile tests in CI, expanded backend coverage, nightly backups with a rehearsed restore, uptime monitoring.
> **Depends on:** Milestone 3 (tests should cover the final algorithm/contract shape)
> **Status:** Not started

## Context (self-contained)

- **Backend tests**: `apps/api/tests/test_client_contracts.py` (+`conftest.py`) — contract assertions for auth/outfits/recommendations, expanded in M2/M3. No coverage of: refresh-token rotation, upload pipeline, full recommendation flow against a seeded DB.
- **Mobile tests**: infrastructure exists (`jest-expo`, `@testing-library/react-native`, `apps/mobile/jest.config.js`, `jest.setup.ts`) but **zero real tests** — CI runs `npm test -- --passWithNoTests` (`.github/workflows/mobile-ci.yml:35`).
- **Mobile architecture** (what to test): Axios API client with refresh interceptor, Zod response schemas, Zustand auth store (tokens in `expo-secure-store`), TanStack Query hooks, Expo Router screens under `apps/mobile/app/` (`(auth)`, `(onboarding)`, `(protected)/(tabs)`).
- **Ops**: Single VPS runs `infra/docker/compose.api.prod.yml` (Postgres 15, Redis, Weaviate with `backup-filesystem` module + `weaviate_backups` volume — enabled in M1, scheduling pending; images already durable in Cloudflare R2 from M1). No backups, no monitoring, no restore procedure today.
- `docs/api-contract.md` (M2) documents exact response shapes — mobile fixture payloads must be copied from it.

## Decisions (pre-made)

- **Defer Maestro/E2E automation.** For a solo developer the ROI is poor right now; instead a written **manual smoke checklist** (below) runs before every tester build. Revisit post-launch.
- **Backups go to a separate R2 bucket** (not the images bucket) via `rclone`, 14-day retention, driven by VPS cron — no extra services.
- **UptimeRobot free tier** (or equivalent) for `/health` monitoring — zero infra.

## Tasks

### 4.1 Backend test expansion (`apps/api/tests/`)

Add, building on existing `conftest.py` fixtures (CI already provisions Postgres 15):

1. **Auth lifecycle**: register → login → authenticated call → refresh (assert rotation semantics match `docs/api-contract.md`) → expired/garbage token → 401; refresh-with-revoked/expired refresh token → 401.
2. **Upload pipeline**: `POST` wardrobe upload with the **storage backend mocked** (the `get_storage()` factory from M1 makes this injectable) and the **classifier factory mocked** (`services/ai/classifier_factory.py`) returning a fixed classification → assert item row, normalized category, processing status transitions.
3. **Recommendation E2E**: seed a synthetic wardrobe via fixtures, mock weather + Weaviate, call `GET /api/v1/recommendations/daily` → assert complete outfit shape (top/bottom/footwear, outerwear gating from M3) and scoring fields.
4. **Taxonomy**: `normalize_category` synonym corpus + slot fallback + unknown logging (if not already done in M2).
5. **Geocoding chain**: request lat/lon beats saved; saved beats city-geocode (mock OpenWeather geo response, assert Redis cache write); total failure → `weather_unavailable: true`.

### 4.2 Mobile test suite (`apps/mobile/`)

Infrastructure is ready — this task is *writing tests*:

1. **API client + refresh interceptor** (highest value — historically the fragile contract): mock Axios adapter; assert 401 → single refresh → retry-once → logout-on-refresh-failure, per `docs/api-contract.md`.
2. **Zod schemas vs contract fixtures**: copy real JSON payloads from `docs/api-contract.md` into `apps/mobile/src/**/__fixtures__/`; assert every Zod response schema parses its fixture. This is the cheap cross-stack contract test — when the backend contract tests and these fixtures agree, the stacks agree.
3. **Zustand auth store**: login/logout/restore-from-SecureStore transitions (mock `expo-secure-store`).
4. **Render tests** (RNTL): sign-in screen (validation + submit), wardrobe grid (loading/empty/populated states), recommendation card (full outfit incl. footwear/outerwear, null slots, `weather_unavailable` banner, error state).
5. **CI gate**: in `.github/workflows/mobile-ci.yml` line 35, change `npm test -- --passWithNoTests` → `npm test`. CI now fails if tests vanish.

### 4.3 Backups, restore, monitoring (VPS)

1. **Postgres**: nightly cron — `docker exec attreq_postgres_prod pg_dump -U $POSTGRES_USER $POSTGRES_DB | gzip` → `rclone copy` to R2 bucket `attreq-backups/postgres/` with date-stamped filenames; prune > 14 days (`rclone delete --min-age 14d`).
2. **Weaviate**: nightly cron — `curl -X POST http://localhost:<weaviate-port>/v1/backups/filesystem` (backup-filesystem module enabled in M1), then `rclone sync` the `weaviate_backups` volume path to `attreq-backups/weaviate/`.
3. **New `docs/restore.md`**: exact commands to restore both stores into a scratch compose project, and how to promote it. **Rehearse the restore once for real** and record the commands actually used — an unrehearsed backup is a hope, not a plan.
4. **Monitoring**: UptimeRobot HTTPS monitor on `https://api.<domain>/health`, 5-min interval, email/push alert.
5. **Manual smoke checklist** — write into `docs/restore.md`'s sibling section or `docs/mobile-release.md` (M5); run before every tester build:
   1. Fresh install, register new account
   2. Login, kill app, reopen → session restored
   3. Onboarding + Style DNA photo upload completes
   4. Camera upload of one item → classification lands with sane category
   5. Gallery batch upload (3+ items) → all process
   6. Dashboard shows daily recommendation with footwear (and outerwear if cold)
   7. Accept/wear an outfit → appears in history
   8. Dismiss → next suggestion loads
   9. Location off → `weather_unavailable` banner, recommendations still render
   10. Images render on LTE (presigned URLs), notification fires

## Out of scope

- Maestro/Detox E2E automation (explicitly deferred). Load testing. `apps/web` tests (legacy). Multi-region/HA — single VPS by design.

## Exit criteria

- Mobile CI runs real tests with `--passWithNoTests` removed; backend CI covers auth lifecycle, upload, recommendation E2E, taxonomy, geocoding.
- Nightly Postgres + Weaviate backups land in R2; a restore has been **rehearsed once** and documented in `docs/restore.md`.
- `/health` is monitored; killing the backend container triggers an alert.

## Verification

```bash
cd apps/api && PYTHONPATH=src ../../.venv/bin/pytest            # all suites green
cd apps/mobile && npm run typecheck && npm test                  # real tests, no --passWithNoTests
```

- Push a PR → both CI workflows green with the new gates.
- On the VPS: run both backup crons manually once → objects appear in `attreq-backups/`; follow `docs/restore.md` into a scratch compose project → app boots with restored data.
- `docker stop attreq_backend_prod` → UptimeRobot alert arrives → `docker start`.
