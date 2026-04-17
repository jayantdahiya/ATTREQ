# Frontend Plan

## Role

This is the authoritative frontend implementation plan for ATTREQ's planned React Native client in `apps/mobile`.

`apps/web` remains in the repository as a legacy or supporting client, but the primary frontend direction is now:

- Expo
- React Native
- TypeScript
- Expo Router
- NativeWind
- react-native-reusables

## Chosen Stack

### Foundation

- Expo SDK 55 baseline
- React Native
- TypeScript
- Expo Router

### UI and Styling

- NativeWind as the primary styling layer
- react-native-reusables for reusable primitives and shadcn-like component ownership
- product-specific custom components for wardrobe grids, recommendation cards, and media flows

### State and Data

- TanStack Query for server state
- Zustand for auth state, transient UI state, and small app-level preferences
- Axios for API requests

### Forms and Validation

- React Hook Form
- Zod

### Device and Performance

- Expo SecureStore for secure session material
- Expo Image for rendering
- Expo ImagePicker for gallery and camera roll flows
- Expo Camera only where custom capture UX is needed
- Expo Notifications for reminders
- Reanimated for motion and gestures
- FlashList for dense wardrobe and history lists

## App Structure

```text
apps/mobile/
  app/
    (auth)/
    (protected)/
    _layout.tsx
  src/
    components/
    features/
      auth/
      wardrobe/
      recommendations/
      outfits/
      profile/
    lib/
      api/
      query/
      storage/
      utils/
    store/
    theme/
```

## Navigation

- Use Expo Router with route groups and nested layouts.
- Use protected layouts for authenticated areas.
- Prefer JavaScript tabs or custom tabs over unstable native-tabs APIs.
- Keep route ownership inside `app/` and shared logic inside `src/`.

## State Split

### TanStack Query

Use for:

- current user
- wardrobe lists and detail fetches
- recommendations
- outfits and history
- mutation state for uploads, feedback, and profile changes

### Zustand

Use for:

- access token and auth bootstrap flags
- short-lived UI concerns such as filters, draft selection, and sheet visibility
- small device-local preferences that do not justify server persistence

Avoid storing large remote datasets in Zustand when they belong in query caches.

## API Layer

- Centralize requests in an Axios client under `src/lib/api`.
- Attach access tokens through interceptors.
- Keep API modules aligned to backend domains:
  - `auth`
  - `users`
  - `wardrobe`
  - `recommendations`
  - `outfits`
- Normalize backend payloads at the API boundary when needed rather than scattering transformation logic across screens.

## Auth Storage

- Store refresh-session material securely with Expo SecureStore.
- Keep short-lived access token state in memory or Zustand-backed auth state.
- On app launch, bootstrap the session before mounting protected routes.
- Clear SecureStore and query caches on logout.

The detailed auth contract lives in `07-authentication.md`.

## Media Flows

### Wardrobe Ingestion

1. Pick from library or capture on device.
2. Preview and confirm the item.
3. Upload multipart data to the API.
4. Poll or refresh item state if processing is asynchronous.

### Rendering

- Use Expo Image for fast display and caching.
- Use FlashList for large wardrobe lists and history views.
- Use custom cards for recommendation presentation rather than generic list cells.

## Permissions

The mobile app must own the permission experience for:

- photo library access,
- camera access,
- notifications,
- location if recommendations use device coordinates.

Permission-denied states must be designed explicitly rather than treated as edge cases.

## Notifications

Use Expo Notifications for:

- daily suggestion reminders,
- re-engagement prompts for inactive users,
- future event- or calendar-based reminders if that feature is added later.

Push strategy can start simple. The main goal for the next version is reliable daily reminder capability.

## Offline and Cache Behavior

- Query caches should minimize unnecessary refetching.
- The app should render useful loading, empty, and retry states.
- Auth bootstrap must be resilient to slow networks.
- Offline support can be partial in the next version:
  - cached profile and lightweight list reuse are useful,
  - full offline mutation queuing is not required for v1.

## Screen Map

### Auth

- welcome / sign-in
- register
- forgot-password or account recovery placeholder if needed

### Protected Core

- dashboard / today's suggestions
- wardrobe list
- wardrobe item detail / edit
- add-item flow
- outfits / history
- profile / settings

### Supporting UI

- permission prompts and recovery screens
- loading / error / empty states
- modal or sheet-based actions for feedback and filters

## Feature Boundaries

### Auth Feature

- session bootstrap
- sign-in and sign-out
- user profile identity

### Wardrobe Feature

- upload
- item list and filter state
- item detail and edit

### Recommendations Feature

- daily suggestion request
- force refresh
- weather and context display

### Outfits Feature

- saved outfits
- wear action
- feedback action

### Profile Feature

- user details
- preferences if exposed through backend
- logout and notification settings

## Guardrails

- Do not force full web/mobile UI parity.
- Do not design around browser limitations anymore.
- Use react-native-reusables for safe primitives, but validate overlay-heavy components early on iOS and Android before making them central to core flows.
