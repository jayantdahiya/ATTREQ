//
//  MultipartEncodingTests.swift
//  ATTREQTests
//
//  Byte-level checks of the multipart/form-data encoder plus an end-to-end
//  wardrobe upload through APIClient (mock URLProtocol), asserting the exact
//  wire format the backend expects (`POST /wardrobe/upload`, part name "file").
//

import Foundation
import Testing
@testable import ATTREQ

/// Dedicated mock transport for this suite — its own static handler, so tests
/// here can never race `MockURLProtocol` used by other (parallel) suites.
final class UploadMockURLProtocol: URLProtocol {
    typealias Handler = @Sendable (URLRequest) -> (status: Int, body: Data)

    static let handler = LockedBox<Handler?>(nil)

    static func makeSession() -> URLSession {
        let configuration = URLSessionConfiguration.ephemeral
        configuration.protocolClasses = [UploadMockURLProtocol.self]
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

/// Drains a request body that `URLProtocol` exposes as a stream (URLSession
/// converts `httpBody` to `httpBodyStream` before the protocol sees it).
private func bodyData(of request: URLRequest) -> Data {
    if let body = request.httpBody {
        return body
    }
    guard let stream = request.httpBodyStream else { return Data() }
    stream.open()
    defer { stream.close() }
    var data = Data()
    let bufferSize = 16 * 1024
    var buffer = [UInt8](repeating: 0, count: bufferSize)
    while stream.hasBytesAvailable {
        let read = stream.read(&buffer, maxLength: bufferSize)
        guard read > 0 else { break }
        data.append(buffer, count: read)
    }
    return data
}

// MARK: - Encoder unit tests

@Suite struct MultipartEncoderTests {
    @Test func encodesFilePartWithExactCRLFLayout() {
        let imageBytes = Data([0xFF, 0xD8, 0xFF, 0xE0, 0x00, 0x10]) // JPEG magic prefix
        let body = MultipartEncoding.encode(
            [MultipartField(name: "file", filename: "photo.jpg", contentType: "image/jpeg", data: imageBytes)],
            boundary: "TESTBOUNDARY"
        )

        var expected = Data(
            (
                "--TESTBOUNDARY\r\n"
                    + "Content-Disposition: form-data; name=\"file\"; filename=\"photo.jpg\"\r\n"
                    + "Content-Type: image/jpeg\r\n"
                    + "\r\n"
            ).utf8
        )
        expected.append(imageBytes)
        expected.append(Data("\r\n--TESTBOUNDARY--\r\n".utf8))

        #expect(body == expected)
    }

    @Test func encodesPlainValueAndFilePartsInOrder() throws {
        let body = MultipartEncoding.encode(
            [
                MultipartField(name: "note", data: Data("hello".utf8)),
                MultipartField(name: "file", filename: "a.png", contentType: "image/png", data: Data([0x89, 0x50])),
            ],
            boundary: "B"
        )
        let text = String(decoding: body, as: UTF8.self)

        // Plain part: no filename, no Content-Type header.
        #expect(text.contains("--B\r\nContent-Disposition: form-data; name=\"note\"\r\n\r\nhello\r\n"))
        // File part follows, then the closing delimiter.
        #expect(text.contains("Content-Disposition: form-data; name=\"file\"; filename=\"a.png\"\r\nContent-Type: image/png\r\n\r\n"))
        #expect(text.hasSuffix("--B--\r\n"))
        let notePosition = try #require(text.range(of: "name=\"note\"")).lowerBound
        let filePosition = try #require(text.range(of: "name=\"file\"")).lowerBound
        #expect(notePosition < filePosition)
    }

    @Test func escapesQuotesAndNewlinesInFilename() {
        let body = MultipartEncoding.encode(
            [MultipartField(name: "file", filename: "we\"ird\r\n.jpg", data: Data())],
            boundary: "B"
        )
        let text = String(decoding: body, as: UTF8.self)
        #expect(text.contains("filename=\"we%22ird%0D%0A.jpg\""))
    }

    @Test func randomBoundaryIsUniqueAndHeaderSafe() {
        let first = MultipartEncoding.randomBoundary()
        let second = MultipartEncoding.randomBoundary()
        #expect(first != second)
        // RFC 2046 bchars subset that never needs quoting: alphanumerics + ".".
        let allowed = CharacterSet.alphanumerics.union(CharacterSet(charactersIn: "."))
        #expect(first.unicodeScalars.allSatisfy { allowed.contains($0) })
        #expect(first.count <= 70) // RFC 2046 boundary length limit
        #expect(MultipartEncoding.contentType(boundary: first) == "multipart/form-data; boundary=\(first)")
    }
}

// MARK: - End-to-end upload through APIClient

@Suite(.serialized) struct WardrobeUploadRequestTests {
    private static let baseURL = URL(string: "http://localhost:8001/api/v1")!

    private static func makeRepository() -> WardrobeRepository {
        let client = APIClient(
            baseURL: baseURL,
            session: UploadMockURLProtocol.makeSession(),
            authSession: nil
        )
        return WardrobeRepository(apiClient: client)
    }

    @Test func uploadSendsBackendExactMultipartRequest() async throws {
        let imageBytes = Data((0 ..< 512).map { UInt8($0 % 251) })
        let captured = LockedBox<(contentType: String?, path: String?, method: String?, body: Data)?>(nil)

        UploadMockURLProtocol.handler.withLock { handler in
            handler = { request in
                captured.withLock {
                    $0 = (
                        request.value(forHTTPHeaderField: "Content-Type"),
                        request.url?.path(),
                        request.httpMethod,
                        bodyData(of: request)
                    )
                }
                let json = """
                {"id":"11111111-2222-3333-4444-555555555555","status":"processing",\
                "message":"Image uploaded successfully. AI processing started.",\
                "original_image_url":"/uploads/originals/x.jpg"}
                """
                return (201, Data(json.utf8))
            }
        }
        defer { UploadMockURLProtocol.handler.withLock { $0 = nil } }

        let response = try await Self.makeRepository().upload(imageData: imageBytes)

        // Response decodes into the shared model.
        #expect(response.id == "11111111-2222-3333-4444-555555555555")
        #expect(response.status == "processing")
        #expect(response.originalImageUrl == "/uploads/originals/x.jpg")

        let request = try #require(captured.withLock { $0 })
        #expect(request.method == "POST")
        #expect(request.path == "/api/v1/wardrobe/upload")

        // Content-Type declares multipart with the same boundary used in the body.
        let contentType = try #require(request.contentType)
        #expect(contentType.hasPrefix("multipart/form-data; boundary="))
        let boundary = String(contentType.dropFirst("multipart/form-data; boundary=".count))
        #expect(!boundary.isEmpty)

        // Body is the exact serialization: backend field name "file",
        // default filename photo.jpg, JPEG content type, raw image bytes.
        var expected = Data(
            (
                "--\(boundary)\r\n"
                    + "Content-Disposition: form-data; name=\"file\"; filename=\"photo.jpg\"\r\n"
                    + "Content-Type: image/jpeg\r\n"
                    + "\r\n"
            ).utf8
        )
        expected.append(imageBytes)
        expected.append(Data("\r\n--\(boundary)--\r\n".utf8))
        #expect(request.body == expected)
    }

    @Test func uploadDerivesPNGContentTypeFromFilename() async throws {
        let captured = LockedBox<Data?>(nil)
        UploadMockURLProtocol.handler.withLock { handler in
            handler = { request in
                captured.withLock { $0 = bodyData(of: request) }
                let json = """
                {"id":"1","status":"processing","message":"ok","original_image_url":"/uploads/originals/y.png"}
                """
                return (201, Data(json.utf8))
            }
        }
        defer { UploadMockURLProtocol.handler.withLock { $0 = nil } }

        _ = try await Self.makeRepository().upload(imageData: Data([0x89]), filename: "closet.PNG")

        let body = try #require(captured.withLock { $0 })
        let text = String(decoding: body, as: UTF8.self)
        #expect(text.contains("filename=\"closet.PNG\""))
        #expect(text.contains("Content-Type: image/png\r\n"))
    }
}
