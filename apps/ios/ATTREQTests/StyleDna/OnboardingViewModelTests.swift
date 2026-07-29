//
//  OnboardingViewModelTests.swift
//  ATTREQTests
//
//  OnboardingViewModel behavior: detected-item extraction from
//  `per_photo_extraction` (snake_case AND camelCase key tolerance, malformed
//  shapes skipped), the retry path's DELETE-before-re-upload ordering (so
//  retries REPLACE server-side seed photos instead of accumulating them),
//  and the skip path's POST /users/onboarding/complete.
//

import Foundation
import Testing
@testable import ATTREQ

/// Dedicated mock transport for this suite — its own static handler, separate
/// from the other suites' protocols, so parallel suites cannot race each other.
final class OnboardingMockURLProtocol: URLProtocol {
    typealias Handler = @Sendable (URLRequest) -> (status: Int, body: Data)

    static let handler = LockedBox<Handler?>(nil)

    static func makeSession() -> URLSession {
        let configuration = URLSessionConfiguration.ephemeral
        configuration.protocolClasses = [OnboardingMockURLProtocol.self]
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

// MARK: - Fixtures

/// Upload response with one usable photo carrying a single detected item
/// (verbatim snake_case keys, the shape the backend emits).
private let uploadSuccessJSON = Data("""
{"photos_processed":3,"photos_skipped":0,"wardrobe_items_seeded":1,"style_dna":null,
"photos":[{"id":"p-1","user_id":"u-1","file_path":"style-dna/p-1.jpg",
"file_url":"/uploads/style-dna/p-1.jpg","quality_ok":true,"quality_reason":null,
"per_photo_extraction":{"usable":true,
"wardrobe_items_detected":[{"category":"top","subcategory":"t-shirt","confidence":0.9}]},
"created_at":"2026-07-15T06:00:00.000000Z"}]}
""".utf8)

private let completedUserJSON = Data("""
{"id":"u-1","email":"a@b.c","full_name":"Test User","location":null,\
"saved_latitude":null,"saved_longitude":null,"saved_city":null,\
"is_active":true,"is_verified":false,\
"created_at":"2026-07-15T06:00:00.000000Z","updated_at":"2026-07-15T06:00:00.000000Z",\
"last_login":null,"oauth_provider":null,"style_preferences":"{}",\
"onboarding_completed":true,"onboarding_step":"complete"}
""".utf8)

// MARK: - Tests

@Suite(.serialized)
@MainActor
struct OnboardingViewModelTests {
    private static let baseURL = URL(string: "http://localhost:8001/api/v1")!

    private static func makeAPIClient() -> APIClient {
        APIClient(
            baseURL: baseURL,
            session: OnboardingMockURLProtocol.makeSession(),
            authSession: nil
        )
    }

    private static func makeRepository() -> StyleDnaRepository {
        StyleDnaRepository(apiClient: makeAPIClient())
    }

    private static func resetHandler() {
        OnboardingMockURLProtocol.handler.withLock { $0 = nil }
    }

    /// Installs a handler that logs "METHOD /path" in arrival order and
    /// responds via `respond`.
    private static func recordRequests(
        respond: @escaping @Sendable (_ method: String, _ path: String) -> (status: Int, body: Data)
    ) -> LockedBox<[String]> {
        let log = LockedBox<[String]>([])
        OnboardingMockURLProtocol.handler.withLock { handler in
            handler = { request in
                let method = request.httpMethod ?? "?"
                let path = request.url?.path() ?? "?"
                log.withLock { $0.append("\(method) \(path)") }
                return respond(method, path)
            }
        }
        return log
    }

    private func makePhoto(extraction: [String: JSONValue]?) -> StyleDnaPhoto {
        StyleDnaPhoto(
            id: "p-1",
            userId: "u-1",
            filePath: "style-dna/p-1.jpg",
            fileUrl: "/uploads/style-dna/p-1.jpg",
            qualityOk: true,
            qualityReason: nil,
            perPhotoExtraction: extraction,
            createdAt: .now
        )
    }

    private func makeResponse(extractions: [[String: JSONValue]?]) -> StyleDnaUploadResponse {
        StyleDnaUploadResponse(
            photosProcessed: extractions.count,
            photosSkipped: 0,
            wardrobeItemsSeeded: 0,
            styleDna: nil,
            photos: extractions.map(makePhoto(extraction:))
        )
    }

    // MARK: Detected-item extraction

    @Test func extractsDetectedItemsFromSnakeCaseKeys() {
        let response = makeResponse(extractions: [[
            "usable": .bool(true),
            "wardrobe_items_detected": .array([
                .object([
                    "category": .string("top"),
                    "subcategory": .string("t-shirt"),
                    "color_primary": .string("navy"),
                    "color_secondary": .string("white"),
                    "pattern": .string("striped"),
                    "occasion": .array([.string("casual"), .string("work")]),
                    "season": .array([.string("all")]),
                    "confidence": .number(0.9),
                    "bounding_region": .string("upper-half"),
                ]),
            ]),
        ]])

        let items = OnboardingViewModel.extractDetectedItems(from: response)

        #expect(items == [
            DetectedWardrobeItem(
                category: "top", subcategory: "t-shirt",
                colorPrimary: "navy", colorSecondary: "white", pattern: "striped",
                occasion: ["casual", "work"], season: ["all"],
                confidence: 0.9, boundingRegion: "upper-half"
            ),
        ])
    }

