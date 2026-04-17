# Development Workflow

## Goal

Keep the development loop simple:

- `apps/api` remains the backend source of truth,
- `apps/mobile` is the next primary client once scaffolded,
- `apps/web` is maintained only where still useful during the transition.

## Working Areas

### Current

- `apps/api`
- `apps/web`
- `infra/docker`
- `docs`

### Planned

- `apps/mobile`

When the mobile app is created, frontend-focused work should move there by default.

## Local Backend Workflow

Typical backend work should happen from `apps/api` with the existing Python, Docker, and migration workflow already established in the repo.

Keep the backend loop focused on:

- endpoint changes,
- migrations,
- upload behavior,
- recommendation logic,
- contract verification for mobile.

## Local Mobile Workflow

Once `apps/mobile` exists, the default workflow should be:

1. run the backend locally or against a reachable staging API,
2. run the Expo dev server,
3. test on simulator, emulator, and at least one real device for camera or notification features,
4. verify auth bootstrap, uploads, and recommendation screens early and often.

## Environment Handling

Maintain explicit environment separation for:

- backend local variables,
- backend deployment variables,
- mobile local development values,
- mobile build-time production values.

Document API base URLs clearly so local-device testing does not depend on guesswork.

## Client Workflow Rules

- new frontend feature work should default to the planned React Native client,
- do not add major new product surface area to `apps/web` unless there is a clear short-term reason,
- keep backend contracts documented before relying on them in mobile UI flows.

## Quality Gates

Before merging meaningful product work:

- run backend checks and tests relevant to the change,
- run mobile tests relevant to the change once the mobile app exists,
- manually verify the affected flow on device or emulator for client-side work,
- update docs when contracts or workflow expectations change.
