import Foundation

/// Mirrors backend `OutfitResponse` (`schemas/outfit.py`) / TS `Outfit`.
struct Outfit: Codable, Sendable, Equatable, Identifiable {
    let id: String
    let userId: String
    let topItemId: String?
    let bottomItemId: String?
    let accessoryIds: [String]?
    let occasionContext: String?
    /// RI-4 outfit slots (launch-M3 footwear/outerwear + the fullbody anchor).
    let footwearItemId: String?
    let outerwearItemId: String?
    let fullbodyItemId: String?
    /// Date-only string, e.g. `"2026-07-12"` (backend `date | None` — not a timestamp).
    let wornDate: String?
    /// -1 (dislike), 0 (neutral), 1 (like).
    let feedbackScore: Int?
    /// Arbitrary weather snapshot (backend `dict | None`). Dictionary keys keep
    /// their raw backend snake_case form (e.g. `"feels_like"`).
    let weatherContext: [String: JSONValue]?
    let createdAt: Date
    let updatedAt: Date
}

/// Mirrors backend `OutfitList` / TS `OutfitListResponse`.
struct OutfitListResponse: Codable, Sendable, Equatable {
    let items: [Outfit]
    let total: Int
    let page: Int
    let pageSize: Int
    let totalPages: Int
}
