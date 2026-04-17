# Mobile Tasks (V1)

## Purpose

This is the active frontend execution checklist for ATTREQ's planned React Native client.

The target app directory is `apps/mobile`. Until that directory exists, treat this file as the implementation backlog and sequencing guide rather than a record of shipped code.

## Phase 1: App Foundation

- [ ] Create `apps/mobile`
- [ ] Initialize Expo + TypeScript baseline
- [ ] Add Expo Router
- [ ] Set up NativeWind
- [ ] Add react-native-reusables base primitives
- [ ] Set up TanStack Query, Zustand, Axios, React Hook Form, and Zod
- [ ] Establish app-level theme tokens and layout conventions

## Phase 2: Auth and Session

- [ ] Build sign-in and registration screens
- [ ] Implement auth store and bootstrap state
- [ ] Add SecureStore-backed session persistence
- [ ] Integrate login, refresh, logout, and current-user flows
- [ ] Add protected-route layouts in Expo Router

## Phase 3: Wardrobe Capture and Upload

- [ ] Add photo library picker flow
- [ ] Add camera capture flow if custom capture is required
- [ ] Build item preview and upload confirmation UI
- [ ] Wire multipart uploads to wardrobe endpoints
- [ ] Show processing, success, and failure states clearly

## Phase 4: Dashboard and Recommendation Loop

- [ ] Build the daily suggestions screen
- [ ] Fetch recommendations through TanStack Query
- [ ] Display context such as weather and refresh state
- [ ] Add force-refresh behavior if supported by the backend
- [ ] Build outfit detail or action surfaces

## Phase 5: Wear and Feedback Loop

- [ ] Add mark-as-worn action
- [ ] Add feedback submission flow
- [ ] Reflect updated outfit state in query caches
- [ ] Add outfits/history screen

## Phase 6: Permissions and Notifications

- [ ] Handle photo permission denied states
- [ ] Handle camera permission denied states
- [ ] Handle notification permission denied states
- [ ] Add daily reminder notification baseline

## Phase 7: Testing and Release Readiness

- [ ] Add `jest-expo`
- [ ] Add React Native Testing Library coverage for core UI
- [ ] Add `expo-router/testing-library` coverage for auth gating
- [ ] Add Maestro coverage for the primary mobile flow
- [ ] Prepare internal distribution build process

## Dependencies

- Backend auth and upload contracts must be stable enough to integrate.
- `apps/mobile` should not be described as implemented until the scaffold exists in the repo.
