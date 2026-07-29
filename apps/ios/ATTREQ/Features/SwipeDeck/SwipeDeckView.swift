//
//  SwipeDeckView.swift
//  ATTREQ
//
//  RI-5 (Task 5.3) — "Rate a few looks" swipe deck sheet. A short, optional
//  deck of freshly-generated outfits to tap/swipe 👍/👎 on. Closable at any
//  point (X in the header) — no confirmation, no guilt copy. No streak
//  counter or completion celebration by design (Stitch Fix Style Shuffle
//  precedent: streaks create unnecessary pressure); the "N of 5" label is a
//  plain fact, not a progress meter to feel behind on.
//

import SwiftUI

struct SwipeDeckView: View {
    let viewModel: SwipeDeckViewModel
    /// Dismisses the sheet — wired by the presenter (`TodayScreen`).
    var onClose: () -> Void

    var body: some View {
        VStack(alignment: .leading, spacing: 0) {
            header
                .padding(.bottom, 18)

            switch viewModel.state {
            case .loading:
                Spacer()
                ProgressView().tint(Theme.t2)
                Spacer()
            case .empty:
                Spacer()
                doneBlock
                Spacer()
            case let .failed(message):
                Spacer()
                errorBlock(message)
                Spacer()
            case .loaded:
                if let current = viewModel.current {
                    cardBlock(current)
                }
                Spacer(minLength: 0)
            }
        }
        .padding(.horizontal, 24)
        .padding(.top, 20)
        .padding(.bottom, 24)
        .background(Theme.bg.ignoresSafeArea())
        .task { await viewModel.load() }
    }

    // MARK: - Header

    private var header: some View {
        HStack(alignment: .center) {
            VStack(alignment: .leading, spacing: 3) {
                Text("Rate a few looks")
                    .font(.attreqDisplay(20, weight: .semiBold, italic: true))
                    .foregroundStyle(Theme.text)
                if viewModel.state == .loaded, viewModel.totalCount > 0 {
                    MonoLabel("\(viewModel.position) of \(viewModel.totalCount)")
                }
            }
            Spacer()
            Button(action: onClose) {
                Circle()
                    .strokeBorder(Theme.border, lineWidth: 1)
                    .frame(width: 34, height: 34)
                    .overlay(Image(systemName: "xmark").font(.system(size: 13, weight: .medium)).foregroundStyle(Theme.t2))
            }
            .buttonStyle(.plain)
            .accessibilityLabel("Close")
            .accessibilityIdentifier("swipe-deck-close")
        }
    }

    // MARK: - Card

    @ViewBuilder
    private func cardBlock(_ suggestion: OutfitSuggestion) -> some View {
        VStack(alignment: .leading, spacing: 0) {
            collage(for: suggestion)
                .padding(.bottom, 12)
            contextRow(for: suggestion)
                .padding(.bottom, 16)

            if viewModel.capReached {
                capReachedBlock
            } else {
                ratingRow
            }

            if let message = viewModel.errorMessage {
                BodyText(message, size: 12, color: Theme.clay)
                    .padding(.top, 8)
            }
        }
        .attreqCard(padding: 16)
    }

    private func collage(for suggestion: OutfitSuggestion) -> some View {
        let isFullbody = suggestion.fullbodyItem != nil
        return GeometryReader { geo in
            HStack(spacing: 8) {
                _SwipeDeckTile(item: suggestion.primaryItem, tone: .top, label: isFullbody ? "Look" : "Top")
                    .frame(width: geo.size.width * (isFullbody ? 1.0 : 0.5))
                if !isFullbody {
                    _SwipeDeckTile(item: suggestion.bottomItem, tone: .bottom, label: "Bottom")
                        .frame(maxWidth: .infinity)
                }
            }
        }
        .frame(height: 190)
    }

