# Implementation Overview

## Purpose

This implementation plan defines ATTREQ's **mobile-first target architecture**.

It should be read together with:

- `../../00-current-status/00-current-status.md` for what exists today,
- `06-frontend.md` for the planned React Native client,
- `11-client-transition.md` for the migration rules from web-first planning to mobile-first implementation.

## Current State

The repository currently contains:

- `apps/api`: active FastAPI backend
- `apps/web`: existing Next.js client
- `infra/docker`: infrastructure configuration

The repository does **not** contain `apps/mobile` yet. All references to the mobile app in this folder describe the intended next client, not an already implemented codebase.

## Target State

The target state for the next development phase is:

- `apps/api` remains the product core and system of record,
- `apps/mobile` becomes the primary client,
- `apps/web` remains a legacy or supporting client until explicitly deprecated.

## Chosen Frontend Stack

- Expo
- React Native
- TypeScript
- Expo Router
- NativeWind
- react-native-reusables
- TanStack Query
- Zustand
- React Hook Form
- Zod
- Axios
- Expo SecureStore
- Reanimated
- FlashList

## Backend Baseline

The backend direction does not change in this docs pass. The backend remains centered on:

- FastAPI
- PostgreSQL
- Redis
- Weaviate
- image upload and processing services
- recommendation and outfit persistence endpoints

## Target Repo Shape

```text
apps/
  api/            # Existing backend and product core
  mobile/         # Planned Expo + React Native client
  web/            # Existing legacy/supporting client
infra/
  docker/         # Containers and infra configuration
docs/
  ...             # Current-state, implementation, execution, research, archive
```

## Phase Order

### Phase 1: Documentation Rebaseline

- make the mobile-first direction explicit,
- archive superseded PWA planning docs,
- align current-state and implementation-plan docs.

### Phase 2: Backend Contract Stabilization

- align auth contracts for mobile,
- confirm wardrobe, outfit, and recommendation payloads,
- close migration gaps and incomplete persistence assumptions.

### Phase 3: Mobile Foundation

- create `apps/mobile`,
- install Expo baseline stack,
- establish routing, query, auth, and design-token foundations.

### Phase 4: Core Mobile Flows

- authentication and session restore,
- wardrobe capture and upload,
- dashboard and daily recommendations,
- outfit wear and feedback loop.

### Phase 5: Release Hardening

- notifications,
- mobile testing layers,
- environment and release workflow,
- distribution readiness.

## Success Criteria

The next version is successful when a user can:

1. sign in on mobile,
2. keep a valid session across launches,
3. add wardrobe items from device photos,
4. retrieve daily recommendations,
5. record wear and feedback actions,
6. receive reminder notifications,
7. complete the loop without relying on the web client.
