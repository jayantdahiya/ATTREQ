//
//  ProfileViewModel.swift
//  ATTREQ
//
//  Live identity-card stats for the Profile tab (M5-WP1, artboard 08):
//  Pieces / Worn / Streak. Identity (name, email, preferences) comes straight
//  from `AppSession.authState`; this model only owns the derived numbers.
//
//  Stat semantics:
//  - Pieces  = wardrobe `total` across all pages (server-side count; fetched
//              with page_size 1 so no item payload is transferred).
//  - Worn    = loaded outfits carrying a `worn_date`. Loaded means the first
//              page at page_size 100 (the backend max) — when `total_pages > 1`
//              (100+ tracked outfits) only that page is counted, an accepted
//              approximation to avoid paging the whole diary for one number.
//  - Streak  = consecutive LOCAL calendar days with >= 1 worn outfit, ending
//              today (today unworn -> 0). Derived from the same loaded page.
//

import Foundation
import Observation

/// Drives the `ProfileScreen` stats row. Owned by `MainTabsView` so the
/// numbers survive tab switches (same lifecycle as the other tab models).
@MainActor
@Observable
final class ProfileViewModel {
    enum LoadState: Equatable {
        case loading
        case loaded
        case failed(String)
    }

    /// The three identity-card numbers (see stat semantics in the header).
    struct Stats: Equatable, Sendable {
        var pieces: Int
        var worn: Int
        var streakDays: Int
    }

    // MARK: State (read by ProfileScreen)

    private(set) var state: LoadState = .loading
    private(set) var stats: Stats?
    /// Refresh failure over already-loaded stats, rendered as a banner
    /// (initial-load failures go through `state` instead).
    var errorMessage: String?

    @ObservationIgnored private var isFetching = false
    /// Set when an in-app action (wearing an outfit, uploading a wardrobe item)
    /// invalidates the stats; `load()` then refetches on next tab entry even
    /// though content is already present. Mirrors `HistoryViewModel`.
    @ObservationIgnored private var needsRefresh = false

    private let wardrobeRepository: WardrobeRepository
    private let outfitsRepository: OutfitsRepository

    init(wardrobeRepository: WardrobeRepository, outfitsRepository: OutfitsRepository) {
        self.wardrobeRepository = wardrobeRepository
        self.outfitsRepository = outfitsRepository
    }

    // MARK: Loading

    /// First load when the tab appears. Safe to call repeatedly (`.task`
    /// re-fires on tab switches) — fetches when nothing is loaded yet or when
    /// an in-app action marked the stats stale.
    func load() async {
        guard stats == nil || needsRefresh, !isFetching else { return }
        await fetch()
    }

    /// Invalidate cached stats so the next `load()` refetches. Called by
    /// `MainTabsView` after a wear/feedback or a wardrobe upload.
    func markStale() {
        needsRefresh = true
    }

    /// Pull-to-refresh / retry: always refetches.
    func refresh() async {
        guard !isFetching else { return }
        await fetch()
    }

    private func fetch() async {
        let hadContent = stats != nil
        if !hadContent {
            state = .loading
        }
        isFetching = true
        defer { isFetching = false }
        do {
            // Both stat sources load concurrently.
            async let wardrobePage = wardrobeRepository.list(page: 1, pageSize: 1)
            async let outfitsPage = outfitsRepository.list(page: 1, pageSize: 100)
            let (wardrobe, outfits) = try await (wardrobePage, outfitsPage)

            let wornDays = Set(outfits.items.compactMap(\.wornDate))
            stats = Stats(
                pieces: wardrobe.total,
                worn: outfits.items.filter { $0.wornDate != nil }.count,
                streakDays: Self.streak(wornDayKeys: wornDays)
            )
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

    // MARK: Streak

    /// Consecutive local calendar days with at least one worn outfit, ending
    /// today: walks backwards from today's local day while each day key
    /// (`"yyyy-MM-dd"`, the backend `worn_date` format) is present. A day
    /// without a wear — including today — ends the walk, so an unworn today
    /// yields 0.
    static func streak(
        wornDayKeys: Set<String>,
        timeZone: TimeZone = .current,
        now: Date = .now
    ) -> Int {
        var calendar = Calendar(identifier: .gregorian)
        calendar.timeZone = timeZone
        let formatter = DateFormatter()
        formatter.locale = Locale(identifier: "en_US_POSIX")
        formatter.timeZone = timeZone
        formatter.dateFormat = "yyyy-MM-dd"

        var day = calendar.startOfDay(for: now)
        var count = 0
        while wornDayKeys.contains(formatter.string(from: day)) {
            count += 1
            guard let previous = calendar.date(byAdding: .day, value: -1, to: day) else { break }
            day = previous
        }
        return count
    }

    // MARK: Errors

    /// Same cancellation policy as `HistoryViewModel` / `WardrobeViewModel`.
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
            return "Couldn't load your profile stats."
        default:
            return "Couldn't load your profile stats."
        }
    }
}
