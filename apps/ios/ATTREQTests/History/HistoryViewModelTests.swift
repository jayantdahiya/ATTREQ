//
//  HistoryViewModelTests.swift
//  ATTREQTests
//
//  HistoryViewModel behavior against mocked GET /outfits responses: request
//  params, date grouping (worn_date ?? created_at LOCAL day, newest first —
//  deliberate divergence from RN's UTC slice), pill precedence (feedback
//  beats worn, per RN history-screen.tsx), presentational titles/pieces,
//  staleness (post-wear refetch), and Wardrobe-style pagination.
//

import Foundation
import Testing
@testable import ATTREQ

/// Dedicated mock transport for this suite — its own static handler, separate
/// from the other suites' protocols, so parallel suites cannot race each other.
final class HistoryMockURLProtocol: URLProtocol {
    typealias Handler = @Sendable (URLRequest, Data?) -> (status: Int, body: Data)

    static let handler = LockedBox<Handler?>(nil)

    static func makeSession() -> URLSession {
        let configuration = URLSessionConfiguration.ephemeral
        configuration.protocolClasses = [HistoryMockURLProtocol.self]
        return URLSession(configuration: configuration)
    }

    override class func canInit(with request: URLRequest) -> Bool { true }
    override class func canonicalRequest(for request: URLRequest) -> URLRequest { request }

    override func startLoading() {
        guard let handler = Self.handler.withLock({ $0 }), let url = request.url else {
            client?.urlProtocol(self, didFailWithError: URLError(.unsupportedURL))
            return
        }
        // Run the handler and deliver OFF the URL loading work queue: a
        // handler that intentionally stalls (the stale load-more race test)
        // must not block that shared serial queue, which would starve every
        // other in-flight request — including parallel test suites'.
        nonisolated(unsafe) let this = self
        let request = request
        DispatchQueue.global().async {
            let (status, body) = handler(request, request.httpBody)
            let response = HTTPURLResponse(
                url: url,
                statusCode: status,
                httpVersion: "HTTP/1.1",
                headerFields: ["Content-Type": "application/json"]
            )!
            this.client?.urlProtocol(this, didReceive: response, cacheStoragePolicy: .notAllowed)
            this.client?.urlProtocol(this, didLoad: body)
            this.client?.urlProtocolDidFinishLoading(this)
        }
    }

    override func stopLoading() {}
}

// MARK: - Backend JSON fixtures (shape from schemas/outfit.py OutfitList)

private func outfitJSON(
    id: String,
    top: String? = "t-1",
    bottom: String? = "b-1",
    accessories: [String] = [],
    occasion: String? = "casual",
    worn: String? = nil,
    feedback: Int? = nil,
    createdAt: String = "2026-06-23T09:00:00.000000Z"
) -> String {
    """
    {"id":"\(id)","user_id":"u-1",\
    "top_item_id":\(top.map { "\"\($0)\"" } ?? "null"),\
    "bottom_item_id":\(bottom.map { "\"\($0)\"" } ?? "null"),\
    "accessory_ids":[\(accessories.map { "\"\($0)\"" }.joined(separator: ","))],\
    "occasion_context":\(occasion.map { "\"\($0)\"" } ?? "null"),\
    "worn_date":\(worn.map { "\"\($0)\"" } ?? "null"),\
    "feedback_score":\(feedback.map(String.init) ?? "null"),\
    "weather_context":null,\
    "created_at":"\(createdAt)","updated_at":"\(createdAt)"}
    """
}

/// ISO 8601 UTC instant (fixture `created_at` format) for `hour` o'clock on
/// `localDay` in the test machine's CURRENT time zone — the local-day
/// grouping fallback then files it under `localDay` regardless of where the
/// tests run.
private func createdAtISO(localDay: String, hour: Int = 12) -> String {
    let parser = DateFormatter()
    parser.locale = Locale(identifier: "en_US_POSIX")
    parser.dateFormat = "yyyy-MM-dd" // parses as local midnight
    let date = parser.date(from: localDay)!.addingTimeInterval(TimeInterval(hour) * 3600)
    let formatter = DateFormatter()
    formatter.locale = Locale(identifier: "en_US_POSIX")
    formatter.timeZone = TimeZone(identifier: "UTC")
    formatter.dateFormat = "yyyy-MM-dd'T'HH:mm:ss.SSSSSS'Z'"
    return formatter.string(from: date)
}

