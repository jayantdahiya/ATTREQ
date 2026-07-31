//
//  StyleDnaEditTests.swift
//  ATTREQTests
//
//  Style DNA correction UI (M5-WP2): the corrections-payload builder
//  (only changed facets, snake_case keys, JSONValue shapes, confidences
//  never sent) and StyleDnaProfileViewModel.applyCorrections (PATCH wire
//  format, server echo replaces state, failure keeps prior state and
//  surfaces saveError).
//

import Foundation
import Testing
@testable import ATTREQ

/// Dedicated mock transport for this suite — its own static handler, separate
/// from the other suites' protocols, so parallel suites cannot race each other.
/// The handler receives the drained request body (URLProtocol only ever sees
/// `httpBodyStream`, never `httpBody`).
final class StyleDnaEditMockURLProtocol: URLProtocol {
    typealias Handler = @Sendable (URLRequest, Data?) -> (status: Int, body: Data)

    static let handler = LockedBox<Handler?>(nil)

    static func makeSession() -> URLSession {
        let configuration = URLSessionConfiguration.ephemeral
        configuration.protocolClasses = [StyleDnaEditMockURLProtocol.self]
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

// MARK: - Fixtures

/// The profile the edit sheet was opened with (diff baseline). Note the
/// fractional formality level under a "smart-casual" label — the builder must
/// treat a reselect of the same LABEL as unchanged.
private let originalDna = StyleDna(
    aesthetic: StyleDnaAesthetic(
        primary: "minimalist",
        secondary: ["classic", "casual"],
        confidence: 0.82
    ),
    colorPalette: StyleDnaColorPalette(
        dominant: ["navy", "white"],
        accent: ["camel"],
        avoids: ["neon"],
        confidence: 0.78
    ),
    patterns: StyleDnaPatterns(preferred: ["solid"], confidence: 0.7),
    silhouette: StyleDnaSilhouette(preference: "tailored", confidence: 0.66),
    formalityBias: StyleDnaFormalityBias(level: 1.8, label: "smart-casual", confidence: 0.74),
    occasions: StyleDnaOccasions(primary: ["work"], confidence: 0.71),
    behaviourWeights: [:]
)

private let originalProfile = StyleDnaProfileResponse(styleDna: originalDna, photos: [])

/// Server echo after a successful PATCH: the merged profile
/// (schemas/style_dna.py shape) with the corrected primary + formality.
private let correctedProfileJSON = Data("""
{"style_dna":{"aesthetic":{"primary":"streetwear","secondary":["classic","casual"],"confidence":0.82},\
"color_palette":{"dominant":["navy","white"],"accent":["camel"],"avoids":["neon"],"confidence":0.78},\
"patterns":{"preferred":["solid"],"confidence":0.7},\
"silhouette":{"preference":"tailored","confidence":0.66},\
"formality_bias":{"level":3.0,"label":"formal","confidence":0.74},\
"occasions":{"primary":["work"],"confidence":0.71},\
"behaviour_weights":{}},"photos":[]}
""".utf8)

// MARK: - Corrections builder

struct StyleDnaCorrectionsBuilderTests {
    @Test func unchangedSelectionsProduceEmptyDict() {
        // Secondary reordered (set-equal) and formality reselected at the
        // same label (stored level is fractional 1.8) — neither is a change.
        let corrections = StyleDnaCorrectionsBuilder.build(
            original: originalDna,
            primary: "minimalist",
            secondary: ["casual", "classic"],
            formality: .smartCasual
        )
        #expect(corrections.isEmpty)
    }

    @Test func nilFormalityIsNeverSent() {
        // Off-vocabulary label (e.g. "business") pre-selects nothing; leaving
        // it untouched must not fabricate a formality correction.
        let corrections = StyleDnaCorrectionsBuilder.build(
            original: originalDna,
            primary: "minimalist",
            secondary: originalDna.aesthetic.secondary,
            formality: nil
        )
        #expect(corrections.isEmpty)
    }

    @Test func primaryChangeSendsOnlyPrimarySubtree() {
        let corrections = StyleDnaCorrectionsBuilder.build(
            original: originalDna,
            primary: "streetwear",
            secondary: originalDna.aesthetic.secondary,
            formality: .smartCasual
        )
        #expect(corrections == [
            "aesthetic": .object(["primary": .string("streetwear")]),
        ])
    }

    @Test func secondaryChangeSendsOnlySecondaryArray() {
        let corrections = StyleDnaCorrectionsBuilder.build(
            original: originalDna,
            primary: "minimalist",
            secondary: ["classic", "sporty"],
            formality: nil
        )
        #expect(corrections == [
            "aesthetic": .object([
                "secondary": .array([.string("classic"), .string("sporty")]),
            ]),
        ])
    }

    @Test func formalityChangeSendsLevelAndLabelUnderSnakeCaseKey() {
        let corrections = StyleDnaCorrectionsBuilder.build(
            original: originalDna,
            primary: "minimalist",
            secondary: originalDna.aesthetic.secondary,
            formality: .formal
        )
        #expect(corrections == [
            "formality_bias": .object([
                "level": .number(3),
                "label": .string("formal"),
            ]),
        ])
    }

    @Test func allFacetsChangedSendsBothSubtreesAndNoConfidences() {
        let corrections = StyleDnaCorrectionsBuilder.build(
            original: originalDna,
            primary: "classic",
            secondary: ["eclectic"],
            formality: .casual
        )
        #expect(corrections == [
            "aesthetic": .object([
                "primary": .string("classic"),
                "secondary": .array([.string("eclectic")]),
            ]),
            "formality_bias": .object([
                "level": .number(1),
                "label": .string("casual"),
            ]),
        ])
        // Confidence keys are never part of a correction — the server's
        // deep-merge keeps the stored ones.
        guard case let .object(aesthetic)? = corrections["aesthetic"] else {
            Issue.record("Expected aesthetic object")
            return
        }
        #expect(aesthetic["confidence"] == nil)
    }

    @Test func formalityChoiceMapsBackendLabels() {
        #expect(StyleDnaFormalityChoice(label: "casual") == .casual)
        #expect(StyleDnaFormalityChoice(label: "smart-casual") == .smartCasual)
        #expect(StyleDnaFormalityChoice(label: "formal") == .formal)
        // Outside the three-step vocabulary → no pre-selection.
        #expect(StyleDnaFormalityChoice(label: "business") == nil)
        #expect(StyleDnaFormalityChoice(label: "athletic") == nil)
    }

    @Test func formalityChoiceLevelsMatchBackendAnchors() {
        // Backend anchors (prompts.py): 0=athletic, 1=casual, 2=business,
        // 3=formal; scoring.py reads `level` as the numeric formality target,
        // so smart-casual must sit BETWEEN casual (1) and business (2) — not
        // on business's anchor.
        #expect(StyleDnaFormalityChoice.casual.level == 1)
        #expect(StyleDnaFormalityChoice.smartCasual.level == 1.5)
        #expect(StyleDnaFormalityChoice.formal.level == 3)
    }
}

