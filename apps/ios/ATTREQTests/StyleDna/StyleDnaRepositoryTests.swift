//
//  StyleDnaRepositoryTests.swift
//  ATTREQTests
//
//  StyleDnaRepository request/response contract against the backend
//  (endpoints/style_dna.py, endpoints/wardrobe.py bulk add, endpoints/users.py
//  onboarding complete): multipart multi-photo encoding, verb+path+body for
//  profile/correct/regenerate/delete, bulk-add encode/decode, and the
//  verbatim-dictionary-key behavior the review screen depends on.
//

import Foundation
import Testing
@testable import ATTREQ

/// Dedicated mock transport for this suite — its own static handler, separate
/// from the other suites' protocols, so parallel suites cannot race each other.
/// The handler receives the drained request body (URLProtocol only ever sees
/// `httpBodyStream`, never `httpBody`).
final class StyleDnaMockURLProtocol: URLProtocol {
    typealias Handler = @Sendable (URLRequest, Data?) -> (status: Int, body: Data)

    static let handler = LockedBox<Handler?>(nil)

    static func makeSession() -> URLSession {
        let configuration = URLSessionConfiguration.ephemeral
        configuration.protocolClasses = [StyleDnaMockURLProtocol.self]
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

// MARK: - Backend JSON fixtures (shapes from schemas/style_dna.py, schemas/wardrobe.py, schemas/user.py)

private let styleDnaJSON = """
{"aesthetic":{"primary":"minimalist","secondary":["classic","casual"],"confidence":0.82},\
"color_palette":{"dominant":["navy","white"],"accent":["camel"],"avoids":["neon"],"confidence":0.78},\
"patterns":{"preferred":["solid","stripe"],"confidence":0.7},\
"silhouette":{"preference":"tailored","confidence":0.66},\
"formality_bias":{"level":1.8,"label":"smart-casual","confidence":0.74},\
"occasions":{"primary":["work","casual"],"confidence":0.71},\
"behaviour_weights":{"category_likes":{"top":0.55}}}
"""

private func photoJSON(id: String, qualityOk: Bool = true) -> String {
    """
    {"id":"\(id)","user_id":"u-1","file_path":"style-dna/\(id).jpg",\
    "file_url":"/uploads/style-dna/\(id).jpg","quality_ok":\(qualityOk),\
    "quality_reason":\(qualityOk ? "null" : #""Photo too dark""#),\
    "per_photo_extraction":{"usable":\(qualityOk),\
    "style_signals":{"aesthetic":"minimalist"},\
    "wardrobe_items_detected":[{"category":"top","subcategory":"t-shirt","confidence":0.9}]},\
    "created_at":"2026-07-15T06:00:00.000000Z"}
    """
}

private func uploadResponseJSON(processed: Int, skipped: Int, seeded: Int, photoIDs: [String]) -> Data {
    let photos = photoIDs.map { photoJSON(id: $0) }.joined(separator: ",")
    return Data("""
    {"photos_processed":\(processed),"photos_skipped":\(skipped),\
    "wardrobe_items_seeded":\(seeded),"style_dna":\(styleDnaJSON),"photos":[\(photos)]}
    """.utf8)
}

private func profileResponseJSON(photoIDs: [String]) -> Data {
    let photos = photoIDs.map { photoJSON(id: $0) }.joined(separator: ",")
    return Data(#"{"style_dna":\#(styleDnaJSON),"photos":[\#(photos)]}"#.utf8)
}

/// Same shape as `styleDnaJSON` plus the RI-3 `personal_color` key the selfie
/// endpoint merges in.
private let styleDnaWithPersonalColorJSON = """
{"aesthetic":{"primary":"minimalist","secondary":["classic","casual"],"confidence":0.82},\
"color_palette":{"dominant":["navy","white"],"accent":["camel"],"avoids":["neon"],"confidence":0.78},\
"patterns":{"preferred":["solid","stripe"],"confidence":0.7},\
"silhouette":{"preference":"tailored","confidence":0.66},\
"formality_bias":{"level":1.8,"label":"smart-casual","confidence":0.74},\
"occasions":{"primary":["work","casual"],"confidence":0.71},\
"behaviour_weights":{"category_likes":{"top":0.55}},\
"personal_color":{"undertone_warm_cool":0.3,"depth_light_deep":-0.4,"confidence":0.82}}
"""

private func profileResponseWithPersonalColorJSON(photoIDs: [String]) -> Data {
    let photos = photoIDs.map { photoJSON(id: $0) }.joined(separator: ",")
    return Data(#"{"style_dna":\#(styleDnaWithPersonalColorJSON),"photos":[\#(photos)]}"#.utf8)
}

private func wardrobeItemJSON(id: String, category: String) -> String {
    """
    {"id":"\(id)","user_id":"u-1","original_image_url":"/uploads/style-dna/placeholder.jpg",\
    "processed_image_url":null,"thumbnail_url":null,"category":"\(category)",\
    "color_primary":"navy","color_secondary":null,"pattern":"solid",\
    "season":["all"],"occasion":["casual"],"detection_confidence":0.9,\
    "classification_source":"style_dna_seed","processing_status":"completed",\
    "wear_count":0,"last_worn":null,\
    "created_at":"2026-07-15T06:00:00.000000Z","updated_at":"2026-07-15T06:00:00.000000Z"}
    """
}

private let userJSON = Data("""
{"id":"u-1","email":"a@b.c","full_name":"Test User","location":null,\
"saved_latitude":null,"saved_longitude":null,"saved_city":null,\
"is_active":true,"is_verified":false,\
"created_at":"2026-07-15T06:00:00.000000Z","updated_at":"2026-07-15T06:00:00.000000Z",\
"last_login":null,"oauth_provider":null,"style_preferences":"{}",\
"onboarding_completed":true,"onboarding_step":"complete"}
""".utf8)

/// One captured request: everything the assertions need, taken inside the handler.
private struct CapturedRequest: Sendable {
    var method: String?
    var path: String?
    var contentType: String?
    var body: Data?
}

// MARK: - Tests

@Suite(.serialized)
struct StyleDnaRepositoryTests {
    private static let baseURL = URL(string: "http://localhost:8001/api/v1")!

    private static func makeRepository() -> StyleDnaRepository {
        let client = APIClient(
            baseURL: baseURL,
            session: StyleDnaMockURLProtocol.makeSession(),
            authSession: nil
        )
        return StyleDnaRepository(apiClient: client)
    }

    /// Installs a handler that captures the request and answers with `status`/`body`.
    private static func capture(status: Int, body: Data) -> LockedBox<CapturedRequest?> {
        let captured = LockedBox<CapturedRequest?>(nil)
        StyleDnaMockURLProtocol.handler.withLock { handler in
            handler = { request, requestBody in
                captured.withLock {
                    $0 = CapturedRequest(
                        method: request.httpMethod,
                        path: request.url?.path(),
                        contentType: request.value(forHTTPHeaderField: "Content-Type"),
                        body: requestBody
                    )
                }
                return (status, body)
            }
        }
        return captured
    }

    private static func resetHandler() {
        StyleDnaMockURLProtocol.handler.withLock { $0 = nil }
    }

    // MARK: Upload (multipart)

    @Test func uploadEncodesOnePartPerPhotoUnderFilesFieldName() async throws {
        defer { Self.resetHandler() }
        let photos = [Data("JPEG-BYTES-0".utf8), Data("JPEG-BYTES-1".utf8), Data("JPEG-BYTES-2".utf8)]
        let captured = Self.capture(
            status: 201,
            body: uploadResponseJSON(processed: 3, skipped: 0, seeded: 5, photoIDs: ["p-1", "p-2", "p-3"])
        )

        let response = try await Self.makeRepository().uploadPhotos(photos)

        let request = try #require(captured.withLock { $0 })
        #expect(request.method == "POST")
        #expect(request.path == "/api/v1/users/style-dna/upload")

        // Content-Type carries the boundary; body is RFC 7578 multipart.
        let contentType = try #require(request.contentType)
        #expect(contentType.hasPrefix("multipart/form-data; boundary="))
        let boundary = String(contentType.dropFirst("multipart/form-data; boundary=".count))
        let bodyData = try #require(request.body)
        let bodyText = try #require(String(data: bodyData, encoding: .utf8))

        // Exactly N parts + the terminator; every part uses the repeated
        // field name "files" (FastAPI list[UploadFile]) with indexed filenames.
        let segments = bodyText.components(separatedBy: "--\(boundary)")
        #expect(segments.count == photos.count + 2) // leading "" + 3 parts + trailing "--\r\n"
        #expect(segments.last == "--\r\n")
        for (index, segment) in segments.dropFirst().dropLast().enumerated() {
            #expect(segment.contains(
                "Content-Disposition: form-data; name=\"files\"; filename=\"photo-\(index).jpg\""
            ))
            #expect(segment.contains("Content-Type: image/jpeg"))
            #expect(segment.contains("JPEG-BYTES-\(index)"))
        }

        #expect(response.photosProcessed == 3)
        #expect(response.photosSkipped == 0)
        #expect(response.wardrobeItemsSeeded == 5)
        #expect(response.styleDna?.aesthetic.primary == "minimalist")
        #expect(response.styleDna?.colorPalette.dominant == ["navy", "white"])
        #expect(response.styleDna?.formalityBias.label == "smart-casual")
        #expect(response.photos.map(\.id) == ["p-1", "p-2", "p-3"])
    }

    /// The review screen reads detected items from
    /// `per_photo_extraction["wardrobe_items_detected"]` — dictionary keys must
    /// arrive VERBATIM (snake_case), untouched by `.convertFromSnakeCase`.
    @Test func uploadResponseKeepsPerPhotoExtractionKeysVerbatim() async throws {
        defer { Self.resetHandler() }
        _ = Self.capture(
            status: 201,
            body: uploadResponseJSON(processed: 3, skipped: 0, seeded: 2, photoIDs: ["p-1"])
        )

        let response = try await Self.makeRepository()
            .uploadPhotos([Data("a".utf8), Data("b".utf8), Data("c".utf8)])

        let extraction = try #require(response.photos.first?.perPhotoExtraction)
        guard case let .array(detected)? = extraction["wardrobe_items_detected"] else {
            Issue.record("Expected verbatim 'wardrobe_items_detected' key, got keys: \(extraction.keys.sorted())")
            return
        }
        #expect(detected.count == 1)
        guard case let .object(item) = detected[0], case .string("t-shirt")? = item["subcategory"] else {
            Issue.record("Unexpected detected item shape: \(detected)")
            return
        }
    }

    // MARK: Profile

    @Test func profileSendsGETAndDecodes() async throws {
        defer { Self.resetHandler() }
        let captured = Self.capture(status: 200, body: profileResponseJSON(photoIDs: ["p-1", "p-2"]))

        let response = try await Self.makeRepository().profile()

        let request = try #require(captured.withLock { $0 })
        #expect(request.method == "GET")
        #expect(request.path == "/api/v1/users/style-dna")
        #expect(request.body == nil || request.body?.isEmpty == true)

        #expect(response.styleDna?.silhouette.preference == "tailored")
        #expect(response.styleDna?.behaviourWeights["category_likes"]?["top"] == 0.55)
        #expect(response.photos.count == 2)
        #expect(response.photos[0].qualityOk)
        #expect(response.photos[0].fileUrl == "/uploads/style-dna/p-1.jpg")
    }

    // MARK: Correct (PATCH)

    /// Corrections travel as `{"corrections": {...}}` with the caller's keys
    /// passed through VERBATIM — the backend deep-merges snake_case keys, so
    /// callers must build them in snake_case (`.convertToSnakeCase` does not
    /// rewrite dictionary keys).
    @Test func correctSendsPATCHWithVerbatimSnakeCaseCorrectionKeys() async throws {
        defer { Self.resetHandler() }
        let captured = Self.capture(status: 200, body: profileResponseJSON(photoIDs: ["p-1"]))

        let response = try await Self.makeRepository().correct([
            "color_palette": .object(["dominant": .array([.string("navy"), .string("olive")])]),
            "aesthetic": .object(["primary": .string("streetwear")]),
        ])

        let request = try #require(captured.withLock { $0 })
        #expect(request.method == "PATCH")
        #expect(request.path == "/api/v1/users/style-dna")
        #expect(request.contentType == "application/json")

        let bodyData = try #require(request.body)
        let payload = try JSONSerialization.jsonObject(with: bodyData) as? NSDictionary
        #expect(payload == [
            "corrections": [
                "color_palette": ["dominant": ["navy", "olive"]],
                "aesthetic": ["primary": "streetwear"],
            ],
        ] as NSDictionary)

        #expect(response.styleDna?.aesthetic.primary == "minimalist") // echoes server profile
    }