private func listJSON(items: [String], total: Int, page: Int, totalPages: Int) -> Data {
    Data("""
    {"items":[\(items.joined(separator: ","))],"total":\(total),\
    "page":\(page),"page_size":50,"total_pages":\(totalPages)}
    """.utf8)
}

/// One captured request, taken inside the handler.
private struct CapturedRequest: Sendable {
    var method: String?
    var url: URL?
    var path: String?
}

// MARK: - Tests

@MainActor
@Suite(.serialized)
struct HistoryViewModelTests {
    private static let baseURL = URL(string: "http://localhost:8001/api/v1")!

    private static func makeViewModel() -> HistoryViewModel {
        let client = APIClient(baseURL: baseURL, session: HistoryMockURLProtocol.makeSession(), authSession: nil)
        return HistoryViewModel(repository: OutfitsRepository(apiClient: client))
    }

    /// Answers by requested `page`; records every request.
    private static func installRouter(pages: [Int: (status: Int, body: Data)]) -> LockedBox<[CapturedRequest]> {
        let captured = LockedBox<[CapturedRequest]>([])
        HistoryMockURLProtocol.handler.withLock { handler in
            handler = { request, _ in
                captured.withLock {
                    $0.append(CapturedRequest(method: request.httpMethod, url: request.url, path: request.url?.path()))
                }
                let page = request.url
                    .flatMap { URLComponents(url: $0, resolvingAgainstBaseURL: false) }?
                    .queryItems?
                    .first { $0.name == "page" }?
                    .value
                    .flatMap(Int.init) ?? 1
                return pages[page] ?? (500, Data("{}".utf8))
            }
        }
        return captured
    }

    private static func resetHandler() {
        HistoryMockURLProtocol.handler.withLock { $0 = nil }
    }

    private static func queryItems(of url: URL?) -> [String: String] {
        guard let url, let components = URLComponents(url: url, resolvingAgainstBaseURL: false) else { return [:] }
        return Dictionary(uniqueKeysWithValues: (components.queryItems ?? []).map { ($0.name, $0.value ?? "") })
    }

    // MARK: Load + grouping

    @Test func loadGroupsByWornDateOrCreatedDayNewestFirst() async throws {
        defer { Self.resetHandler() }
        let page1 = listJSON(
            items: [
                // Same day via two different keys: worn_date vs created_at LOCAL day.
                outfitJSON(id: "o-1", worn: "2026-06-23", createdAt: "2026-06-20T10:00:00.000000Z"),
                outfitJSON(id: "o-2", createdAt: createdAtISO(localDay: "2026-06-23")),
                outfitJSON(id: "o-3", worn: "2026-06-22"),
            ],
            total: 3,
            page: 1,
            totalPages: 1
        )
        let captured = Self.installRouter(pages: [1: (200, page1)])
        let viewModel = Self.makeViewModel()

        await viewModel.load()

        let request = try #require(captured.withLock { $0.first })
        #expect(request.method == "GET")
        #expect(request.path == "/api/v1/outfits")
        let query = Self.queryItems(of: request.url)
        #expect(query["page"] == "1")
        #expect(query["page_size"] == "50")

        #expect(viewModel.state == .loaded)
        #expect(viewModel.totalTracked == 3)
        try #require(viewModel.groups.count == 2)
        // Newest day first; entries keep server order within a group.
        #expect(viewModel.groups[0].isoLabel == "2026-06-23")
        #expect(viewModel.groups[0].dateLabel == "Tuesday 06/23")
        #expect(viewModel.groups[0].entries.map(\.id) == ["o-1", "o-2"])
        #expect(viewModel.groups[1].isoLabel == "2026-06-22")
        #expect(viewModel.groups[1].dateLabel == "Monday 06/22")
        #expect(viewModel.groups[1].entries.map(\.id) == ["o-3"])
    }

    @Test func emptyListBecomesEmptyState() async throws {
        defer { Self.resetHandler() }
        _ = Self.installRouter(pages: [1: (200, listJSON(items: [], total: 0, page: 1, totalPages: 0))])
        let viewModel = Self.makeViewModel()

        await viewModel.load()

        #expect(viewModel.state == .empty)
        #expect(viewModel.groups.isEmpty)
        #expect(viewModel.totalTracked == 0)
    }

