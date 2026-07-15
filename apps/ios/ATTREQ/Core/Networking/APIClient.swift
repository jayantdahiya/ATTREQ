import Foundation

/// URLSession-based API client. Decodes snake_case JSON into camelCase models
/// (`.convertFromSnakeCase`), injects bearer tokens via `AuthSession`, and on a 401
/// performs a single-flight token refresh then retries the request exactly once.
final class APIClient: Sendable {
    private let baseURL: URL
    private let urlSession: URLSession
    private let authSession: AuthSession?

    /// - Parameters:
    ///   - baseURL: versioned API base, e.g. `http://localhost:8001/api/v1`.
    ///   - session: injectable for tests (mock `URLProtocol`).
    ///   - authSession: token provider; pass `nil` for a fully unauthenticated client.
    init(baseURL: URL, session: URLSession = .shared, authSession: AuthSession?) {
        self.baseURL = baseURL
        self.urlSession = session
        self.authSession = authSession
    }

    /// Performs the endpoint and decodes the response body into `T`.
    func request<T: Decodable & Sendable>(_ endpoint: Endpoint) async throws -> T {
        let (data, _) = try await perform(endpoint)
        do {
            return try Self.makeDecoder().decode(T.self, from: data)
        } catch {
            throw APIError.decoding(error)
        }
    }

    /// Performs the endpoint, ignoring the response body.
    func requestVoid(_ endpoint: Endpoint) async throws {
        _ = try await perform(endpoint)
    }

    // MARK: - Core

    private func perform(_ endpoint: Endpoint) async throws -> (Data, HTTPURLResponse) {
        var (data, response, sentToken) = try await send(endpoint)

        // 401 on an authenticated call: single-flight refresh, then retry exactly once.
        if response.statusCode == 401, endpoint.requiresAuth, let authSession {
            guard try await authSession.handleUnauthorized(failedToken: sentToken) else {
                throw APIError.unauthorized
            }
            (data, response, _) = try await send(endpoint)
        }

        guard (200 ..< 300).contains(response.statusCode) else {
            if response.statusCode == 401 {
                throw APIError.unauthorized
            }
            throw APIError.http(status: response.statusCode, body: data)
        }
        return (data, response)
    }

    /// Sends the request and returns the payload, response, and the bearer token used
    /// (so a 401 handler can tell whether the token has since been refreshed).
    private func send(_ endpoint: Endpoint) async throws -> (Data, HTTPURLResponse, String?) {
        var request = try makeURLRequest(for: endpoint)
        var sentToken: String?
        if endpoint.requiresAuth, let authSession {
            try await authSession.authorize(&request)
            if let header = request.value(forHTTPHeaderField: "Authorization"),
               header.hasPrefix("Bearer ") {
                sentToken = String(header.dropFirst("Bearer ".count))
            }
        }

        let data: Data
        let response: URLResponse
        do {
            (data, response) = try await urlSession.data(for: request)
        } catch {
            throw APIError.network(error)
        }
        guard let http = response as? HTTPURLResponse else {
            throw APIError.invalidResponse
        }
        return (data, http, sentToken)
    }

    // MARK: - Request building

    private func makeURLRequest(for endpoint: Endpoint) throws -> URLRequest {
        let path = endpoint.path.hasPrefix("/") ? String(endpoint.path.dropFirst()) : endpoint.path
        var url = baseURL.appending(path: path)
        if !endpoint.query.isEmpty {
            url.append(queryItems: endpoint.query)
        }

        var request = URLRequest(url: url)
        request.httpMethod = endpoint.method.rawValue
        request.timeoutInterval = 30
        request.setValue("application/json", forHTTPHeaderField: "Accept")

        switch endpoint.body {
        case .none:
            break
        case let .json(payload):
            request.setValue("application/json", forHTTPHeaderField: "Content-Type")
            do {
                request.httpBody = try Self.makeEncoder().encode(payload)
            } catch {
                throw APIError.decoding(error)
            }
        case let .form(fields):
            request.setValue("application/x-www-form-urlencoded", forHTTPHeaderField: "Content-Type")
            request.httpBody = Data(Self.formEncode(fields).utf8)
        case let .raw(data, contentType):
            request.setValue(contentType, forHTTPHeaderField: "Content-Type")
            request.httpBody = data
        }
        return request
    }

    private static func formEncode(_ fields: [String: String]) -> String {
        var allowed = CharacterSet.alphanumerics
        allowed.insert(charactersIn: "-._~")
        return fields
            .sorted { $0.key < $1.key }
            .map { key, value in
                let k = key.addingPercentEncoding(withAllowedCharacters: allowed) ?? key
                let v = value.addingPercentEncoding(withAllowedCharacters: allowed) ?? value
                return "\(k)=\(v)"
            }
            .joined(separator: "&")
    }

    // MARK: - Coding

    /// Decoder for backend JSON: snake_case keys → camelCase properties, ISO 8601 dates
    /// with fractional seconds (backend emits e.g. `2026-07-15T06:35:37.729782Z`).
    static func makeDecoder() -> JSONDecoder {
        let decoder = JSONDecoder()
        decoder.keyDecodingStrategy = .convertFromSnakeCase
        decoder.dateDecodingStrategy = .custom { decoder in
            let container = try decoder.singleValueContainer()
            let string = try container.decode(String.self)
            guard let date = parseISO8601(string) else {
                throw DecodingError.dataCorruptedError(
                    in: container,
                    debugDescription: "Unrecognized ISO 8601 date: \(string)"
                )
            }
            return date
        }
        return decoder
    }

    static func makeEncoder() -> JSONEncoder {
        let encoder = JSONEncoder()
        encoder.keyEncodingStrategy = .convertToSnakeCase
        encoder.dateEncodingStrategy = .iso8601
        return encoder
    }

    private static func parseISO8601(_ string: String) -> Date? {
        // Naive timestamps (no zone designator) are treated as UTC.
        let normalized: String
        if string.hasSuffix("Z") || string.contains("+") || string.dropFirst(10).contains("-") {
            normalized = string
        } else {
            normalized = string + "Z"
        }
        let fractional = Date.ISO8601FormatStyle(includingFractionalSeconds: true)
        let plain = Date.ISO8601FormatStyle()
        if let date = (try? fractional.parse(normalized)) ?? (try? plain.parse(normalized)) {
            return date
        }
        // Last resort: truncate sub-millisecond fractions (e.g. `.729782` → `.729`)
        // in case the parser rejects a fraction length it doesn't expect.
        if let dotIndex = normalized.firstIndex(of: ".") {
            let fractionStart = normalized.index(after: dotIndex)
            let fractionEnd = normalized[fractionStart...].firstIndex { !$0.isNumber } ?? normalized.endIndex
            let fraction = normalized[fractionStart ..< fractionEnd].prefix(3)
            let truncated = normalized[..<fractionStart] + fraction + normalized[fractionEnd...]
            return try? fractional.parse(String(truncated))
        }
        return nil
    }
}
