//
//  HistoryViewModel.swift
//  ATTREQ
//
//  Observable state for the History / Diary tab (M4, artboard 07): the
//  outfit list grouped by day with status pills.
//
//  RN semantics mirrored (history-screen.tsx `HistoryLookCard`):
//  - Group key = `worn_date ?? created_at day` — worn_date verbatim, the
//    created_at fallback in the user's LOCAL calendar day (deliberate
//    divergence from RN's UTC `.slice(0, 10)`; see `dayKey`), groups sorted
//    newest-day first, entries in server order within a group.
//  - Pill precedence: feedback BEATS worn — feedback_score 1 → "Loved"
//    (gold), -1 → "Skipped" (clay), else worn_date set → "Worn" (moss),
//    else "Tracked" (muted). (The milestone doc lists worn first; RN checks
//    feedback first, and RN wins.)
//  - Pagination mirrors WardrobeViewModel: page_size 50, prefetch when a
//    card near the end appears.
//

import Foundation
import Observation

/// One diary entry: the outfit plus precomputed display bits.
struct HistoryEntry: Identifiable, Equatable, Sendable {
    /// Status pill, precedence per RN `HistoryLookCard` (feedback beats worn).
    enum Pill: Equatable, Sendable {
        case loved
        case skipped
        case worn
        case tracked

        var label: String {
            switch self {
            case .loved: "Loved"
            case .skipped: "Skipped"
            case .worn: "Worn"
            case .tracked: "Tracked"
            }
        }

        /// Design-system tone (RN `StatusPill` variants): Loved gold,
        /// Skipped clay, Worn moss, Tracked muted.
        var variant: PillVariant {
            switch self {
            case .loved: .gold
            case .skipped: .clay
            case .worn: .moss
            case .tracked: .muted
            }
        }
    }

    let outfit: Outfit
    /// Presentational italic title — same curated generator as the Today tab
    /// (`LookTitles`), keyed by the outfit's occasion + position in its group.
    /// RN shows the raw occasion; the design shows editorial names.
    let title: String
    /// "N pieces" — count of non-nil item ids (top + bottom + accessories).
    let piecesCount: Int
    let pill: Pill

    var id: String { outfit.id }
}

/// One date section of the diary.
struct HistoryGroup: Identifiable, Equatable, Sendable {
    /// Heading, e.g. `"Monday 06/23"` (RN Intl en: long weekday + 2-digit
    /// month/day).
    let dateLabel: String
    /// ISO day key / right-hand mono label, e.g. `"2026-06-23"`.
    let isoLabel: String
    let entries: [HistoryEntry]

    var id: String { isoLabel }
}

/// Drives `HistoryScreen`. Owned by `MainTabsView` so state survives tab switches.
@MainActor
@Observable
final class HistoryViewModel {
    enum LoadState: Equatable {
        case loading
        case loaded
        case failed(String)
        case empty
    }

    // MARK: State (read by HistoryScreen)

    private(set) var state: LoadState = .loading
    /// Date sections, newest day first.
    private(set) var groups: [HistoryGroup] = []
    /// Server-side total across all pages (the "N looks tracked" line).
    private(set) var totalTracked = 0
    /// Last load failure over existing content, rendered as a banner.
    var errorMessage: String?

    // MARK: Pagination internals

    /// Flat outfit list in server order (groups are derived from it).
    @ObservationIgnored private var items: [Outfit] = []
    @ObservationIgnored private var currentPage = 1
    @ObservationIgnored private var totalPages = 1
    @ObservationIgnored private var isLoadingMore = false
    @ObservationIgnored private var isFetching = false
    /// Set by `markStale()` (Today recorded a wear/feedback) so the next
    /// `load()` refetches even though content is already loaded.
    @ObservationIgnored private var needsRefresh = false
    /// Bumped by every `fetch()` (load/refresh). `loadMoreIfNeeded` re-checks
    /// it after its await so a next-page response that raced a refresh is
    /// discarded instead of appending onto the fresh page 1.
    @ObservationIgnored private var fetchGeneration = 0

    private let repository: OutfitsRepository

    init(repository: OutfitsRepository) {
        self.repository = repository
    }

    // MARK: Loading

    /// Marks the loaded history stale — e.g. the Today tab just recorded a
    /// wear or feedback — so the next `load()` (the screen's `.task`, which
    /// re-fires on tab entry) refetches instead of returning early.
    func markStale() {
        needsRefresh = true
    }

    /// First load when the screen appears. Safe to call repeatedly (`.task`
    /// re-fires on tab switches) — only fetches when nothing is loaded yet or
    /// the content was marked stale (`markStale()`).
    func load() async {
        guard items.isEmpty || needsRefresh, !isFetching else { return }
        await fetch()
    }

    /// Pull-to-refresh (and post-wear refresh): reload of page 1, resetting
    /// pagination.
    func refresh() async {
        await fetch()
    }

    private func fetch() async {
        let hadContent = !items.isEmpty
        if !hadContent {
            state = .loading
        }
        fetchGeneration += 1
        isFetching = true
        defer { isFetching = false }
        do {
            let response = try await repository.list()
            items = response.items
            totalTracked = response.total
            currentPage = response.page
            totalPages = response.totalPages
            errorMessage = nil
            needsRefresh = false
            rebuildGroups()
            state = items.isEmpty ? .empty : .loaded
        } catch {
            guard !Self.isCancellation(error) else { return }
            let message = Self.message(for: error, fallback: "Couldn't load your outfit history.")
            if hadContent {
                errorMessage = message
            } else {
                state = .failed(message)
            }
        }
    }

