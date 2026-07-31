//
//  WardrobeItemV2Tests.swift
//  ATTREQTests
//
//  RI-2: classifier schema v2 decode + low-confidence-flag coverage.
//  1. A legacy (schema_version=1) row with every v2 key absent decodes
//     without crashing (old rows predate these fields entirely).
//  2. A v2 row with the 11 new fields populated decodes them correctly.
//  3. `WardrobeItemDetailViewModel.isLowConfidence` flags a field whose
//     backend-reported confidence is below the 0.6 "tap to confirm" threshold
//     and does not flag a well-confident one.
//

import Foundation
import Testing
@testable import ATTREQ

/// Dedicated mock transport — separate static handler from other suites'
/// protocols (see `PollingMockURLProtocol`'s doc comment) so parallel test
/// suites cannot race each other.
final class WardrobeV2MockURLProtocol: URLProtocol {
    typealias Handler = @Sendable (URLRequest) -> (status: Int, body: Data)

    static let handler = LockedBox<Handler?>(nil)

    static func makeSession() -> URLSession {
        let configuration = URLSessionConfiguration.ephemeral
        configuration.protocolClasses = [WardrobeV2MockURLProtocol.self]
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

private let legacyV1ItemJSON = """
{"id":"item-1","user_id":"u-1","original_image_url":"/uploads/originals/item-1.jpg",\
"processed_image_url":null,"thumbnail_url":null,\
"category":"shirt","color_primary":"blue","color_secondary":null,"pattern":"solid",\
"season":["summer"],"occasion":["casual"],"detection_confidence":0.9,\
"classification_source":"ai","processing_status":"completed",\
"wear_count":1,"last_worn":null,\
"created_at":"2026-07-15T06:00:00.000000Z","updated_at":"2026-07-15T06:00:00.000000Z"}
"""

private func v2ItemJSON(attributeConfidence: String) -> String {
    """
    {"id":"item-2","user_id":"u-1","original_image_url":"/uploads/originals/item-2.jpg",\
    "processed_image_url":"/uploads/processed/item-2.png","thumbnail_url":null,\
    "category":"shirt","color_primary":"navy","color_secondary":null,"pattern":"solid",\
    "season":["summer"],"occasion":["casual"],"detection_confidence":0.9,\
    "classification_source":"ai","processing_status":"completed",\
    "wear_count":1,"last_worn":null,\
    "texture":"knit","silhouette":"oversized","neckline":"crew","sleeve_length":"long",\
    "statement_level":"statement","llm_formality":2,"is_fullbody":false,\
    "color_palette":[{"lab":[13.0,47.5,-64.7],"hex":"#000080","share":0.8,"is_neutral":false,"name":"navy"}],\
    "color_extraction_source":"pixel",\
    "attribute_confidence":\(attributeConfidence),\
    "schema_version":2,\
    "created_at":"2026-07-15T06:00:00.000000Z","updated_at":"2026-07-15T06:00:00.000000Z"}
    """
}

private func photosJSON() -> Data {
    Data("[]".utf8)
}

@Suite(.serialized)
@MainActor
struct WardrobeItemV2Tests {
    private static let baseURL = URL(string: "http://localhost:8001/api/v1")!

    private static func makeRepository() -> WardrobeRepository {
        let client = APIClient(
            baseURL: baseURL,
            session: WardrobeV2MockURLProtocol.makeSession(),
            authSession: nil
        )
        return WardrobeRepository(apiClient: client)
    }

    @Test
    func legacyV1RowWithNoV2FieldsDecodesWithDefaults() throws {
        let item = try APIClient.makeDecoder().decode(WardrobeItem.self, from: Data(legacyV1ItemJSON.utf8))

        #expect(item.category == "shirt")
        #expect(item.texture == nil)
        #expect(item.silhouette == nil)
        #expect(item.neckline == nil)
        #expect(item.sleeveLength == nil)
        #expect(item.statementLevel == nil)
        #expect(item.llmFormality == nil)
        #expect(item.isFullbody == false)
        #expect(item.colorPalette == nil)
        #expect(item.attributeConfidence == nil)
        #expect(item.schemaVersion == 1)
    }

    @Test
    func v2RowDecodesAllElevenFields() throws {
        let json = v2ItemJSON(attributeConfidence: "{\"category\":0.95,\"texture\":0.4}")
        let item = try APIClient.makeDecoder().decode(WardrobeItem.self, from: Data(json.utf8))

        #expect(item.texture == .knit)
        #expect(item.silhouette == .oversized)
        #expect(item.neckline == .crew)
        #expect(item.sleeveLength == .long)
        #expect(item.statementLevel == .statement)
        #expect(item.llmFormality == 2)
        #expect(item.isFullbody == false)
        #expect(item.schemaVersion == 2)
        #expect(item.colorPalette?.first?.name == "navy")
        #expect(item.colorPalette?.first?.isNeutral == false)
        // Dictionary keys pass through JSONDecoder verbatim (no snake_case
        // conversion applied to keys, only to struct property names).
        #expect(item.attributeConfidence?["category"] == 0.95)
        #expect(item.attributeConfidence?["texture"] == 0.4)
    }

    @Test
    func lowConfidenceFieldIsFlaggedAndConfidentFieldIsNot() async throws {
        let json = v2ItemJSON(attributeConfidence: "{\"category\":0.95,\"texture\":0.4}")

        WardrobeV2MockURLProtocol.handler.withLock { $0 = { request in
            if request.url?.path.hasSuffix("/photos") == true {
                return (200, photosJSON())
            }
            return (200, Data(json.utf8))
        } }
        defer { WardrobeV2MockURLProtocol.handler.withLock { $0 = nil } }

        let model = WardrobeItemDetailViewModel(itemId: "item-2", repository: Self.makeRepository())
        await model.load()

        #expect(model.isLowConfidence("texture") == true) // 0.4 < 0.6
        #expect(model.isLowConfidence("category") == false) // 0.95 >= 0.6
        #expect(model.isLowConfidence("silhouette") == false) // absent key -> not flagged
    }
}
