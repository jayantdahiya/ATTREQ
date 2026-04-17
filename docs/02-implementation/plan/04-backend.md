# Backend Plan

## Role of the Backend

`apps/api` remains the product core for ATTREQ. The mobile transition does not change that.

The backend continues to own:

- authentication,
- user profiles,
- wardrobe persistence,
- outfit persistence,
- recommendation generation,
- image-processing workflows,
- caching and search integrations.

## Primary Goal for the Next Phase

The backend priority is **contract stabilization for mobile**, not a backend rewrite.

That means:

- aligning auth request and refresh behavior,
- validating wardrobe and outfit payloads,
- ensuring recommendation responses are complete for mobile screens,
- confirming migrations and persistence cover the live models,
- closing gaps that would make the mobile client build against unstable assumptions.

## Functional Areas

### Authentication

- registration and login
- access token issuance
- refresh token flow
- current-user retrieval
- profile updates and password changes

### Wardrobe

- image upload endpoints
- wardrobe item CRUD
- metadata enrichment pipeline
- file storage and cleanup

### Outfits and Recommendations

- outfit creation and listing
- daily recommendations
- wear tracking
- feedback capture
- recommendation cache invalidation

### Support Services

- weather data retrieval
- Redis caching
- Weaviate search and embeddings
- image-processing tasks

## Backend Work Required Before or During Mobile Build

1. Confirm the auth contract is mobile-friendly and explicit.
2. Ensure migrations cover wardrobe and outfit schema expectations.
3. Remove placeholder behaviors that would undermine mobile flows.
4. Verify upload and recommendation endpoints are stable enough to treat as source of truth.
5. Add targeted automated tests around auth, uploads, and recommendations.

## Contract Rule

The mobile client should adapt to the backend only after the backend contracts are intentionally defined. Do not let undocumented web behavior become the de facto API contract for the mobile app.