    // MARK: Regenerate

    /// Backend truth: regenerate returns StyleDnaUploadResponse (not the profile
    /// shape) with `wardrobe_items_seeded` always 0.
    @Test func regenerateSendsPOSTAndDecodesUploadResponse() async throws {
        defer { Self.resetHandler() }
        let captured = Self.capture(
            status: 200,
            body: uploadResponseJSON(processed: 4, skipped: 1, seeded: 0, photoIDs: ["p-1"])
        )

        let response = try await Self.makeRepository().regenerate()

        let request = try #require(captured.withLock { $0 })
        #expect(request.method == "POST")
        #expect(request.path == "/api/v1/users/style-dna/regenerate")
        #expect(request.body == nil || request.body?.isEmpty == true)

        #expect(response.photosProcessed == 4)
        #expect(response.photosSkipped == 1)
        #expect(response.wardrobeItemsSeeded == 0)
        #expect(response.styleDna?.occasions.primary == ["work", "casual"])
    }

    // MARK: Delete photos

    /// Backend truth: DELETE /users/style-dna/photos deletes ALL seed photos
    /// (204, empty body); there is no per-photo delete.
    @Test func deletePhotosSendsDELETEAndAcceptsEmpty204() async throws {
        defer { Self.resetHandler() }
        let captured = Self.capture(status: 204, body: Data())

        try await Self.makeRepository().deletePhotos()

        let request = try #require(captured.withLock { $0 })
        #expect(request.method == "DELETE")
        #expect(request.path == "/api/v1/users/style-dna/photos")
        #expect(request.body == nil || request.body?.isEmpty == true)
    }

