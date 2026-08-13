# ATTREQ Beta Readiness — Immediate Execution Tracker

> **Status:** Active — next work to execute
> **Last audited:** 2026-08-14
> **Goal:** Run an invite-only Android beta against the Raspberry Pi backend through a stable Cloudflare hostname, then publish every beta APK as a traceable GitHub prerelease.
> **Audience:** An LLM or developer should be able to execute this tracker without prior chat history.

## Outcome

This phase is complete when a tester can install a release-signed APK from GitHub Releases and complete this flow over mobile data:

`register → onboarding → upload photos → AI classification → daily recommendation → feedback/wear → history`

The APK must call the Raspberry Pi backend through HTTPS, not the development backend on the Mac. The backend must survive restarts, keep its database on the Pi's SSD, keep user images in durable object storage, and have a tested backup/restore path.

## Current Verified Truth

These facts were checked against the repository and machines on 2026-08-14. Code wins if any fact later becomes stale.

### Repository and quality baseline

- The beta-readiness implementation and Android release work are merged directly into and pushed on `main`.
- Recommendation Intelligence RI-1 through RI-7 is merged into `main`, despite stale `Not started` headers in some individual milestone files.
- Backend verification passes when pointed at the ATTREQ PostgreSQL instance on host port `5433`: **409 tests passed** and Ruff passed.
- Android verification passes: TypeScript passes and **61 tests passed**.
- A clean-checkout signed release build succeeds for all four Android ABIs and creates a 68.8 MB APK.
- The permanent RSA-4096 ATTREQ upload key is stored outside Git, backed up off-machine, and its password is held in the macOS Keychain. Release builds fail closed when signing inputs are absent.
- `.github/workflows/mobile-ci.yml` builds only `assembleDebug`; it does not publish a release APK.
- GitHub already contains the development release/tag `v0.1.0-android`.
- GitHub prerelease [`v0.2.0-beta.1`](https://github.com/jayantdahiya/ATTREQ/releases/tag/v0.2.0-beta.1) contains the release-signed APK and its SHA-256 checksum from tagged commit `9e49837a81fbf714dccbe27737095dd02cf9708a`.

### Preserve the existing working tree

At audit time, four tracked files contained an unfinished reliability patch:

- `apps/api/src/attreq_api/api/v1/endpoints/recommendations.py`
- `apps/api/src/attreq_api/services/ai/groq_classifier.py`
- `apps/api/src/attreq_api/services/style_dna/style_dna_service.py`
- `apps/mobile/src/lib/api/style-dna.ts`

The patch adds saved-city weather fallback, Groq retry/backoff and reasoning-model handling, clearer Style DNA provider failures, request staggering, and a longer mobile Style DNA timeout. It has now been reviewed, completed, and directly tested under BR-01; its origin as preserved user work remains recorded here so a future agent does not accidentally separate or discard it.

There are also unrelated untracked paths. Do not stage them with a blanket `git add .`; stage only files intentionally belonging to the current unit of work.

### Raspberry Pi baseline

- Host alias: `raspberry-pi`
- Hardware: Raspberry Pi 5 Model B, ARM64, 4 cores, 8 GB RAM
- OS: Ubuntu, ARM64
- System disk: approximately 59 GB microSD
- Data disk: approximately 233 GB ext4 mounted at `/mnt/storage`
- Network: wired Ethernet
- Docker Engine 29.7.2 and Docker Compose 5.4.0 are installed from Docker's official Ubuntu repository. The repository is cloned at `/opt/attreq`; optional-component benchmarking is in progress before the production stack starts.

The Pi is suitable for a small invite-only beta. Put PostgreSQL data and backups on `/mnt/storage`, not the microSD card.

### Domain and tunnel baseline

- `https://dev-server-1.online/health` currently returns HTTP 200 through Cloudflare.
- It currently routes to the **Mac development backend**, and the response reports `"environment":"development"`.
- `apps/mobile/src/lib/utils/env.ts` hard-codes `https://dev-server-1.online/api/v1`.
- The beta must either migrate `dev-server-1.online` to a named tunnel on the Pi or use a new hostname such as `api.<owned-domain>`.
- Do not open or forward the backend port on the home router. Cloudflare Tunnel should make an outbound connection from the Pi and route directly to the backend service.

## Target Architecture

```mermaid
flowchart LR
    A["Android beta APK"] -->|"HTTPS api.<domain>"| C["Cloudflare edge"]
    C -->|"Named outbound tunnel"| T["cloudflared on Raspberry Pi"]
    T --> B["FastAPI backend"]
    B --> P["PostgreSQL on /mnt/storage"]
    B --> R["Redis"]
    B --> O["Cloudflare R2 private bucket"]
    B --> G["Groq classifier / optional reranker"]
    B --> W["OpenWeather"]
    B --> S["Sentry"]
    B -. "feature-gated evaluation" .-> V["Weaviate / FashionCLIP"]
```

## Decisions Required From the User

Do not invent these values or place credentials in documentation:

The user resolved the original decisions on 2026-08-14: retain and migrate `dev-server-1.online`, use private Cloudflare R2, publish the Android beta in the public repository, and authorize the Pi installation under `/mnt/storage/attreq`. The permanent Android key is backed up outside the repository.

Remaining user-only acceptance is a physical Android smoke test over mobile data after the Pi cutover. No infrastructure secret needs to be pasted into chat.

Never ask the user to paste API keys, tunnel tokens, database passwords, or keystore passwords into chat or commit them to Git. Use configured secret stores, local environment files with mode `0600`, or GitHub Actions secrets.

## Execution Order

The ten work packages below are the known immediate beta-readiness scope. Finish them in order unless a dependency explicitly permits parallel work.

| ID | Work package | Depends on | Status |
|---|---|---|---|
| BR-01 | Finish and test the reliability patch | — | Complete; pushed on `main` |
| BR-02 | Make Android location UX honest | BR-01 | Complete; pushed on `main` |
| BR-03 | Add protection for public, costly endpoints | — | Application limiter complete; edge rule remains part of BR-06 |
| BR-04 | Benchmark optional AI/vector components on the Pi and record the decision | — | Three local components measured; reranker awaits credential rotation/retest |
| BR-05 | Build the Pi-specific production stack | BR-03, BR-04 | Docker/repository ready; stack waits for Groq key rotation and final flags |
| BR-06 | Move the Cloudflare hostname/tunnel to the Pi | BR-05 | Dedicated `attreq-pi-beta` tunnel created; DNS cutover waits for Pi health |
| BR-07 | Wire R2, persistence, backup, restore, and monitoring | BR-05 | Existing private R2 create/read/delete probe passed; live storage/backup/monitoring checks remain |
| BR-08 | Configure durable Android signing, versioning, and API URL selection | BR-06 | Complete; release URL stays stable across the pending hostname cutover |
| BR-09 | Publish the beta APK through GitHub Releases | BR-08 | Complete; public prerelease `v0.2.0-beta.1` published |
| BR-10 | Run the remote-device beta gate and close the milestone | BR-06, BR-07, BR-09 | Not started |

## Implementation Progress — 2026-08-14

The code wave is pushed; the release is published; the live Pi/R2/tunnel wave is active.

- **BR-01:** saved-city weather fallback now serves both daily suggestions and the swipe deck; Groq calls have bounded retries for 429/502/503/504, capped backoff, and a narrowly gated Qwen reasoning setting; Style DNA distinguishes unusable photos from HTTP, transport, malformed-output, and deployment failures; mobile Style DNA build calls use a 180-second timeout. Direct backend and mobile regression tests were added.
- **BR-02:** registration no longer advertises a device-location action that deterministically fails. Manual city entry is the supported beta path and its registration payload is tested.
- **BR-03:** a reusable Redis/Lua fixed-window limiter now protects shared auth, wardrobe-image, Style-DNA-build, and explicit recommendation-refresh budgets. Batch uploads charge by image count. It emits a stable `429` with `Retry-After`, hashes subjects in Redis keys, logs and fails open when Redis is unavailable, and trusts `CF-Connecting-IP`/`X-Forwarded-For` only when proxy trust is explicitly enabled and the immediate peer matches an allowlisted CIDR.
- **BR-04:** the reproducible harness, synthetic reranker cases, loopback-only benchmark Compose profiles, and [BR-04 runbook](02-br04-pi-benchmark-runbook.md) were exercised on the Pi. Native ARM64 FashionCLIP and manual-vector Weaviate passed; `text2vec-transformers` failed the sustained CPU gate. The run found and fixed the ARM64 NumPy/Torch ABI constraint, separate CLIP modality processing, and shallow-container harness parsing. Reranker measurement is paused until the Groq credential is rotated and retested.
- **BR-05:** the [Pi stack runbook](03-br05-pi-stack-runbook.md), production Compose, names-only env template, and safe operator script are ready. The minimal stack has PostgreSQL 15, Redis 7, one-shot migrations, FastAPI, and a pinned ARM64-capable `cloudflared`; it publishes no host ports and stores persistent bind data under `/mnt/storage/attreq`. Weaviate and `text2vec-transformers` remain independent profiles, while FashionCLIP and reranking remain independent flags. Docker/Compose are installed, `/opt/attreq` is at a reviewed commit, and production secrets are staged outside Git; the stack remains stopped until BR-04 finishes.
- **BR-06/BR-07:** the dedicated `attreq-pi-beta` named tunnel exists without changing live DNS. The existing private R2 bucket and scoped credentials passed a non-user-data create/read/delete probe; the probe object was deleted. The Pi's external mode-`0600` environment file contains generated production database/JWT values and the configured R2/provider values without exposing them in Git or chat.
- **BR-08/BR-09:** version code `2` / version `0.2.0-beta.1`, permanent external signing, release/development API separation, clean-build native compatibility, signer verification, checksum generation, tag, and GitHub prerelease are complete. The APK SHA-256 is `7920a34f1d2102bf83ec82c7119e466fc3268dcd780062764e1b5b51616ca487`.

Integrated local verification before repository commit:

- backend: 409 tests passed;
- backend Ruff: passed;
- mobile TypeScript: passed;
- mobile Jest: 12 suites / 61 tests passed;
- BR-04/BR-05: Python compilation, three-case reranker dry-run, two architecture-pin tests, both Docker Compose configurations (all optional profiles), shell syntax, pinned `cloudflared` registry/ARM64 manifest, and diff whitespace checks passed.

BR-01, BR-02, BR-08, and BR-09 are complete and pushed. BR-03's application layer is complete. BR-04 through BR-07 and the physical-device BR-10 acceptance gate remain open.

## BR-01 — Finish and Test the Reliability Patch

### Scope

1. Review the four modified files listed under **Preserve the existing working tree**.
2. Keep the intended behaviors:
   - explicit request coordinates win over saved coordinates;
   - saved coordinates win over saved city;
   - saved city calls `get_weather_by_city`;
   - a user with no location receives the existing clear 400 response;
   - Groq retries only retryable 429/502/503/504 responses with bounded backoff;
   - model-specific `reasoning_effort` is sent only to supported model families;
   - Style DNA distinguishes provider outages from unusable photos;
   - mobile upload/regenerate requests have sufficient timeout headroom.
3. Add direct regression tests. Existing broad tests passing is not enough because the new branches currently lack explicit coverage.
4. Run backend and mobile verification.
5. Commit only the intended patch and its tests on a feature branch; do not absorb unrelated untracked files.

### Required verification

```bash
cd apps/api
DATABASE_URL='postgresql+asyncpg://attreq_user:attreq_password@localhost:5433/attreq_db' \
  PYTHONPATH=src ../../.venv/bin/python -m pytest
../../.venv/bin/ruff check src tests

cd ../mobile
npm run typecheck
npm test -- --runInBand
```

### Exit criteria

- Every new fallback/retry/error branch has a focused test.
- The complete backend and Android suites pass.
- The patch is committed and pushed under the repository's milestone push policy.

## BR-02 — Make Android Location UX Honest

### Problem

`RegisterScreen` shows a **Use device location** action, while `src/lib/location/location.ts` deliberately throws that device location is unavailable. Manual city entry works and is enough for beta once BR-01's saved-city weather fallback ships.

### Beta decision

Do not leave an attractive control that always fails. For beta, either:

- implement and test native device location with runtime permission handling, reverse geocoding, denial states, and cancellation; or
- remove/disable the action and clearly make manual city entry the supported flow.

Default to the smaller honest flow—manual city—unless the user explicitly prioritizes native location for this beta.

### Files to inspect

- `apps/mobile/src/features/auth/RegisterScreen.tsx`
- `apps/mobile/src/lib/location/location.ts`
- `apps/mobile/src/features/profile/LocationEditModal.tsx`
- associated Android tests and `AndroidManifest.xml`

### Exit criteria

- No visible action deterministically fails by design.
- Registration and profile location editing feed a city that produces weather-aware recommendations.
- Permission denial is tested if native location is implemented.

## BR-03 — Protect Public and Costly Endpoints

### Problem

Cloudflare Tunnel removes the need for inbound port forwarding, but it does not make public endpoints private. ATTREQ currently lacks a general application-level limiter for login, registration, uploads, Style DNA builds, and force-refresh requests. Several of those paths can create paid third-party calls or CPU-heavy work.

### Scope

1. Add Cloudflare-side rate limiting where supported.
2. Add an application-side limiter for critical routes so protection does not depend entirely on account tier or proxy configuration.
3. Key authenticated limits by user ID and unauthenticated limits by trusted proxy client IP.
4. Ensure forwarded-client-IP trust is restricted to the Cloudflare/Tunnel deployment; never blindly trust arbitrary `X-Forwarded-For` on a directly exposed service.
5. Return stable `429` responses that the Android client can display.
6. Add tests for allowed requests, exceeded limits, and limiter-store failure behavior.

### Initial beta policy

Use conservative documented defaults and make them configurable:

- login/register: 10 attempts per minute per client IP;
- wardrobe uploads: 20 images per hour per authenticated user;
- Style DNA upload/regenerate: 5 builds per hour per authenticated user;
- recommendation force refresh: 20 per hour per authenticated user.

### Exit criteria

- Public endpoints cannot be used for an unbounded password-guessing or LLM-cost attack.
- Normal onboarding and beta testing do not trip the defaults.
- Limits and reset behavior are documented in the deployment runbook.

## BR-04 — Benchmark Optional AI and Vector Components on the Pi

### Purpose

Do not permanently disable FashionCLIP, Weaviate, the text-transformer container, or the optional LLM reranker based only on assumptions. Measure them on the actual Pi before choosing the beta topology.

The components are distinct and must be evaluated separately:

- **FashionCLIP inference:** local model load/inference, gated by `EMBEDDINGS_ENABLED`.
- **Weaviate vector storage:** local database and query overhead.
- **`text2vec-transformers`:** heavyweight local inference service used by the legacy `ClothingItem` collection.
- **LLM reranker:** remote Groq call, gated by `RERANKER_ENABLED`; Pi CPU impact is small, but latency, cost, provider limits, and ranking quality matter.

### Test protocol

1. First deploy the minimal API/PostgreSQL/Redis stack or run equivalent ARM64 containers without exposing it publicly.
2. Confirm every candidate image has an ARM64-compatible image/build path. An image that cannot run natively is a failed result; do not hide emulation cost.
3. Record idle RAM/CPU and startup time.
4. Enable one component at a time.
5. Use representative data and record:
   - cold model-load time;
   - steady-state RAM;
   - peak RAM;
   - single-image embedding latency;
   - five concurrent upload/embedding jobs;
   - Weaviate insert/query latency;
   - API health/recommendation latency while the job runs;
   - reranker p50/p95 latency, Groq errors/rate limits, and qualitative order improvement.
6. Reboot the Pi and repeat the chosen configuration to catch persistence/startup failures.
7. Save the measurements and decision in this file or a linked report under this folder.

### Decision gate

- Enable a component for beta only if it runs natively, stays within a planned memory ceiling, does not destabilize uploads/recommendations, and provides observable product value.
- Keep a feature flag off when the test fails. Do not delete the implementation.
- The LLM reranker may be enabled independently of FashionCLIP/transformer services.
- Never enable all components at once without the one-at-a-time results.

### Live results — 2026-08-14

| Component | Native ARM64 | Startup | Resource/latency result | Decision |
|---|---|---:|---|---|
| FashionCLIP | Yes | 57.587 s cold / 7.584 s warm | Valid normalized 512-d vectors; warm image p50/p95 374.5/385.5 ms; five-job wall 2.087 s; 427.5 MiB warm peak; 53.3% host CPU mean; 64.45°C peak; no OOM | **Pass; enable behind `EMBEDDINGS_ENABLED` with manual-vector Weaviate and monitor load** |
| Weaviate manual vectors | Yes | 12.170 s cold / 3.395 s warm | 47.3 MiB peak; 22.5% host CPU mean; 55.1°C peak; 200/200 inserts and 60/60 queries succeeded; warm query p95 1.98 ms | **Pass; enable only with manual FashionCLIP embeddings** |
| `text2vec-transformers` | Yes | 11.519 s cold / 6.600 s warm | 360.8 MiB observed; 384-d vectors; warm p95 50.8 ms, but confirmation load sustained 92.0% host CPU mean; 61.7°C peak | **Fail the <85% CPU gate; keep the `text2vec` profile disabled for beta** |
| Groq reranker | Remote | Pending | Provider test stopped before a valid result; rotate the credential and repeat the synthetic ranking/latency gate | **Keep disabled until a clean retest passes** |

The isolated tests did not deploy the production API, so the selected final topology still requires the BR-05 health/recommendation impact and reboot gates. Raw non-secret JSON remains on the Pi under `/mnt/storage/attreq/benchmarks/results/` and is intentionally excluded from Git. Temporary reranker environment and diagnostic files were securely removed after a credential prefix reached a validation traceback; that provider key must be revoked before deployment.

### Exit criteria

- A measured enable/disable decision exists for each of the four components.
- The Pi Compose file reflects those decisions through feature flags/profiles.
- A future agent can reproduce the benchmark from documented commands.

## BR-05 — Build the Pi-Specific Production Stack

### Scope

1. Install Docker Engine and the Compose plugin on the Pi using current official instructions.
2. Create `/mnt/storage/attreq` with explicit subdirectories for PostgreSQL, backups, and any selected local service data.
3. Add a Pi production Compose file under `infra/docker/` rather than deploying the stale `compose.api.prod.yml` unchanged.
4. Include:
   - PostgreSQL 15;
   - Redis 7;
   - FastAPI backend;
   - `cloudflared` or a separately managed system service;
   - only BR-04 components that passed their gate.
5. Wire current settings: Groq, OpenWeather, Redis, storage, Sentry, trusted hosts, and selected feature flags.
6. Remove obsolete Google OAuth/Gemini-only assumptions from the deployed Compose environment.
7. Do not publish PostgreSQL, Redis, Weaviate, or FastAPI ports to the LAN/WAN. `cloudflared` should reach the backend on the Docker network.
8. Run migrations before application startup with a bounded failure strategy; avoid blind sleeps.
9. Add health checks, restart policies, resource limits/reservations where supported, and log rotation.

### Secrets

- Store the Pi production environment outside the Git checkout with mode `0600`.
- Commit only an `.env.example` containing names and explanations, never values.
- Generate unique production JWT and database secrets. Do not reuse development values.

### Rollback

- Preserve the prior image/tag and database backup.
- Roll back by deploying the prior Git tag and restoring only if the migration is incompatible.
- Never use destructive Git or Docker volume commands as a rollback shortcut.

### Exit criteria

- A reboot returns every required service to healthy without manual commands.
- No backend dependency is publicly listening on the router or Pi host.
- Persistent state resolves under `/mnt/storage/attreq` or R2 as designed.

## BR-06 — Move the Cloudflare Hostname to the Pi

### Scope

1. Create a named Cloudflare Tunnel for the Pi.
2. Route the chosen beta hostname to the backend service, for example `http://backend:8000` when `cloudflared` shares the Compose network.
3. Update the Cloudflare DNS route for the hostname.
4. Confirm the old Mac tunnel no longer owns the beta hostname.
5. Keep the Mac development tunnel on a different hostname if still needed.
6. Verify from a phone on mobile data, not merely from the home LAN.

### Required verification

```bash
curl -fsS https://api.example.com/health
```

Expected properties:

- HTTP 200;
- `environment` is `production` or `beta`, never `development`;
- Cloudflare serves the certificate;
- stopping the Mac backend does not affect the beta hostname;
- rebooting the Pi restores the tunnel automatically.

### Rollback

Keep the prior tunnel/route definition until the Pi health and end-to-end checks pass. DNS/tunnel rollback must not require changing the APK if the same hostname is retained.

## BR-07 — Wire R2, Persistence, Backup, Restore, and Monitoring

### Object storage

The S3-compatible R2 storage implementation already exists under `apps/api/src/attreq_api/services/storage/`. Configure and verify it; do not rewrite it unnecessarily.

- private R2 bucket;
- object keys stored in PostgreSQL;
- presigned URLs returned to clients;
- no public bucket access;
- upload, thumbnail, Style DNA, additional-photo, delete, and archive flows tested.

### Database and service backups

1. Schedule PostgreSQL backups to `/mnt/storage/attreq/backups`.
2. Copy backups off the Pi on a defined schedule; the SSD is not an off-site backup.
3. If Weaviate is enabled, back up its selected collection(s) and document restore.
4. Define retention and test an actual restore into an isolated database.

### Monitoring

- external HTTPS monitor for `/health`;
- Sentry backend DSN and deliberate test event;
- disk-space alert for `/mnt/storage` and `/`;
- container restart/unhealthy visibility;
- documented response for power/network outage.

### Exit criteria

- User images survive backend container replacement.
- A PostgreSQL restore drill succeeds.
- A forced backend exception reaches Sentry.
- External monitoring detects a stopped tunnel/backend.

## BR-08 — Configure Android Signing, Versioning, and API URL Selection

### Signing

1. Generate one long-lived Android upload/release keystore outside the repository.
2. Back it up securely in the user-approved location.
3. Load the keystore path, alias, and passwords from local/CI secrets.
4. Update `apps/mobile/android/app/build.gradle` so `release` never silently falls back to `signingConfigs.debug`.
5. Never commit a keystore, password, `key.properties`, or secret-bearing Gradle properties.

### Versioning

- Increment `versionCode` for every distributed build.
- Use an explicit prerelease `versionName`, for example `0.2.0-beta.1`.
- Make the Git tag, GitHub Release title, and Android version agree.

### API URL

- Remove the assumption that every build should use the hard-coded Mac development endpoint.
- Create explicit development and beta/release configuration paths.
- Fail release builds when the beta API URL is missing or uses a development hostname unintentionally.
- If the same `dev-server-1.online` hostname is retained, still make the environment explicit so future development and production endpoints can diverge safely.

### Required verification

```bash
cd apps/mobile/android
./gradlew :app:assembleRelease --no-daemon

APKSIGNER="$HOME/Library/Android/sdk/build-tools/35.0.0/apksigner"
"$APKSIGNER" verify --print-certs app/build/outputs/apk/release/app-release.apk
shasum -a 256 app/build/outputs/apk/release/app-release.apk
```

The signer must not be `CN=Android Debug`.

## BR-09 — Publish the Beta APK Through GitHub Releases

### Invariants

- Commit and push source code; do **not** commit APKs under `apps/mobile/android/app/build/`.
- Build from a clean, reviewed, tagged commit.
- Never tag or publish from a dirty working tree.
- A beta milestone is not complete until the GitHub prerelease contains the APK and checksum, unless the user explicitly defers publication.

### Manual first-release flow

```bash
git status --short

# Run backend/mobile verification from BR-01, then build from the clean commit.
cd apps/mobile/android
./gradlew :app:assembleRelease --no-daemon

cd ../../..
git tag -a v0.2.0-beta.1 -m "ATTREQ Android beta 0.2.0-beta.1"
git push origin v0.2.0-beta.1

shasum -a 256 apps/mobile/android/app/build/outputs/apk/release/app-release.apk \
  > apps/mobile/android/app/build/outputs/apk/release/app-release.apk.sha256

gh release create v0.2.0-beta.1 \
  apps/mobile/android/app/build/outputs/apk/release/app-release.apk \
  apps/mobile/android/app/build/outputs/apk/release/app-release.apk.sha256 \
  --prerelease \
  --generate-notes \
  --title "ATTREQ Android v0.2.0-beta.1"
```

Pushing and creating a release are outward-facing actions. Follow `AGENTS.md`: verify first and obtain user confirmation before performing them.

### Automation after the manual release is proven

Add a GitHub Actions workflow triggered by an Android beta tag or `workflow_dispatch` that:

1. checks out the exact tag;
2. installs Node, JDK 17, and Android SDK;
3. runs typecheck/tests;
4. reconstructs the keystore from GitHub Actions secrets in a temporary path;
5. builds and verifies the release APK;
6. emits SHA-256;
7. uploads both files to a GitHub prerelease;
8. deletes temporary secret material.

Do not automate until the manual signed release succeeds once.

## BR-10 — Remote-Device Beta Gate and Milestone Closure

### Preconditions

- Pi and tunnel survive reboot.
- R2 and PostgreSQL backup/restore are verified.
- Signed APK is attached to a GitHub prerelease.
- The APK points at the Pi hostname.

### Test matrix

Run on at least one physical Android phone over mobile data:

1. install the APK from GitHub Releases;
2. register a new account;
3. enter or resolve location;
4. complete/skip Style DNA as designed;
5. upload realistic wardrobe photos;
6. observe pending → processing → completed/failed states;
7. request daily recommendations and a swipe deck;
8. submit feedback and mark an outfit worn;
9. confirm History and Stats update;
10. close/reopen the app and verify session restoration;
11. let an access token expire or exercise refresh behavior;
12. deny camera/photo permissions and verify recovery;
13. temporarily stop the backend/tunnel and verify understandable offline behavior;
14. confirm images still render after backend restart;
15. upgrade over the previous beta build and verify app data/session behavior.

### Closure updates

When the gate passes:

- mark every BR item complete in this table;
- record the Git tag, GitHub Release URL, backend commit, hostname, and test date;
- update conflicting status trackers under `docs/00-current-status/`, `docs/05-roadmap/`, and `docs/Pending.md`;
- push the completed milestone documentation to GitHub under the mandatory milestone policy.

## Definition of Done

- [ ] Reliability patch is directly tested, committed, and pushed.
- [ ] Android location UX has no deterministic dead action.
- [ ] Public/costly endpoints are rate-limited.
- [ ] FashionCLIP, Weaviate, text-transformers, and reranker have measured Pi decisions.
- [ ] Pi stack is reproducible and reboot-safe.
- [ ] Stable Cloudflare hostname reaches the Pi, not the Mac.
- [ ] R2, database backup, restore, Sentry, and uptime monitoring are verified.
- [ ] APK uses permanent release signing and explicit beta API configuration.
- [ ] GitHub prerelease contains APK and checksum from the tagged commit.
- [ ] Physical-device mobile-data gate passes end to end.
