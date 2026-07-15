# M1 — Networking Core & Auth

> **Status:** In progress (started 2026-07-15)
> **Parent:** [`00-goal.md`](00-goal.md). Environment facts (backend on :8001, compose project `attreq-dev`, ports 5433/6380): see [`01-milestone-0-scaffold.md`](01-milestone-0-scaffold.md).

## Objective

Login (artboard 01), 3-step registration wizard (artboards 02–04), and the root routing gate work end-to-end against the local backend, in light and dark. Token lifecycle (Keychain storage, transparent 401 refresh, logout) is implemented and unit-tested.

## Behavioral references (read before implementing)

- RN client: `apps/mobile/src/lib/api/client.ts` (Axios + refresh interceptor), `session.ts`, `auth.ts`, `users.ts`, `src/store/auth-store.ts`, `app/index.tsx` (routing gate)
- Backend truth: `apps/api/src/attreq_api/api/v1/endpoints/auth.py`, `users.py`; `schemas/user.py`, `schemas/auth*.py`
- Design: `assets/design/ios-redesign-v2/attreq-auth.jsx` (all four screens, exact measurements)

Key backend facts: `POST /auth/register` returns the **User only** (no tokens) — the RN client follows with `POST /auth/login`; replicate that. Access token 15 min, refresh 7 days; refresh endpoint per RN `session.ts`.

## Architecture

```
ATTREQ/Core/
├── Networking/    APIClient (URLSession async/await), Endpoint, APIError, AuthSession (actor)
├── Keychain/      KeychainStore (kSecClassGenericPassword wrapper)
├── Location/      LocationProvider (CLLocationManager async wrapper, when-in-use)
└── Models/        Codable mirrors of apps/mobile/src/lib/api/types.ts (ALL of them now — later milestones reuse)
ATTREQ/Features/Auth/
├── LoginView.swift + LoginViewModel.swift
├── Register/      RegisterFlowView (wizard shell + AttreqStepNav), AccountStepView, StyleStepView, LocationStepView, RegisterViewModel
ATTREQ/App/        AppSession (@Observable: authState .loading/.loggedOut/.authenticated(User)), RootView gate
```

Contracts:
- `APIClient.request<T: Decodable>(_ endpoint: Endpoint) async throws -> T`; snake_case keyDecodingStrategy; base URL `http://localhost:8001/api/v1` in Debug (compile-time constant, overridable via `ATTREQ_API_URL` env).
- `AuthSession` (actor): holds tokens, injects `Authorization: Bearer`, on 401 performs **single-flight** refresh then retries once; failed refresh → logout notification. Tokens persist via KeychainStore.
- `AppSession` (@Observable, @MainActor): `bootstrap()` (load tokens → `GET /users/me`), `login/register/logout`. RootView switches: loggedOut → LoginView/Register; authenticated + `!onboarding_completed` → onboarding placeholder; else → tabs placeholder (real screens in M2–M4).

## Registration wizard mapping

Step 1 (account): local validation only (email format, password ≥ 8, match). Step 2 (style): chips (Minimal/Earthy/Tailored/Layered/Casual/Formal/Streetwear/Athleisure) + occasions text → joined string for `style_preferences`. Step 3 (location): "Use device location" row → CoreLocation → reverse-geocode city; or manual city text. Submit = `POST /auth/register` → `POST /auth/login` → `PUT /users/me` (style_preferences) → `PATCH /users/me/location` (best-effort; failures non-fatal, user proceeds). "Forgot password" on login renders as inert MonoLabel (no backend endpoint — goal-doc note).

## Work packages

| WP | Files | Content |
|---|---|---|
| WP0 (orchestrator) | pbxproj | Add ATTREQTests unit-test target (synchronized folder ATTREQTests/) |
| WP1 | Core/Networking/, Core/Keychain/ | APIClient, Endpoint, APIError, AuthSession actor, KeychainStore + tests (single-flight refresh via mock URLProtocol, Keychain roundtrip) |
| WP2 | Core/Models/ | All Codable models from types.ts + decoding tests with real backend JSON fixtures |
| WP3 | Features/Auth/, Core/Location/ | All four screens pixel-faithful to attreq-auth.jsx + view models + LocationProvider |
| WP4 (after WP1–3 interfaces) | App/ | AppSession, RootView gate, logout wiring |

## Exit criteria

1. Fresh simulator install: register via wizard → lands authenticated; relaunch app → still authenticated (Keychain); logout → back to login; login again works. All against localhost:8001.
2. 401-refresh single-flight and Keychain tests green via `xcodebuild test`.
3. Screens match artboards 01–04 in light + dark (screenshots).
4. Committed on `ios-native`.
