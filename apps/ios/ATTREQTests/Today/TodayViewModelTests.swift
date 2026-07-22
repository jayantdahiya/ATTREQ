//
//  TodayViewModelTests.swift
//  ATTREQTests
//
//  TodayViewModel behavior against mocked backend responses: load/refresh
//  states and params, the RN action semantics (Wear = create + mark-worn,
//  heart = feedback 1 and stay, X = feedback -1 and advance, Skip = local
//  advance only, create-or-reuse per suggestion), and the greeting helpers.
//

import Foundation
import Testing
@testable import ATTREQ

/// Dedicated mock transport for this suite — its own static handler, separate
/// from the other suites' protocols, so parallel suites cannot race each other.
/// The handler receives the drained request body (URLProtocol only ever sees
/// `httpBodyStream`, never `httpBody`).
final class TodayMockURLProtocol: URLProtocol {
    typealias Handler = @Sendable (URLRequest, Data?) -> (status: Int, body: Data)

    static let handler = LockedBox<Handler?>(nil)

    static func makeSession() -> URLSession {
        let configuration = URLSessionConfiguration.ephemeral
        configuration.protocolClasses = [TodayMockURLProtocol.self]
        return URLSession(configuration: configuration)
    }

    override class func canInit(with request: URLRequest) -> Bool { true }
    override class func canonicalRequest(for request: URLRequest) -> URLRequest { request }

    override func startLoading() {
        guard let handler = Self.handler.withLock({ $0 }), let url = request.url else {
            client?.urlProtocol(self, didFailWithError: URLError(.unsupportedURL))
            return
        }
        let (status, body) = handler(request, Self.drainBody(request))
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

    private static func drainBody(_ request: URLRequest) -> Data? {
        if let body = request.httpBody { return body }
        guard let stream = request.httpBodyStream else { return nil }
        stream.open()
        defer { stream.close() }
        var data = Data()
        let bufferSize = 64 * 1024
        var buffer = [UInt8](repeating: 0, count: bufferSize)
        while stream.hasBytesAvailable {
            let read = stream.read(&buffer, maxLength: bufferSize)
            guard read > 0 else { break }
            data.append(buffer, count: read)
        }
        return data
    }
}

// MARK: - Backend JSON fixtures

private let weatherJSON = """
{"temp":21.5,"feels_like":20.1,"condition":"Clear","description":"clear sky",\
"humidity":40,"wind_speed":3.2,"icon":"01d"}
"""

private func suggestionJSON(top: String, bottom: String, accessory: String? = nil) -> String {
    let accessoryJSON = accessory.map {
        #"{"id":"\#($0)","category":"accessory","color_primary":null,"pattern":null,"image_url":null,"thumbnail_url":null}"#
    } ?? "null"
    return """
    {"top_item_id":"\(top)",\
    "top_item":{"id":"\(top)","category":"top","color_primary":"navy","pattern":"solid","image_url":null,"thumbnail_url":null},\
    "bottom_item_id":"\(bottom)",\
    "bottom_item":{"id":"\(bottom)","category":"bottom","color_primary":"beige","pattern":null,"image_url":null,"thumbnail_url":null},\
    "accessory_item":\(accessoryJSON),\
    "scores":{"color_harmony":0.8,"formality":0.7,"preference_bonus":0.1,"total":0.86},\
    "weather_context":\(weatherJSON),\
    "occasion_context":"casual"}
    """
}

/// Two suggestions: the second carries an accessory (exercises accessory_ids).
private func dailyJSON() -> Data {
    Data("""
    {"suggestions":[\(suggestionJSON(top: "t-1", bottom: "b-1")),\(suggestionJSON(top: "t-2", bottom: "b-2", accessory: "a-2"))],\
    "total_suggestions":2,"generated_at":"2026-07-15T06:00:00",\
    "weather":\(weatherJSON),"occasion":"casual","cached":false}
    """.utf8)
}

private func outfitJSON(id: String, worn: String? = nil, feedback: Int? = nil) -> Data {
    Data("""
    {"id":"\(id)","user_id":"u-1","top_item_id":"t-1","bottom_item_id":"b-1",\
    "accessory_ids":[],"occasion_context":"casual",\
    "worn_date":\(worn.map { "\"\($0)\"" } ?? "null"),\
    "feedback_score":\(feedback.map(String.init) ?? "null"),"weather_context":null,\
    "created_at":"2026-07-15T06:00:00.000000Z","updated_at":"2026-07-15T06:00:00.000000Z"}
    """.utf8)
}

/// One captured request, taken inside the handler.
private struct CapturedRequest: Sendable {
    var method: String?
    var url: URL?
    var path: String?
    var body: Data?
}

// MARK: - Tests

@MainActor
@Suite(.serialized)
struct TodayViewModelTests {
    private static let baseURL = URL(string: "http://localhost:8001/api/v1")!

