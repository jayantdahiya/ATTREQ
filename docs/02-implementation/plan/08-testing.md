# Testing Plan

## Goal

Testing should cover the backend as the product core and the planned mobile app as the primary client.

The old web-first testing plan is no longer the reference point. For the next phase, the main client-side testing layers should be React Native focused.

## Backend Testing

Backend tests remain important because `apps/api` is the shared product core for both the legacy web client and the planned mobile app.

Priority backend test areas:

- auth login and refresh flows,
- current-user retrieval,
- wardrobe upload endpoints,
- outfit wear and feedback endpoints,
- recommendation generation and cache behavior,
- migration coverage for live models.

Recommended baseline:

- `pytest`
- `pytest-asyncio`
- API-level integration tests around critical contracts

## Mobile Testing

### Unit and Component Tests

Use:

- `jest-expo`
- React Native Testing Library

Focus on:

- auth screens,
- form validation,
- permission-denied UI,
- wardrobe item cards and recommendation cards,
- error, empty, and loading states.

### Router and Navigation Tests

Use:

- `expo-router/testing-library`

Focus on:

- protected route gating,
- auth-to-app redirects,
- bootstrap loading states,
- tab or stack transitions that contain business rules.

### End-to-End Tests

Use:

- Maestro

Focus on the critical user journey:

1. sign in,
2. restore a session,
3. upload or pick a wardrobe image,
4. fetch daily recommendations,
5. mark an outfit worn or submit feedback,
6. log out.

## Test Environment Priorities

- Emulator coverage for Android and iOS where available
- At least one physical-device smoke test for image picking, permissions, and notifications
- Local backend or stable staging backend for mobile integration tests

## Non-Goals for the First Test Pass

- exhaustive snapshot testing,
- large brittle UI test suites,
- full offline mutation replay coverage.

The first goal is confidence around the core daily-use path.
