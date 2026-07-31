//
//  OutfitsRepository.swift
//  ATTREQ
//
//  Outfits API calls (M4). Backend contract:
//  apps/api/src/attreq_api/api/v1/endpoints/outfits.py
//  - GET  /outfits?page=&page_size=   (page >= 1, page_size 1...100, default 50)
//  - POST /outfits                    body = OutfitCreate (schemas/outfit.py)
//  - POST /outfits/{id}/wear          {"worn_date": "YYYY-MM-DD"}
//  - POST /outfits/{id}/feedback      {"feedback_score": -1|0|1}
//
//  Note the create schema has NO `worn_date` / `weather_context` /
//  `feedback_score` fields — wearing and feedback are separate endpoints, and
//  `weather_context` is never sent by the client at all (RN included). The RN
//  "Wear this" flow is therefore two calls: POST /outfits, then
//  POST /outfits/{id}/wear with today's date.
//

import Foundation

/// Request body for `POST /outfits` (backend `OutfitCreate`). Encoded with
/// `.convertToSnakeCase` (`top_item_id`, `accessory_ids`, ...).
///
/// RI-4 adds `footwear_item_id`/`outerwear_item_id`/`fullbody_item_id` —
/// without sending these, an accepted footwear/outerwear/fullbody outfit
/// would silently drop those items server-side (see `endpoints/outfits.py
/// ::create_outfit`, which now validates + persists all three the same way
/// it already does for top/bottom).
struct OutfitCreateRequest: Codable, Sendable, Equatable {
    var topItemId: String?
    var bottomItemId: String?
    var accessoryIds: [String]?
    var occasionContext: String?
    var footwearItemId: String?
    var outerwearItemId: String?
    var fullbodyItemId: String?

    init(
        topItemId: String? = nil,
        bottomItemId: String? = nil,
        accessoryIds: [String]? = nil,
        occasionContext: String? = nil,
        footwearItemId: String? = nil,
        outerwearItemId: String? = nil,
        fullbodyItemId: String? = nil
    ) {
        self.topItemId = topItemId
        self.bottomItemId = bottomItemId
        self.accessoryIds = accessoryIds
        self.occasionContext = occasionContext
        self.footwearItemId = footwearItemId
        self.outerwearItemId = outerwearItemId
        self.fullbodyItemId = fullbodyItemId
    }

    /// RN `outfitsApi.createFromSuggestion` body shape: top/bottom ids,
    /// `accessory_ids` as `[accessory.id]` when present or `[]` (never
    /// omitted), and the suggestion's occasion. RI-4: also passes through
    /// whichever of footwear/outerwear/fullbody the suggestion carries.
    init(suggestion: OutfitSuggestion) {
        self.init(
            topItemId: suggestion.topItemId,
            bottomItemId: suggestion.bottomItemId,
            accessoryIds: suggestion.accessoryItem.map { [$0.id] } ?? [],
            occasionContext: suggestion.occasionContext,
            footwearItemId: suggestion.footwearItemId,
            outerwearItemId: suggestion.outerwearItemId,
            fullbodyItemId: suggestion.fullbodyItemId
        )
    }
}

/// Stateless facade over the outfit endpoints. Mirrors RN
/// `apps/mobile/src/lib/api/outfits.ts`.
final class OutfitsRepository: Sendable {
    private let apiClient: APIClient

    init(apiClient: APIClient) {
        self.apiClient = apiClient
    }

    /// `GET /outfits` — the user's outfit diary, paginated (RN always uses
    /// page_size 50).
    func list(page: Int = 1, pageSize: Int = 50) async throws -> OutfitListResponse {
        try await apiClient.request(
            Endpoint(
                method: .get,
                path: "outfits",
                query: [
                    URLQueryItem(name: "page", value: String(page)),
                    URLQueryItem(name: "page_size", value: String(pageSize)),
                ]
            )
        )
    }

    /// `POST /outfits` — persist an outfit (typically from a daily suggestion,
    /// see `OutfitCreateRequest.init(suggestion:)`).
    func create(_ body: OutfitCreateRequest) async throws -> Outfit {
        try await apiClient.request(
            Endpoint(method: .post, path: "outfits", body: .json(body))
        )
    }

    /// `POST /outfits/{id}/wear` — record the outfit as worn on `wornDate`
    /// (date-only string `"YYYY-MM-DD"`; RN sends
    /// `new Date().toISOString().slice(0, 10)`, i.e. today's UTC date).
    /// Also increments wear counts on the outfit's items server-side.
    func markWorn(outfitId: String, wornDate: String) async throws -> Outfit {
        try await apiClient.request(
            Endpoint(
                method: .post,
                path: "outfits/\(outfitId)/wear",
                body: .json(WearBody(wornDate: wornDate))
            )
        )
    }

    /// `POST /outfits/{id}/feedback` — like (1) / dislike (-1) / neutral (0).
    func submitFeedback(outfitId: String, score: Int) async throws -> Outfit {
        try await apiClient.request(
            Endpoint(
                method: .post,
                path: "outfits/\(outfitId)/feedback",
                body: .json(FeedbackBody(feedbackScore: score))
            )
        )
    }

    private struct WearBody: Codable, Sendable {
        var wornDate: String
    }

    private struct FeedbackBody: Codable, Sendable {
        var feedbackScore: Int
    }
}
