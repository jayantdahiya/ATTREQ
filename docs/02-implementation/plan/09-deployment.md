# Deployment Plan

## Split the Problem Correctly

ATTREQ deployment now has two separate concerns:

1. **backend hosting** for `apps/api` and its supporting services,
2. **mobile distribution** for the planned Expo app in `apps/mobile`.

The old idea of a single web deployment target is no longer the active frontend plan.

## Backend Hosting

The backend can continue to be self-hosted on the Raspberry Pi environment or another Linux host.

That deployment should cover:

- FastAPI API
- PostgreSQL
- Redis
- Weaviate
- upload persistence
- reverse proxy and TLS when exposed externally

Backend deployment guidance belongs primarily in:

- `../../03-execution/deployment/raspberry-pi-backend-deployment.md`
- `../../03-execution/deployment/raspberry-pi-testing-guide.md`

## Mobile Distribution

The planned mobile app should use an Expo-oriented release workflow.

Recommended baseline:

- Expo development builds for local device testing
- internal distribution for team and device validation
- EAS Build for release artifacts
- EAS Submit or equivalent store submission workflow when ready

## Environment Strategy

At minimum, distinguish:

- local development API URL,
- staging or self-hosted validation API URL,
- production API URL,
- mobile build-time environment values.

The mobile app should not depend on web-only environment assumptions or browser URL discovery.

## Release Priorities

### Backend

- stable migrations,
- stable HTTPS endpoint,
- durable storage,
- basic observability and log access.

### Mobile

- signed builds,
- device-level auth verification,
- camera/library permission validation,
- notification setup validation,
- release notes and versioning discipline.

## `apps/web` Position

If the web client continues to be deployed, treat it as optional support infrastructure. It should not block the mobile release path.
