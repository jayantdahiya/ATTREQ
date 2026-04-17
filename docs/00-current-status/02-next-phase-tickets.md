# ATTREQ Next-Phase Development Tickets

## Purpose

This backlog translates the current repo state into a mobile-first delivery sequence. The documentation rebaseline is complete. The next phase is about:

1. stabilizing the backend contract for clients,
2. shipping the React Native app foundation,
3. wiring the core daily-use loop on mobile,
4. and preparing the mobile client for real testing and release.

## Recommended Phase Focus

The next phase should be executed in this order:

1. Backend contract hardening for mobile
2. Expo app foundation
3. Core mobile auth and wardrobe flows
4. Recommendation loop and notifications
5. Mobile testing and release readiness

## Ticket Backlog

---

## TKT-001 - Re-baseline docs for the React Native transition

**Priority**: P0  
**Area**: Documentation  
**Status**: Complete

### Problem

The active docs needed to be re-baselined to match the mobile-first implementation direction.

### Scope

- Make React Native the active frontend direction in current docs
- Archive superseded PWA frontend planning docs
- Add mobile research docs for stack and component-library decisions
- Update current-status docs to distinguish present repo truth from target mobile design

### Acceptance criteria

- Active docs describe `apps/mobile` as planned and `apps/web` as legacy/supporting
- Active frontend plan points to React Native, not the former PWA plan
- Archived PWA planning docs are preserved under `docs/99-archive/pre-react-native-transition/`

---

## TKT-002 - Stabilize backend client contracts for native clients

**Priority**: P0  
**Area**: Backend + Client Integration  
**Status**: Ready

### Problem

The existing client/backend contracts around auth, session refresh, location handling, and recommendation actions are not clean enough to reuse directly in a native client.

### Scope

- Standardize login response handling
- Standardize refresh-token request and retry behavior
- Confirm how recommendation cards map to persisted outfits
- Tighten location and geocoding expectations for client use

### Acceptance criteria

- Mobile client auth bootstrap can be implemented without contract ambiguity
- Recommendation actions have a stable server-side contract
- Location update and recommendation requests have documented, reliable inputs

---

## TKT-003 - Create the Expo mobile app foundation

**Priority**: P0  
**Area**: Mobile Foundation  
**Status**: Ready

### Problem

There is no `apps/mobile` app yet, so the mobile program cannot start until the baseline stack is scaffolded.

### Scope

- Create `apps/mobile` with Expo SDK 55, TypeScript, and Expo Router
- Add NativeWind, react-native-reusables, TanStack Query, Zustand, RHF, Zod, Axios, Reanimated, and FlashList
- Set up app structure, route groups, env handling, and shared client utilities

### Acceptance criteria

- `apps/mobile` runs locally on simulator/device
- Core providers and route groups are in place
- API layer, query layer, and storage layer are initialized

---

## TKT-004 - Implement mobile auth and session bootstrap

**Priority**: P0  
**Area**: Mobile Auth  
**Status**: Ready

### Problem

The mobile app needs a native auth/session lifecycle with SecureStore and protected routes.

### Scope

- Build sign-in and sign-up screens
- Persist refresh token and session state with SecureStore
- Add app bootstrap logic to restore or refresh sessions
- Protect authenticated routes with Expo Router

### Acceptance criteria

- A user can sign in and reopen the app without being logged out unexpectedly
- Expired access tokens are refreshed correctly
- Protected screens are inaccessible when not authenticated

---

## TKT-005 - Implement mobile wardrobe capture and upload

**Priority**: P0  
**Area**: Mobile Wardrobe  
**Status**: Ready

### Problem

Wardrobe ingestion is the most mobile-native part of ATTREQ and must work well in the new client.

### Scope

- Support camera and library selection
- Upload images to the existing wardrobe endpoints
- Show processing states and error states
- Display wardrobe items in performant native lists/grids

### Acceptance criteria

- A user can add wardrobe items from camera or gallery
- Upload feedback is clear and recoverable
- Wardrobe inventory is viewable and scroll-performant on mobile

---

## TKT-006 - Implement the mobile dashboard and recommendation loop

**Priority**: P0  
**Area**: Mobile Recommendations  
**Status**: Ready

### Problem

The daily use loop is incomplete today and must be rebuilt natively around the existing recommendation endpoints.

### Scope

- Fetch daily suggestions with native loading and empty states
- Render outfit cards optimized for touch interaction
- Support refresh, wear tracking, and outfit feedback
- Handle location-aware recommendation requests

### Acceptance criteria

- Users can fetch, review, and act on outfit suggestions on mobile
- Wear tracking and feedback mutations work end to end
- Recommendation state refreshes cleanly after mutations

---

## TKT-007 - Add mobile notifications and reminder flow

**Priority**: P1  
**Area**: Mobile Engagement  
**Status**: Ready

### Problem

The product’s daily-use habit is much stronger on native once reminders exist.

### Scope

- Register notification permissions
- Set up local or backend-driven daily reminder flow
- Document notification token handling and environment assumptions

### Acceptance criteria

- Users can opt into reminders
- Notification behavior is documented and testable on real devices

---

## TKT-008 - Build the mobile test suite

**Priority**: P1  
**Area**: Mobile Quality  
**Status**: Ready

### Problem

The next client should not repeat the current lack of automated confidence around core flows.

### Scope

- Add `jest-expo` and React Native Testing Library
- Add Expo Router integration tests
- Add Maestro E2E coverage for critical mobile journeys

### Acceptance criteria

- Unit and integration tests run locally
- Core auth, upload, and recommendation flows are covered by E2E tests

---

## TKT-009 - Prepare mobile release and distribution baseline

**Priority**: P1  
**Area**: Release Readiness  
**Status**: Ready

### Problem

The app needs a practical path from local development to internal testing and later store release.

### Scope

- Define EAS build profiles
- Document development builds vs internal distribution vs production builds
- Separate backend hosting docs from mobile release docs

### Acceptance criteria

- The team can generate development and internal-test builds consistently
- Environment and secret handling are documented for mobile release flows

---

## Definition Of Done For This Phase

This phase is complete when:

- Docs clearly reflect the mobile-first direction
- Backend client contracts are stable enough for a native app
- `apps/mobile` exists and runs
- Mobile auth, wardrobe upload, dashboard, and feedback loop are wired
- Notification strategy is in place
- Mobile automated testing exists
- A repeatable internal-distribution path is documented
