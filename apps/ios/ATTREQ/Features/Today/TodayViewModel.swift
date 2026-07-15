//
//  TodayViewModel.swift
//  ATTREQ
//
//  Observable state for the Today dashboard (M4, artboard 05): daily
//  weather-aware outfit suggestions with Wear / Skip / feedback actions.
//
//  RN semantics mirrored here (dashboard-screen.tsx + recommendation-card.tsx):
//  - "Wear this" / swipe right → POST /outfits (create-or-reuse) then
//    POST /outfits/{id}/wear with today's LOCAL date (deliberate divergence
//    from RN's UTC date; see `todayWornDate`).
//  - Heart button → POST /outfits/{id}/feedback with feedback_score 1
//    (create-or-reuse first). The card stays visible in RN, so `love` does
//    NOT advance the index.
//  - X button / swipe left ("Skip" overlay) → POST /outfits/{id}/feedback
//    with feedback_score -1 (`dismiss` here). RN renders every suggestion in
//    a list so nothing moves; on our index-paged card, dismissing advances.
//  - The mono "Skip / Wear" row in RN is purely decorative (no handlers);
//    our `skip()` is the local-only advance with no API call.
//  - Suggestions created once per session are remembered by
//    "topId:bottomId" key so heart-then-wear reuses the same outfit row
//    (RN `persistedOutfits`).
//

import Foundation
import Observation

/// Deterministic, PURELY PRESENTATIONAL look titles. The backend has no
/// concept of outfit names and RN shows the capitalized occasion; the design
/// (artboard 05/07) shows editorial names like "The Long Walk", so we generate
/// display names client-side from a small curated list keyed by
/// occasion + index (per docs/06-ios-native/05-milestone-4-today-outfits.md).
/// Never send these to the API.
enum LookTitles {
    private static let titlesByOccasion: [String: [String]] = [
        "casual": ["The Long Walk", "Casual Friday", "Corner Café", "Open Air"],
        "formal": ["Evening Edit", "The Gallery", "First Impression", "Candlelight"],
        "party": ["After Hours", "The Guest List", "Neon Nights", "Last Dance"],
        "business": ["The Boardroom", "Nine to Five", "Signature Move", "Closing Note"],
        "athletic": ["Morning Run", "Second Wind", "The Warm-Up", "Fresh Pace"],
    ]
    /// Unknown occasions cycle the design artboard's sample names.
    private static let fallback = ["The Long Walk", "Casual Friday", "Evening Edit", "Morning Run"]

    /// Title for the look at `index` (0-based) under `occasion`. Same inputs
    /// always give the same title; consecutive indices cycle the list.
    static func title(occasion: String?, index: Int) -> String {
        let titles = titlesByOccasion[occasion?.lowercased() ?? ""] ?? fallback
        return titles[max(index, 0) % titles.count]
    }
}

/// Drives `TodayScreen`. Owned by `MainTabsView` so state survives tab switches.
@MainActor
@Observable
final class TodayViewModel {
    enum LoadState: Equatable {
        case loading
        case loaded
        /// Fatal first-load failure (message rendered full-screen).
        case failed(String)
        /// Successful call but nothing to show — no suggestions, or the
        /// backend's 404 "insufficient wardrobe items" (RN renders its empty
        /// closet card for both).
        case empty
    }

    // MARK: State (read by TodayScreen)

    private(set) var state: LoadState = .loading
    /// Today's suggestions in server order (RN renders them all; we page by index).
    private(set) var suggestions: [OutfitSuggestion] = []
    /// Index of the suggestion currently on the card.
    private(set) var currentIndex = 0
    /// Weather used for generation (drives the weather strip). `nil` until loaded.
    private(set) var weather: WeatherData?
    /// Occasion actually used by the server (echoed in the response).
    /// Requests send `occasion ?? "casual"` — RN always requests "casual".
    private(set) var occasion: String?
    /// True while the wear flow (create + mark-worn) is in flight.
    private(set) var isWearing = false
    /// True while a heart/X feedback flow is in flight (RN disables the
    /// buttons while any mutation is pending).
    private(set) var isSubmittingFeedback = false
    /// Last action/load failure, rendered as a banner; cleared on next success.
    var errorMessage: String?

