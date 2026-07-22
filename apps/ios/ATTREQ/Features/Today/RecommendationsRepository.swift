//
//  RecommendationsRepository.swift
//  ATTREQ
//
//  Recommendations API calls (M4). Backend contract:
//  apps/api/src/attreq_api/api/v1/endpoints/recommendations.py
//  - GET /recommendations/daily?lat=&lon=&occasion=&force_refresh=
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
//  TTL); `force_refresh=true` bypasses that cache and regenerates.
//

import Foundation

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
    func daily(refresh: Bool = false, occasion: String? = nil) async throws -> DailySuggestionsResponse {
        var query: [URLQueryItem] = []
        if let occasion {
            query.append(URLQueryItem(name: "occasion", value: occasion))
        }
        if refresh {
            query.append(URLQueryItem(name: "force_refresh", value: "true"))
        }
        return try await apiClient.request(
            Endpoint(method: .get, path: "recommendations/daily", query: query)
        )
    }
}
