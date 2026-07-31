# Roadmap to Beta Launch — Overview

> **Status:** Active roadmap (created 2026-06-10)
> **Audience:** Any LLM or developer executing a milestone. Read this file + the single milestone file you are executing. Each milestone file is self-contained.

## Goal of this phase

Take ATTREQ from "feature-complete mobile app on a laptop" to "beta app installed on testers' phones against a real production backend":

- Backend live on a **single VPS via Docker Compose** (`infra/docker/compose.api.prod.yml`), TLS via Caddy
- Wardrobe images in **Cloudflare R2** object storage (private bucket, presigned URLs)
- Canonical **clothing category taxonomy** replacing free-text categories
- **Complete outfits** (footwear always, outerwear when weather demands)
- Real test coverage and nightly backups
- **TestFlight + Google Play internal track** distribution with Sentry crash reporting

This roadmap sequences and supersedes the open items in [`docs/Pending.md`](../Pending.md) and the remaining tickets **TKT-002** (backend↔mobile contract stabilization → Milestone 2) and **TKT-009** (release & distribution baseline → Milestone 5) from [`docs/00-current-status/02-next-phase-tickets.md`](../00-current-status/02-next-phase-tickets.md).

## Milestones

| # | File | Goal (one line) | Depends on | Status |
|---|------|-----------------|------------|--------|
| M1 | [01-milestone-1-production-backend.md](01-milestone-1-production-backend.md) | API live on VPS with R2 storage, fixed prod compose, Caddy TLS, deploy runbook | — | Not started |
| M2 | [02-milestone-2-data-model-contracts.md](02-milestone-2-data-model-contracts.md) | Canonical category taxonomy, API contract doc + tests, geocoding fallback, remove OAuth ghost | M1 (verify against prod) | Not started |
| M3 | [03-milestone-3-complete-outfits.md](03-milestone-3-complete-outfits.md) | Footwear + outerwear slots in schema and scoring algorithm | M2 (taxonomy) | Not started |
| M4 | [04-milestone-4-testing-reliability.md](04-milestone-4-testing-reliability.md) | Real backend + mobile test suites, nightly backups, uptime monitoring | M3 (test final algorithm) | Not started |
| M5 | [05-milestone-5-distribution-beta.md](05-milestone-5-distribution-beta.md) | EAS builds, TestFlight/Play internal distribution, mobile Sentry, beta launch | M4 | Not started |

## Sequencing rationale

1. **M1 first** — `compose.api.prod.yml` is currently broken (no Weaviate service, dead Gemini/Google env vars, no Groq/Sentry/Redis/storage wiring), and every later milestone needs a real environment to verify against. Image storage must move off local disk before any tester touches the app.
2. **M2 before M3** — outfit slots (footwear/outerwear pools) are unimplementable while categories are free-text. M2 also runs while there are **zero production users**, so data migrations are free.
3. **M3 before M4** — tests should cover the final shape of the recommendation algorithm, not one about to churn.
4. **M4 before M5** — the first build that reaches a tester's phone should already be instrumented (Sentry) and covered by tests + a smoke checklist.

## Start immediately (during M1) — slow external dependencies

These have multi-day/multi-week lead times outside our control. Kick them off in parallel with M1 work:

- **Apple Developer Program enrollment** (~1–2 days approval) and App Store Connect app creation for the bundle ID in `apps/mobile/app.json`
- **Google Play Console** account + app creation. Note: Play requires a **12-tester / 14-day closed-testing soak** before production access is granted — start the clock as early as possible.

## Conventions for executing a milestone

- Each milestone file has: **Context** (current state, restated — no chat history needed), **Tasks** with exact file paths and pre-made decisions, **Out of scope**, **Exit criteria**, and **Verification** with concrete commands.
- When a milestone completes: update its Status in the table above, and update [`docs/Pending.md`](../Pending.md) rows it resolves.
- Backend commands run from `apps/api/` (pytest, alembic, ruff); mobile commands from `apps/mobile/` (`npm run typecheck`, `npm test`). CI must stay green: `.github/workflows/backend-ci.yml`, `.github/workflows/mobile-ci.yml`.
- `apps/web` (Next.js) is **legacy** — no milestone invests in it. Mobile (`apps/mobile`, Expo) is the primary client.
