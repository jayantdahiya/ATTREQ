import Foundation

/// Declarative description of a single API call, relative to the versioned base URL
/// (e.g. `http://localhost:8001/api/v1`).
struct Endpoint: Sendable {
    enum Method: String, Sendable {
        case get = "GET"
        case post = "POST"
        case put = "PUT"
        case patch = "PATCH"
        case delete = "DELETE"
    }

    /// Request payload.
    enum Body: Sendable {
        /// No body.
        case none
        /// JSON-encoded via `JSONEncoder` with `.convertToSnakeCase`.
        case json(any Encodable & Sendable)
        /// `application/x-www-form-urlencoded` (backend login uses OAuth2 password form).
        case form([String: String])
        /// Pre-encoded raw payload with an explicit content type (escape hatch).
        case raw(data: Data, contentType: String)
        /// `multipart/form-data` (wardrobe photo upload). `APIClient` encodes the
        /// parts with a random boundary per request.
        case multipart([MultipartField])
    }

    var method: Method
    /// Path relative to `/api/v1`, e.g. `"auth/login"` or `"/users/me"` (leading slash tolerated).
    var path: String
    var query: [URLQueryItem]
    var body: Body
    /// When `true`, `APIClient` injects `Authorization: Bearer` and performs the 401→refresh→retry dance.
    var requiresAuth: Bool

    init(
        method: Method,
        path: String,
        query: [URLQueryItem] = [],
        body: Body = .none,
        requiresAuth: Bool = true
    ) {
        self.method = method
        self.path = path
        self.query = query
        self.body = body
        self.requiresAuth = requiresAuth
    }
}

/// One part of a `multipart/form-data` request body: a plain form value, or a
/// file part when `filename` (and typically `contentType`) is set.
struct MultipartField: Sendable {
    var name: String
    var filename: String? = nil
    var contentType: String? = nil
    var data: Data
}

/// Encodes `[MultipartField]` into a CRLF-correct `multipart/form-data` body
/// (RFC 7578). Kept separate from `APIClient` so unit tests can exercise the
/// exact byte layout with a fixed boundary.
enum MultipartEncoding {
    /// Random per-request boundary. Alphanumerics only, so it never needs
    /// quoting in the `Content-Type` header and cannot collide with CRLF.
    static func randomBoundary() -> String {
        "attreq.\(UUID().uuidString.replacingOccurrences(of: "-", with: ""))"
    }

    /// `Content-Type` header value for a body encoded with `boundary`.
    static func contentType(boundary: String) -> String {
        "multipart/form-data; boundary=\(boundary)"
    }

    /// Serializes the fields:
    /// ```
    /// --boundary\r\n
    /// Content-Disposition: form-data; name="…"[; filename="…"]\r\n
    /// [Content-Type: …\r\n]
    /// \r\n
    /// <data>\r\n
    /// …
    /// --boundary--\r\n
    /// ```
    static func encode(_ fields: [MultipartField], boundary: String) -> Data {
        let crlf = "\r\n"
        var body = Data()
        for field in fields {
            body.append(Data("--\(boundary)\(crlf)".utf8))
            var disposition = "Content-Disposition: form-data; name=\"\(escape(field.name))\""
            if let filename = field.filename {
                disposition += "; filename=\"\(escape(filename))\""
            }
            body.append(Data("\(disposition)\(crlf)".utf8))
            if let contentType = field.contentType {
                body.append(Data("Content-Type: \(contentType)\(crlf)".utf8))
            }
            body.append(Data(crlf.utf8))
            body.append(field.data)
            body.append(Data(crlf.utf8))
        }
        body.append(Data("--\(boundary)--\(crlf)".utf8))
        return body
    }

    /// Quoted-string escaping for name/filename parameters (WHATWG
    /// multipart/form-data serialization: percent-encode `"`, CR, LF).
    private static func escape(_ value: String) -> String {
        value
            .replacingOccurrences(of: "\r", with: "%0D")
            .replacingOccurrences(of: "\n", with: "%0A")
            .replacingOccurrences(of: "\"", with: "%22")
    }
}
