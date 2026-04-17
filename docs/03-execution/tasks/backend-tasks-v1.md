# Backend Tasks (V1)

## Purpose

This file tracks backend work that still matters while ATTREQ transitions to a mobile-first client strategy.

The backend remains the product core in `apps/api`. These tasks are backend-facing and should not be read as a web-only backlog.

## Completed Baseline

- [x] FastAPI backend established in `apps/api`
- [x] user auth endpoints and profile endpoints exist
- [x] wardrobe and outfit domain models exist
- [x] image-processing pipeline and storage flow exist
- [x] recommendation endpoints and caching exist
- [x] Docker-based local and deployment workflows exist

## Remaining High-Priority Work

### Contracts and Persistence

- [ ] Confirm database migrations cover the live wardrobe and outfit model set
- [ ] Audit auth request and refresh contracts for mobile use
- [ ] Normalize recommendation, outfit, and wardrobe response shapes where the current behavior is inconsistent

### Reliability

- [ ] Replace placeholder or fallback behaviors that would undermine the mobile experience
- [ ] Tighten upload error handling and processing-state reporting
- [ ] Verify Redis and Weaviate failure behavior for recommendation and search paths

### Testing

- [ ] Add backend tests for login, refresh, and current-user flows
- [ ] Add backend tests for wardrobe upload and item retrieval
- [ ] Add backend tests for recommendation generation and cache invalidation
- [ ] Add backend tests for outfit wear and feedback endpoints

## Coordination Notes

- New mobile work should consume documented backend contracts instead of inheriting accidental web behavior.
- When backend contracts change, update the active docs under `docs/02-implementation/plan/`.
