# ATTREQ Task Tracker

This tracker separates what is already present in the repo from what is still planned for the React Native transition.

Legend:

- `[x]` Implemented and verified in the repo
- `[ ]` Pending, partial, or not yet verified

## A) Backend Completed Baseline

- [x] `apps/api` exists with FastAPI app scaffold and versioned routing
- [x] Health endpoint, root endpoint, config, security, and database modules exist
- [x] JWT auth flow exists: register, login, refresh, logout
- [x] User profile endpoints exist, including location update
- [x] SQLAlchemy models exist for `User`, `WardrobeItem`, and `Outfit`
- [x] CRUD layers exist for users, wardrobe items, and outfits
- [x] Wardrobe upload, batch upload, list, get, update, and delete endpoints exist
- [x] Outfit create, list, get, delete, wear tracking, and feedback endpoints exist
- [x] Recommendation endpoint exists with weather integration and Redis caching
- [x] AI services exist for classification, background removal, embeddings, and recommendation scoring
- [x] Dockerized backend infrastructure exists under `apps/api` and `infra/docker`

## B) Legacy Web Client Completed Baseline

- [x] `apps/web` exists and provides a working baseline web client
- [x] Auth pages exist
- [x] Main pages exist for dashboard, wardrobe, and profile
- [x] Axios-based API clients exist for auth, wardrobe, and recommendations
- [x] Zustand stores exist for auth and wardrobe state
- [x] Route protection exists in the current web client
- [x] The web client is good enough to preserve as legacy/supporting context

## C) Pending Mobile Implementation Work

- [x] Create `apps/mobile` as the new primary client
- [x] Bootstrap Expo + TypeScript + Expo Router foundation
- [x] Implement TanStack Query, Zustand, Axios, and Zod/RHF foundations for native
- [x] Implement mobile auth session bootstrap using SecureStore and token refresh
- [x] Implement protected-route structure with Expo Router
- [x] Implement wardrobe capture and upload flows using image picker and camera
- [x] Implement dashboard recommendations flow in native UI
- [x] Implement native wear tracking and outfit feedback loop
- [x] Implement notification registration and daily reminder flow
- [x] Add mobile unit, integration, and E2E coverage
- [ ] Define mobile build, internal distribution, and release process

## D) Pending Backend Work Needed For Mobile

- [x] Fix client/backend auth contract mismatches that still affect the current web client and would affect mobile
- [ ] Complete Alembic migration coverage for wardrobe and outfit models
- [ ] Normalize clothing category semantics end to end
- [ ] Replace placeholder geocoding flow with a real provider-backed implementation
- [x] Expand automated backend test coverage for critical flows
- [ ] Re-verify deployment assumptions for a mobile-first client architecture

## E) Docs Migration Completed

- [x] React Native is the authoritative frontend direction in active docs
- [x] Superseded PWA planning docs are archived under `docs/99-archive/pre-react-native-transition/`
- [x] Mobile stack research and component-library evaluation live under `docs/04-research/mobile-frontend/`
- [x] Active docs point to `mobile-tasks-v1.md`
- [x] Old web-primary client assumptions were removed from active implementation docs
- [x] Active docs now use current repo structure and current pathing

## F) Important Status Notes

- [x] `apps/mobile` is now implemented as a source baseline and should be treated as the primary frontend code path in the repo
- [x] The current web client remains useful for backend integration checking and legacy continuity
- [ ] Geocoding is still intentionally deferred and recommendation actions still rely on outfit materialization through `/outfits`