    // MARK: Pagination

    /// How close to the end of the flat list an entry must be to prefetch the
    /// next page (same threshold as `WardrobeViewModel`).
    private static let loadMoreThreshold = 6

    /// Called from each history card's `.onAppear`: when `currentEntry` is
    /// within the last `loadMoreThreshold` outfits, more pages exist, and no
    /// next-page fetch is already running, fetches the next page and appends
    /// it. Failures are silent — scrolling again retries.
    func loadMoreIfNeeded(currentEntry: HistoryEntry) async {
        guard !isLoadingMore, !isFetching, currentPage < totalPages else { return }
        guard let index = items.firstIndex(where: { $0.id == currentEntry.id }),
              index >= items.count - Self.loadMoreThreshold else { return }
        isLoadingMore = true
        defer { isLoadingMore = false }
        let generation = fetchGeneration
        do {
            let response = try await repository.list(page: currentPage + 1)
            // A refresh/load ran while this page was in flight — its page 1
            // replaced `items`, so appending this stale page would corrupt it.
            guard generation == fetchGeneration else { return }
            currentPage = response.page
            totalPages = response.totalPages
            totalTracked = response.total
            let loadedIDs = Set(items.map(\.id))
            items += response.items.filter { !loadedIDs.contains($0.id) }
            rebuildGroups()
        } catch {
            // Silent (includes cancellation); the next .onAppear retries.
        }
    }

    // MARK: Grouping

    private func rebuildGroups() {
        var keyed: [String: [Outfit]] = [:]
        for outfit in items {
            keyed[Self.dayKey(for: outfit), default: []].append(outfit)
        }
        groups = keyed.keys.sorted(by: >).map { key in
            let entries = keyed[key, default: []].enumerated().map { index, outfit in
                HistoryEntry(
                    outfit: outfit,
                    title: LookTitles.title(occasion: outfit.occasionContext, index: index),
                    piecesCount: Self.piecesCount(for: outfit),
                    pill: Self.pill(for: outfit)
                )
            }
            return HistoryGroup(dateLabel: Self.dateLabel(forDayKey: key), isoLabel: key, entries: entries)
        }
    }

    /// RN `dateKey`: `worn_date ?? created_at day`. Backend `worn_date`
    /// strings are plain dates and pass through verbatim; the fallback
    /// derives the day of `created_at` in the user's local time zone.
    ///
    /// Deliberate divergence from RN (product decision recorded in review):
    /// RN's `created_at.slice(0, 10)` takes the UTC day of the ISO string,
    /// which files a late-evening entry under the wrong diary day for users
    /// west of UTC. The diary means the user's local day — matching
    /// `TodayViewModel.todayWornDate()`'s local `worn_date`.
    static func dayKey(for outfit: Outfit, timeZone: TimeZone = .current) -> String {
        if let wornDate = outfit.wornDate {
            return wornDate
        }
        let formatter = DateFormatter()
        formatter.locale = Locale(identifier: "en_US_POSIX")
        formatter.timeZone = timeZone
        formatter.dateFormat = "yyyy-MM-dd"
        return formatter.string(from: outfit.createdAt)
    }

    /// RN `formatDay`: parse the key as a local calendar day and render
    /// long weekday + 2-digit month/day, e.g. `"Monday 06/23"`. Falls back to
    /// the raw key when it doesn't parse (RN's NaN branch).
    static func dateLabel(forDayKey key: String) -> String {
        let parser = DateFormatter()
        parser.locale = Locale(identifier: "en_US_POSIX")
        parser.dateFormat = "yyyy-MM-dd"
        guard let date = parser.date(from: key) else { return key }
        let formatter = DateFormatter()
        formatter.locale = Locale(identifier: "en_US_POSIX")
        formatter.dateFormat = "EEEE MM/dd"
        return formatter.string(from: date)
    }

    /// Pill precedence per RN: feedback === 1 → Loved, === -1 → Skipped,
    /// then worn_date → Worn, else Tracked. A feedback_score of 0 (or nil)
    /// falls through to the worn check.
    static func pill(for outfit: Outfit) -> HistoryEntry.Pill {
        if outfit.feedbackScore == 1 { return .loved }
        if outfit.feedbackScore == -1 { return .skipped }
        if outfit.wornDate != nil { return .worn }
        return .tracked
    }

    /// Non-nil item ids: top + bottom + each accessory. (RN hardcodes
    /// "3 pieces"; counting real ids is the honest version of the same line.)
    static func piecesCount(for outfit: Outfit) -> Int {
        (outfit.topItemId == nil ? 0 : 1)
            + (outfit.bottomItemId == nil ? 0 : 1)
            + (outfit.accessoryIds?.count ?? 0)
    }

    // MARK: Errors

    /// Same policy as `WardrobeViewModel`.
    private static func isCancellation(_ error: any Error) -> Bool {
        if error is CancellationError { return true }
        if (error as? URLError)?.code == .cancelled { return true }
        if case let APIError.network(underlying) = error {
            return isCancellation(underlying)
        }
        return false
    }

    private static func message(for error: any Error, fallback: String) -> String {
        switch error {
        case APIError.network:
            return "Can't reach ATTREQ. Check your connection."
        case let APIError.http(_, body):
            if let object = try? JSONSerialization.jsonObject(with: body) as? [String: Any],
               let detail = object["detail"] as? String,
               !detail.isEmpty {
                return detail
            }
            return fallback
        default:
            return fallback
        }
    }
}
