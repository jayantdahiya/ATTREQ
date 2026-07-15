//
//  AppSession.swift
//  ATTREQ
//
//  App-wide authentication state (M1). Mirrors the RN client's
//  `src/store/auth-store.ts` semantics: bootstrap from Keychain, login,
//  register (register → login → best-effort profile enrichment), logout.
//

import Foundation
import Observation
import os

/// Owns the app's authentication state and drives the `RootView` routing gate.
///
/// Built on the M1 networking core: `KeychainStore` → `AuthSession` (token
/// lifecycle, single-flight 401 refresh) → `APIClient`.
@MainActor
@Observable
final class AppSession {
    /// Routing gate state. `.loading` only during initial `bootstrap()`.
    enum AuthState {
        case loading
        case loggedOut
        case authenticated(User)
    }

    private(set) var authState: AuthState = .loading

    private let authSession: AuthSession
    private let apiClient: APIClient

    /// Authenticated API client for feature repositories (M2+ tabs).
    var api: APIClient { apiClient }
    private let logger = Logger(subsystem: "com.attreq.ios", category: "AppSession")

    /// `bootstrap()` runs once per process; `.task` re-fires are no-ops.
    @ObservationIgnored private var didBootstrap = false

    init() {
        let baseURL = AppConfig.apiBaseURL
        let auth = AuthSession(keychain: KeychainStore(), baseURL: baseURL)
        authSession = auth
        apiClient = APIClient(baseURL: baseURL, authSession: auth)
    }

    // MARK: - Lifecycle

    /// Restores the session on launch: with stored tokens, validates them via
    /// `GET /users/me` (the API client transparently refreshes on 401).
    ///
    /// Failure policy:
    /// - auth failure (401 unrecoverable by refresh) → tokens cleared, `.loggedOut`
    /// - connectivity/server failure → retried once, then `.loggedOut` WITHOUT
    ///   clearing tokens so the next launch can try again.
    func bootstrap() async {
        // Route back to login whenever a refresh ultimately fails mid-session.
        await authSession.setOnSessionExpired { [weak self] in
            Task { @MainActor [weak self] in
                self?.authState = .loggedOut
            }
        }

        guard !didBootstrap else { return }
        didBootstrap = true

        // UI-test hook: start from a clean keychain so flows are deterministic.
        if CommandLine.arguments.contains("-reset-auth") {
            await authSession.clear()
        }

        let hasTokens = ((try? await authSession.validAccessToken()) ?? nil) != nil
        guard hasTokens else {
            authState = .loggedOut
            return
        }

        do {
            let user = try await fetchCurrentUserRetryingOnce()
            authState = .authenticated(user)
        } catch APIError.unauthorized {
            // Genuine auth failure (refresh included): drop the stale tokens.
            await authSession.clear()
            authState = .loggedOut
        } catch {
            // Connectivity or server failure: show login but KEEP tokens.
            logger.error("bootstrap: GET /users/me failed, keeping tokens: \(String(describing: error))")
            authState = .loggedOut
        }
    }

    // MARK: - Auth actions

    /// `POST /auth/login` (OAuth2 password form) → store tokens → authenticated.
    func login(email: String, password: String) async throws {
        let auth = try await performLogin(email: email, password: password)
        authState = .authenticated(auth.user)
    }

