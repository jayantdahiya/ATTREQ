import Foundation

/// Errors surfaced by `APIClient` and `AuthSession`.
enum APIError: Error {
    /// The response was not an `HTTPURLResponse`.
    case invalidResponse
    /// A non-2xx (and non-401-recoverable) HTTP status; raw body retained for callers.
    case http(status: Int, body: Data)
    /// The response body could not be decoded into the requested type.
    case decoding(Error)
    /// 401 that could not be recovered by a token refresh.
    case unauthorized
    /// Transport-level failure (no HTTP response received).
    case network(Error)
}

extension APIError: CustomStringConvertible {
    var description: String {
        switch self {
        case .invalidResponse:
            return "Invalid (non-HTTP) response"
        case let .http(status, body):
            let text = String(data: body, encoding: .utf8) ?? "<\(body.count) bytes>"
            return "HTTP \(status): \(text)"
        case let .decoding(error):
            return "Decoding failed: \(error)"
        case .unauthorized:
            return "Unauthorized"
        case let .network(error):
            return "Network error: \(error.localizedDescription)"
        }
    }
}
