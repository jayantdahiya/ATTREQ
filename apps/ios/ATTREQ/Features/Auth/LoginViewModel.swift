//
//  LoginViewModel.swift
//  ATTREQ
//
//  State + submit logic for the login screen (artboard 01).
//

import Foundation
import Observation

@MainActor
@Observable
final class LoginViewModel {
    var email = ""
    var password = ""
    var isLoading = false
    var errorMessage: String?

    var canSubmit: Bool {
        !email.trimmingCharacters(in: .whitespaces).isEmpty && !password.isEmpty
    }

    /// Signs in via `AppSession`. On success the session's `authState` flips to
    /// `.authenticated`, which drives navigation away from this screen.
    func signIn(using session: AppSession) async {
        guard !isLoading else { return }
        errorMessage = nil
        isLoading = true
        defer { isLoading = false }
        do {
            try await session.login(
                email: email.trimmingCharacters(in: .whitespaces),
                password: password
            )
        } catch {
            errorMessage = AuthErrorMessage.describe(error)
        }
    }
}

// MARK: - User-facing error mapping

/// Maps thrown errors to short, human-readable copy for the inline
/// clay error labels on the auth screens. Shared by login + register.
enum AuthErrorMessage {
    static func describe(_ error: Error) -> String {
        switch error {
        case let apiError as APIError:
            describe(apiError)
        case let localized as LocalizedError:
            localized.errorDescription ?? fallback
        default:
            fallback
        }
    }

    private static func describe(_ error: APIError) -> String {
        switch error {
        case .unauthorized:
            return "Incorrect email or password."
        case let .http(status, body):
            if let detail = detail(from: body) { return detail }
            return status >= 500
                ? "Something went wrong on our end. Try again."
                : "That didn't work. Check your details and try again."
        case .network:
            return "Can't reach ATTREQ. Check your connection."
        case .invalidResponse, .decoding:
            return fallback
        }
    }

    /// Pulls FastAPI's `detail` out of an error body. Handles both the plain
    /// string shape `{"detail": "..."}` and the 422 validation-error array
    /// shape `{"detail": [{"loc": [...], "msg": "..."}, ...]}` (one message
    /// per line, with pydantic's "Value error, " prefix stripped).
    private static func detail(from body: Data) -> String? {
        guard
            let object = try? JSONSerialization.jsonObject(with: body) as? [String: Any],
            let detail = object["detail"]
        else { return nil }

        if let text = detail as? String {
            return text
        }
        if let items = detail as? [[String: Any]] {
            let prefix = "Value error, "
            let messages = items.compactMap { item -> String? in
                guard let message = item["msg"] as? String, !message.isEmpty else { return nil }
                return message.hasPrefix(prefix) ? String(message.dropFirst(prefix.count)) : message
            }
            return messages.isEmpty ? nil : messages.joined(separator: "\n")
        }
        return nil
    }

    private static let fallback = "Something went wrong. Try again."
}
