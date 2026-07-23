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
///
/// RI-4 adds `base_compatibility`/`cold_start_bonus`/`rediscovery_bonus`/
/// `rotation_penalty` server-side, all with `= 0.0` defaults — same "backend
/// wins, optional here" treatment as `style_dna`/`behaviour` above; nothing in
/// the client currently reads them.
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
///
/// RI-4: `topItemId`/`topItem`/`bottomItemId`/`bottomItem` are optional — a
/// fullbody-anchored outfit (`fullbodyItemId` set) has neither. The new
/// `explanation`/`confidence`/`rediscovery`/`rediscoveryItemId` fields are
/// optional here for the same "backend wins" reason `styleDna`/`behaviour`
/// are above: the backend defaults them (never required), so older or
/// hand-authored fixture JSON that omits them must still decode cleanly.
struct OutfitSuggestion: Codable, Sendable, Equatable {
    let topItemId: String?
    let topItem: OutfitItemDetail?
    let bottomItemId: String?
    let bottomItem: OutfitItemDetail?
    /// RI-4: fullbody anchor slot — consumes both top and bottom; never
    /// coexists with `bottomItem`.
    let fullbodyItemId: String?
    let fullbodyItem: OutfitItemDetail?
    let footwearItemId: String?
    let footwearItem: OutfitItemDetail?
    let outerwearItemId: String?
    let outerwearItem: OutfitItemDetail?
    let accessoryItem: OutfitItemDetail?
    let scores: OutfitScores
    let weatherContext: WeatherData
    let occasionContext: String
    /// 0-based position within the shown batch (RI-1). Stamped by the backend
    /// endpoint at generation time — the value `RecommendationsRepository
    /// .submitFeedback` must send back for this suggestion to be addressable.
    let outfitIndex: Int
    /// RI-4: template-composed, one-line reason for this pick. `nil` only for
    /// fixture JSON predating RI-4 — real responses always populate it (the
    /// backend default is `""`, not omission).
    let explanation: String?
    /// RI-4: "low" hedges the explanation copy when `base_compatibility` is
    /// weak (sparse wardrobe, forced picks) — render with a distinct,
    /// non-error "Experimental" treatment rather than suppressing the pick.
    let confidence: String?
    /// RI-4: at most one `true` per shown batch — a grey-inventory
    /// (neglected-item) pick, paired with `rediscoveryItemId`.
    let rediscovery: Bool?
    let rediscoveryItemId: String?

    /// Convenience: whichever anchor item this suggestion is centered on —
    /// the fullbody item when present, else the top item. Used by the
    /// collage view to render a single-tile fullbody layout gracefully.
    var primaryItem: OutfitItemDetail? { fullbodyItem ?? topItem }

    var isLowConfidence: Bool { confidence == "low" }
    var isRediscovery: Bool { rediscovery == true }
}

/// Mirrors backend `DailySuggestionsResponse` / TS `DailySuggestionsResponse`.
///
/// Warning: the backend emits `generated_at` via `datetime.utcnow().isoformat()`
/// — a timezone-NAIVE ISO string (no `Z`/offset). The API client's date decoding
/// strategy must accept naive timestamps (assume UTC) or decoding this response
/// will fail.
struct DailySuggestionsResponse: Codable, Sendable, Equatable {
    /// Groups this generation batch (RI-1) — every suggestion's `outfitIndex` is
    /// addressed against this id via `POST /recommendations/{id}/feedback`.
    let recommendationId: String
    let suggestions: [OutfitSuggestion]
    let totalSuggestions: Int
    let generatedAt: Date
    let weather: WeatherData
    let occasion: String
    let cached: Bool
}

/// Mirrors backend `SwipeDeckStatusResponse` (RI-5, `GET
/// /recommendations/swipe-deck/status`) — today's rating count + the daily
/// cap, so the client can show/hide the swipe-deck entry point without
/// inferring state from a 429 on the feedback endpoint.
struct SwipeDeckStatus: Codable, Sendable, Equatable {
    let ratingsToday: Int
    let cap: Int

    var hasRatingsRemaining: Bool { ratingsToday < cap }
}
