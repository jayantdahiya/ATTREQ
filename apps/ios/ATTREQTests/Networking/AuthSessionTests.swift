import Foundation
import Testing
@testable import ATTREQ

// MARK: - Test helpers

/// Minimal lock-protected mutable box (Mutex requires iOS 18; deployment target is 17).
final class LockedBox<Value>: @unchecked Sendable {
    private let lock = NSLock()
    private var value: Value

    init(_ value: Value) {
        self.value = value
    }

    func withLock<R>(_ body: (inout Value) -> R) -> R {
        lock.lock()
        defer { lock.unlock() }
        return body(&value)
    }
}

/// URLProtocol that answers every request via a static, lock-protected handler.
/// Tests using it must run serialized (shared static state).
/// A non-positive `status` simulates a transport-level failure (the request
/// throws `URLError(.notConnectedToInternet)` instead of receiving a response).
final class MockURLProtocol: URLProtocol {
    typealias Handler = @Sendable (URLRequest) -> (status: Int, body: Data)

    static let handler = LockedBox<Handler?>(nil)

    static func makeSession() -> URLSession {
        let configuration = URLSessionConfiguration.ephemeral
        configuration.protocolClasses = [MockURLProtocol.self]
        return URLSession(configuration: configuration)
    }

    override class func canInit(with request: URLRequest) -> Bool { true }
    override class func canonicalRequest(for request: URLRequest) -> URLRequest { request }

    override func startLoading() {
        guard let handler = Self.handler.withLock({ $0 }), let url = request.url else {
            client?.urlProtocol(self, didFailWithError: URLError(.unsupportedURL))
            return
        }
        let (status, body) = handler(request)
        guard status > 0 else {
            client?.urlProtocol(self, didFailWithError: URLError(.notConnectedToInternet))
            return
        }
        let response = HTTPURLResponse(
            url: url,
            statusCode: status,
            httpVersion: "HTTP/1.1",
            headerFields: ["Content-Type": "application/json"]
        )!
        client?.urlProtocol(self, didReceive: response, cacheStoragePolicy: .notAllowed)
        client?.urlProtocol(self, didLoad: body)
        client?.urlProtocolDidFinishLoading(self)
    }

    override func stopLoading() {}
}

// MARK: - Tests

@Suite(.serialized)
struct AuthSessionTests {
    private static let baseURL = URL(string: "http://localhost:8001/api/v1")!

    private static func makeStack() -> (KeychainStore, AuthSession, APIClient) {
        let keychain = KeychainStore(service: "com.attreq.ios.tests.\(UUID().uuidString)")
        let session = MockURLProtocol.makeSession()
        let auth = AuthSession(keychain: keychain, baseURL: baseURL, session: session)
        let client = APIClient(baseURL: baseURL, session: session, authSession: auth)
        return (keychain, auth, client)
    }

    private struct Message: Decodable, Sendable {
        let message: String
    }

