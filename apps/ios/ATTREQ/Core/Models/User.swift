import Foundation

/// Mirrors backend `UserResponse` (`schemas/user.py`) / TS `User`.
///
/// Returned by `POST /auth/register`, `GET /users/me`, `PUT /users/me`,
/// `PATCH /users/me/location`, `POST /users/onboarding/complete`, and nested
/// inside the login response.
struct User: Codable, Sendable, Equatable, Identifiable {
    let id: String
    let email: String
    let fullName: String?
    let location: String?
    let savedLatitude: Double?
    let savedLongitude: Double?
    let savedCity: String?
    let isActive: Bool
    let isVerified: Bool
    let createdAt: Date
    let updatedAt: Date
    let lastLogin: Date?
    let oauthProvider: String?
    let stylePreferences: String?
    let onboardingCompleted: Bool
    let onboardingStep: String?
}

/// Request body for `PUT /users/me` (backend `UserUpdate`).
///
/// Note: the backend `UserUpdate` schema has NO `style_preferences` field —
/// extra keys are silently ignored by Pydantic.
struct UserUpdateRequest: Codable, Sendable, Equatable {
    var fullName: String?
    var location: String?
    var savedLatitude: Double?
    var savedLongitude: Double?
    var savedCity: String?
    var isActive: Bool?
}

/// Request body for `PATCH /users/me/location` (backend `LocationUpdate`).
struct LocationUpdateRequest: Codable, Sendable, Equatable {
    var lat: Double
    var lon: Double
    var city: String?
}
