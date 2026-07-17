//
//  ProfileTests.swift
//  ATTREQTests
//
//  StylePreferencesValue parsing (the backend column is DNA-owned) and
//  ProfileViewModel staleness (markStale → refetch on next load), M5 review.
//

import Foundation
import Testing
@testable import ATTREQ

// MARK: - StylePreferencesValue

struct StylePreferencesValueTests {
    @Test func dnaJsonIsTreatedAsUnset() {
        let dna = #"{"aesthetic": {"primary": "minimalist"}, "color_palette": {}}"#
        let value = StylePreferencesValue.parse(dna)
        #expect(value == .dnaOwned)
        #expect(value.isDnaOwned)
        #expect(value.displayString == "Not set")
        #expect(value.prefillParts.isEmpty)
    }

    @Test func leadingWhitespaceBeforeBraceStillDnaOwned() {
        #expect(StylePreferencesValue.parse("  \n {\"x\":1}") == .dnaOwned)
    }

    @Test func plainChipStringIsDisplayedAndPrefilled() {
        let value = StylePreferencesValue.parse("Minimal, Earthy, Layered, Work")
        #expect(value == .plain("Minimal, Earthy, Layered, Work"))
        #expect(value.displayString == "Minimal, Earthy, Layered, Work")
        #expect(value.prefillParts == ["Minimal", "Earthy", "Layered", "Work"])
    }

    @Test func nilAndBlankAreEmpty() {
        #expect(StylePreferencesValue.parse(nil) == .empty)
        #expect(StylePreferencesValue.parse("   ") == .empty)
        #expect(StylePreferencesValue.parse(nil).displayString == "Not set")
        #expect(StylePreferencesValue.parse(nil).prefillParts.isEmpty)
    }
}

// MARK: - ProfileViewModel staleness

final class ProfileMockURLProtocol: URLProtocol {
    typealias Handler = @Sendable (URLRequest) -> (status: Int, body: Data)
    static let handler = LockedBox<Handler?>(nil)

    static func makeSession() -> URLSession {
        let configuration = URLSessionConfiguration.ephemeral
        configuration.protocolClasses = [ProfileMockURLProtocol.self]
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
            url: url, statusCode: status, httpVersion: "HTTP/1.1",
            headerFields: ["Content-Type": "application/json"]
        )!
        client?.urlProtocol(self, didReceive: response, cacheStoragePolicy: .notAllowed)
        client?.urlProtocol(self, didLoad: body)
        client?.urlProtocolDidFinishLoading(self)
    }

    override func stopLoading() {}
}

private func wardrobeListJSON(total: Int) -> Data {
    Data("""
    {"items":[],"total":\(total),"page":1,"page_size":1,"total_pages":1}
    """.utf8)
}

private func outfitsListJSON(worn: [String]) -> Data {
    let items = worn.enumerated().map { index, day in
        """
        {"id":"o-\(index)","user_id":"u-1","top_item_id":"t","bottom_item_id":"b",\
        "accessory_ids":[],"occasion_context":"casual","worn_date":"\(day)",\
        "feedback_score":null,"weather_context":null,\
        "created_at":"2026-06-23T09:00:00.000000Z","updated_at":"2026-06-23T09:00:00.000000Z"}
        """
    }
    return Data("""
    {"items":[\(items.joined(separator: ","))],"total":\(worn.count),\
    "page":1,"page_size":100,"total_pages":1}
    """.utf8)
}

/// Routes by path; `pieces` drives the wardrobe total.
private func installProfileRouter(pieces: LockedBox<Int>, worn: LockedBox<[String]>) {
    ProfileMockURLProtocol.handler.withLock { handler in
        handler = { request in
            let path = request.url?.path() ?? ""
            if path.contains("/wardrobe/items") {
                return (200, wardrobeListJSON(total: pieces.withLock { $0 }))
            }
            if path.contains("/outfits") {
                return (200, outfitsListJSON(worn: worn.withLock { $0 }))
            }
            return (404, Data("{}".utf8))
        }
    }
}

@MainActor
@Suite(.serialized)
struct ProfileViewModelTests {
    private static let baseURL = URL(string: "http://localhost:8001/api/v1")!

    private static func makeViewModel() -> ProfileViewModel {
        let client = APIClient(baseURL: baseURL, session: ProfileMockURLProtocol.makeSession(), authSession: nil)
        return ProfileViewModel(
            wardrobeRepository: WardrobeRepository(apiClient: client),
            outfitsRepository: OutfitsRepository(apiClient: client)
        )
    }

    @Test func loadIsIdempotentUntilMarkedStale() async {
        let pieces = LockedBox(3)
        let worn = LockedBox<[String]>([])
        installProfileRouter(pieces: pieces, worn: worn)

        let viewModel = Self.makeViewModel()
        await viewModel.load()
        #expect(viewModel.stats?.pieces == 3)

        // Backend changes underneath; a plain re-load must NOT refetch.
        pieces.withLock { $0 = 9 }
        await viewModel.load()
        #expect(viewModel.stats?.pieces == 3)

        // After markStale, the next load refetches and picks up the new count.
        viewModel.markStale()
        await viewModel.load()
        #expect(viewModel.stats?.pieces == 9)
    }

    @Test func refreshAlwaysRefetches() async {
        let pieces = LockedBox(1)
        let worn = LockedBox<[String]>([])
        installProfileRouter(pieces: pieces, worn: worn)

        let viewModel = Self.makeViewModel()
        await viewModel.load()
        #expect(viewModel.stats?.pieces == 1)

        pieces.withLock { $0 = 5 }
        await viewModel.refresh()
        #expect(viewModel.stats?.pieces == 5)
    }
}