    /// N concurrent requests hit 401 with the stale token; exactly ONE refresh call is
    /// made, and all N requests succeed after the transparent retry.
    @Test func concurrent401sTriggerSingleFlightRefreshAndAllSucceed() async throws {
        let (keychain, auth, client) = Self.makeStack()
        defer { try? keychain.delete("auth.access_token"); try? keychain.delete("auth.refresh_token") }

        await auth.store(access: "expired-token", refresh: "refresh-token")

        let refreshCalls = LockedBox(0)
        MockURLProtocol.handler.withLock { handler in
            handler = { request in
                if request.url?.path().hasSuffix("/auth/refresh") == true {
                    refreshCalls.withLock { $0 += 1 }
                    // Hold the refresh open briefly so concurrent 401 handlers join it.
                    Thread.sleep(forTimeInterval: 0.05)
                    return (200, Data(#"{"access_token":"fresh-token","token_type":"bearer"}"#.utf8))
                }
                if request.value(forHTTPHeaderField: "Authorization") == "Bearer fresh-token" {
                    return (200, Data(#"{"message":"ok"}"#.utf8))
                }
                return (401, Data(#"{"detail":"Could not validate credentials"}"#.utf8))
            }
        }
        defer { MockURLProtocol.handler.withLock { $0 = nil } }

        let requestCount = 8
        let results = try await withThrowingTaskGroup(of: Message.self) { group in
            for _ in 0 ..< requestCount {
                group.addTask {
                    try await client.request(Endpoint(method: .get, path: "users/me"))
                }
            }
            var collected: [Message] = []
            for try await message in group {
                collected.append(message)
            }
            return collected
        }

        #expect(results.count == requestCount)
        #expect(results.allSatisfy { $0.message == "ok" })
        #expect(refreshCalls.withLock { $0 } == 1)

        let currentToken = try await auth.validAccessToken()
        #expect(currentToken == "fresh-token")
        // New access token persisted; refresh token untouched (backend does not rotate it).
        #expect(try keychain.get("auth.access_token") == "fresh-token")
        #expect(try keychain.get("auth.refresh_token") == "refresh-token")
    }

    /// 401 with a refresh that also fails: request surfaces `.unauthorized`,
    /// `onSessionExpired` fires exactly once, and tokens are cleared everywhere.
    @Test func failedRefreshFiresSessionExpiredAndClearsTokens() async throws {
        let (keychain, auth, client) = Self.makeStack()

        await auth.store(access: "expired-token", refresh: "dead-refresh-token")

        MockURLProtocol.handler.withLock { handler in
            handler = { request in
                if request.url?.path().hasSuffix("/auth/refresh") == true {
                    return (401, Data(#"{"detail":"Invalid refresh token"}"#.utf8))
                }
                return (401, Data(#"{"detail":"Could not validate credentials"}"#.utf8))
            }
        }
        defer { MockURLProtocol.handler.withLock { $0 = nil } }

        await confirmation("onSessionExpired fires exactly once", expectedCount: 1) { expired in
            await auth.setOnSessionExpired { expired() }

            do {
                try await client.requestVoid(Endpoint(method: .get, path: "users/me"))
                Issue.record("Expected APIError.unauthorized to be thrown")
            } catch let error as APIError {
                guard case .unauthorized = error else {
                    Issue.record("Expected .unauthorized, got \(error)")
                    return
                }
            } catch {
                Issue.record("Expected APIError.unauthorized, got \(error)")
            }
        }

        let token = try await auth.validAccessToken()
        #expect(token == nil)
        #expect(try keychain.get("auth.access_token") == nil)
        #expect(try keychain.get("auth.refresh_token") == nil)
    }

    /// Tokens stored by one AuthSession are visible to a fresh instance via the Keychain
    /// (app-relaunch persistence), and `clear()` removes them.
    @Test func tokensPersistAcrossInstancesAndClearRemovesThem() async throws {
        let keychain = KeychainStore(service: "com.attreq.ios.tests.\(UUID().uuidString)")
        let session = MockURLProtocol.makeSession()

        let first = AuthSession(keychain: keychain, baseURL: Self.baseURL, session: session)
        await first.store(access: "persisted-access", refresh: "persisted-refresh")

        let second = AuthSession(keychain: keychain, baseURL: Self.baseURL, session: session)
        let restored = try await second.validAccessToken()
        #expect(restored == "persisted-access")

        await second.clear()
        let afterClear = try await second.validAccessToken()
        #expect(afterClear == nil)

        let third = AuthSession(keychain: keychain, baseURL: Self.baseURL, session: session)
        let afterRelaunch = try await third.validAccessToken()
        #expect(afterRelaunch == nil)
    }

    /// Unauthenticated endpoints (login/register/refresh) never trigger the refresh dance —
    /// a 401 surfaces directly (mirrors the RN interceptor's URL exclusions).
    @Test func unauthenticatedEndpointDoesNotAttemptRefresh() async throws {
        let (_, auth, client) = Self.makeStack()
        await auth.store(access: "expired-token", refresh: "refresh-token")

        let refreshCalls = LockedBox(0)
        MockURLProtocol.handler.withLock { handler in
            handler = { request in
                if request.url?.path().hasSuffix("/auth/refresh") == true {
                    refreshCalls.withLock { $0 += 1 }
                    return (200, Data(#"{"access_token":"fresh-token","token_type":"bearer"}"#.utf8))
                }
                return (401, Data(#"{"detail":"Incorrect email or password"}"#.utf8))
            }
        }
        defer { MockURLProtocol.handler.withLock { $0 = nil } }

        do {
            try await client.requestVoid(
                Endpoint(
                    method: .post,
                    path: "auth/login",
                    body: .form(["username": "a@b.c", "password": "nope"]),
                    requiresAuth: false
                )
            )
            Issue.record("Expected APIError.unauthorized to be thrown")
        } catch let error as APIError {
            guard case .unauthorized = error else {
                Issue.record("Expected .unauthorized, got \(error)")
                return
            }
        }

        #expect(refreshCalls.withLock { $0 } == 0)
    }

    /// Logging out (`clear()`) while a refresh request is still in flight must win:
    /// when the refresh later completes with a fresh token, that stale result is
    /// discarded — nothing is written back to memory or the Keychain.
    @Test func clearDuringInFlightRefreshDoesNotResurrectTokens() async throws {
        let (keychain, auth, client) = Self.makeStack()
        defer { try? keychain.delete("auth.access_token"); try? keychain.delete("auth.refresh_token") }

        await auth.store(access: "expired-token", refresh: "refresh-token")

        let refreshStarted = DispatchSemaphore(value: 0)
        let releaseRefresh = DispatchSemaphore(value: 0)
        MockURLProtocol.handler.withLock { handler in
            handler = { request in
                if request.url?.path().hasSuffix("/auth/refresh") == true {
                    refreshStarted.signal()
                    // Hold the refresh open until the test has logged out.
                    releaseRefresh.wait()
                    return (200, Data(#"{"access_token":"resurrected-token","token_type":"bearer"}"#.utf8))
                }
                return (401, Data(#"{"detail":"Could not validate credentials"}"#.utf8))
            }
        }
        defer { MockURLProtocol.handler.withLock { $0 = nil } }

        // Kick off a request that 401s and starts the (held-open) refresh.
        let requestTask = Task {
            try await client.requestVoid(Endpoint(method: .get, path: "users/me"))
        }

        // Wait (off the cooperative pool) until the refresh is actually in flight.
        await withCheckedContinuation { continuation in
            DispatchQueue.global().async {
                refreshStarted.wait()
                continuation.resume()
            }
        }

        await auth.clear() // logout while the refresh is in flight
        releaseRefresh.signal() // now let the refresh "succeed"

        _ = await requestTask.result // outcome of the original request is irrelevant here

        let token = try await auth.validAccessToken()
        #expect(token == nil)
        #expect(try keychain.get("auth.access_token") == nil)
        #expect(try keychain.get("auth.refresh_token") == nil)
    }

    /// A transport-level refresh failure is transient: tokens are retained,
    /// `onSessionExpired` does NOT fire, and the original request surfaces
    /// `.network` instead of `.unauthorized`.
    @Test func transientNetworkRefreshFailureKeepsTokensAndDoesNotExpireSession() async throws {
        let (keychain, auth, client) = Self.makeStack()
        defer { try? keychain.delete("auth.access_token"); try? keychain.delete("auth.refresh_token") }

        await auth.store(access: "expired-token", refresh: "refresh-token")

        MockURLProtocol.handler.withLock { handler in
            handler = { request in
                if request.url?.path().hasSuffix("/auth/refresh") == true {
                    return (-1, Data()) // transport failure (URLError)
                }
                return (401, Data(#"{"detail":"Could not validate credentials"}"#.utf8))
            }
        }
        defer { MockURLProtocol.handler.withLock { $0 = nil } }

        let expiredFired = LockedBox(false)
        await auth.setOnSessionExpired { expiredFired.withLock { $0 = true } }

        do {
            try await client.requestVoid(Endpoint(method: .get, path: "users/me"))
            Issue.record("Expected APIError.network to be thrown")
        } catch let error as APIError {
            guard case .network = error else {
                Issue.record("Expected .network, got \(error)")
                return
            }
        }

        #expect(expiredFired.withLock { $0 } == false)
        let token = try await auth.validAccessToken()
        #expect(token == "expired-token")
        #expect(try keychain.get("auth.access_token") == "expired-token")
        #expect(try keychain.get("auth.refresh_token") == "refresh-token")
    }

    /// A 5xx from the refresh endpoint is transient too: tokens are retained,
    /// `onSessionExpired` does NOT fire, and the original request surfaces
    /// `.http(status: 503, ...)`.
    @Test func serverErrorRefreshFailureKeepsTokensAndSurfacesHTTPError() async throws {
        let (keychain, auth, client) = Self.makeStack()
        defer { try? keychain.delete("auth.access_token"); try? keychain.delete("auth.refresh_token") }

        await auth.store(access: "expired-token", refresh: "refresh-token")

        MockURLProtocol.handler.withLock { handler in
            handler = { request in
                if request.url?.path().hasSuffix("/auth/refresh") == true {
                    return (503, Data(#"{"detail":"Service unavailable"}"#.utf8))
                }
                return (401, Data(#"{"detail":"Could not validate credentials"}"#.utf8))
            }
        }
        defer { MockURLProtocol.handler.withLock { $0 = nil } }

        let expiredFired = LockedBox(false)
        await auth.setOnSessionExpired { expiredFired.withLock { $0 = true } }

        do {
            try await client.requestVoid(Endpoint(method: .get, path: "users/me"))
            Issue.record("Expected APIError.http to be thrown")
        } catch let error as APIError {
            guard case let .http(status, _) = error, status == 503 else {
                Issue.record("Expected .http(503), got \(error)")
                return
            }
        }

        #expect(expiredFired.withLock { $0 } == false)
        let token = try await auth.validAccessToken()
        #expect(token == "expired-token")
        #expect(try keychain.get("auth.access_token") == "expired-token")
        #expect(try keychain.get("auth.refresh_token") == "refresh-token")
    }
}