    private static func makeModels() -> (viewModel: TodayViewModel, outfits: OutfitsRepository) {
        let client = APIClient(baseURL: baseURL, session: TodayMockURLProtocol.makeSession(), authSession: nil)
        return (
            TodayViewModel(repository: RecommendationsRepository(apiClient: client)),
            OutfitsRepository(apiClient: client)
        )
    }

    /// Routes daily → outfits-create → wear/feedback and records every request.
    private static func installRouter(
        dailyStatus: Int = 200,
        dailyBody: Data? = nil,
        createStatus: Int = 201,
        createBody: Data? = nil
    ) -> LockedBox<[CapturedRequest]> {
        let captured = LockedBox<[CapturedRequest]>([])
        TodayMockURLProtocol.handler.withLock { handler in
            handler = { request, body in
                captured.withLock {
                    $0.append(CapturedRequest(method: request.httpMethod, url: request.url, path: request.url?.path(), body: body))
                }
                let path = request.url?.path() ?? ""
                if path.hasSuffix("recommendations/daily") {
                    return (dailyStatus, dailyBody ?? dailyJSON())
                }
                if request.httpMethod == "POST", path.hasSuffix("/outfits") {
                    return (createStatus, createBody ?? outfitJSON(id: "o-1"))
                }
                if path.hasSuffix("/wear") {
                    return (200, outfitJSON(id: "o-1", worn: "2026-07-15"))
                }
                if path.hasSuffix("/feedback") {
                    return (200, outfitJSON(id: "o-1", feedback: 1))
                }
                return (500, Data("{}".utf8))
            }
        }
        return captured
    }

    private static func resetHandler() {
        TodayMockURLProtocol.handler.withLock { $0 = nil }
    }

    private static func queryItems(of url: URL?) -> [String: String] {
        guard let url, let components = URLComponents(url: url, resolvingAgainstBaseURL: false) else { return [:] }
        return Dictionary(uniqueKeysWithValues: (components.queryItems ?? []).map { ($0.name, $0.value ?? "") })
    }

    private static func json(_ data: Data?) throws -> NSDictionary {
        let data = try #require(data)
        let object = try JSONSerialization.jsonObject(with: data)
        return try #require(object as? NSDictionary)
    }

    // MARK: Load / refresh

    @Test func loadPopulatesStateAndRequestsCasualWithoutForceRefresh() async throws {
        defer { Self.resetHandler() }
        let captured = Self.installRouter()
        let (viewModel, _) = Self.makeModels()

        await viewModel.load()

        #expect(viewModel.state == .loaded)
        #expect(viewModel.suggestions.count == 2)
        #expect(viewModel.totalLooks == 2)
        #expect(viewModel.currentIndex == 0)
        #expect(viewModel.current?.topItemId == "t-1")
        #expect(viewModel.weather?.temp == 21.5)
        #expect(viewModel.occasion == "casual")
        #expect(viewModel.errorMessage == nil)

        let request = try #require(captured.withLock { $0.first })
        #expect(request.method == "GET")
        #expect(request.path == "/api/v1/recommendations/daily")
        let query = Self.queryItems(of: request.url)
        #expect(query["occasion"] == "casual")
        #expect(query["force_refresh"] == nil)
        #expect(query["lat"] == nil && query["lon"] == nil)
    }

    @Test func refreshSendsForceRefreshTrue() async throws {
        defer { Self.resetHandler() }
        let captured = Self.installRouter()
        let (viewModel, _) = Self.makeModels()

        await viewModel.refresh()

        let request = try #require(captured.withLock { $0.first })
        let query = Self.queryItems(of: request.url)
        #expect(query["force_refresh"] == "true")
        #expect(query["occasion"] == "casual")
        #expect(viewModel.state == .loaded)
    }

