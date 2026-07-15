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

    /// Request payload. Designed for extension (multipart upload arrives in a later milestone).
    enum Body: Sendable {
        /// No body.
        case none
        /// JSON-encoded via `JSONEncoder` with `.convertToSnakeCase`.
        case json(any Encodable & Sendable)
        /// `application/x-www-form-urlencoded` (backend login uses OAuth2 password form).
        case form([String: String])
        /// Pre-encoded raw payload with an explicit content type (escape hatch / future multipart).
        case raw(data: Data, contentType: String)
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
