import Foundation

/// Mirrors TS `StyleDnaAesthetic`.
struct StyleDnaAesthetic: Codable, Sendable, Equatable {
    let primary: String
    let secondary: [String]
    let confidence: Double
}

/// Mirrors TS `StyleDnaColorPalette`.
struct StyleDnaColorPalette: Codable, Sendable, Equatable {
    let dominant: [String]
    let accent: [String]
    let avoids: [String]
    let confidence: Double
}

/// Mirrors TS `StyleDna.patterns`.
struct StyleDnaPatterns: Codable, Sendable, Equatable {
    let preferred: [String]
    let confidence: Double
}

/// Mirrors TS `StyleDna.silhouette`.
struct StyleDnaSilhouette: Codable, Sendable, Equatable {
    /// One of `slim-fitted|relaxed-fitted|oversized|structured|draped|tailored|mixed`.
    let preference: String
    let confidence: Double
}

/// Mirrors TS `StyleDna.formality_bias`.
struct StyleDnaFormalityBias: Codable, Sendable, Equatable {
    /// 0.0–3.0 weighted average (0 = athletic … 3 = formal).
    let level: Double
    /// One of `athletic|casual|smart-casual|business|formal`.
    let label: String
    let confidence: Double
}

/// Mirrors TS `StyleDna.occasions`.
struct StyleDnaOccasions: Codable, Sendable, Equatable {
    let primary: [String]
    let confidence: Double
}

/// Mirrors TS `StyleDna`. The backend types this as `dict[str, Any]`; the
/// concrete shape comes from the synthesis prompt in
/// `services/style_dna/prompts.py`, which matches the TS interface exactly.
struct StyleDna: Codable, Sendable, Equatable {
    let aesthetic: StyleDnaAesthetic
    let colorPalette: StyleDnaColorPalette
    let patterns: StyleDnaPatterns
    let silhouette: StyleDnaSilhouette
    let formalityBias: StyleDnaFormalityBias
    let occasions: StyleDnaOccasions
    /// Feedback-derived weights, e.g. `{"category_likes": {"top": 1.5}}`.
    /// Dictionary String keys keep their raw backend snake_case form —
    /// `.convertFromSnakeCase` does not rewrite dictionary keys on this runtime.
    let behaviourWeights: [String: [String: Double]]
}

/// Mirrors backend `StyleDnaPhotoResponse` (`schemas/style_dna.py`) / TS `StyleDnaPhoto`.
struct StyleDnaPhoto: Codable, Sendable, Equatable, Identifiable {
    let id: String
    let userId: String
    let filePath: String
    let fileUrl: String
    let qualityOk: Bool
    let qualityReason: String?
    /// Arbitrary per-photo extraction JSON (backend `dict[str, Any] | None`).
    /// Dictionary keys keep their raw backend snake_case form.
    let perPhotoExtraction: [String: JSONValue]?
    let createdAt: Date
}

/// Mirrors backend `StyleDnaUploadResponse` / TS `StyleDnaUploadResponse`.
struct StyleDnaUploadResponse: Codable, Sendable, Equatable {
    let photosProcessed: Int
    let photosSkipped: Int
    let wardrobeItemsSeeded: Int
    let styleDna: StyleDna?
    let photos: [StyleDnaPhoto]
}

/// Mirrors backend `StyleDnaProfileResponse` / TS `StyleDnaProfileResponse`.
struct StyleDnaProfileResponse: Codable, Sendable, Equatable {
    let styleDna: StyleDna?
    let photos: [StyleDnaPhoto]
}

/// Mirrors backend `StyleDnaCorrection` / TS `StyleDnaCorrection`.
///
/// TS types this as `Partial<StyleDna>`, which has no direct Swift analogue;
/// the backend accepts `dict[str, Any]`, so corrections are sent as arbitrary
/// JSON. Build keys in camelCase — the encoder's `.convertToSnakeCase` strategy
/// converts them to the snake_case keys the backend expects.
struct StyleDnaCorrection: Codable, Sendable, Equatable {
    var corrections: [String: JSONValue]
}