    /// Backend 404 = insufficient wardrobe items → honest empty state (RN
    /// shows the empty closet card), not a failure.
    @Test func load404BecomesEmptyState() async throws {
        defer { Self.resetHandler() }
        _ = Self.installRouter(
            dailyStatus: 404,
            dailyBody: Data(#"{"detail":"Insufficient wardrobe items to generate outfit suggestions."}"#.utf8)
        )
        let (viewModel, _) = Self.makeModels()

        await viewModel.load()

        #expect(viewModel.state == .empty)
        #expect(viewModel.current == nil)
        #expect(viewModel.errorMessage == nil)
    }

    @Test func loadFailureSurfacesFastAPIDetail() async throws {
        defer { Self.resetHandler() }
        _ = Self.installRouter(
            dailyStatus: 400,
            dailyBody: Data(#"{"detail":"No location available. Please provide coordinates or set your location in profile."}"#.utf8)
        )
        let (viewModel, _) = Self.makeModels()

        await viewModel.load()

        #expect(viewModel.state == .failed(
            "No location available. Please provide coordinates or set your location in profile."
        ))
    }

    /// Tab re-entry re-fires `.task` `load()`: once loaded it must be a
    /// no-op (no refetch, `currentIndex` preserved), while pull-to-refresh
    /// stays the full reset.
    @Test func loadIsIdempotentOnceLoadedButRefreshStillResets() async throws {
        defer { Self.resetHandler() }
        let captured = Self.installRouter()
        let (viewModel, _) = Self.makeModels()

        await viewModel.load()
        viewModel.skip() // mid-session position that must survive tab switches

        await viewModel.load() // tab re-entry
        #expect(captured.withLock { $0.count } == 1) // no redundant refetch
        #expect(viewModel.currentIndex == 1)
        #expect(viewModel.state == .loaded)

        await viewModel.refresh() // pull-to-refresh: full reset as before
        #expect(captured.withLock { $0.count } == 2)
        #expect(viewModel.currentIndex == 0)
    }

    /// The loaded-guard must not swallow retries: failed and empty states
    /// still refetch on the next `load()`.
    @Test func loadRetriesAfterFailure() async throws {
        defer { Self.resetHandler() }
        _ = Self.installRouter(dailyStatus: 500, dailyBody: Data("{}".utf8))
        let (viewModel, _) = Self.makeModels()

        await viewModel.load()
        #expect(viewModel.state == .failed("Couldn't load today's looks."))

        _ = Self.installRouter() // backend recovers
        await viewModel.load()
        #expect(viewModel.state == .loaded)
        #expect(viewModel.suggestions.count == 2)
    }

    @Test func loadWithZeroSuggestionsBecomesEmpty() async throws {
        defer { Self.resetHandler() }
        _ = Self.installRouter(dailyBody: Data("""
        {"suggestions":[],"total_suggestions":0,"generated_at":"2026-07-15T06:00:00",\
        "weather":\(weatherJSON),"occasion":"casual","cached":false}
        """.utf8))
        let (viewModel, _) = Self.makeModels()

        await viewModel.load()

        #expect(viewModel.state == .empty)
        #expect(viewModel.weather != nil) // weather strip still renders
    }

    // MARK: Skip (local only)

    @Test func skipAdvancesAndWrapsWithoutAnyAPICall() async throws {
        defer { Self.resetHandler() }
        let captured = Self.installRouter()
        let (viewModel, _) = Self.makeModels()
        await viewModel.load()

        viewModel.skip()
        #expect(viewModel.currentIndex == 1)
        #expect(viewModel.current?.topItemId == "t-2")

        viewModel.skip()
        #expect(viewModel.currentIndex == 0) // wraps

        // Only the initial GET happened — skip never touches the network.
        #expect(captured.withLock { $0.count } == 1)
    }

    // MARK: Wear

