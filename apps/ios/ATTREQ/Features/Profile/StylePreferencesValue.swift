//
//  StylePreferencesValue.swift
//  ATTREQ
//
//  Interpretation of the backend `users.style_preferences` column (M5 review
//  fix). The column is DNA-OWNED: the Style DNA service stores
//  `json.dumps(style_dna)` in it and `GET /users/me` returns that blob
//  verbatim. Only legacy/registration writes leave a plain comma-separated
//  chip string there. The Profile UI must therefore treat a JSON value as
//  "no chip preferences set" — never display it, never prefill from it, and
//  never round-trip a chip string over it.
//

import Foundation

/// Classifies a raw `style_preferences` value from `GET /users/me` so the
/// Profile row and the edit sheet agree on what the column holds.
enum StylePreferencesValue: Equatable, Sendable {
    /// The column holds the Style DNA JSON blob (trimmed value starts with `{`).
    case dnaOwned
    /// A plain comma-separated chip/occasions string (trimmed).
    case plain(String)
    /// Nil or blank.
    case empty

    /// A value whose whitespace-trimmed form starts with `{` is the Style DNA
    /// JSON; anything else non-blank is a plain chip string.
    static func parse(_ raw: String?) -> StylePreferencesValue {
        let trimmed = (raw ?? "").trimmingCharacters(in: .whitespacesAndNewlines)
        if trimmed.isEmpty { return .empty }
        if trimmed.hasPrefix("{") { return .dnaOwned }
        return .plain(trimmed)
    }

    /// Row subtitle for the Profile preferences card — DNA JSON and blank
    /// values both read "Not set".
    var displayString: String {
        if case let .plain(value) = self { return value }
        return "Not set"
    }

    /// `", "`-separated parts for the editor prefill; empty unless `.plain`.
    var prefillParts: [String] {
        guard case let .plain(value) = self else { return [] }
        return value
            .components(separatedBy: ", ")
            .map { $0.trimmingCharacters(in: .whitespacesAndNewlines) }
            .filter { !$0.isEmpty }
    }

    var isDnaOwned: Bool { self == .dnaOwned }
}