    /// Full registration flow, mirroring the RN client:
    /// 1. `POST /auth/register` — backend returns the **User only**, no tokens.
    /// 2. `POST /auth/login` — obtain the token pair.
    /// 3. Best-effort `PUT /users/me` (style preferences, manual city) and
    ///    `PATCH /users/me/location` (device coordinates). Failures here are
    ///    logged and never fail registration.
    /// 4. `GET /users/me` to pick up the enrichment, then authenticated.
    func register(_ data: RegistrationData) async throws {
        let trimmedName = data.fullName.trimmingCharacters(in: .whitespacesAndNewlines)
        let registerBody = RegisterRequest(
            email: data.email,
            password: data.password,
            fullName: trimmedName.isEmpty ? nil : trimmedName
        )
        let _: User = try await apiClient.request(
            Endpoint(method: .post, path: "auth/register", body: .json(registerBody), requiresAuth: false)
        )

        let auth = try await performLogin(email: data.email, password: data.password)

        // Best-effort profile enrichment — must never fail registration.
        var profile = ProfileUpdateBody()
        var styleParts = data.styleKeywords
        let occasions = data.occasions.trimmingCharacters(in: .whitespacesAndNewlines)
        if !occasions.isEmpty {
            styleParts.append(occasions)
        }
        if !styleParts.isEmpty {
            profile.stylePreferences = styleParts.joined(separator: ", ")
        }
        if case let .city(city) = data.location {
            profile.location = city
            profile.savedCity = city
        }
        if profile.stylePreferences != nil || profile.location != nil {
            do {
                let _: User = try await apiClient.request(
                    Endpoint(method: .put, path: "users/me", body: .json(profile))
                )
            } catch {
                logger.error("register: PUT /users/me failed (non-fatal): \(String(describing: error))")
            }
        }
        if case let .coordinates(latitude, longitude, city) = data.location {
            do {
                let _: User = try await apiClient.request(
                    Endpoint(
                        method: .patch,
                        path: "users/me/location",
                        body: .json(LocationUpdateRequest(lat: latitude, lon: longitude, city: city))
                    )
                )
            } catch {
                logger.error("register: PATCH /users/me/location failed (non-fatal): \(String(describing: error))")
            }
        }

        // Refresh so authState reflects the enrichment; fall back to the login user.
        let user = (try? await fetchCurrentUser()) ?? auth.user
        // If the session expired during the best-effort calls (onSessionExpired
        // already routed to .loggedOut and cleared tokens), don't resurrect an
        // authenticated state without tokens behind it.
        guard ((try? await authSession.validAccessToken()) ?? nil) != nil else { return }
        authState = .authenticated(user)
    }

    /// Best-effort `POST /auth/logout` (the API is stateless), then clears
    /// tokens locally and routes back to login. Never throws.
    func logout() async {
        do {
            try await apiClient.requestVoid(Endpoint(method: .post, path: "auth/logout"))
        } catch {
            logger.info("logout: POST /auth/logout failed (best-effort): \(String(describing: error))")
        }
        await authSession.clear()
        authState = .loggedOut
    }

    // MARK: - User refresh

    /// `POST /users/onboarding/complete`; the endpoint returns the refreshed
    /// user, which becomes the new authenticated payload (flips the gate).
    func completeOnboarding() async throws {
        let user: User = try await apiClient.request(
            Endpoint(method: .post, path: "users/onboarding/complete")
        )
        authState = .authenticated(user)
    }

    /// `GET /users/me` → replace the authenticated payload.
    func refreshUser() async throws {
        let user = try await fetchCurrentUser()
        authState = .authenticated(user)
    }

    // MARK: - Private

    private func performLogin(email: String, password: String) async throws -> AuthResponse {
        let auth: AuthResponse = try await apiClient.request(
            Endpoint(
                method: .post,
                path: "auth/login",
                body: .form(["username": email, "password": password]),
                requiresAuth: false
            )
        )
        await authSession.store(access: auth.accessToken, refresh: auth.refreshToken)
        return auth
    }

    private func fetchCurrentUser() async throws -> User {
        try await apiClient.request(Endpoint(method: .get, path: "users/me"))
    }

    /// One extra attempt after a transport-level failure (connectivity blip on
    /// launch); auth and server errors propagate immediately.
    private func fetchCurrentUserRetryingOnce() async throws -> User {
        do {
            return try await fetchCurrentUser()
        } catch let error as APIError {
            guard case .network = error else { throw error }
            try? await Task.sleep(for: .milliseconds(750))
            return try await fetchCurrentUser()
        }
    }
}

// MARK: - Request payloads

/// `PUT /users/me` body. Nil fields are omitted, matching the endpoint's
/// `exclude_unset` semantics.
///
/// Private (not `Core/Models/UserUpdateRequest`) because it additionally
/// carries `style_preferences` per the M1 registration mapping. NOTE: the
/// backend `UserUpdate` schema does not declare `style_preferences` today
/// (see `apps/api/src/attreq_api/schemas/user.py`), so the server silently
/// ignores it; sent anyway so the client is ready the moment the backend
/// accepts it.
private struct ProfileUpdateBody: Encodable {
    var stylePreferences: String?
    var location: String?
    var savedCity: String?
}
