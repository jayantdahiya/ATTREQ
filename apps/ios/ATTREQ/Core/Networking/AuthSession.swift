import Foundation

/// Owns the access/refresh token pair: Keychain-persisted, in-memory cached, with
/// single-flight refresh on 401 (mirrors the RN Axios interceptor semantics in
/// `apps/mobile/src/lib/api/client.ts`).
actor AuthSession {
    private enum Keys {
        static let access = "auth.access_token"
        static let refresh = "auth.refresh_token"
    }

    /// Response of `POST /auth/refresh` (backend also sends `token_type`, ignored here).
    private struct RefreshResponse: Decodable {
        let accessToken: String
    }

    /// Outcome of a single `POST /auth/refresh` attempt.
    private enum RefreshOutcome: Sendable {
        /// The endpoint returned a new access token.
        case success(newToken: String)
        /// The endpoint rejected the refresh token (HTTP 4xx) — the session is dead.
        case authRejected
        /// Transient failure (transport error, 5xx, malformed body): tokens must be kept.
        case transient(APIError)
    }

    /// Result committed by `finishRefresh` and observed by every awaiter.
    private enum RefreshResolution: Sendable {
        /// A new access token was stored; retry the original request.
        case refreshed
        /// The refresh was rejected; tokens cleared and `onSessionExpired` fired.
        case sessionExpired
        /// Transient failure; tokens kept, error surfaced to the caller.
        case transient(APIError)
        /// `store()`/`clear()` moved the session generation while the refresh was
        /// in flight; the stale result was discarded without touching tokens.
        case superseded
    }

    private let keychain: KeychainStore
    private let baseURL: URL
    private let urlSession: URLSession

    private var accessToken: String?
    private var refreshToken: String?
    private var hasLoadedFromKeychain = false

    /// Bumped by `store()` and `clear()` so an in-flight refresh started against an
    /// older token state can detect the change and discard its result (a logout must
    /// never be resurrected by a late refresh response, and a fresh login must never
    /// be wiped by a stale refresh failure).
    private var generation = 0

    /// In-flight refresh; concurrent 401 handlers await this instead of firing their own refresh.
    private var refreshTask: Task<RefreshResolution, Never>?

    /// Fired exactly once per auth-rejected refresh, after tokens are cleared
    /// (e.g. to route back to login). Transient refresh failures do NOT fire this.
    var onSessionExpired: (@Sendable () -> Void)?

    /// - Parameters:
    ///   - keychain: persistent token storage.
    ///   - baseURL: versioned API base (includes `/api/v1`), used for `POST auth/refresh`.
    ///   - session: injectable for tests (mock `URLProtocol`).
    init(keychain: KeychainStore, baseURL: URL, session: URLSession = .shared) {
        self.keychain = keychain
        self.baseURL = baseURL
        self.urlSession = session
    }

    /// Cross-actor setter for `onSessionExpired` (actor properties cannot be assigned from outside).
    func setOnSessionExpired(_ handler: (@Sendable () -> Void)?) {
        onSessionExpired = handler
    }

    /// Current access token (loaded from the Keychain on first use), or `nil` when logged out.
    func validAccessToken() async throws -> String? {
        loadFromKeychainIfNeeded()
        return accessToken
    }

    /// Injects `Authorization: Bearer <token>` when a token is available.
    /// Nonisolated so the `inout` request never crosses the actor boundary.
    nonisolated func authorize(_ request: inout URLRequest) async throws {
        if let token = try await validAccessToken() {
            request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        }
    }

    /// Handles a 401 from an authenticated request with a single-flight refresh:
    /// concurrent callers all await the same refresh task. Returns `true` when a new
    /// access token was obtained (caller should retry exactly once). When the refresh
    /// endpoint rejects the token (4xx), tokens are cleared, `onSessionExpired` fires
    /// once, and this returns `false`. When the refresh fails transiently (transport
    /// error or 5xx), tokens are KEPT and the failure is thrown as `APIError.network`
    /// / `APIError.http` so callers can apply their keep-tokens retry policies.
    ///
    /// - Parameter failedToken: the access token the failed request was sent with, when
    ///   known. If the current token already differs (a refresh completed in the
    ///   meantime), no new refresh is started — the caller simply retries.
    func handleUnauthorized(failedToken: String? = nil) async throws -> Bool {
        loadFromKeychainIfNeeded()

        // A refresh (or re-login) already replaced the token this request used.
        if let failedToken, accessToken != failedToken {
            return accessToken != nil
        }

        if let inFlight = refreshTask {
            let resolution = await inFlight.value
            return try Self.resolve(resolution)
        }

        guard let refreshToken else {
            // Nothing to refresh — e.g. a stray authenticated request completing
            // after logout. Fail the request without re-firing onSessionExpired.
            return false
        }

        // The task commits its outcome (store token / expire session) BEFORE completing,
        // so every awaiter observes the final token state as soon as it resumes. It
        // captures the current generation: if store()/clear() runs while the refresh
        // is in flight, the stale result is discarded.
        let startGeneration = generation
        let task = Task { [baseURL, urlSession] () -> RefreshResolution in
            let outcome = await Self.performRefresh(
                refreshToken: refreshToken,
                baseURL: baseURL,
                session: urlSession
            )
            return await self.finishRefresh(outcome, startedAt: startGeneration)
        }
        refreshTask = task
        let resolution = await task.value
        return try Self.resolve(resolution)
    }

    /// Persists a fresh token pair (login/registration success).
    func store(access: String, refresh: String) async {
        generation += 1
        accessToken = access
        refreshToken = refresh
        hasLoadedFromKeychain = true
        try? keychain.set(access, for: Keys.access)
        try? keychain.set(refresh, for: Keys.refresh)
    }

    /// Drops tokens from memory and the Keychain (logout).
    func clear() async {
        generation += 1
        accessToken = nil
        refreshToken = nil
        hasLoadedFromKeychain = true
        try? keychain.delete(Keys.access)
        try? keychain.delete(Keys.refresh)
    }

    // MARK: - Private

    /// Maps a committed refresh resolution to the caller contract:
    /// retry (`true`), give up (`false`), or throw the transient failure.
    private static func resolve(_ resolution: RefreshResolution) throws -> Bool {
        switch resolution {
        case .refreshed:
            return true
        case .sessionExpired, .superseded:
            return false
        case let .transient(error):
            throw error
        }
    }

    /// Runs inside the refresh task, before it completes: commits the outcome
    /// (store token / expire session / keep tokens on transient failure) and
    /// releases the single-flight slot. If `store()`/`clear()` moved the session
    /// generation while the refresh was in flight, the result is discarded —
    /// no token write, no `expireSession()`.
    private func finishRefresh(_ outcome: RefreshOutcome, startedAt startGeneration: Int) -> RefreshResolution {
        refreshTask = nil
        guard generation == startGeneration else { return .superseded }
        switch outcome {
        case let .success(newToken):
            accessToken = newToken
            try? keychain.set(newToken, for: Keys.access)
            return .refreshed
        case .authRejected:
            expireSession()
            return .sessionExpired
        case let .transient(error):
            return .transient(error)
        }
    }

    private func loadFromKeychainIfNeeded() {
        guard !hasLoadedFromKeychain else { return }
        hasLoadedFromKeychain = true
        accessToken = try? keychain.get(Keys.access)
        refreshToken = try? keychain.get(Keys.refresh)
    }

    private func expireSession() {
        accessToken = nil
        refreshToken = nil
        try? keychain.delete(Keys.access)
        try? keychain.delete(Keys.refresh)
        onSessionExpired?()
    }

    /// `POST {base}/auth/refresh` with `{"refresh_token": ...}`.
    /// Backend returns `{"access_token": ..., "token_type": "bearer"}` — the refresh
    /// token is NOT rotated, so the existing one is kept. Only an HTTP 4xx counts as
    /// the session being rejected; anything else (transport error, 5xx, malformed
    /// body) is a transient failure that must not destroy the session.
    private static func performRefresh(
        refreshToken: String,
        baseURL: URL,
        session: URLSession
    ) async -> RefreshOutcome {
        var request = URLRequest(url: baseURL.appending(path: "auth/refresh"))
        request.httpMethod = "POST"
        request.timeoutInterval = 30
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.httpBody = try? JSONEncoder().encode(["refresh_token": refreshToken])

        do {
            let (data, response) = try await session.data(for: request)
            guard let http = response as? HTTPURLResponse else {
                return .transient(.invalidResponse)
            }
            switch http.statusCode {
            case 200 ..< 300:
                let decoder = JSONDecoder()
                decoder.keyDecodingStrategy = .convertFromSnakeCase
                do {
                    let token = try decoder.decode(RefreshResponse.self, from: data).accessToken
                    return .success(newToken: token)
                } catch {
                    return .transient(.decoding(error))
                }
            case 400 ..< 500:
                return .authRejected
            default:
                return .transient(.http(status: http.statusCode, body: data))
            }
        } catch {
            return .transient(.network(error))
        }
    }
}
