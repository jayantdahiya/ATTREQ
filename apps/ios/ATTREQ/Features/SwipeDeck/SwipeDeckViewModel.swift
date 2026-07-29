//
//  SwipeDeckViewModel.swift
//  ATTREQ
//
//  RI-5 (Task 5.3) — "Rate a few looks" swipe deck. A short, optional,
//  seconds-long deck of freshly-generated outfits to rate 👍/👎. Ratings
//  submit through the SAME recommendation-feedback endpoint the Today card
//  uses (`RecommendationsRepository.submitFeedback`, action accepted/
//  rejected) — reusing the RI-1 telemetry contract; the shown batch's
//  `context.source == "swipe_deck"` (set server-side at generation time)
//  distinguishes it from a normal daily batch. No outfit row is ever created
//  here (unlike Today's wear flow) — a rating is a preference signal, not
//  "I wore this."
//
//  Deliberately no streaks/progress pressure (Stitch Fix Style Shuffle
//  precedent; competitor evidence that streaks create unnecessary pressure)
//  — the deck is closable at any point, and running out of ratings for the
//  day (`capReached`) is a quiet, factual state, never a failure banner.
//

import Foundation
import Observation
import os

@MainActor
@Observable
final class SwipeDeckViewModel {
    enum LoadState: Equatable {
        case loading
        case loaded
        /// Deck came back empty (insufficient wardrobe, or nothing left to
        /// rate) — same "honest empty state" treatment as Today's `.empty`.
        case empty
        case failed(String)
    }

    private(set) var state: LoadState = .loading
    private(set) var suggestions: [OutfitSuggestion] = []
    private(set) var currentIndex = 0
    private(set) var isSubmitting = false
    /// Set once the server refuses a rating with 429 (daily cap reached
    /// mid-session, e.g. a second device rating concurrently) — the deck
    /// stops accepting ratings but stays browsable/closable.
    private(set) var capReached = false
    var errorMessage: String?

    private let repository: RecommendationsRepository
    private let logger = Logger(subsystem: "com.attreq.ios", category: "SwipeDeckViewModel")

    @ObservationIgnored private var recommendationId: String?

    /// Card currently on screen, `nil` once the deck is exhausted.
    var current: OutfitSuggestion? {
        suggestions.indices.contains(currentIndex) ? suggestions[currentIndex] : nil
    }

    var totalCount: Int { suggestions.count }
    /// 1-based position for a light "2 of 5" label — factual, not a pressure meter.
    var position: Int { currentIndex + 1 }

    init(repository: RecommendationsRepository) {
        self.repository = repository
    }

    func load() async {
        state = .loading
        errorMessage = nil
        do {
            let response = try await repository.swipeDeck()
            suggestions = response.suggestions
            currentIndex = 0
            recommendationId = response.recommendationId
            state = suggestions.isEmpty ? .empty : .loaded
        } catch {
            if case let APIError.http(status, _) = error, status == 404 {
                state = .empty
                return
            }
            state = .failed(Self.message(for: error))
        }
    }

    /// Rate the current card 👍/👎 and advance to the next (or end the deck
    /// if this was the last card). Returns `false` without advancing on a
    /// 429 (`capReached` is set so the view can stop offering the buttons).
    @discardableResult
    func rate(liked: Bool) async -> Bool {
        guard let suggestion = current, let recommendationId, !isSubmitting else { return false }
        isSubmitting = true
        defer { isSubmitting = false }
        do {
            try await repository.submitFeedback(
                recommendationId: recommendationId,
                outfitIndex: suggestion.outfitIndex,
                action: liked ? .accepted : .rejected
            )
            advance()
            return true
        } catch {
            if case let APIError.http(status, _) = error, status == 429 {
                capReached = true
                return false
            }
            logger.error("swipe-deck rating failed (non-fatal): \(String(describing: error))")
            errorMessage = Self.message(for: error)
            return false
        }
    }

    private func advance() {
        guard currentIndex < suggestions.count - 1 else {
            // Deck exhausted: clear `suggestions` too, not just flip `state`
            // — `current` reads `suggestions`/`currentIndex` directly, so
            // leaving the last card's data in place would keep it visible
            // despite `state == .empty`.
            suggestions = []
            currentIndex = 0
            state = .empty
            return
        }
        currentIndex += 1
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
            return "Couldn't load the swipe deck."
        default:
            return "Couldn't load the swipe deck."
        }
    }
}
