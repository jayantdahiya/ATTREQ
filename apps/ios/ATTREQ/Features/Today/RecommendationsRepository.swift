//
//  RecommendationsRepository.swift
//  ATTREQ
//
//  Recommendations API calls (M4, + RI-1 telemetry feedback). Backend contract:
//  apps/api/src/attreq_api/api/v1/endpoints/recommendations.py
//  - GET  /recommendations/daily?lat=&lon=&occasion=&force_refresh=
//  - POST /recommendations/{recommendation_id}/feedback
//
//  Location: `lat`/`lon` are OPTIONAL query params. When omitted, the backend
//  falls back to the user's saved profile location (`saved_latitude`/
//  `saved_longitude`) and answers 400 if neither is available. The RN
//  dashboard only sends lat/lon right after a fresh device-location grant
//  (before that it gates the query on a saved location existing); the steady
//  state is the saved-location path, which this repository mirrors — it never
//  sends lat/lon.
//
//  Caching: responses are cached server-side per user+day+occasion (24h Redis
//  TTL); `force_refresh=true` bypasses that cache and regenerates. Each cache
//  miss (including the very first daily generation) writes a `shown` telemetry
//  row per suggestion server-side, keyed by `recommendationId`; the feedback
//  endpoint below records what the user did with one of those rows.
//

import Foundation

/// Action a user can take on a shown outfit suggestion (RI-1). Mirrors backend
/// `RecommendationFeedbackAction` (`schemas/telemetry.py`).
enum RecommendationFeedbackAction: String, Codable, Sendable {
    case accepted
    case rejected
    case swapped
}

/// Fixed rejection-reason vocabulary (RI-1). Mirrors backend `RejectionReason`
/// (`schemas/telemetry.py`) — keep the raw values in sync with the backend enum.
enum RejectionReason: String, Codable, Sendable, CaseIterable, Hashable {
    case tooFormal = "too_formal"
    case tooCasual = "too_casual"
    case dontLikeCombo = "dont_like_combo"
    case weatherWrong = "weather_wrong"
    case woreRecently = "wore_recently"
    case dislikeItem = "dislike_item"
    case other

    /// Chip/label copy for `RejectionReasonSheet`. `.other` has no chip (see
    /// that file) — it is only ever sent implicitly when the user types a
    /// note without picking one of the six explicit reasons.
    var display: String {
        switch self {
        case .tooFormal: "Too formal"
        case .tooCasual: "Too casual"
        case .dontLikeCombo: "Don't like the combo"
        case .weatherWrong: "Wrong for the weather"
        case .woreRecently: "Wore this recently"
        case .dislikeItem: "Dislike an item"
        case .other: "Other"
        }
    }
}

/// Stateless facade over the recommendations endpoint. Mirrors RN
/// `apps/mobile/src/lib/api/recommendations.ts`.
final class RecommendationsRepository: Sendable {
    private let apiClient: APIClient

    init(apiClient: APIClient) {
        self.apiClient = apiClient
    }

    /// `GET /recommendations/daily` — today's weather-aware outfit suggestions.
    ///
    /// - Parameters:
    ///   - refresh: when true, sent as `force_refresh=true` to bypass the
    ///     server's daily cache. Omitted when false — RN never sends the
    ///     param at all (axios drops `undefined`), so neither do we.
    ///   - occasion: occasion type (`casual`, `formal`, `party`, `business`,
    ///     `athletic`). RN always sends `"casual"`; the backend defaults to
    ///     `"casual"` when omitted, so `nil` sends nothing.
    ///   - occasionHint: RI-5 morning-vibe hint (`sharp`/`relaxed`/`bold`) —
    ///     omitted (not `""`) when the user hasn't answered/skipped the
    ///     prompt yet, matching the backend's "unknown/absent -> no-op" contract.
    func daily(refresh: Bool = false, occasion: String? = nil, occasionHint: String? = nil) async throws -> DailySuggestionsResponse {
        var query: [URLQueryItem] = []
        if let occasion {
            query.append(URLQueryItem(name: "occasion", value: occasion))
        }
        if let occasionHint {
            query.append(URLQueryItem(name: "occasion_hint", value: occasionHint))
        }
        if refresh {
            query.append(URLQueryItem(name: "force_refresh", value: "true"))
        }
        return try await apiClient.request(
            Endpoint(method: .get, path: "recommendations/daily", query: query)
        )
    }

    /// `GET /recommendations/swipe-deck` (RI-5) — a fresh, uncached deck of
    /// outfits to rate. Never itself rate-limited; only ratings (via
    /// `submitFeedback` below) are capped server-side.
    func swipeDeck(occasion: String? = nil) async throws -> DailySuggestionsResponse {
        var query: [URLQueryItem] = []
        if let occasion {
            query.append(URLQueryItem(name: "occasion", value: occasion))
        }
        return try await apiClient.request(
            Endpoint(method: .get, path: "recommendations/swipe-deck", query: query)
        )
    }

    /// `GET /recommendations/swipe-deck/status` (RI-5) — today's rating
    /// count + cap, so the entry point can hide itself once exhausted.
    func swipeDeckStatus() async throws -> SwipeDeckStatus {
        try await apiClient.request(
            Endpoint(method: .get, path: "recommendations/swipe-deck/status")
        )
    }

    /// `POST /recommendations/{recommendationId}/feedback` — records
    /// accepted/rejected/swapped for one suggestion in a shown batch (RI-1).
    /// This is the recommendation-level telemetry signal that feeds the
    /// preference-pair pipeline; it is independent of (and in addition to)
    /// the existing outfit-level `POST /outfits/{id}/feedback` contract,
    /// which is unchanged.
    ///
    /// Uses `requestVoid` — the response body isn't needed at any call site,
    /// and `request<T>` can't infer `T` when its result would just be discarded.
    func submitFeedback(
        recommendationId: String,
        outfitIndex: Int,
        action: RecommendationFeedbackAction,
        rejectionReason: RejectionReason? = nil,
        rejectionNote: String? = nil
    ) async throws {
        try await apiClient.requestVoid(
            Endpoint(
                method: .post,
                path: "recommendations/\(recommendationId)/feedback",
                body: .json(
                    FeedbackBody(
                        outfitIndex: outfitIndex,
                        action: action,
                        rejectionReason: rejectionReason,
                        rejectionNote: rejectionNote
                    )
                )
            )
        )
    }

    /// Request body for the feedback endpoint (backend
    /// `RecommendationFeedbackRequest`). Encoded with `.convertToSnakeCase`
    /// (`outfit_index`, `rejection_reason`, `rejection_note`), mirroring
    /// `OutfitsRepository`'s private body-struct convention.
    private struct FeedbackBody: Codable, Sendable {
        var outfitIndex: Int
        var action: RecommendationFeedbackAction
        var rejectionReason: RejectionReason?
        var rejectionNote: String?
    }
}
