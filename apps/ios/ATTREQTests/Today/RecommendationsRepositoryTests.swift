//
//  RecommendationsRepositoryTests.swift
//  ATTREQTests
//
//  RecommendationsRepository contract against the backend
//  (endpoints/recommendations.py GET /recommendations/daily): verb, path,
//  query params (occasion / force_refresh, and NO lat/lon — the saved-location
//  path), and response decoding including the naive `generated_at` timestamp.
//

import Foundation
import Testing
@testable import ATTREQ

/// Dedicated mock transport for this suite — its own static handler, separate
/// from the other suites' protocols, so parallel suites cannot race each other.
final class RecommendationsMockURLProtocol: URLProtocol {
    typealias Handler = @Sendable (URLRequest, Data?) -> (status: Int, body: Data)

    static let handler = LockedBox<Handler?>(nil)

    static func makeSession() -> URLSession {
        let configuration = URLSessionConfiguration.ephemeral
        configuration.protocolClasses = [RecommendationsMockURLProtocol.self]
        return URLSession(configuration: configuration)
    }

    override class func canInit(with request: URLRequest) -> Bool { true }
    override class func canonicalRequest(for request: URLRequest) -> URLRequest { request }

    override func startLoading() {
        guard let handler = Self.handler.withLock({ $0 }), let url = request.url else {
            client?.urlProtocol(self, didFailWithError: URLError(.unsupportedURL))
            return
        }
        let (status, body) = handler(request, request.httpBody)
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

// MARK: - Backend JSON fixtures (shapes from schemas/recommendation.py)

private let weatherJSON = """
{"temp":21.5,"feels_like":20.1,"condition":"Clear","description":"clear sky",\
"humidity":40,"wind_speed":3.2,"icon":"01d"}
"""

private func suggestionJSON(top: String, bottom: String, occasion: String = "casual") -> String {
    """
    {"top_item_id":"\(top)",\
    "top_item":{"id":"\(top)","category":"top","color_primary":"navy","pattern":"solid",\
    "image_url":"/uploads/\(top).jpg","thumbnail_url":null},\
    "bottom_item_id":"\(bottom)",\
    "bottom_item":{"id":"\(bottom)","category":"bottom","color_primary":"beige","pattern":null,\
    "image_url":null,"thumbnail_url":"/uploads/\(bottom)-thumb.jpg"},\
    "accessory_item":null,\
    "scores":{"color_harmony":0.8,"formality":0.7,"preference_bonus":0.1,"total":0.86},\
    "weather_context":\(weatherJSON),\
    "occasion_context":"\(occasion)"}
    """
}

/// `generated_at` is deliberately timezone-naive — the backend emits
/// `datetime.utcnow().isoformat()`.
private func dailyResponseJSON(suggestions: [String], occasion: String = "casual", cached: Bool = false) -> Data {
    Data("""
    {"suggestions":[\(suggestions.joined(separator: ","))],\
    "total_suggestions":\(suggestions.count),\
    "generated_at":"2026-07-15T06:35:37.729782",\
    "weather":\(weatherJSON),\
    "occasion":"\(occasion)","cached":\(cached)}
    """.utf8)
}

/// One captured request: everything the assertions need, taken inside the handler.
private struct CapturedRequest: Sendable {
    var method: String?
    var url: URL?
    var path: String?
}

// MARK: - Tests

@Suite(.serialized)
struct RecommendationsRepositoryTests {
    private static let baseURL = URL(string: "http://localhost:8001/api/v1")!

    private static func makeRepository() -> RecommendationsRepository {
        let client = APIClient(
            baseURL: baseURL,
            session: RecommendationsMockURLProtocol.makeSession(),
            authSession: nil
        )
        return RecommendationsRepository(apiClient: client)
    }

    private static func capture(status: Int, body: Data) -> LockedBox<CapturedRequest?> {
        let captured = LockedBox<CapturedRequest?>(nil)
        RecommendationsMockURLProtocol.handler.withLock { handler in
            handler = { request, _ in
                captured.withLock {
                    $0 = CapturedRequest(method: request.httpMethod, url: request.url, path: request.url?.path())
                }
                return (status, body)
            }
        }
        return captured
    }

    private static func resetHandler() {
        RecommendationsMockURLProtocol.handler.withLock { $0 = nil }
    }

    private static func queryItems(of url: URL?) -> [String: String] {
        guard let url, let components = URLComponents(url: url, resolvingAgainstBaseURL: false) else { return [:] }
        return Dictionary(uniqueKeysWithValues: (components.queryItems ?? []).map { ($0.name, $0.value ?? "") })
    }

    /// Defaults mirror RN's steady state: no lat/lon (the backend uses the
    /// saved profile location), no force_refresh param at all.
    @Test func dailyDefaultsSendGETWithNoLocationAndNoForceRefresh() async throws {
        defer { Self.resetHandler() }
        let captured = Self.capture(
            status: 200,
            body: dailyResponseJSON(suggestions: [suggestionJSON(top: "t-1", bottom: "b-1")])
        )

        let response = try await Self.makeRepository().daily()

        let request = try #require(captured.withLock { $0 })
        #expect(request.method == "GET")
        #expect(request.path == "/api/v1/recommendations/daily")
        let query = Self.queryItems(of: request.url)
        #expect(query["lat"] == nil)
        #expect(query["lon"] == nil)
        #expect(query["force_refresh"] == nil)
        #expect(query["occasion"] == nil)

        #expect(response.suggestions.count == 1)
        #expect(response.totalSuggestions == 1)
        #expect(response.occasion == "casual")
        #expect(!response.cached)
    }

    @Test func dailySendsOccasionAndForceRefreshWhenAsked() async throws {
        defer { Self.resetHandler() }
        let captured = Self.capture(
            status: 200,
            body: dailyResponseJSON(suggestions: [suggestionJSON(top: "t-1", bottom: "b-1", occasion: "formal")], occasion: "formal")
        )

        _ = try await Self.makeRepository().daily(refresh: true, occasion: "formal")

        let request = try #require(captured.withLock { $0 })
        let query = Self.queryItems(of: request.url)
        #expect(query["occasion"] == "formal")
        #expect(query["force_refresh"] == "true")
    }

    @Test func dailyDecodesSuggestionsWeatherAndNaiveGeneratedAt() async throws {
        defer { Self.resetHandler() }
        _ = Self.capture(
            status: 200,
            body: dailyResponseJSON(
                suggestions: [suggestionJSON(top: "t-1", bottom: "b-1"), suggestionJSON(top: "t-2", bottom: "b-2")],
                cached: true
            )
        )

        let response = try await Self.makeRepository().daily()

        #expect(response.suggestions.map(\.topItemId) == ["t-1", "t-2"])
        #expect(response.suggestions[0].topItem.colorPrimary == "navy")
        #expect(response.suggestions[0].bottomItem.thumbnailUrl == "/uploads/b-1-thumb.jpg")
        #expect(response.suggestions[0].accessoryItem == nil)
        #expect(response.suggestions[0].scores.total == 0.86)
        #expect(response.suggestions[0].weatherContext.temp == 21.5)
        #expect(response.weather.condition == "Clear")
        #expect(response.weather.windSpeed == 3.2)
        #expect(response.cached)
        // Naive timestamp treated as UTC.
        #expect(abs(response.generatedAt.timeIntervalSince(Date(timeIntervalSince1970: 1_784_097_337.729782))) < 1)
    }

    @Test func dailySurfacesHTTPErrorsAsAPIError() async throws {
        defer { Self.resetHandler() }
        _ = Self.capture(
            status: 404,
            body: Data(#"{"detail":"Insufficient wardrobe items to generate outfit suggestions."}"#.utf8)
        )

        await #expect(throws: APIError.self) {
            _ = try await Self.makeRepository().daily()
        }
    }
}
