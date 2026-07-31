//
//  SwipeDeckViewModelTests.swift
//  ATTREQTests
//
//  RI-5 (Task 5.3) — SwipeDeckViewModel: load/empty/failed states, rating
//  advances the deck, 429 sets `capReached` without advancing.
//

import Foundation
import Testing
@testable import ATTREQ

/// Dedicated mock transport — its own static handler, separate from other
/// suites' protocols so parallel suites cannot race each other.
final class SwipeDeckMockURLProtocol: URLProtocol {
    typealias Handler = @Sendable (URLRequest, Data?) -> (status: Int, body: Data)

    static let handler = LockedBox<Handler?>(nil)

    static func makeSession() -> URLSession {
        let configuration = URLSessionConfiguration.ephemeral
        configuration.protocolClasses = [SwipeDeckMockURLProtocol.self]
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
            url: url, statusCode: status, httpVersion: "HTTP/1.1", headerFields: ["Content-Type": "application/json"]
        )!
        client?.urlProtocol(self, didReceive: response, cacheStoragePolicy: .notAllowed)
        client?.urlProtocol(self, didLoad: body)
        client?.urlProtocolDidFinishLoading(self)
    }

    override func stopLoading() {}
}

private let weatherJSON = """
{"temp":21.5,"feels_like":20.1,"condition":"Clear","description":"clear sky",\
"humidity":40,"wind_speed":3.2,"icon":"01d"}
"""

private func suggestionJSON(top: String, bottom: String, index: Int) -> String {
    """
    {"top_item_id":"\(top)",\
    "top_item":{"id":"\(top)","category":"top","color_primary":"navy","pattern":"solid","image_url":null,"thumbnail_url":null},\
    "bottom_item_id":"\(bottom)",\
    "bottom_item":{"id":"\(bottom)","category":"bottom","color_primary":"beige","pattern":null,"image_url":null,"thumbnail_url":null},\
    "accessory_item":null,\
    "scores":{"color_harmony":0.8,"formality":0.7,"preference_bonus":0.1,"total":0.86},\
    "weather_context":\(weatherJSON),\
    "occasion_context":"casual",\
    "outfit_index":\(index)}
    """
}

private func swipeDeckJSON(count: Int, recommendationId: String = "rec-swipe-1") -> Data {
    let suggestions = (0..<count).map { suggestionJSON(top: "t-\($0)", bottom: "b-\($0)", index: $0) }
    return Data("""
    {"recommendation_id":"\(recommendationId)",\
    "suggestions":[\(suggestions.joined(separator: ","))],\
    "total_suggestions":\(count),"generated_at":"2026-07-15T06:00:00",\
    "weather":\(weatherJSON),"occasion":"casual","cached":false}
    """.utf8)
}

@MainActor
@Suite(.serialized)
struct SwipeDeckViewModelTests {
    private static let baseURL = URL(string: "http://localhost:8001/api/v1")!

    private static func makeViewModel() -> SwipeDeckViewModel {
        let client = APIClient(baseURL: baseURL, session: SwipeDeckMockURLProtocol.makeSession(), authSession: nil)
        return SwipeDeckViewModel(repository: RecommendationsRepository(apiClient: client))
    }

    /// Routes `swipe-deck` (load) and `/feedback` (rate). `feedbackStatus`
    /// lets tests simulate the daily-cap 429.
    private static func installRouter(deckBody: Data? = nil, feedbackStatus: Int = 200) {
        SwipeDeckMockURLProtocol.handler.withLock { handler in
            handler = { request, _ in
                let path = request.url?.path() ?? ""
                if path.hasSuffix("swipe-deck") {
                    return (200, deckBody ?? swipeDeckJSON(count: 3))
                }
                if path.contains("/recommendations/"), path.hasSuffix("/feedback") {
                    return (feedbackStatus, Data("{}".utf8))
                }
                return (500, Data("{}".utf8))
            }
        }
    }

    private static func resetHandler() {
        SwipeDeckMockURLProtocol.handler.withLock { $0 = nil }
    }

    @Test func loadPopulatesSuggestionsAndLoadedState() async throws {
        defer { Self.resetHandler() }
        Self.installRouter(deckBody: swipeDeckJSON(count: 3))
        let viewModel = Self.makeViewModel()

        await viewModel.load()

        #expect(viewModel.state == .loaded)
        #expect(viewModel.totalCount == 3)
        #expect(viewModel.currentIndex == 0)
        #expect(viewModel.position == 1)
        #expect(viewModel.current?.topItemId == "t-0")
    }

    @Test func load404BecomesEmptyState() async throws {
        defer { Self.resetHandler() }
        SwipeDeckMockURLProtocol.handler.withLock { handler in
            handler = { _, _ in (404, Data(#"{"detail":"Insufficient wardrobe items to generate a swipe deck."}"#.utf8)) }
        }
        let viewModel = Self.makeViewModel()

        await viewModel.load()

        #expect(viewModel.state == .empty)
        #expect(viewModel.current == nil)
    }

    @Test func rateAdvancesToNextCard() async throws {
        defer { Self.resetHandler() }
        Self.installRouter(deckBody: swipeDeckJSON(count: 3))
        let viewModel = Self.makeViewModel()
        await viewModel.load()

        let recorded = await viewModel.rate(liked: true)

        #expect(recorded == true)
        #expect(viewModel.currentIndex == 1)
        #expect(viewModel.current?.topItemId == "t-1")
    }

    @Test func ratingLastCardEndsTheDeck() async throws {
        defer { Self.resetHandler() }
        Self.installRouter(deckBody: swipeDeckJSON(count: 1))
        let viewModel = Self.makeViewModel()
        await viewModel.load()

        _ = await viewModel.rate(liked: false)

        #expect(viewModel.state == .empty)
        #expect(viewModel.current == nil)
    }

    @Test func rate429SetsCapReachedWithoutAdvancing() async throws {
        defer { Self.resetHandler() }
        Self.installRouter(deckBody: swipeDeckJSON(count: 3), feedbackStatus: 429)
        let viewModel = Self.makeViewModel()
        await viewModel.load()

        let recorded = await viewModel.rate(liked: true)

        #expect(recorded == false)
        #expect(viewModel.capReached == true)
        #expect(viewModel.currentIndex == 0)
    }

    @Test func isSubmittingResetsAfterRatingCompletes() async throws {
        defer { Self.resetHandler() }
        Self.installRouter(deckBody: swipeDeckJSON(count: 3))
        let viewModel = Self.makeViewModel()
        await viewModel.load()

        _ = await viewModel.rate(liked: true)

        #expect(viewModel.isSubmitting == false)
    }
}
