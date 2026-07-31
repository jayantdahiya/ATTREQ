# Milestone 1 — Production Backend Live on VPS

> **Goal:** ATTREQ API running at `https://api.<domain>` on a single VPS via Docker Compose, with wardrobe images in Cloudflare R2 and Sentry receiving real errors.
> **Depends on:** nothing (first milestone)
> **Status:** Not started

## Context (self-contained — read this even if you know the repo)

- Backend: FastAPI app at `apps/api/src/attreq_api/` (async SQLAlchemy 2, PostgreSQL 15, Redis 7, Weaviate for embeddings, Alembic migrations). Runs as a Python package; entry `attreq_api.main:app`.
- Image storage today is **local disk only**: `apps/api/src/attreq_api/services/storage/file_handler.py` defines `FileStorageService` writing under `settings.upload_dir` (`apps/api/uploads/` with `originals/`, `processed/`, `thumbnails/`, `style-dna/` subdirs) and exposes a **module-level singleton** `file_storage` (line 247). This breaks production: no durability, no horizontal scaling, images die with the container/disk.
- The singleton is imported in exactly these places (update all of them):
  - `apps/api/src/attreq_api/api/v1/endpoints/wardrobe.py`
  - `apps/api/src/attreq_api/workers/image_processor.py`
  - `apps/api/src/attreq_api/workers/batch_image_processor.py`
  - `apps/api/src/attreq_api/services/style_dna/style_dna_service.py`
- `infra/docker/compose.api.prod.yml` is **broken as written** (verified 2026-06-10):
  - No `weaviate` service at all (the dev stack `infra/docker/compose.api.yml` has one) → embeddings/vector search would fail in prod.
  - Injects env vars for **deleted features**: `GEMINI_API_KEY`, `GEMINI_MODEL_NAME`, `GEMINI_BATCH_SIZE` (Gemini classifier was removed; Groq is the live default) and `GOOGLE_CLIENT_ID/SECRET/REDIRECT_URI` (OAuth was never wired).
  - Missing env vars the app actually needs: `GROQ_API_KEY`, `GROQ_MODEL_NAME`, `CLASSIFIER_PROVIDER`, `SENTRY_DSN`, `REDIS_URL` (and Redis service has no URL wiring to backend), `WEAVIATE_URL`.
  - Publishes `8000:8000` directly with no TLS; uses `sleep 10` in the start command despite already having `depends_on: postgres: condition: service_healthy`.
- Settings live in `apps/api/src/attreq_api/config/settings.py` (Pydantic settings with env aliases; `sentry_dsn` already exists at line ~94). Sentry SDK is already integrated on the backend, guarded by `SENTRY_DSN`.
- Classifier: Groq Llama 4 Scout default via `services/ai/classifier_factory.py` (`CLASSIFIER_PROVIDER` selects groq/claude/openai).

## Decisions (pre-made — do not re-litigate)

- **Cloudflare R2, not MinIO.** MinIO-on-VPS keeps images on the same single disk we're trying to protect; R2 gives high durability, S3-compatible API, **zero egress fees** (image-heavy app), 10 GB free tier.
- **Private bucket + presigned GET URLs (24 h expiry)** generated at response-serialization time. These are personal photos — never a public bucket.
- **Store object keys, not URLs, in the DB.** The existing `original_image_url` / `processed_image_url` / `thumbnail_url` columns hold object keys (e.g. `originals/{user_id}_{uuid}.jpg`) when `STORAGE_BACKEND=s3`, or `/uploads/...` paths when `local`.
- **Caddy, not nginx**, as reverse proxy: ~2-line Caddyfile, automatic Let's Encrypt.
- **No data migration**: prod deploys fresh; existing dev uploads are discarded or re-uploaded.

## Tasks

### 1.1 Storage abstraction + R2 backend

1. **New** `apps/api/src/attreq_api/services/storage/base.py` — a `StorageBackend` `Protocol` mirroring the current `FileStorageService` surface:
   - `async save_upload_file(file: UploadFile, user_id, subdirectory) -> tuple[str, str]` — returns `(object_key, url_or_key)`
   - `save_image_from_bytes(image_bytes, user_id, subdirectory, extension) -> tuple[str, str]`
   - `generate_thumbnail(...)` — **refactor to bytes-based**: current implementation (`file_handler.py:152-199`) opens a disk path with PIL; change the shared signature to accept `image_bytes: bytes` and return thumbnail bytes + key, so both backends reuse one PIL resize helper (extract the RGBA→RGB + `thumbnail((size,size), LANCZOS)` logic into a pure function in `base.py`).
   - `delete_file(key_or_path) -> bool`
   - `get_file_url(key_or_path) -> str`
2. **New** `apps/api/src/attreq_api/services/storage/s3_storage.py` — `S3StorageService` implementing the protocol with `aioboto3` (add `aioboto3` to `apps/api/requirements.txt`):
   - Client configured from settings: `S3_ENDPOINT_URL` (R2 endpoint `https://<account_id>.r2.cloudflarestorage.com`), `S3_BUCKET`, `S3_ACCESS_KEY_ID`, `S3_SECRET_ACCESS_KEY`, `region_name="auto"`.
   - Keys follow existing layout: `{subdirectory}/{user_id}_{uuid4}.{ext}` (reuse the filename logic from `file_handler.py:38-49`).
   - `get_file_url(key)` returns a **presigned GET URL, 24 h expiry** (`generate_presigned_url("get_object", ExpiresIn=86400)`).