    // MARK: Bulk add

    /// POST /wardrobe/items/bulk takes a TOP-LEVEL JSON ARRAY of item dicts with
    /// snake_case keys and returns the created WardrobeItemResponse list.
    @Test func bulkAddEncodesTopLevelSnakeCaseArrayAndDecodesCreatedItems() async throws {
        defer { Self.resetHandler() }
        let responseBody = Data(
            "[\(wardrobeItemJSON(id: "w-1", category: "t-shirt")),\(wardrobeItemJSON(id: "w-2", category: "chinos"))]".utf8
        )
        let captured = Self.capture(status: 201, body: responseBody)

        let detected = [
            DetectedWardrobeItem(
                category: "top", subcategory: "t-shirt",
                colorPrimary: "navy", colorSecondary: nil, pattern: "solid",
                occasion: ["casual"], season: ["all"],
                confidence: 0.9, boundingRegion: "upper-half"
            ),
            DetectedWardrobeItem(
                category: "bottom", subcategory: "chinos",
                colorPrimary: "beige", colorSecondary: nil, pattern: nil,
                occasion: ["casual", "work"], season: ["all"],
                confidence: 0.75, boundingRegion: "lower-half"
            ),
        ]
        let created = try await Self.makeRepository().bulkAddItems(detected)

        let request = try #require(captured.withLock { $0 })
        #expect(request.method == "POST")
        #expect(request.path == "/api/v1/wardrobe/items/bulk")
        #expect(request.contentType == "application/json")

        let bodyData = try #require(request.body)
        let payload = try JSONSerialization.jsonObject(with: bodyData) as? NSArray
        // JSONEncoder omits nil optionals; struct keys become snake_case.
        #expect(payload == [
            [
                "category": "top", "subcategory": "t-shirt",
                "color_primary": "navy", "pattern": "solid",
                "occasion": ["casual"], "season": ["all"],
                "confidence": 0.9, "bounding_region": "upper-half",
            ],
            [
                "category": "bottom", "subcategory": "chinos",
                "color_primary": "beige",
                "occasion": ["casual", "work"], "season": ["all"],
                "confidence": 0.75, "bounding_region": "lower-half",
            ],
        ] as NSArray)

        #expect(created.map(\.id) == ["w-1", "w-2"])
        #expect(created.map(\.category) == ["t-shirt", "chinos"])
        #expect(created.allSatisfy { $0.classificationSource == "style_dna_seed" })
        #expect(created.allSatisfy { $0.processingStatus == .completed })
    }

    // MARK: Onboarding complete

    @Test func completeOnboardingSendsPOSTAndDecodesUser() async throws {
        defer { Self.resetHandler() }
        let captured = Self.capture(status: 200, body: userJSON)

        let user = try await Self.makeRepository().completeOnboarding()

        let request = try #require(captured.withLock { $0 })
        #expect(request.method == "POST")
        #expect(request.path == "/api/v1/users/onboarding/complete")

        #expect(user.onboardingCompleted)
        #expect(user.onboardingStep == "complete")
    }

    // MARK: Personal-color selfie (RI-3)

    @Test func estimatePersonalColorEncodesFileAndConsentAndDecodesPersonalColor() async throws {
        defer { Self.resetHandler() }
        let captured = Self.capture(
            status: 200,
            body: profileResponseWithPersonalColorJSON(photoIDs: ["p-1"])
        )

        let response = try await Self.makeRepository().estimatePersonalColor(
            imageData: Data("SELFIE-BYTES".utf8),
            consent: true
        )

        let request = try #require(captured.withLock { $0 })
        #expect(request.method == "POST")
        #expect(request.path == "/api/v1/users/style-dna/selfie")

        let contentType = try #require(request.contentType)
        #expect(contentType.hasPrefix("multipart/form-data; boundary="))
        let boundary = String(contentType.dropFirst("multipart/form-data; boundary=".count))
        let bodyData = try #require(request.body)
        let bodyText = try #require(String(data: bodyData, encoding: .utf8))

        // Exactly 2 parts (file + consent) + the terminator.
        let segments = bodyText.components(separatedBy: "--\(boundary)")
        #expect(segments.count == 2 + 2)
        #expect(bodyText.contains(
            "Content-Disposition: form-data; name=\"file\"; filename=\"selfie.jpg\""
        ))
        #expect(bodyText.contains("Content-Type: image/jpeg"))
        #expect(bodyText.contains("SELFIE-BYTES"))
        #expect(bodyText.contains("Content-Disposition: form-data; name=\"consent\""))
        #expect(bodyText.contains("\r\n\r\ntrue\r\n"))

        #expect(response.styleDna?.aesthetic.primary == "minimalist") // unrelated fields still decode
        #expect(response.styleDna?.personalColor?.undertoneWarmCool == 0.3)
        #expect(response.styleDna?.personalColor?.depthLightDeep == -0.4)
        #expect(response.styleDna?.personalColor?.confidence == 0.82)
    }

    /// The endpoint is feature-flagged (404 when disabled) and 400s without
    /// consent; both must surface as an ordinary `APIError`, never crash —
    /// callers (`OnboardingViewModel`) are responsible for treating this as a
    /// soft, non-blocking failure.
    @Test func estimatePersonalColorSurfacesHTTPErrorsAsAPIError() async throws {
        defer { Self.resetHandler() }
        _ = Self.capture(
            status: 404,
            body: Data(#"{"detail":"Personal-color selfie estimation is not enabled"}"#.utf8)
        )

        await #expect(throws: APIError.self) {
            _ = try await Self.makeRepository().estimatePersonalColor(
                imageData: Data("x".utf8),
                consent: true
            )
        }
    }

    /// `StyleDna` without a `personal_color` key decodes it as `nil`, not a
    /// decode failure — an absent optional key must not poison the rest of
    /// the profile the way a missing REQUIRED field does.
    @Test func profileWithoutPersonalColorKeyDecodesNilPersonalColor() async throws {
        defer { Self.resetHandler() }
        _ = Self.capture(status: 200, body: profileResponseJSON(photoIDs: ["p-1"]))

        let response = try await Self.makeRepository().profile()

        #expect(response.styleDna != nil)
        #expect(response.styleDna?.personalColor == nil)
    }
}
