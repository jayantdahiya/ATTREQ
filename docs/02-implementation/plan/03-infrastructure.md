# Infrastructure Plan

## Scope

This document covers the infrastructure required to support ATTREQ's backend and the planned mobile client.

The key distinction is:

- the backend is deployed and hosted infrastructure,
- the mobile client is distributed to devices and talks to that backend,
- the web client is not the primary deployment target for the next phase.

## Active Infrastructure Components

### API and Data Services

- FastAPI application in `apps/api`
- PostgreSQL for relational product data
- Redis for caching and ephemeral coordination
- Weaviate for semantic search and vector storage
- persistent upload storage for wardrobe media

### Repo and Infra Layout

- `apps/api`
- `apps/web`
- planned `apps/mobile`
- `infra/docker`

## Raspberry Pi Role

The Raspberry Pi environment remains a valid self-hosting target for the backend stack.

It should host:

- the API service,
- PostgreSQL,
- Redis,
- Weaviate,
- upload storage,
- reverse proxy / TLS termination if exposed beyond the local network.

It should **not** be treated as the place where the mobile client runs. The mobile app is built and distributed separately.

## Container and Volume Expectations

The Docker-based deployment should maintain clear separation for:

- database persistence,
- Redis data,
- Weaviate data,
- uploaded images,
- logs and backups.

Those concerns belong under the infrastructure layer in `infra/docker` and deployment-specific host paths, not under old pre-restructure app paths.

## Network Expectations

- The API should be reachable over a stable base URL.
- Mobile clients should use HTTPS for non-local environments.
- CORS remains relevant for `apps/web`, but it is not the main client concern for `apps/mobile`.
- Authentication, uploads, and recommendation endpoints must be reachable from both local development devices and production mobile builds.

## Environment Separation

At minimum, maintain separate environment handling for:

- local development,
- Raspberry Pi or self-hosted staging,
- production backend deployment,
- mobile build-time configuration for API URLs and keys.

## Infrastructure Priorities for the Next Phase

1. Keep backend deployment stable and repeatable.
2. Ensure the API base URL strategy works for mobile development and release builds.
3. Keep upload and database persistence durable.
4. Avoid web-only assumptions in deployment or reverse-proxy configuration.
