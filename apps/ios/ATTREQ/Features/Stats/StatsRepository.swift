//
//  StatsRepository.swift
//  ATTREQ
//
//  Wardrobe stats & forgotten-items API calls (RI-7). Backend contract:
//  apps/api/src/attreq_api/api/v1/endpoints/stats.py
//  - GET /stats/wardrobe?force_refresh=
//  - GET /stats/forgotten?force_refresh=&days_threshold=
//
//  Both responses are Redis-cached server-side (1h); `forceRefresh` bypasses
//  the cache and recomputes.
//

import Foundation

/// Stateless facade over the stats endpoints.
final class StatsRepository: Sendable {
    private let apiClient: APIClient

    init(apiClient: APIClient) {
        self.apiClient = apiClient
    }

    /// `GET /stats/wardrobe` — composition, closet value, cost-per-wear,
    /// most/least worn, never-worn %. Computed over active items only.
    func wardrobeStats(forceRefresh: Bool = false) async throws -> WardrobeStatsResponse {
        try await apiClient.request(
            Endpoint(
                method: .get,
                path: "stats/wardrobe",
                query: [URLQueryItem(name: "force_refresh", value: forceRefresh ? "true" : "false")]
            )
        )
    }

    /// `GET /stats/forgotten` — items unworn (or not worn in `daysThreshold`
    /// days), each with an optional "wear it with…" pairing suggestion.
    func forgottenItems(
        forceRefresh: Bool = false,
        daysThreshold: Int = 60
    ) async throws -> ForgottenItemsResponse {
        try await apiClient.request(
            Endpoint(
                method: .get,
                path: "stats/forgotten",
                query: [
                    URLQueryItem(name: "force_refresh", value: forceRefresh ? "true" : "false"),
                    URLQueryItem(name: "days_threshold", value: String(daysThreshold)),
                ]
            )
        )
    }
}