    @Test func extractsDetectedItemsFromCamelCaseKeys() {
        let response = makeResponse(extractions: [[
            "wardrobeItemsDetected": .array([
                .object([
                    "category": .string("bottom"),
                    "subcategory": .string("chinos"),
                    "colorPrimary": .string("beige"),
                    "occasion": .array([.string("casual")]),
                    "season": .array([.string("summer")]),
                    "confidence": .number(0.75),
                    "boundingRegion": .string("lower-half"),
                ]),
            ]),
        ]])

        let items = OnboardingViewModel.extractDetectedItems(from: response)

        #expect(items.count == 1)
        #expect(items.first?.category == "bottom")
        #expect(items.first?.colorPrimary == "beige")
        #expect(items.first?.confidence == 0.75)
        #expect(items.first?.boundingRegion == "lower-half")
    }

    @Test func missingDetectedItemsKeyYieldsNoItems() {
        let response = makeResponse(extractions: [
            ["usable": .bool(true), "style_signals": .object(["aesthetic": .string("minimalist")])],
            nil, // photo without any extraction blob
        ])

        #expect(OnboardingViewModel.extractDetectedItems(from: response).isEmpty)
    }

    @Test func wrongTypedDetectedItemsAreSkippedWithoutCrashing() {
        let response = makeResponse(extractions: [
            // Detected list is not an array at all → whole photo yields nothing.
            ["wardrobe_items_detected": .string("oops")],
            [
                "wardrobe_items_detected": .array([
                    .string("not-an-object"), // skipped
                    .object(["subcategory": .string("t-shirt")]), // no category → skipped
                    .object(["category": .number(7)]), // category not a string → skipped
                    .object([
                        // Valid category; malformed optional fields degrade
                        // instead of dropping the item.
                        "category": .string("shoes"),
                        "confidence": .string("high"), // not a number → 0
                        "occasion": .string("casual"), // not an array → []
                        "subcategory": .null, // not a string → ""
                    ]),
                ]),
            ],
        ])

        let items = OnboardingViewModel.extractDetectedItems(from: response)

        #expect(items == [
            DetectedWardrobeItem(
                category: "shoes", subcategory: "",
                colorPrimary: nil, colorSecondary: nil, pattern: nil,
                occasion: [], season: [],
                confidence: 0, boundingRegion: ""
            ),
        ])
    }

    // MARK: Retry replaces seed photos

    /// A retry after a failed upload must DELETE /users/style-dna/photos
    /// (best-effort) BEFORE the second upload POST, so the stored seed set is
    /// replaced rather than accumulated. The first attempt must NOT delete.
    @Test func retryDeletesStoredSeedPhotosBeforeReUploading() async throws {
        defer { Self.resetHandler() }
        let uploadCount = LockedBox(0)
        let log = Self.recordRequests { method, path in
            switch (method, path) {
            case ("DELETE", "/api/v1/users/style-dna/photos"):
                return (204, Data())
            case ("POST", "/api/v1/users/style-dna/upload"):
                let attempt = uploadCount.withLock { (count: inout Int) -> Int in
                    count += 1
                    return count
                }
                return attempt == 1
                    ? (500, Data(#"{"detail":"boom"}"#.utf8))
                    : (201, uploadSuccessJSON)
            default:
                return (404, Data())
            }
        }

        let repository = Self.makeRepository()
        let model = OnboardingViewModel()
        model.addPhotos([Data("a".utf8), Data("b".utf8), Data("c".utf8)])

        // First attempt: no delete, upload fails.
        await model.buildStyleDna(using: repository)
        guard case .failed = model.uploadState else {
            Issue.record("Expected .failed after 500, got \(model.uploadState)")
            return
        }
        #expect(log.withLock { $0 } == ["POST /api/v1/users/style-dna/upload"])

        // Retry: delete runs before the second upload POST.
        await model.buildStyleDna(using: repository)
        #expect(log.withLock { $0 } == [
            "POST /api/v1/users/style-dna/upload",
            "DELETE /api/v1/users/style-dna/photos",
            "POST /api/v1/users/style-dna/upload",
        ])
        #expect(model.uploadResponse != nil)
        #expect(model.detectedItems.map(\.subcategory) == ["t-shirt"])
        #expect(model.reviewSelection == [0])
    }

    /// The delete is best-effort: a failing DELETE must not block the retry's
    /// upload.
    @Test func retryStillUploadsWhenDeleteFails() async throws {
        defer { Self.resetHandler() }
        let uploadCount = LockedBox(0)
        let log = Self.recordRequests { method, path in
            switch (method, path) {
            case ("DELETE", "/api/v1/users/style-dna/photos"):
                return (500, Data(#"{"detail":"delete failed"}"#.utf8))
            case ("POST", "/api/v1/users/style-dna/upload"):
                let attempt = uploadCount.withLock { (count: inout Int) -> Int in
                    count += 1
                    return count
                }
                return attempt == 1
                    ? (500, Data(#"{"detail":"boom"}"#.utf8))
                    : (201, uploadSuccessJSON)
            default:
                return (404, Data())
            }
        }

        let repository = Self.makeRepository()
        let model = OnboardingViewModel()
        model.addPhotos([Data("a".utf8), Data("b".utf8), Data("c".utf8)])

        await model.buildStyleDna(using: repository)
        await model.buildStyleDna(using: repository)

        #expect(log.withLock { $0 }.last == "POST /api/v1/users/style-dna/upload")
        #expect(model.uploadResponse != nil)
    }

    // MARK: Skip

    /// "Skip for now" goes straight to POST /users/onboarding/complete —
    /// no upload, no delete.
    @Test func skipPostsOnboardingComplete() async throws {
        defer { Self.resetHandler() }
        let log = Self.recordRequests { method, path in
            if method == "POST", path == "/api/v1/users/onboarding/complete" {
                return (200, completedUserJSON)
            }
            return (404, Data())
        }

        let session = AppSession(
            apiClient: Self.makeAPIClient(),
            authSession: AuthSession(keychain: KeychainStore(), baseURL: Self.baseURL)
        )
        let model = OnboardingViewModel()

        await model.skip(session: session)

        #expect(log.withLock { $0 } == ["POST /api/v1/users/onboarding/complete"])
        #expect(model.completionError == nil)
        guard case let .authenticated(user) = session.authState else {
            Issue.record("Expected authenticated state after skip, got \(session.authState)")
            return
        }
        #expect(user.onboardingCompleted)
    }

    // MARK: - Personal-color selfie (RI-3)

    /// A successful analysis lands in `.done`.
    @Test func estimatePersonalColorSucceedsAndLandsInDoneState() async throws {
        defer { Self.resetHandler() }
        _ = Self.recordRequests { method, path in
            if method == "POST", path == "/api/v1/users/style-dna/selfie" {
                return (200, Data(#"{"style_dna":null,"photos":[]}"#.utf8))
            }
            return (404, Data())
        }

        let model = OnboardingViewModel()
        #expect(model.personalColorState == .idle)

        await model.estimatePersonalColor(
            imageData: Data("selfie".utf8),
            consent: true,
            using: Self.makeRepository()
        )

        #expect(model.personalColorState == .done)
        #expect(!model.isAnalyzingPersonalColor)
    }

    /// The endpoint is feature-flagged OFF by default (404) — this MUST NOT
    /// throw out of the view model or otherwise block the onboarding flow;
    /// it just lands in `.failed` so the view can still offer "Continue".
    @Test func estimatePersonalColor404DegradesToFailedStateWithoutBlockingFlow() async throws {
        defer { Self.resetHandler() }
        _ = Self.recordRequests { _, _ in
            (404, Data(#"{"detail":"Personal-color selfie estimation is not enabled"}"#.utf8))
        }

        let model = OnboardingViewModel()

        await model.estimatePersonalColor(
            imageData: Data("selfie".utf8),
            consent: true,
            using: Self.makeRepository()
        )

        guard case .failed = model.personalColorState else {
            Issue.record("Expected .failed after 404, got \(model.personalColorState)")
            return
        }

        // The flow is never blocked by this failure: onboarding completion
        // still succeeds independently of the selfie outcome.
        let log = Self.recordRequests { method, path in
            if method == "POST", path == "/api/v1/users/onboarding/complete" {
                return (200, completedUserJSON)
            }
            return (404, Data())
        }
        let session = AppSession(
            apiClient: Self.makeAPIClient(),
            authSession: AuthSession(keychain: KeychainStore(), baseURL: Self.baseURL)
        )
        await model.skip(session: session)
        #expect(log.withLock { $0 } == ["POST /api/v1/users/onboarding/complete"])
        #expect(model.completionError == nil)
    }
}