    /// Suggestion on the card, `nil` when there are none.
    var current: OutfitSuggestion? {
        suggestions.indices.contains(currentIndex) ? suggestions[currentIndex] : nil
    }

    /// "N looks" mono counter.
    var totalLooks: Int { suggestions.count }

    /// Presentational italic title for the look at `index` (see `LookTitles`).
    func lookTitle(at index: Int) -> String {
        let occasionKey = suggestions.indices.contains(index) ? suggestions[index].occasionContext : occasion
        return LookTitles.title(occasion: occasionKey, index: index)
    }

    /// Presentational italic title for the current look.
    var currentLookTitle: String { lookTitle(at: currentIndex) }

    // MARK: Greeting helpers

    /// Header date mono line, e.g. `"Monday 23/06"` (artboard 05 shows
    /// day/month; note RN uses Intl `en` month-first — design wins here).
    static func dateLine(for date: Date = .now) -> String {
        let formatter = DateFormatter()
        formatter.locale = Locale(identifier: "en_US_POSIX")
        formatter.dateFormat = "EEEE dd/MM"
        return formatter.string(from: date)
    }

    /// "Good morning" before 12, "Good afternoon" 12–16, "Good evening" from 17.
    static func greeting(for date: Date = .now, calendar: Calendar = .current) -> String {
        switch calendar.component(.hour, from: date) {
        case ..<12: "Good morning"
        case ..<17: "Good afternoon"
        default: "Good evening"
        }
    }

    /// First word of the user's full name, `"there"` when unknown
    /// (RN: `full_name?.split(' ')[0] ?? 'there'`).
    static func firstName(from user: User?) -> String {
        guard let first = user?.fullName?.split(separator: " ").first else { return "there" }
        return String(first)
    }

    // MARK: Dependencies

    private let repository: RecommendationsRepository

    /// Outfit ids already created this session, keyed "topId:bottomId" —
    /// mirrors RN's `persistedOutfits` so heart + wear on the same suggestion
    /// creates only one outfit row.
    @ObservationIgnored private var persistedOutfits: [String: String] = [:]

    init(repository: RecommendationsRepository) {
        self.repository = repository
    }

    // MARK: Loading

    /// First load / re-entry load. Uses the server's daily cache. Safe to
    /// call repeatedly (`.task` re-fires on every tab switch): once content
    /// is loaded it returns immediately — preserving `currentIndex` and any
    /// in-flight wear — while failed/empty/initial-loading states retry.
    func load() async {
        guard state != .loaded else { return }
        await fetch(refresh: false)
    }

    /// Pull-to-refresh: `force_refresh=true` regenerates past the daily cache.
    func refresh() async {
        await fetch(refresh: true)
    }

    private func fetch(refresh: Bool) async {
        let hadContent = state == .loaded
        if !hadContent {
            state = .loading
        }
        do {
            let response = try await repository.daily(refresh: refresh, occasion: occasion ?? "casual")
            suggestions = response.suggestions
            currentIndex = 0
            weather = response.weather
            occasion = response.occasion
            errorMessage = nil
            state = suggestions.isEmpty ? .empty : .loaded
        } catch {
            guard !Self.isCancellation(error) else { return }
            // 404 = "insufficient wardrobe items" — an honest empty state,
            // not an error (RN shows the empty closet card whenever no
            // suggestions arrive).
            if case let APIError.http(status, _) = error, status == 404 {
                suggestions = []
                currentIndex = 0
                state = .empty
                return
            }
            let message = Self.message(for: error, fallback: "Couldn't load today's looks.")
            if hadContent {
                errorMessage = message
            } else {
                state = .failed(message)
            }
        }
    }

    // MARK: Actions

