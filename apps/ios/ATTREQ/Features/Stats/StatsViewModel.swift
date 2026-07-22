//
//  StatsViewModel.swift
//  ATTREQ
//
//  Observable state for the Stats tab (RI-7): wardrobe composition, closet
//  value, cost-per-wear, most/least worn, and the forgotten-items surface.
//  Loads both `GET /stats/wardrobe` and `GET /stats/forgotten` concurrently,
//  same pattern as `ProfileViewModel` loading wardrobe + outfits together.
//

import Foundation
import Observation

/// Drives `StatsScreen`. Owned by `MainTabsView` so state survives tab switches
/// (same lifecycle as the other tab models).
@MainActor
@Observable
final class StatsViewModel {
    enum LoadState: Equatable {
        case loading
        case loaded
        case failed(String)
    }

    // MARK: State (read by StatsScreen)

    private(set) var state: LoadState = .loading
    private(set) var wardrobeStats: WardrobeStatsResponse?
    private(set) var forgottenItems: ForgottenItemsResponse?
    /// Refresh failure over already-loaded stats, rendered as a banner
    /// (initial-load failures go through `state` instead).
    var errorMessage: String?

    @ObservationIgnored private var isFetching = false
    /// Set when an in-app action (archiving an item) invalidates these stats;
    /// `load()` then refetches on next tab entry even though content is
    /// already present. Mirrors `ProfileViewModel.needsRefresh`.
    @ObservationIgnored private var needsRefresh = false

    private let repository: StatsRepository

    init(repository: StatsRepository) {
        self.repository = repository
    }

    private var hasContent: Bool {
        wardrobeStats != nil || forgottenItems != nil
    }

    // MARK: Loading

    /// First load when the tab appears. Safe to call repeatedly (`.task`
    /// re-fires on tab switches) — fetches when nothing is loaded yet or when
    /// an in-app action marked the stats stale.
    func load() async {
        guard !hasContent || needsRefresh, !isFetching else { return }
        await fetch(forceRefresh: false)
    }

    /// Invalidate cached stats so the next `load()` refetches (e.g. after
    /// archiving/unarchiving a wardrobe item).
    func markStale() {
        needsRefresh = true
    }

    /// Pull-to-refresh / retry: always refetches, bypassing the server cache
    /// (`force_refresh=true`) so a just-archived item's numbers update immediately.
    func refresh() async {
        guard !isFetching else { return }
        await fetch(forceRefresh: true)
    }

    private func fetch(forceRefresh: Bool) async {
        let hadContent = hasContent
        if !hadContent {
            state = .loading
        }
        isFetching = true
        defer { isFetching = false }
        do {
            async let wardrobe = repository.wardrobeStats(forceRefresh: forceRefresh)
            async let forgotten = repository.forgottenItems(forceRefresh: forceRefresh)
            let (wardrobeResult, forgottenResult) = try await (wardrobe, forgotten)
            wardrobeStats = wardrobeResult
            forgottenItems = forgottenResult
            errorMessage = nil
            needsRefresh = false
            state = .loaded
        } catch {
            guard !Self.isCancellation(error) else { return }
            let message = Self.message(for: error)
            if hadContent {
                errorMessage = message
            } else {
                state = .failed(message)
            }
        }
    }

    // MARK: Errors

    private static func isCancellation(_ error: any Error) -> Bool {
        if error is CancellationError { return true }
        if (error as? URLError)?.code == .cancelled { return true }
        if case let APIError.network(underlying) = error {
            return isCancellation(underlying)
        }
        return false
    }

    private static func message(for error: any Error) -> String {
        switch error {
        case APIError.network:
            return "Can't reach ATTREQ. Check your connection."
        case let APIError.http(_, body):
            if let object = try? JSONSerialization.jsonObject(with: body) as? [String: Any],
               let detail = object["detail"] as? String,
               !detail.isEmpty {
                return detail
            }
            return "Couldn't load your wardrobe stats."
        default:
            return "Couldn't load your wardrobe stats."
        }
    }
}
