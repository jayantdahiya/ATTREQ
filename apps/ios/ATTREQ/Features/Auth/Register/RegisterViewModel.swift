//
//  RegisterViewModel.swift
//  ATTREQ
//
//  State, validation, and submit logic for the 3-step registration wizard
//  (artboards 02–04). Owns the `RegistrationData` payload handed to
//  `AppSession.register(_:)`.
//

import Foundation
import Observation

// MARK: - Registration payload

/// Everything gathered by the wizard, handed to `AppSession.register(_:)`.
struct RegistrationData: Sendable {
    var email: String
    var fullName: String
    var password: String
    var styleKeywords: [String]
    var occasions: String
    var location: RegistrationLocation?
}

/// Location as provided in step 3 — device coordinates or a typed city.
enum RegistrationLocation: Sendable {
    case coordinates(latitude: Double, longitude: Double, city: String?)
    case city(String)
}

// MARK: - View model

@MainActor
@Observable
final class RegisterViewModel {
    /// The eight style keywords from artboard 03, in design order.
    static let styleOptions = [
        "Minimal", "Earthy", "Tailored", "Layered", "Casual", "Formal", "Streetwear", "Athleisure"
    ]

    // Step 1 — account
    var email = ""
    var fullName = ""
    var password = ""
    var confirmPassword = ""

    // Step 2 — style
    var selectedKeywords: [String] = []
    var occasions = ""

    // Step 3 — location
    var manualCity = ""
    private(set) var deviceLocation: (latitude: Double, longitude: Double, city: String?)?
    private(set) var isLocating = false
    var locationErrorMessage: String?

    // Submission
    private(set) var isLoading = false
    var errorMessage: String?

    private let locationProvider = LocationProvider()

    /// City resolved from the device, for display on the location row.
    var resolvedCity: String? {
        guard let deviceLocation else { return nil }
        return deviceLocation.city ?? "Location captured"
    }

    // MARK: Step 1 validation

    /// Validates the account step, storing user-facing copy in `errorMessage`.
    func validateAccount() -> Bool {
        errorMessage = nil
        let trimmedEmail = email.trimmingCharacters(in: .whitespaces)
        guard isValidEmail(trimmedEmail) else {
            errorMessage = "Enter a valid email address."
            return false
        }
        guard !fullName.trimmingCharacters(in: .whitespaces).isEmpty else {
            errorMessage = "Enter your full name."
            return false
        }
        // Mirrors the backend policy (`UserCreate.validate_password` in
        // apps/api/src/attreq_api/schemas/user.py): 8–72 chars with at least
        // one uppercase letter, one lowercase letter, and one digit.
        guard password.count >= 8 else {
            errorMessage = "Password must be at least 8 characters."
            return false
        }
        guard password.count <= 72 else {
            errorMessage = "Password must be 72 characters or fewer."
            return false
        }
        guard password.contains(where: \.isUppercase) else {
            errorMessage = "Password must contain at least one uppercase letter."
            return false
        }
        guard password.contains(where: \.isLowercase) else {
            errorMessage = "Password must contain at least one lowercase letter."
            return false
        }
        guard password.contains(where: \.isNumber) else {
            errorMessage = "Password must contain at least one digit."
            return false
        }
        guard password == confirmPassword else {
            errorMessage = "Passwords don't match."
            return false
        }
        return true
    }

    private func isValidEmail(_ value: String) -> Bool {
        // Pragmatic shape check (something@something.tld); the backend is the final judge.
        value.range(of: #"^[^@\s]+@[^@\s]+\.[^@\s]+$"#, options: .regularExpression) != nil
    }

    // MARK: Step 2

    func toggleKeyword(_ keyword: String) {
        if let index = selectedKeywords.firstIndex(of: keyword) {
            selectedKeywords.remove(at: index)
        } else {
            selectedKeywords.append(keyword)
        }
    }

    // MARK: Step 3

    /// Requests a single device location + reverse-geocoded city, surfacing
    /// failures inline on the location row.
    func requestDeviceLocation() async {
        guard !isLocating else { return }
        locationErrorMessage = nil
        isLocating = true
        defer { isLocating = false }
        do {
            deviceLocation = try await locationProvider.requestLocation()
        } catch {
            deviceLocation = nil
            locationErrorMessage = AuthErrorMessage.describe(error)
        }
    }

    // MARK: Submit

    /// Builds `RegistrationData` and registers via `AppSession`. On success the
    /// session's `authState` flips to `.authenticated`, which drives navigation.
    func submit(using session: AppSession) async {
        guard !isLoading else { return }
        errorMessage = nil
        isLoading = true
        defer { isLoading = false }
        do {
            try await session.register(registrationData())
        } catch {
            errorMessage = AuthErrorMessage.describe(error)
        }
    }

    private func registrationData() -> RegistrationData {
        RegistrationData(
            email: email.trimmingCharacters(in: .whitespaces),
            fullName: fullName.trimmingCharacters(in: .whitespaces),
            password: password,
            styleKeywords: selectedKeywords,
            occasions: occasions.trimmingCharacters(in: .whitespaces),
            location: registrationLocation()
        )
    }

    private func registrationLocation() -> RegistrationLocation? {
        let typedCity = manualCity.trimmingCharacters(in: .whitespaces)
        // A typed city is a deliberate override of the device lookup.
        if !typedCity.isEmpty { return .city(typedCity) }
        if let deviceLocation {
            return .coordinates(
                latitude: deviceLocation.latitude,
                longitude: deviceLocation.longitude,
                city: deviceLocation.city
            )
        }
        return nil
    }
}
