# ATTREQ Agent Guide

## Start Here

- Repository truth starts in `docs/README.md`.
- Current implementation status lives in `docs/00-current-status/`.
- Product and planning context lives under `docs/01-product/` and `docs/02-implementation/plan/`.

## Monorepo Layout

```text
apps/api            FastAPI backend using a src layout (`src/attreq_api`)
apps/web            Next.js frontend using a src layout (`src/app`, `src/components`, `src/lib`)
infra/docker        Docker Compose definitions
scripts/dev         Local developer helpers
scripts/test        Manual API and integration smoke tests
scripts/data        Test-image download helpers and shared fixture data
docs                Canonical documentation
assets/design       Design assets
research            Research and model work
```

## Canonical Commands

```bash
make compose-up
make compose-down
make dev-api
make dev-web
make test
make lint
```

## Backend Notes

- Python package root: `apps/api/src/attreq_api`
- Local run command: `PYTHONPATH=src uvicorn attreq_api.main:app --reload`
- Alembic config stays in `apps/api/alembic.ini`
- Uploads directory: `apps/api/uploads`

## Frontend Notes

- App Router root: `apps/web/src/app`
- Shared UI components: `apps/web/src/components`
- Shared client code: `apps/web/src/lib`
- Zustand stores: `apps/web/src/store`

## Compose Files

- Development stack: `infra/docker/compose.api.yml`
- Local dependencies only: `infra/docker/compose.api.dev.yml`
- Production stack: `infra/docker/compose.api.prod.yml`
