import Foundation

/// Mirrors backend `OutfitItemDetail` (`schemas/recommendation.py`) / TS `OutfitItemDetail`.
struct OutfitItemDetail: Codable, Sendable, Equatable, Identifiable {
    let id: String
    let category: String?
    let colorPrimary: String?
    let pattern: String?
    let imageUrl: String?
    let thumbnailUrl: String?
}

/// Scoring breakdown for an outfit suggestion (all values 0–1).
///
/// TS declares `style_dna` and `behaviour` as required, but the backend response
/// schema `OutfitScores` (`schemas/recommendation.py`) only declares
/// `color_harmony`, `formality`, `preference_bonus`, `total` — Pydantic drops the
/// extra keys the algorithm computes, so they are optional here (backend wins).
struct OutfitScores: Codable, Sendable, Equatable {
    let colorHarmony: Double
    let formality: Double
    let preferenceBonus: Double
    let styleDna: Double?
    let behaviour: Double?
    let total: Double
}

/// Mirrors backend `OutfitSuggestion` / TS `OutfitSuggestion`.
///
/// `weather_context` is `dict[str, Any]` on the backend, but it is always the
/// same weather dict that validates as `WeatherData` for the response's top-level
/// `weather` field, so it is decoded as `WeatherData` (matching the TS types).
struct OutfitSuggestion: Codable, Sendable, Equatable {
    let topItemId: String
    let topItem: OutfitItemDetail
    let bottomItemId: String
    let bottomItem: OutfitItemDetail
    let accessoryItem: OutfitItemDetail?
    let scores: OutfitScores
    let weatherContext: WeatherData
    let occasionContext: String
}

/// Mirrors backend `DailySuggestionsResponse` / TS `DailySuggestionsResponse`.
///
/// Warning: the backend emits `generated_at` via `datetime.utcnow().isoformat()`
/// — a timezone-NAIVE ISO string (no `Z`/offset). The API client's date decoding
/// strategy must accept naive timestamps (assume UTC) or decoding this response
/// will fail.
struct DailySuggestionsResponse: Codable, Sendable, Equatable {
    let suggestions: [OutfitSuggestion]
    let totalSuggestions: Int
    let generatedAt: Date
    let weather: WeatherData
    let occasion: String
    let cached: Bool
}