    private func contextRow(for suggestion: OutfitSuggestion) -> some View {
        HStack(spacing: 10) {
            MonoLabel("\(Int(suggestion.weatherContext.temp.rounded()))°C — \(suggestion.weatherContext.condition)")
                .lineLimit(1)
            MonoLabel("— \(suggestion.occasionContext)", color: Theme.accent)
                .lineLimit(1)
        }
    }

    private var ratingRow: some View {
        HStack(spacing: 12) {
            ratingButton(systemImage: "hand.thumbsdown", tint: Theme.clay, label: "Not for me") {
                Task { await viewModel.rate(liked: false) }
            }
            ratingButton(systemImage: "hand.thumbsup", tint: Theme.moss, label: "Like this") {
                Task { await viewModel.rate(liked: true) }
            }
        }
        .disabled(viewModel.isSubmitting)
    }

    private func ratingButton(systemImage: String, tint: Color, label: String, action: @escaping () -> Void) -> some View {
        Button(action: action) {
            HStack {
                Spacer()
                Image(systemName: systemImage)
                    .font(.system(size: 18, weight: .medium))
                Spacer()
            }
            .padding(.vertical, 14)
            .foregroundStyle(tint)
            .background(tint.opacity(0.12), in: RoundedRectangle(cornerRadius: 14, style: .continuous))
        }
        .buttonStyle(.plain)
        .accessibilityLabel(label)
    }

    // MARK: - Terminal states

    private var doneBlock: some View {
        VStack(alignment: .leading, spacing: 10) {
            MonoLabel("All set", size: 11)
            BodyText("Thanks for rating today's looks — they'll help sharpen tomorrow's picks.", size: 13)
            AttreqPrimaryButton("Close", action: onClose)
                .padding(.top, 6)
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .attreqCard(padding: 16)
    }

    private var capReachedBlock: some View {
        VStack(alignment: .leading, spacing: 8) {
            MonoLabel("Cap reached for today", size: 10)
            BodyText("You've rated the max looks for today — come back tomorrow for more.", size: 13, color: Theme.t2)
        }
        .frame(maxWidth: .infinity, alignment: .leading)
    }

    private func errorBlock(_ message: String) -> some View {
        VStack(alignment: .leading, spacing: 10) {
            BodyText(message, size: 13, color: Theme.clay)
            AttreqPrimaryButton("Try again") {
                Task { await viewModel.load() }
            }
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .attreqCard(padding: 16)
    }
}

// MARK: - Tile

/// Minimal image-or-placeholder tile for the swipe deck — deliberately
/// simpler than `RecommendationCard`'s full collage (that view's
/// `SuggestionGarmentTile` is file-private), same visual language.
private struct _SwipeDeckTile: View {
    let item: OutfitItemDetail?
    let tone: GarmentTone
    let label: String

    private static let shape = RoundedRectangle(cornerRadius: 16, style: .continuous)

    private var imageURL: URL? {
        guard let item else { return nil }
        return AppConfig.absoluteMediaURL(item.thumbnailUrl ?? item.imageUrl)
    }

    var body: some View {
        Group {
            if let imageURL {
                AsyncImage(url: imageURL) { phase in
                    if case let .success(image) = phase {
                        Color.clear.overlay(image.resizable().scaledToFill())
                    } else {
                        GarmentPlaceholder(tone: tone, label: label, cornerRadius: 16)
                    }
                }
            } else {
                GarmentPlaceholder(tone: tone, label: label, cornerRadius: 16)
            }
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .clipShape(Self.shape)
    }
}

// MARK: - Previews

#Preview("Swipe deck") {
    let auth = AuthSession(keychain: KeychainStore(), baseURL: AppConfig.apiBaseURL)
    let client = APIClient(baseURL: AppConfig.apiBaseURL, authSession: auth)
    SwipeDeckView(
        viewModel: SwipeDeckViewModel(repository: RecommendationsRepository(apiClient: client)),
        onClose: {}
    )
}