    /// "Wear this" / swipe right: persist the suggestion (create-or-reuse)
    /// then mark it worn today (the user's LOCAL date — see `todayWornDate`).
    /// Advances to the next look on success. Returns whether it succeeded so
    /// the screen can refresh the History tab.
    func wear(using outfitsRepository: OutfitsRepository) async -> Bool {
        guard let suggestion = current, !isWearing, !isSubmittingFeedback else { return false }
        isWearing = true
        defer { isWearing = false }
        do {
            let outfitId = try await persistedOutfitId(for: suggestion, using: outfitsRepository)
            _ = try await outfitsRepository.markWorn(outfitId: outfitId, wornDate: Self.todayWornDate())
            errorMessage = nil
            advance()
            return true
        } catch {
            errorMessage = Self.message(for: error, fallback: "Unable to track outfit.")
            return false
        }
    }

    /// Local-only advance to the next suggestion — no API call (the RN
    /// "Skip" mono label has no handler; only the X/swipe-left path posts
    /// feedback, which is `dismiss`). Wraps past the last look so Skip always
    /// shows another suggestion.
    func skip() {
        advance()
    }

    /// Heart: `feedback_score 1` ("we will bias toward outfits like this").
    /// The card stays put — RN keeps the card visible after loving it.
    func love(using outfitsRepository: OutfitsRepository) async -> Bool {
        await submitFeedback(1, using: outfitsRepository)
    }

    /// X / swipe left: `feedback_score -1` ("we will steer away from looks
    /// like this"), then advance — the index-paged mirror of RN's Skip swipe.
    func dismiss(using outfitsRepository: OutfitsRepository) async -> Bool {
        let succeeded = await submitFeedback(-1, using: outfitsRepository)
        if succeeded {
            advance()
        }
        return succeeded
    }

    private func submitFeedback(_ score: Int, using outfitsRepository: OutfitsRepository) async -> Bool {
        guard let suggestion = current, !isWearing, !isSubmittingFeedback else { return false }
        isSubmittingFeedback = true
        defer { isSubmittingFeedback = false }
        do {
            let outfitId = try await persistedOutfitId(for: suggestion, using: outfitsRepository)
            _ = try await outfitsRepository.submitFeedback(outfitId: outfitId, score: score)
            errorMessage = nil
            return true
        } catch {
            errorMessage = Self.message(for: error, fallback: "Unable to save feedback.")
            return false
        }
    }

    /// Create-or-reuse: one outfit row per suggestion per session (RN
    /// `persistedOutfits` keyed `${top_item_id}:${bottom_item_id}`).
    private func persistedOutfitId(
        for suggestion: OutfitSuggestion,
        using outfitsRepository: OutfitsRepository
    ) async throws -> String {
        let key = "\(suggestion.topItemId):\(suggestion.bottomItemId)"
        if let existing = persistedOutfits[key] {
            return existing
        }
        let outfit = try await outfitsRepository.create(OutfitCreateRequest(suggestion: suggestion))
        persistedOutfits[key] = outfit.id
        return outfit.id
    }

    private func advance() {
        guard !suggestions.isEmpty else { return }
        currentIndex = (currentIndex + 1) % suggestions.count
    }

    /// Today as a `"YYYY-MM-DD"` string in the user's LOCAL calendar day.
    ///
    /// Deliberate divergence from RN (product decision recorded in review):
    /// RN used `new Date().toISOString().slice(0, 10)` — the UTC day — which
    /// stamps an evening wear west of UTC with tomorrow's date. Wearing is a
    /// diary action; the day the user means is their local one. The backend
    /// stores the plain date verbatim, and History's `dayKey` fallback uses
    /// the same local-day convention.
    static func todayWornDate(now: Date = .now, timeZone: TimeZone = .current) -> String {
        let formatter = DateFormatter()
        formatter.locale = Locale(identifier: "en_US_POSIX")
        formatter.timeZone = timeZone
        formatter.dateFormat = "yyyy-MM-dd"
        return formatter.string(from: now)
    }

    // MARK: Errors

    /// Same policy as `WardrobeViewModel`: cancelled requests are never errors.
    private static func isCancellation(_ error: any Error) -> Bool {
        if error is CancellationError { return true }
        if (error as? URLError)?.code == .cancelled { return true }
        if case let APIError.network(underlying) = error {
            return isCancellation(underlying)
        }
        return false
    }

    /// Same policy as `WardrobeViewModel`: connectivity gets a friendly line,
    /// FastAPI `detail` strings pass through, everything else falls back.
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
