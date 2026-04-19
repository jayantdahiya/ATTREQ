# Authentication Plan

## Goal

Support reliable mobile authentication for the planned Expo app without forcing browser-specific assumptions into the client contract.

## Principles

- The mobile app should use explicit token handling, not web-cookie assumptions.
- Sensitive session material should be stored in Expo SecureStore.
- Protected route access should be controlled through Expo Router layouts.
- Logout must fully clear local auth state and cached user data.

## Planned Client Contract

### Login

1. The user submits credentials from the mobile auth flow.
2. The API returns access and refresh credentials according to the backend contract.
3. The client stores refresh-session material in SecureStore.
4. The client stores short-lived access state in the auth store and enables protected navigation.

Current contract:

- `POST /auth/login`
- `Content-Type: application/x-www-form-urlencoded`
- fields: `username`, `password`
- response: `access_token`, `refresh_token`, `token_type`, `user`

### Bootstrap on Launch

1. The app checks SecureStore during startup.
2. If refresh-session material exists, the app attempts token refresh before rendering protected routes.
3. If refresh fails, the app clears stored credentials and returns to the auth flow.

### Access Token Usage

- Attach the access token through the shared Axios client.
- Treat the access token as short-lived.
- Refresh only through the explicit refresh endpoint rather than hidden browser behavior.

### Refresh Behavior

- Use a dedicated refresh action in the auth layer.
- If the current backend expects the refresh token in the request body, preserve that explicit contract until the backend is intentionally changed.
- On refresh failure, the user should be logged out cleanly rather than left in an indeterminate state.

Current contract:

- `POST /auth/refresh`
- `Content-Type: application/json`
- body: `{ "refresh_token": string }`
- response: `access_token`, `token_type`

## Router Protection

Use Expo Router layouts and route groups such as:

```text
app/
  (auth)/
  (protected)/
```

Rules:

- unauthenticated users stay inside `(auth)`,
- authenticated users are redirected into `(protected)`,
- bootstrap screens block navigation while the session state is resolving.

## Auth Store Responsibilities

The auth store should own:

- access token state,
- bootstrap status,
- refresh status,
- sign-in and sign-out actions,
- current session validity.

It should not own large user-profile datasets that belong in query state.

## Query Cache Rules

- `me` or current-user data should come from TanStack Query.
- On logout, clear auth state and invalidate or clear related query caches.
- On refresh success, retry failed authenticated requests where appropriate.

## Current Mobile Action Mapping

- Recommendation cards do not currently include persisted outfit IDs.
- The mobile client should materialize a suggestion through `POST /outfits` before calling:
  - `POST /outfits/{outfit_id}/wear`
  - `POST /outfits/{outfit_id}/feedback`
- This keeps wear tracking and feedback wired without inventing a separate recommendation-action API.

## Security Notes

- Use SecureStore for persisted sensitive auth material.
- Avoid writing tokens to AsyncStorage unless there is a deliberate non-sensitive reason.
- Do not rely on web-only cookie handling as the mobile default.

## Deferred Scope

The following can be deferred until the core mobile loop is stable:

- Google OAuth and social login
- biometric unlock wrappers
- advanced multi-device session management
