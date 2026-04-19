# Mobile Tasks (V1)

## Purpose

This is the active frontend execution checklist for ATTREQ's planned React Native client.

The target app directory is `apps/mobile`. Until that directory exists, treat this file as the implementation backlog and sequencing guide rather than a record of shipped code.

## Phase 1: App Foundation

- [x] Create `apps/mobile`
- [x] Initialize Expo + TypeScript baseline
- [x] Add Expo Router
- [x] Set up NativeWind
- [x] Add react-native-reusables base primitives
- [x] Set up TanStack Query, Zustand, Axios, React Hook Form, and Zod
- [x] Establish app-level theme tokens and layout conventions

## Phase 2: Auth and Session

- [x] Build sign-in and registration screens
- [x] Implement auth store and bootstrap state
- [x] Add SecureStore-backed session persistence
- [x] Integrate login, refresh, logout, and current-user flows
- [x] Add protected-route layouts in Expo Router

## Phase 3: Wardrobe Capture and Upload

- [x] Add photo library picker flow
- [x] Add camera capture flow if custom capture is required
- [x] Build item preview and upload confirmation UI
- [x] Wire multipart uploads to wardrobe endpoints
- [x] Show processing, success, and failure states clearly

## Phase 4: Dashboard and Recommendation Loop

- [x] Build the daily suggestions screen
- [x] Fetch recommendations through TanStack Query
- [x] Display context such as weather and refresh state
- [x] Add force-refresh behavior if supported by the backend
- [x] Build outfit detail or action surfaces

## Phase 5: Wear and Feedback Loop

- [x] Add mark-as-worn action
- [x] Add feedback submission flow
- [x] Reflect updated outfit state in query caches
- [x] Add outfits/history screen

## Phase 6: Permissions and Notifications

- [x] Handle photo permission denied states
- [x] Handle camera permission denied states
- [x] Handle notification permission denied states
- [x] Add daily reminder notification baseline

## Phase 7: Testing and Release Readiness

- [x] Add `jest-expo`
- [x] Add React Native Testing Library coverage for core UI
- [x] Add `expo-router/testing-library` coverage for auth gating
- [x] Add Maestro coverage for the primary mobile flow
- [ ] Prepare internal distribution build process

## Dependencies

- Backend auth and upload contracts must be stable enough to integrate.
- `apps/mobile` now exists in the repo and should be treated as the active mobile client baseline.