    @Test func wearCreatesOutfitThenMarksWornTodayAndAdvances() async throws {
        defer { Self.resetHandler() }
        let captured = Self.installRouter()
        let (viewModel, outfits) = Self.makeModels()
        await viewModel.load()

        let succeeded = await viewModel.wear(using: outfits)

        #expect(succeeded)
        #expect(viewModel.currentIndex == 1)
        #expect(viewModel.errorMessage == nil)

        let requests = captured.withLock { $0 }
        try #require(requests.count == 3) // daily, create, wear

        #expect(requests[1].method == "POST")
        #expect(requests[1].path == "/api/v1/outfits")
        let createBody = try Self.json(requests[1].body)
        #expect(createBody == [
            "top_item_id": "t-1",
            "bottom_item_id": "b-1",
            "accessory_ids": [],
            "occasion_context": "casual",
        ] as NSDictionary)

        #expect(requests[2].method == "POST")
        #expect(requests[2].path == "/api/v1/outfits/o-1/wear")
        let wearBody = try Self.json(requests[2].body)
        #expect(wearBody == ["worn_date": TodayViewModel.todayWornDate()] as NSDictionary)
    }

    @Test func wearIncludesAccessoryIdWhenSuggestionHasOne() async throws {
        defer { Self.resetHandler() }
        let captured = Self.installRouter()
        let (viewModel, outfits) = Self.makeModels()
        await viewModel.load()
        viewModel.skip() // move to t-2/b-2 which carries accessory a-2

        _ = await viewModel.wear(using: outfits)

        let createBody = try Self.json(captured.withLock { $0 }[1].body)
        #expect(createBody["accessory_ids"] as? [String] == ["a-2"])
        #expect(createBody["top_item_id"] as? String == "t-2")
    }

    @Test func wearFailureSetsErrorMessageAndDoesNotAdvance() async throws {
        defer { Self.resetHandler() }
        _ = Self.installRouter(
            createStatus: 404,
            createBody: Data(#"{"detail":"Top item t-1 not found"}"#.utf8)
        )
        let (viewModel, outfits) = Self.makeModels()
        await viewModel.load()

        let succeeded = await viewModel.wear(using: outfits)

        #expect(!succeeded)
        #expect(viewModel.errorMessage == "Top item t-1 not found")
        #expect(viewModel.currentIndex == 0)
    }

    // MARK: Feedback (heart / X)

    @Test func loveSubmitsFeedbackScoreOneAndStays() async throws {
        defer { Self.resetHandler() }
        let captured = Self.installRouter()
        let (viewModel, outfits) = Self.makeModels()
        await viewModel.load()

        let succeeded = await viewModel.love(using: outfits)

        #expect(succeeded)
        #expect(viewModel.currentIndex == 0) // RN keeps the card visible

        let requests = captured.withLock { $0 }
        try #require(requests.count == 3) // daily, create, feedback
        #expect(requests[1].path == "/api/v1/outfits")
        #expect(requests[2].method == "POST")
        #expect(requests[2].path == "/api/v1/outfits/o-1/feedback")
        let body = try Self.json(requests[2].body)
        #expect(body == ["feedback_score": 1] as NSDictionary)
    }

    @Test func dismissSubmitsFeedbackScoreMinusOneAndAdvances() async throws {
        defer { Self.resetHandler() }
        let captured = Self.installRouter()
        let (viewModel, outfits) = Self.makeModels()
        await viewModel.load()

        let succeeded = await viewModel.dismiss(using: outfits)

        #expect(succeeded)
        #expect(viewModel.currentIndex == 1)

        let requests = captured.withLock { $0 }
        #expect(requests.last?.path == "/api/v1/outfits/o-1/feedback")
        let body = try Self.json(requests.last?.body)
        #expect(body == ["feedback_score": -1] as NSDictionary)
    }

    /// RN `persistedOutfits`: heart then wear on the same suggestion creates
    /// only ONE outfit row and reuses its id.
    @Test func loveThenWearReusesThePersistedOutfit() async throws {
        defer { Self.resetHandler() }
        let captured = Self.installRouter()
        let (viewModel, outfits) = Self.makeModels()
        await viewModel.load()

        _ = await viewModel.love(using: outfits)
        _ = await viewModel.wear(using: outfits)

        let requests = captured.withLock { $0 }
        let creates = requests.filter { $0.method == "POST" && $0.path == "/api/v1/outfits" }
        #expect(creates.count == 1)
        #expect(requests.last?.path == "/api/v1/outfits/o-1/wear")
    }

    // MARK: Presentational titles

    @Test func lookTitlesAreDeterministicPerOccasionAndIndex() {
        #expect(LookTitles.title(occasion: "casual", index: 0) == LookTitles.title(occasion: "casual", index: 0))
        #expect(LookTitles.title(occasion: "casual", index: 0) != LookTitles.title(occasion: "casual", index: 1))
        #expect(LookTitles.title(occasion: "casual", index: 0) == "The Long Walk")
        #expect(LookTitles.title(occasion: "CASUAL", index: 0) == "The Long Walk") // case-insensitive
        #expect(LookTitles.title(occasion: "casual", index: 4) == LookTitles.title(occasion: "casual", index: 0)) // cycles
        #expect(LookTitles.title(occasion: nil, index: 0) == "The Long Walk") // fallback list
        #expect(LookTitles.title(occasion: "athletic", index: 0) == "Morning Run")
    }

    // MARK: Greeting helpers

    @Test func greetingFollowsHourOfDay() throws {
        let calendar = Calendar.current
        let morning = try #require(calendar.date(bySettingHour: 9, minute: 0, second: 0, of: .now))
        let afternoon = try #require(calendar.date(bySettingHour: 14, minute: 30, second: 0, of: .now))
        let evening = try #require(calendar.date(bySettingHour: 19, minute: 0, second: 0, of: .now))
        #expect(TodayViewModel.greeting(for: morning) == "Good morning")
        #expect(TodayViewModel.greeting(for: afternoon) == "Good afternoon")
        #expect(TodayViewModel.greeting(for: evening) == "Good evening")
    }

    @Test func dateLineIsWeekdayThenDayMonth() throws {
        // 2025-06-23 is a Monday (design artboard: "Monday 23/06").
        let date = try #require(Calendar.current.date(from: DateComponents(year: 2025, month: 6, day: 23, hour: 12)))
        #expect(TodayViewModel.dateLine(for: date) == "Monday 23/06")
    }

    @Test func firstNameTakesFirstWordOrThere() {
        #expect(TodayViewModel.firstName(from: nil) == "there")
        #expect(TodayViewModel.firstName(from: Self.makeUser(fullName: nil)) == "there")
        #expect(TodayViewModel.firstName(from: Self.makeUser(fullName: "Natasha Roy")) == "Natasha")
        #expect(TodayViewModel.firstName(from: Self.makeUser(fullName: "Cher")) == "Cher")
    }

    /// The worn date is the user's LOCAL calendar day — deliberate divergence
    /// from RN's `toISOString().slice(0, 10)` UTC day (diary semantics: an
    /// evening wear belongs to the user's day, not tomorrow's UTC day).
    @Test func todayWornDateUsesLocalCalendarDay() throws {
        // 2026-07-15T23:30:00Z — the same instant is a different diary day
        // east of UTC+00:30.
        let instant = Date(timeIntervalSince1970: 1_784_158_200)
        let utc = try #require(TimeZone(identifier: "UTC"))
        let kolkata = try #require(TimeZone(identifier: "Asia/Kolkata")) // UTC+5:30
        let honolulu = try #require(TimeZone(identifier: "Pacific/Honolulu")) // UTC-10
        #expect(TodayViewModel.todayWornDate(now: instant, timeZone: utc) == "2026-07-15")
        #expect(TodayViewModel.todayWornDate(now: instant, timeZone: kolkata) == "2026-07-16")
        #expect(TodayViewModel.todayWornDate(now: instant, timeZone: honolulu) == "2026-07-15")
        // The default is the device's zone.
        #expect(TodayViewModel.todayWornDate(now: instant)
            == TodayViewModel.todayWornDate(now: instant, timeZone: .current))
    }

    private static func makeUser(fullName: String?) -> User {
        User(
            id: "u-1",
            email: "a@b.c",
            fullName: fullName,
            location: nil,
            savedLatitude: nil,
            savedLongitude: nil,
            savedCity: nil,
            isActive: true,
            isVerified: false,
            createdAt: Date(),
            updatedAt: Date(),
            lastLogin: nil,
            oauthProvider: nil,
            stylePreferences: nil,
            onboardingCompleted: true,
            onboardingStep: nil
        )
    }
}