3. **Keep** `file_handler.py` as the `local` backend (it already conforms once `generate_thumbnail` is adapted; its `get_file_url` keeps returning `/uploads/...`).
4. **Factory** in `apps/api/src/attreq_api/services/storage/__init__.py`: `get_storage() -> StorageBackend` selected by new setting `STORAGE_BACKEND` (`local` default | `s3`). Replace the `file_storage` singleton import in the 4 call sites listed in Context with `get_storage()`.
5. **Settings** (`config/settings.py`): add `storage_backend` (alias `STORAGE_BACKEND`, default `"local"`), `s3_endpoint_url`, `s3_bucket`, `s3_access_key_id`, `s3_secret_access_key` (all `str | None`, aliases uppercase). Add to `apps/api/.env.example`.
6. **URL resolution at serialization**: wardrobe/recommendation/style-DNA response schemas currently pass through stored values (see `algorithm.py` outfit candidate dicts using `item.thumbnail_url` etc.). Add a small `resolve_image_url(value: str | None) -> str | None` helper (in `services/storage/__init__.py`) that presigns when `STORAGE_BACKEND=s3` and passes `/uploads/...` through for `local`; apply it wherever image URLs enter API responses (wardrobe endpoints, recommendation payload construction in `services/recommendation/algorithm.py`, style-DNA responses).

### 1.2 Fix `infra/docker/compose.api.prod.yml`

Mirror the dev stack `infra/docker/compose.api.yml` for service shape:

- **Add `weaviate` service** (same image/config as dev, including the `backup-filesystem` module and a `weaviate_backups` volume — M4 backups depend on this) and set `WEAVIATE_URL=http://weaviate:8080` on backend.
- **Remove** `GEMINI_API_KEY`, `GEMINI_MODEL_NAME`, `GEMINI_BATCH_SIZE`, `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `GOOGLE_REDIRECT_URI` from the backend environment block.
- **Add** to backend environment: `GROQ_API_KEY`, `GROQ_MODEL_NAME`, `CLASSIFIER_PROVIDER=groq`, `SENTRY_DSN`, `REDIS_URL=redis://redis:6379/0`, `STORAGE_BACKEND=s3`, `S3_ENDPOINT_URL`, `S3_BUCKET`, `S3_ACCESS_KEY_ID`, `S3_SECRET_ACCESS_KEY` (all `${VAR}` from `.env.prod`).
- **Add `caddy` service**: `caddy:2-alpine`, ports `80:80` + `443:443`, mounted `Caddyfile` (new file `infra/docker/Caddyfile`) reverse-proxying `api.<domain>` → `backend:8000`, volumes for `caddy_data`/`caddy_config`. **Remove `ports: "8000:8000"` from backend** — only Caddy is exposed.
- **Remove** the `sleep 10` from the backend command (`depends_on: condition: service_healthy` already handles readiness); keep `alembic upgrade head` before uvicorn.
- **Drop** the `uploads_data` volume and its mount (images now in R2).
- Add `restart: unless-stopped` + healthcheck to weaviate/caddy consistent with existing services.

### 1.3 Deployment runbook — new `docs/deployment.md`

Write a runbook covering, in order:

1. VPS prereqs: Docker + Compose plugin, firewall (only 22/80/443), DNS A record `api.<domain>` → VPS IP.
2. Cloudflare R2 setup: create bucket, create API token (Object Read & Write), note account-id endpoint.
3. Secrets: `.env.prod` on the VPS (`chmod 600`, never committed) listing every `${VAR}` referenced by `compose.api.prod.yml` with descriptions.
4. Deploy: `git pull && docker compose -f infra/docker/compose.api.prod.yml --env-file .env.prod up -d --build`. Note that migrations run on container start.
5. Rollback: `git checkout <previous-tag>` + same compose command; DB rollback via `alembic downgrade` only if a migration is at fault.
6. Smoke-test checklist (also used after every deploy): `curl https://api.<domain>/health`; register → login → upload item → poll classification → GET `/api/v1/recommendations/daily` from a phone on LTE; confirm image renders (presigned URL); trigger a deliberate 500 and confirm it appears in Sentry.

## Out of scope

- Category taxonomy, contract docs, geocoding (M2). Outfit slots (M3). Backups/monitoring (M4 — but the Weaviate backup *module* is enabled here so M4 can use it). EAS/mobile distribution (M5).
- Multi-server scaling, CDN, managed Postgres — single VPS is the explicit target.

## Exit criteria

- A phone on LTE (not the dev LAN) completes **signup → wardrobe upload → AI classification → daily recommendation** against `https://api.<domain>`, with images rendering via presigned R2 URLs.
- A forced exception shows up in Sentry.

## Verification

```bash
# Local, before deploy (storage factory works in both modes)
cd apps/api && PYTHONPATH=src ../../.venv/bin/pytest          # CI uses STORAGE_BACKEND=local default
ruff check src

# Config sanity
docker compose -f infra/docker/compose.api.yml config -q
docker compose -f infra/docker/compose.api.prod.yml --env-file .env.prod config -q

# On VPS
docker compose -f infra/docker/compose.api.prod.yml --env-file .env.prod up -d --build
curl -f https://api.<domain>/health
# then run the full smoke-test checklist from docs/deployment.md on a real device
```

Backend CI (`.github/workflows/backend-ci.yml`: ruff, alembic check, pytest) must stay green — local backend remains the default so tests need no R2 credentials.