    @Test func loadFailureSurfacesFastAPIDetail() async throws {
        defer { Self.resetHandler() }
        _ = Self.installRouter(pages: [1: (503, Data(#"{"detail":"Service temporarily unavailable"}"#.utf8))])
        let viewModel = Self.makeViewModel()

        await viewModel.load()

        #expect(viewModel.state == .failed("Service temporarily unavailable"))
    }

    // MARK: Staleness (post-wear refetch)

    /// `markStale()` (fired by Today after a recorded wear/feedback) makes the
    /// next `load()` refetch even though content is loaded; the flag clears so
    /// subsequent loads are no-ops again.
    @Test func markStaleTriggersRefetchOnNextLoad() async throws {
        defer { Self.resetHandler() }
        let page1 = listJSON(
            items: [outfitJSON(id: "o-1", worn: "2026-06-23")],
            total: 1, page: 1, totalPages: 1
        )
        let captured = Self.installRouter(pages: [1: (200, page1)])
        let viewModel = Self.makeViewModel()

        await viewModel.load()
        await viewModel.load() // .task re-fire without staleness: no refetch
        #expect(captured.withLock { $0.count } == 1)

        // Today recorded a wear → the backend now has a new entry.
        let updated = listJSON(
            items: [
                outfitJSON(id: "o-2", worn: "2026-06-24"),
                outfitJSON(id: "o-1", worn: "2026-06-23"),
            ],
            total: 2, page: 1, totalPages: 1
        )
        let recaptured = Self.installRouter(pages: [1: (200, updated)])
        viewModel.markStale()
        await viewModel.load()

        #expect(recaptured.withLock { $0.count } == 1) // stale → refetched
        #expect(viewModel.totalTracked == 2)
        #expect(viewModel.groups.flatMap { $0.entries.map(\.id) }.contains("o-2"))

        await viewModel.load() // flag cleared → back to no-op
        #expect(recaptured.withLock { $0.count } == 1)
    }

    // MARK: Pills (precedence per RN history-screen HistoryLookCard)

    @Test func pillPrecedenceFeedbackBeatsWorn() {
        // feedback 1 wins over worn → Loved (gold)
        #expect(HistoryViewModel.pill(for: Self.makeOutfit(worn: "2026-06-23", feedback: 1)) == .loved)
        // feedback -1 wins over worn → Skipped (clay)
        #expect(HistoryViewModel.pill(for: Self.makeOutfit(worn: "2026-06-23", feedback: -1)) == .skipped)
        // worn without feedback → Worn (moss)
        #expect(HistoryViewModel.pill(for: Self.makeOutfit(worn: "2026-06-23", feedback: nil)) == .worn)
        // feedback 0 falls through to worn (RN uses === 1 / === -1)
        #expect(HistoryViewModel.pill(for: Self.makeOutfit(worn: "2026-06-23", feedback: 0)) == .worn)
        // nothing → Tracked (muted)
        #expect(HistoryViewModel.pill(for: Self.makeOutfit(worn: nil, feedback: nil)) == .tracked)

        #expect(HistoryEntry.Pill.loved.label == "Loved")
        #expect(HistoryEntry.Pill.skipped.label == "Skipped")
        #expect(HistoryEntry.Pill.worn.label == "Worn")
        #expect(HistoryEntry.Pill.tracked.label == "Tracked")
    }

    @Test func entriesCarryPillsFromLoadedOutfits() async throws {
        defer { Self.resetHandler() }
        let page1 = listJSON(
            items: [
                outfitJSON(id: "o-1", worn: "2026-06-23", feedback: 1),
                outfitJSON(id: "o-2", worn: "2026-06-23", feedback: -1),
                outfitJSON(id: "o-3", worn: "2026-06-23"),
                outfitJSON(id: "o-4", createdAt: createdAtISO(localDay: "2026-06-23")),
            ],
            total: 4,
            page: 1,
            totalPages: 1
        )
        _ = Self.installRouter(pages: [1: (200, page1)])
        let viewModel = Self.makeViewModel()

        await viewModel.load()

        let entries = try #require(viewModel.groups.first?.entries)
        #expect(entries.map(\.pill) == [.loved, .skipped, .worn, .tracked])
    }

    // MARK: Display bits

    @Test func piecesCountCountsNonNilItemIds() {
        #expect(HistoryViewModel.piecesCount(for: Self.makeOutfit(top: "t-1", bottom: "b-1", accessories: ["a-1", "a-2"])) == 4)
        #expect(HistoryViewModel.piecesCount(for: Self.makeOutfit(top: "t-1", bottom: nil, accessories: nil)) == 1)
        #expect(HistoryViewModel.piecesCount(for: Self.makeOutfit(top: nil, bottom: nil, accessories: [])) == 0)
    }

    @Test func titlesUseCuratedGeneratorKeyedByOccasionAndGroupIndex() async throws {
        defer { Self.resetHandler() }
        let page1 = listJSON(
            items: [
                outfitJSON(id: "o-1", occasion: "casual", worn: "2026-06-23"),
                outfitJSON(id: "o-2", occasion: "athletic", worn: "2026-06-23"),
            ],
            total: 2,
            page: 1,
            totalPages: 1
        )
        _ = Self.installRouter(pages: [1: (200, page1)])
        let viewModel = Self.makeViewModel()

        await viewModel.load()

        let entries = try #require(viewModel.groups.first?.entries)
        #expect(entries[0].title == LookTitles.title(occasion: "casual", index: 0))
        #expect(entries[1].title == LookTitles.title(occasion: "athletic", index: 1))
    }

    @Test func dateLabelFallsBackToRawKeyWhenUnparseable() {
        #expect(HistoryViewModel.dateLabel(forDayKey: "not-a-date") == "not-a-date")
        #expect(HistoryViewModel.dateLabel(forDayKey: "2026-06-22") == "Monday 06/22")
    }

    /// The `created_at` fallback groups by the user's LOCAL calendar day —
    /// deliberate divergence from RN's `created_at.slice(0, 10)` UTC day
    /// (diary semantics; matches `TodayViewModel.todayWornDate`). Backend
    /// `worn_date` strings are plain dates and pass through verbatim.
    @Test func dayKeyFallbackUsesLocalCalendarDay() throws {
        // 2026-06-23T23:30:00Z — a different diary day east of UTC+00:30.
        let instant = Date(timeIntervalSince1970: 1_782_257_400)
        let utc = try #require(TimeZone(identifier: "UTC"))
        let kolkata = try #require(TimeZone(identifier: "Asia/Kolkata")) // UTC+5:30

        let unworn = Self.makeOutfit(createdAt: instant)
        #expect(HistoryViewModel.dayKey(for: unworn, timeZone: utc) == "2026-06-23")
        #expect(HistoryViewModel.dayKey(for: unworn, timeZone: kolkata) == "2026-06-24")
        // The default is the device's zone.
        #expect(HistoryViewModel.dayKey(for: unworn)
            == HistoryViewModel.dayKey(for: unworn, timeZone: .current))

        let worn = Self.makeOutfit(worn: "2026-06-20", createdAt: instant)
        #expect(HistoryViewModel.dayKey(for: worn, timeZone: kolkata) == "2026-06-20")
    }

    // MARK: Pagination (mirrors WardrobeViewModel)

    @Test func loadMoreFetchesNextPageAppendsAndDeduplicates() async throws {
        defer { Self.resetHandler() }
        let page1Items = (1 ... 8).map { outfitJSON(id: "o-\($0)", worn: "2026-06-23") }
        // Page 2 re-sends o-8 (overlap) plus genuinely new items.
        let page2Items = [
            outfitJSON(id: "o-8", worn: "2026-06-23"),
            outfitJSON(id: "o-9", worn: "2026-06-22"),
            outfitJSON(id: "o-10", worn: "2026-06-22"),
        ]
        let captured = Self.installRouter(pages: [
            1: (200, listJSON(items: page1Items, total: 10, page: 1, totalPages: 2)),
            2: (200, listJSON(items: page2Items, total: 10, page: 2, totalPages: 2)),
        ])
        let viewModel = Self.makeViewModel()
        await viewModel.load()

        // An entry near the end of the flat list triggers the prefetch.
        let nearEnd = try #require(viewModel.groups.first?.entries.last)
        await viewModel.loadMoreIfNeeded(currentEntry: nearEnd)

        let requests = captured.withLock { $0 }
        try #require(requests.count == 2)
        #expect(Self.queryItems(of: requests[1].url)["page"] == "2")
        #expect(Self.queryItems(of: requests[1].url)["page_size"] == "50")

        let allIDs = viewModel.groups.flatMap { $0.entries.map(\.id) }
        #expect(allIDs.count == 10) // o-8 not duplicated
        #expect(allIDs.contains("o-9") && allIDs.contains("o-10"))
        #expect(viewModel.groups.map(\.isoLabel) == ["2026-06-23", "2026-06-22"])
        #expect(viewModel.totalTracked == 10)
    }

    @Test func loadMoreDoesNothingFarFromTheEndOrOnLastPage() async throws {
        defer { Self.resetHandler() }
        let page1Items = (1 ... 8).map { outfitJSON(id: "o-\($0)", worn: "2026-06-23") }
        let captured = Self.installRouter(pages: [
            1: (200, listJSON(items: page1Items, total: 10, page: 1, totalPages: 2)),
        ])
        let viewModel = Self.makeViewModel()
        await viewModel.load()

        // First entry is more than `loadMoreThreshold` from the end — no fetch.
        let first = try #require(viewModel.groups.first?.entries.first)
        await viewModel.loadMoreIfNeeded(currentEntry: first)
        #expect(captured.withLock { $0.count } == 1)
    }

    /// A next-page response that races a refresh must be discarded: the
    /// refresh bumps the fetch generation, and `loadMoreIfNeeded` re-checks
    /// it after its await instead of appending stale items onto the fresh
    /// page 1.
    @Test func staleLoadMoreResponseAfterRefreshIsDiscarded() async throws {
        defer { Self.resetHandler() }
        let initialPage1 = listJSON(
            items: (1 ... 8).map { outfitJSON(id: "o-\($0)", worn: "2026-06-23") },
            total: 10, page: 1, totalPages: 2
        )
        let freshPage1 = listJSON(
            items: [outfitJSON(id: "fresh-1", worn: "2026-06-24")],
            total: 1, page: 1, totalPages: 1
        )
        let stalePage2 = listJSON(
            items: [outfitJSON(id: "stale-9", worn: "2026-06-22")],
            total: 10, page: 2, totalPages: 2
        )

        // The page-2 response is held on `gate` until the refresh finished,
        // forcing the load-more/refresh interleave deterministically.
        let gate = DispatchSemaphore(value: 0)
        let page2Started = LockedBox(false)
        let page1Hits = LockedBox(0)
        HistoryMockURLProtocol.handler.withLock { handler in
            handler = { request, _ in
                let page = request.url
                    .flatMap { URLComponents(url: $0, resolvingAgainstBaseURL: false) }?
                    .queryItems?
                    .first { $0.name == "page" }?
                    .value
                    .flatMap(Int.init) ?? 1
                if page == 2 {
                    page2Started.withLock { $0 = true }
                    // Blocks a global-queue delivery thread (never the URL
                    // loading queue — see `startLoading`); bounded so a bug
                    // fails the test instead of hanging it.
                    _ = gate.wait(timeout: .now() + 10)
                    return (200, stalePage2)
                }
                let isInitialLoad = page1Hits.withLock { hits -> Bool in
                    hits += 1
                    return hits == 1
                }
                return (200, isInitialLoad ? initialPage1 : freshPage1)
            }
        }

        let viewModel = Self.makeViewModel()
        await viewModel.load()
        let nearEnd = try #require(viewModel.groups.first?.entries.last)
        let loadMore = Task { await viewModel.loadMoreIfNeeded(currentEntry: nearEnd) }

        // Wait until the page-2 request is actually in flight.
        for _ in 0 ..< 500 where !page2Started.withLock({ $0 }) {
            try await Task.sleep(for: .milliseconds(10))
        }
        #expect(page2Started.withLock { $0 })

        await viewModel.refresh() // bumps the generation, installs fresh page 1
        gate.signal() // now release the stale page-2 response
        await loadMore.value

        let allIDs = viewModel.groups.flatMap { $0.entries.map(\.id) }
        #expect(allIDs == ["fresh-1"]) // stale-9 discarded, not appended
        #expect(viewModel.totalTracked == 1)
    }

    // MARK: Fixture builders

    private static func makeOutfit(
        top: String? = "t-1",
        bottom: String? = "b-1",
        accessories: [String]? = [],
        worn: String? = nil,
        feedback: Int? = nil,
        createdAt: Date = Date(timeIntervalSince1970: 1_782_000_000)
    ) -> Outfit {
        Outfit(
            id: "o-x",
            userId: "u-1",
            topItemId: top,
            bottomItemId: bottom,
            accessoryIds: accessories,
            occasionContext: "casual",
            footwearItemId: nil,
            outerwearItemId: nil,
            fullbodyItemId: nil,
            wornDate: worn,
            feedbackScore: feedback,
            weatherContext: nil,
            createdAt: createdAt,
            updatedAt: createdAt
        )
    }
}