// MARK: - applyCorrections

@Suite(.serialized)
@MainActor
struct StyleDnaApplyCorrectionsTests {
    private static let baseURL = URL(string: "http://localhost:8001/api/v1")!

    private static func makeViewModel() -> StyleDnaProfileViewModel {
        let client = APIClient(
            baseURL: baseURL,
            session: StyleDnaEditMockURLProtocol.makeSession(),
            authSession: nil
        )
        return StyleDnaProfileViewModel(
            repository: StyleDnaRepository(apiClient: client),
            initialState: .loaded(originalProfile)
        )
    }

    /// One captured request: everything the assertions need, taken inside the handler.
    private struct CapturedRequest: Sendable {
        var method: String?
        var path: String?
        var contentType: String?
        var body: Data?
    }

    /// Installs a handler that captures the request and answers with `status`/`body`.
    private static func capture(status: Int, body: Data) -> LockedBox<CapturedRequest?> {
        let captured = LockedBox<CapturedRequest?>(nil)
        StyleDnaEditMockURLProtocol.handler.withLock { handler in
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
        StyleDnaEditMockURLProtocol.handler.withLock { $0 = nil }
    }

    private static func loadedProfile(_ viewModel: StyleDnaProfileViewModel) -> StyleDnaProfileResponse? {
        if case .loaded(let profile) = viewModel.state { return profile }
        return nil
    }

    @Test func happyPathSendsPATCHAndReplacesStateWithServerEcho() async throws {
        defer { Self.resetHandler() }
        let captured = Self.capture(status: 200, body: correctedProfileJSON)
        let viewModel = Self.makeViewModel()

        await viewModel.applyCorrections([
            "aesthetic": .object(["primary": .string("streetwear")]),
            "formality_bias": .object(["level": .number(3), "label": .string("formal")]),
        ])

        let request = try #require(captured.withLock { $0 })
        #expect(request.method == "PATCH")
        #expect(request.path == "/api/v1/users/style-dna")
        #expect(request.contentType == "application/json")

        // Wire format: {"corrections": {...}} with verbatim snake_case keys.
        let bodyData = try #require(request.body)
        let payload = try JSONSerialization.jsonObject(with: bodyData) as? NSDictionary
        #expect(payload == [
            "corrections": [
                "aesthetic": ["primary": "streetwear"],
                "formality_bias": ["level": 3, "label": "formal"],
            ],
        ] as NSDictionary)

        // The server echo (merged profile) replaces local state.
        let profile = try #require(Self.loadedProfile(viewModel))
        #expect(profile.styleDna?.aesthetic.primary == "streetwear")
        #expect(profile.styleDna?.formalityBias.label == "formal")
        #expect(profile.styleDna?.formalityBias.level == 3.0)
        // Untouched facets keep their stored confidences.
        #expect(profile.styleDna?.aesthetic.confidence == 0.82)
        #expect(viewModel.saveError == nil)
        #expect(!viewModel.isSaving)
    }

    @Test func failureKeepsPriorStateAndSurfacesDetailAsSaveError() async throws {
        defer { Self.resetHandler() }
        _ = Self.capture(
            status: 404,
            body: Data(#"{"detail":"No Style DNA profile found. Upload photos first."}"#.utf8)
        )
        let viewModel = Self.makeViewModel()

        await viewModel.applyCorrections([
            "aesthetic": .object(["primary": .string("streetwear")]),
        ])

        // Prior state survives untouched; FastAPI's detail becomes the banner.
        let profile = try #require(Self.loadedProfile(viewModel))
        #expect(profile == originalProfile)
        #expect(viewModel.saveError == "No Style DNA profile found. Upload photos first.")
        #expect(!viewModel.isSaving)

        // The sheet clears the stale error on reappear.
        viewModel.clearSaveError()
        #expect(viewModel.saveError == nil)
    }

    @Test func networkFailureUsesFriendlyMessageAndKeepsState() async throws {
        defer { Self.resetHandler() }
        // No handler installed → URLProtocol fails the load (network-level error).
        let viewModel = Self.makeViewModel()

        await viewModel.applyCorrections([
            "aesthetic": .object(["primary": .string("streetwear")]),
        ])

        let profile = try #require(Self.loadedProfile(viewModel))
        #expect(profile == originalProfile)
        #expect(viewModel.saveError == "Can't reach ATTREQ. Check your connection.")
    }
}
