# Raspberry Pi Backend Deployment

## Scope

This guide covers deployment of the ATTREQ backend stack from the current repo layout.

Use it for:

- `apps/api`
- PostgreSQL
- Redis
- Weaviate
- upload persistence

It does **not** describe deployment of the planned mobile client. The mobile app is distributed separately.

## Repo Paths

Use the current repo structure:

- backend application: `apps/api`
- infrastructure config: `infra/docker`

Do not use legacy pre-restructure pathing from superseded docs.

## Expected Host Responsibilities

The Raspberry Pi host should provide:

- Docker Engine
- Docker Compose
- persistent storage
- a stable LAN or public base URL for the API
- TLS and reverse proxying if the API is exposed beyond local development

## Deployment Flow

1. Clone the repository onto the Raspberry Pi.
2. Move into the backend or infrastructure working area using current repo paths.
3. Create production environment variables for the API and supporting services.
4. Start the backend stack with the appropriate Docker Compose configuration from the current repo.
5. Apply migrations and verify health endpoints.

## Production Checklist

- [ ] API starts successfully
- [ ] database is reachable
- [ ] Redis is reachable
- [ ] Weaviate is reachable
- [ ] upload storage is writable
- [ ] migrations are applied
- [ ] API base URL is reachable from a development phone or emulator
- [ ] HTTPS is configured if used outside trusted local development

## Mobile-Specific Reminder

When the React Native client is introduced, the most important deployment outcome is a stable backend URL that works from real devices. Browser-specific assumptions are not sufficient anymore.
