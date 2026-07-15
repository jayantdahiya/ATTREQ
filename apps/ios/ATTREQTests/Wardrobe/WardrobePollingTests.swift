//
//  WardrobePollingTests.swift
//  ATTREQTests
//
//  WardrobeViewModel status polling (short injected durations): polls while
//  items are pending/processing, stops when all terminal, respects the poll
//  cap, and cancels via stopPolling(). Plus the chip → free-text-category
//  bucketing rules mirrored from the RN app.
//

import Foundation
import Testing
@testable import ATTREQ

/// Dedicated mock transport for this suite — separate static handler from the
/// other suites' protocols, so parallel suites cannot race each other.
final class PollingMockURLProtocol: URLProtocol {
    typealias Handler = @Sendable (URLRequest) -> (status: Int, body: Data)

    static let handler = LockedBox<Handler?>(nil)

    static func makeSession() -> URLSession {
        let configuration = URLSessionConfiguration.ephemeral
        configuration.protocolClasses = [PollingMockURLProtocol.self]
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

// MARK: - JSON fixtures

private func itemJSON(id: String, status: String, category: String? = nil) -> String {
    """
    {"id":"\(id)","user_id":"u-1","original_image_url":"/uploads/originals/\(id).jpg",\
    "processed_image_url":null,"thumbnail_url":null,\
    "category":\(category.map { "\"\($0)\"" } ?? "null"),\
    "color_primary":null,"color_secondary":null,"pattern":null,\
    "season":null,"occasion":null,"detection_confidence":null,\
    "classification_source":null,"processing_status":"\(status)",\
    "wear_count":0,"last_worn":null,\
    "created_at":"2026-07-15T06:00:00.000000Z","updated_at":"2026-07-15T06:00:00.000000Z"}
    """
}

private func listJSON(items: [String], total: Int? = nil, page: Int = 1, totalPages: Int? = nil) -> Data {
    let body = """
    {"items":[\(items.joined(separator: ","))],"total":\(total ?? items.count),\
    "page":\(page),"page_size":50,"total_pages":\(totalPages ?? (items.isEmpty ? 0 : 1))}
    """
    return Data(body.utf8)
}

// MARK: - Polling tests

@Suite(.serialized)
@MainActor
struct WardrobePollingTests {
    private static let baseURL = URL(string: "http://localhost:8001/api/v1")!

    private static func makeViewModel(
        pollInterval: Duration = .milliseconds(20),
        pollCap: Duration = .seconds(5)
    ) -> WardrobeViewModel {
        let client = APIClient(
            baseURL: baseURL,
            session: PollingMockURLProtocol.makeSession(),
            authSession: nil
        )
        return WardrobeViewModel(
            repository: WardrobeRepository(apiClient: client),
            pollInterval: pollInterval,
            pollCap: pollCap
        )
    }

    /// Waits (bounded) for `condition` to become true; returns whether it did.
    private static func waitUntil(
        timeout: Duration = .seconds(3),
        _ condition: @MainActor () -> Bool
    ) async -> Bool {
        let clock = ContinuousClock()
        let deadline = clock.now.advanced(by: timeout)
        while clock.now < deadline {
            if condition() { return true }
            try? await clock.sleep(for: .milliseconds(10))
        }
        return condition()
    }

    @Test func pendingItemPollsUntilCompletedThenStops() async throws {
        let listCalls = LockedBox(0)
        PollingMockURLProtocol.handler.withLock { handler in
            handler = { request in
                guard request.url?.path() == "/api/v1/wardrobe/items" else {
                    return (404, Data(#"{"detail":"not found"}"#.utf8))
                }
                let call = listCalls.withLock { count -> Int in
                    count += 1
                    return count
                }
                // Two fetches see the item mid-pipeline, then it completes.
                let item = call <= 2
                    ? itemJSON(id: "i-1", status: call == 1 ? "pending" : "processing")
                    : itemJSON(id: "i-1", status: "completed", category: "Cotton Shirt")
                return (200, listJSON(items: [item]))
            }
        }
        defer { PollingMockURLProtocol.handler.withLock { $0 = nil } }

        let viewModel = Self.makeViewModel()
        await viewModel.loadInitial()
        #expect(viewModel.items.count == 1)
        #expect(viewModel.items[0].processingStatus == .pending)
        #expect(viewModel.totalCount == 1)

        viewModel.startPollingIfNeeded()
        let completed = await Self.waitUntil {
            viewModel.items.first?.processingStatus == .completed
        }
        #expect(completed, "polling should refetch until the item is terminal")
        #expect(viewModel.items.first?.category == "Cotton Shirt")

        // Terminal → the loop must stop issuing requests.
        try await Task.sleep(for: .milliseconds(150))
        let settled = listCalls.withLock { $0 }
        try await Task.sleep(for: .milliseconds(150))
        #expect(listCalls.withLock { $0 } == settled, "polling must stop once all items are terminal")

        // And restarting is a no-op while nothing is processing.
        viewModel.startPollingIfNeeded()
        try await Task.sleep(for: .milliseconds(100))
        #expect(listCalls.withLock { $0 } == settled)
    }

    @Test func pollingStopsAtCapEvenIfItemsNeverComplete() async throws {
        let listCalls = LockedBox(0)
        PollingMockURLProtocol.handler.withLock { handler in
            handler = { _ in
                listCalls.withLock { $0 += 1 }
                return (200, listJSON(items: [itemJSON(id: "i-stuck", status: "processing")]))
            }
        }
        defer { PollingMockURLProtocol.handler.withLock { $0 = nil } }

        // Cap after ~5 poll ticks.
        let viewModel = Self.makeViewModel(pollInterval: .milliseconds(20), pollCap: .milliseconds(100))
        await viewModel.loadInitial()
        viewModel.startPollingIfNeeded()

        // Give it well past the cap, then verify requests have stopped.
        try await Task.sleep(for: .milliseconds(400))
        let afterCap = listCalls.withLock { $0 }
        try await Task.sleep(for: .milliseconds(200))
        #expect(listCalls.withLock { $0 } == afterCap, "polling must stop at the cap")

        #expect(afterCap >= 2, "at least one poll fetch should happen before the cap")
        #expect(viewModel.items.first?.processingStatus == .processing)
    }

    @Test func stopPollingCancelsTheLoop() async throws {
        let listCalls = LockedBox(0)
        PollingMockURLProtocol.handler.withLock { handler in
            handler = { _ in
                listCalls.withLock { $0 += 1 }
                return (200, listJSON(items: [itemJSON(id: "i-1", status: "pending")]))
            }
        }
        defer { PollingMockURLProtocol.handler.withLock { $0 = nil } }

        let viewModel = Self.makeViewModel()
        await viewModel.loadInitial()
        viewModel.startPollingIfNeeded()
        _ = await Self.waitUntil { listCalls.withLock { $0 } >= 2 }

        viewModel.stopPolling()
        try await Task.sleep(for: .milliseconds(100))
        let afterStop = listCalls.withLock { $0 }
        try await Task.sleep(for: .milliseconds(150))
        #expect(listCalls.withLock { $0 } == afterStop, "stopPolling must cancel the loop")
    }

    /// `page` query parameter of a list request (default 1).
    private nonisolated static func pageParam(of request: URLRequest) -> Int {
        guard let url = request.url,
              let components = URLComponents(url: url, resolvingAgainstBaseURL: false),
              let value = components.queryItems?.first(where: { $0.name == "page" })?.value
        else { return 1 }
        return Int(value) ?? 1
    }

    @Test func loadMoreFetchesNextPageAndAppends() async throws {
        let pageRequests = LockedBox<[Int]>([])
        PollingMockURLProtocol.handler.withLock { handler in
            handler = { request in
                let page = Self.pageParam(of: request)
                pageRequests.withLock { $0.append(page) }
                if page == 1 {
                    let items = (1 ... 8).map { itemJSON(id: "p1-\($0)", status: "completed") }
                    return (200, listJSON(items: items, total: 12, page: 1, totalPages: 2))
                }
                let items = (1 ... 4).map { itemJSON(id: "p2-\($0)", status: "completed") }
                return (200, listJSON(items: items, total: 12, page: 2, totalPages: 2))
            }
        }
        defer { PollingMockURLProtocol.handler.withLock { $0 = nil } }

        let viewModel = Self.makeViewModel()
        await viewModel.loadInitial()
        #expect(viewModel.items.count == 8)
        #expect(viewModel.totalCount == 12)

        // An item outside the trailing window must not trigger a page fetch.
        await viewModel.loadMoreIfNeeded(currentItem: viewModel.items[0])
        #expect(viewModel.items.count == 8)
        #expect(pageRequests.withLock { $0 } == [1])

        // An item within the last 6 fetches page 2 and appends it.
        await viewModel.loadMoreIfNeeded(currentItem: viewModel.items[6])
        #expect(viewModel.items.count == 12)
        #expect(viewModel.items.suffix(4).map(\.id) == ["p2-1", "p2-2", "p2-3", "p2-4"])
        #expect(pageRequests.withLock { $0 } == [1, 2])

        // All pages loaded → further calls are no-ops.
        await viewModel.loadMoreIfNeeded(currentItem: viewModel.items[11])
        #expect(pageRequests.withLock { $0 } == [1, 2])
    }

    @Test func pollMergeUpdatesPageOneAndKeepsAppendedPages() async throws {
        let pendingDone = LockedBox(false)
        PollingMockURLProtocol.handler.withLock { handler in
            handler = { request in
                if Self.pageParam(of: request) == 2 {
                    let items = [
                        itemJSON(id: "old-1", status: "completed"),
                        itemJSON(id: "old-2", status: "completed"),
                    ]
                    return (200, listJSON(items: items, total: 4, page: 2, totalPages: 2))
                }
                let first = pendingDone.withLock { $0 }
                    ? itemJSON(id: "p-1", status: "completed", category: "jeans")
                    : itemJSON(id: "p-1", status: "pending")
                let items = [first, itemJSON(id: "a-1", status: "completed")]
                return (200, listJSON(items: items, total: 4, page: 1, totalPages: 2))
            }
        }
        defer { PollingMockURLProtocol.handler.withLock { $0 = nil } }

        let viewModel = Self.makeViewModel()
        await viewModel.loadInitial()
        await viewModel.loadMoreIfNeeded(currentItem: viewModel.items[1])
        #expect(viewModel.items.map(\.id) == ["p-1", "a-1", "old-1", "old-2"])

        pendingDone.withLock { $0 = true }
        viewModel.startPollingIfNeeded()
        let completed = await Self.waitUntil {
            viewModel.items.first(where: { $0.id == "p-1" })?.processingStatus == .completed
        }
        #expect(completed, "the poll must refresh page-1 items in place")
        #expect(
            viewModel.items.map(\.id) == ["p-1", "a-1", "old-1", "old-2"],
            "a poll refetch must merge by id and keep items loaded from later pages"
        )
        #expect(viewModel.items.first(where: { $0.id == "p-1" })?.category == "jeans")
    }

    @Test func listRequestUsesBackendPaginationParams() async throws {
        let capturedQuery = LockedBox<String?>(nil)
        PollingMockURLProtocol.handler.withLock { handler in
            handler = { request in
                capturedQuery.withLock { $0 = request.url?.query() }
                return (200, listJSON(items: []))
            }
        }
        defer { PollingMockURLProtocol.handler.withLock { $0 = nil } }

        let viewModel = Self.makeViewModel()
        await viewModel.loadInitial()

        let query = try #require(capturedQuery.withLock { $0 })
        #expect(query.contains("page=1"))
        #expect(query.contains("page_size=50"))
        #expect(viewModel.items.isEmpty)
        #expect(viewModel.totalCount == 0)
        #expect(viewModel.errorMessage == nil)
        // Nothing pending in an empty wardrobe → polling never starts.
        viewModel.startPollingIfNeeded()
        try await Task.sleep(for: .milliseconds(100))
        #expect(viewModel.lastAddedRelative == nil)
    }
}

// MARK: - Filter bucketing (mirrors RN toneForCategory)

@Suite struct WardrobeFilterTests {
    @Test func chipLabelsMatchDesign() {
        #expect(WardrobeFilter.allCases.map(\.label) == ["All", "Tops", "Bottoms", "Outer", "Accents", "Shoes"])
    }

    /// The FULL closed vocabulary the backend classifiers emit
    /// (`apps/api/src/attreq_api/services/ai/groq_classifier.py`
    /// `CLASSIFICATION_PROMPT`), each mapped to its chip. Dress/jumpsuit/
    /// romper intentionally land on the Tops fallback (RN precedence).
    @Test(arguments: [
        ("shirt", WardrobeFilter.tops),
        ("jeans", .bottoms),
        ("dress", .tops),
        ("jacket", .outer),
        ("sweater", .tops),
        ("pants", .bottoms),
        ("coat", .outer),
        ("blouse", .tops),
        ("skirt", .bottoms),
        ("shorts", .bottoms),
        ("t-shirt", .tops),
        ("hoodie", .tops),
        ("blazer", .outer),
        ("cardigan", .tops),
        ("tank-top", .tops),
        ("polo", .tops),
        ("chinos", .bottoms),
        ("leggings", .bottoms),
        ("jumpsuit", .tops),
        ("romper", .tops),
    ] as [(String, WardrobeFilter)])
    func bucketsFullClassifierVocabulary(category: String, expected: WardrobeFilter) {
        #expect(WardrobeFilter.bucket(for: category) == expected)
        #expect(expected.matches(category))
        #expect(WardrobeFilter.all.matches(category))
    }

    /// Future-proof free-text terms (shoes/accessories aren't in the
    /// classifier vocabulary yet) plus the nil → Tops fallback.
    @Test(arguments: [
        ("running shoes", WardrobeFilter.shoes),
        ("sneakers", .shoes),
        ("leather sandal", .shoes),
        ("Chelsea boot", .shoes),
        ("block heels", .shoes),
        ("tote bag", .accents),
        ("woven belt", .accents),
        ("bucket hat", .accents),
        ("silk scarf", .accents),
        ("gold jewelry", .accents),
        ("Accessory", .accents),
        ("Wide-leg trousers", .bottoms),
        ("bottomwear", .bottoms),
        ("Overcoat", .outer),
        ("outerwear", .outer),
        (nil, .tops), // unclassified items fall back to Tops, like RN's default tone
    ] as [(String?, WardrobeFilter)])
    func bucketsFutureProofFreeText(category: String?, expected: WardrobeFilter) {
        #expect(WardrobeFilter.bucket(for: category) == expected)
        #expect(expected.matches(category))
        #expect(WardrobeFilter.all.matches(category))
    }

    @Test func precedenceMatchesRNOrdering() {
        // RN checks bottoms → shoes → outer → bag/accents, first match wins.
        // "boot-cut pants" hits both "boot" (shoes) and "pant" (bottoms):
        #expect(WardrobeFilter.bucket(for: "boot-cut pants") == .bottoms)
        // "jacket bag" hits both "jacket" (outer) and "bag" (accents):
        #expect(WardrobeFilter.bucket(for: "jacket bag") == .outer)
    }
}
