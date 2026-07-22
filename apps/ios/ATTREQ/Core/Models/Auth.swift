import Foundation

/// Request body for `POST /auth/register` (backend `UserCreate`).
///
/// The backend responds with a `User` only — no tokens. The client must follow
/// up with `POST /auth/login` (mirrors the RN client behavior).
struct RegisterRequest: Codable, Sendable, Equatable {
    var email: String
    var password: String
    var fullName: String?
}

/// Credentials for `POST /auth/login`.
///
/// Note: the login endpoint consumes an OAuth2 password form
/// (`application/x-www-form-urlencoded` with fields `username` and `password`,
/// where `username` carries the email) — it is NOT a JSON body. `Codable`
/// conformance is provided for consistency, but the networking layer must
/// form-encode this request.
struct LoginRequest: Codable, Sendable, Equatable {
    var email: String
    var password: String
}

/// Mirrors backend `LoginResponse` (`schemas/token.py`) / TS `AuthResponse`.
struct AuthResponse: Codable, Sendable, Equatable {
    let accessToken: String
    let refreshToken: String
    let tokenType: String
    let user: User
}

/// Request body for `POST /auth/refresh` (backend `TokenRefresh`).
struct TokenRefreshRequest: Codable, Sendable, Equatable {
    var refreshToken: String
}

/// Mirrors backend `TokenRefreshResponse`: a new access token only —
/// the refresh token is NOT rotated and no user payload is returned.
struct TokenRefreshResponse: Codable, Sendable, Equatable {
    let accessToken: String
    let tokenType: String
}

/// Generic `{"message": "..."}` payload (e.g. `POST /auth/logout`).
struct MessageResponse: Codable, Sendable, Equatable {
    let message: String
}
