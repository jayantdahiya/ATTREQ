//
//  RecommendationCard.swift
//  ATTREQ
//
//  Outfit suggestion card (M4, artboard 05). Pixel source:
//  assets/design/ios-redesign-v2/attreq-app.jsx → ATTREQRecoCard.
//  Mono accent "Look No. NN" + italic display 22 title + muted match pill,
//  190pt garment collage (54% left tile + stacked 57%/43% right column, gap 8,
//  radius 16), mono weather/occasion row, borderSoft hairline, Skip | Wear
//  mono actions + heart/x circles, "Wear this" primary CTA.
//

import SwiftUI

/// One daily outfit suggestion with its wear/skip/feedback actions.
struct RecommendationCard: View {
    let suggestion: OutfitSuggestion
    /// 1-based position of the suggestion ("Look No. 01").
    let lookNumber: Int
    /// Presentational display name generated client-side (e.g. "The Long Walk").
    let title: String
    /// Wear flow (create + mark-worn) in flight — drives the CTA spinner and
    /// disables the actions row.
    let isWearing: Bool
    /// Heart/X feedback POST in flight — disables all actions (mirrors RN's
    /// pending-mutation button disabling).
    let isSubmittingFeedback: Bool
    let onWear: () -> Void
    let onSkip: () -> Void
    let onLove: () -> Void
    let onDismiss: () -> Void

    private var matchText: String {
        let percent = min(100, max(0, Int((suggestion.scores.total * 100).rounded())))
        return "\(percent)% match"
    }

    private var weatherLine: String {
        let weather = suggestion.weatherContext
        return "\(Int(weather.temp.rounded()))°C — \(weather.condition)"
    }

    /// RI-4: template-composed one-line reason for this pick. Falls back to
    /// an empty string for fixture JSON predating RI-4 (`explanation == nil`)
    /// so `explanationLine` simply doesn't render rather than showing "nil".
    private var explanationText: String? {
        guard let explanation = suggestion.explanation, !explanation.isEmpty else { return nil }
        return explanation
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 0) {
            titleRow
                .padding(.bottom, 14)
            collage
                .padding(.bottom, 12)
            if let explanationText {
                explanationLine(explanationText)
                    .padding(.bottom, 11)
            }
            contextRow
                .padding(.bottom, 11)
            Rectangle()
                .fill(Theme.borderSoft)
                .frame(height: 1)
                .padding(.bottom, 11)
            actionsRow
                .padding(.bottom, 11)
            AttreqPrimaryButton(
                "Wear this",
                systemImage: "checkmark",
                isLoading: isWearing,
                action: onWear
            )
            .disabled(isSubmittingFeedback)
        }
        .attreqCard(padding: 16)
    }

    // MARK: - Title row

    private var titleRow: some View {
        HStack(alignment: .top) {
            VStack(alignment: .leading, spacing: 3) {
                MonoLabel(String(format: "Look No. %02d", lookNumber), color: Theme.accent)
                Text(title)
                    .font(.attreqDisplay(22, weight: .semiBold, italic: true))
                    .foregroundStyle(Theme.text)
            }
            Spacer(minLength: 10)
            VStack(alignment: .trailing, spacing: 6) {
                // RI-4: distinct, non-error treatment for a hedged pick —
                // never suppress the recommendation, just label it honestly.
                if suggestion.isLowConfidence {
                    AttreqPill("Experimental", variant: .clay)
                } else {
                    AttreqPill(matchText, variant: .muted)
                }
                if suggestion.isRediscovery {
                    AttreqPill("Rediscover", variant: .gold)
                }
            }
        }
    }

    /// RI-4: the composed explanation line, rendered under the collage.
    /// Low-confidence picks get a dashed rule above the text (rather than
    /// the pill row alone) so the hedge reads as a deliberate, calm signal —
    /// not an error state.
    private func explanationLine(_ text: String) -> some View {
        VStack(alignment: .leading, spacing: 6) {
            if suggestion.isLowConfidence {
                Rectangle()
                    .stroke(style: StrokeStyle(lineWidth: 1, dash: [3, 3]))
                    .foregroundStyle(Theme.clay)
                    .frame(height: 1)
            }
            Text(text)
                .font(.attreqBody(13))
                .foregroundStyle(suggestion.isLowConfidence ? Theme.clay : Theme.t2)
                .fixedSize(horizontal: false, vertical: true)
                .accessibilityIdentifier("label-explanation")
        }
    }

    // MARK: - Garment collage

    /// 190pt collage: left tile 54% width full height, right column stacked
    /// 57% / remainder with 8pt gaps, all radius 16.
    private var collage: some View {
        // RI-4: a fullbody-anchored outfit has no bottom — the right column
        // drops the "Bottom" tile entirely (rather than rendering it empty)
        // and the left tile shows the fullbody item under a "Look" label.
        let isFullbody = suggestion.fullbodyItem != nil
        return GeometryReader { geo in
            HStack(spacing: 8) {
                SuggestionGarmentTile(
                    item: suggestion.primaryItem, tone: .top, label: isFullbody ? "Look" : "Top"
                )
                .frame(width: geo.size.width * 0.54)
                VStack(spacing: 8) {
                    if !isFullbody {
                        SuggestionGarmentTile(item: suggestion.bottomItem, tone: .bottom, label: "Bottom")
                            .frame(height: geo.size.height * 0.57)
                    }
                    SuggestionGarmentTile(item: suggestion.accessoryItem, tone: .accent, label: "Accent")
                        .frame(maxHeight: .infinity)
                }
            }
        }
        .frame(height: 190)
    }

    // MARK: - Weather / occasion row

    private var contextRow: some View {
        HStack(spacing: 10) {
            MonoLabel(weatherLine)
                .lineLimit(1)
            MonoLabel("— \(suggestion.occasionContext)", color: Theme.accent)
                .lineLimit(1)
        }
    }

    // MARK: - Actions row

    private var actionsRow: some View {
        HStack(spacing: 0) {
            HStack(spacing: 10) {
                Button(action: onSkip) {
                    HStack(spacing: 4) {
                        Image(systemName: "arrow.left")
                            .font(.system(size: 11, weight: .medium))
                            .foregroundStyle(Theme.t3)
                        MonoLabel("Skip")
                    }
                    .contentShape(Rectangle())
                }
                .buttonStyle(.plain)
                .accessibilityLabel("Skip look")
                .accessibilityIdentifier("action-skip")

                Rectangle()
                    .fill(Theme.border)
                    .frame(width: 1, height: 11)

                Button(action: onWear) {
                    HStack(spacing: 4) {
                        MonoLabel("Wear", color: Theme.moss)
                        Image(systemName: "arrow.right")
                            .font(.system(size: 11, weight: .medium))
                            .foregroundStyle(Theme.moss)
                    }
                    .contentShape(Rectangle())
                }
                .buttonStyle(.plain)
                .accessibilityLabel("Wear look")
                .accessibilityIdentifier("action-wear")
            }

            Spacer(minLength: 10)

            HStack(spacing: 6) {
                Button(action: onLove) {
                    Circle()
                        .strokeBorder(Theme.border, lineWidth: 1)
                        .frame(width: 33, height: 33)
                        .overlay(AttreqIcon.heart.view(size: 13, color: Theme.accent))
                        .contentShape(Circle())
                }
                .buttonStyle(.plain)
                .accessibilityLabel("Love look")
                .accessibilityIdentifier("action-love")

                Button(action: onDismiss) {
                    Circle()
                        .fill(Theme.accentSoft)
                        .frame(width: 33, height: 33)
                        .overlay(AttreqIcon.x.view(size: 13, color: Theme.t2))
                        .contentShape(Circle())
                }
                .buttonStyle(.plain)
                .accessibilityLabel("Dismiss look")
                .accessibilityIdentifier("action-dismiss")
            }
        }
        .disabled(isWearing || isSubmittingFeedback)
    }
}

// MARK: - Garment tile

/// One collage tile: real item thumbnail when available, otherwise the toned
/// `GarmentPlaceholder`. Mono label pinned bottom-left in both cases.
private struct SuggestionGarmentTile: View {
    let item: OutfitItemDetail?
    let tone: GarmentTone
    let label: String

    private static let shape = RoundedRectangle(cornerRadius: 16, style: .continuous)

    /// Best available image resolved against the API origin: thumbnail → full.
    /// (`OutfitItemDetail` carries no processed URL — `image_url` is already
    /// the backend's display image for the item.)
    private var imageURL: URL? {
        guard let item else { return nil }
        return AppConfig.absoluteMediaURL(item.thumbnailUrl ?? item.imageUrl)
    }

    var body: some View {
        Group {
            if let imageURL {
                AsyncImage(url: imageURL) { phase in
                    if case let .success(image) = phase {
                        Color.clear
                            .overlay(image.resizable().scaledToFill())
                            .overlay(alignment: .bottomLeading) { tileLabel }
                    } else {
                        placeholder
                    }
                }
            } else {
                placeholder
            }
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .clipShape(Self.shape)
    }

    private var placeholder: some View {
        GarmentPlaceholder(tone: tone, label: label, cornerRadius: 16)
    }

    /// Same metrics as `GarmentPlaceholder`'s label (mono 7.5, tracking 0.8).
    private var tileLabel: some View {
        Text(label.uppercased())
            .font(.attreqMono(7.5))
            .tracking(0.8)
            .foregroundStyle(Theme.t3)
            .lineLimit(1)
            .padding(.leading, 8)
            .padding(.bottom, 7)
    }
}

// MARK: - Preview fixtures

extension OutfitSuggestion {
    /// Deterministic fixture for previews (no network — placeholder tiles).
    static var previewFixture: OutfitSuggestion {
        let weather = WeatherData(
            temp: 22.0,
            feelsLike: 21.4,
            condition: "Partly Cloudy",
            description: "scattered clouds",
            humidity: 58,
            windSpeed: 3.4,
            icon: "02d"
        )
        return OutfitSuggestion(
            topItemId: "top-1",
            topItem: OutfitItemDetail(
                id: "top-1",
                category: "top",
                colorPrimary: "cream",
                pattern: "solid",
                imageUrl: nil,
                thumbnailUrl: nil
            ),
            bottomItemId: "bottom-1",
            bottomItem: OutfitItemDetail(
                id: "bottom-1",
                category: "bottom",
                colorPrimary: "charcoal",
                pattern: "solid",
                imageUrl: nil,
                thumbnailUrl: nil
            ),
            fullbodyItemId: nil,
            fullbodyItem: nil,
            footwearItemId: nil,
            footwearItem: nil,
            outerwearItemId: nil,
            outerwearItem: nil,
            accessoryItem: OutfitItemDetail(
                id: "accessory-1",
                category: "accessory",
                colorPrimary: "camel",
                pattern: nil,
                imageUrl: nil,
                thumbnailUrl: nil
            ),
            scores: OutfitScores(
                colorHarmony: 0.82,
                formality: 0.9,
                preferenceBonus: 0.1,
                styleDna: nil,
                behaviour: nil,
                total: 0.87
            ),
            weatherContext: weather,
            occasionContext: "Casual",
            outfitIndex: 0,
            explanation: "Cream + charcoal: strong neutral contrast + dialed in for casual",
            confidence: "normal",
            rediscovery: false,
            rediscoveryItemId: nil
        )
    }

    /// RI-4 fixture: a low-confidence, rediscovery-marked, fullbody-anchored
    /// outfit — exercises every new client-visible state in one preview.
    static var previewFullbodyRediscoveryFixture: OutfitSuggestion {
        let weather = WeatherData(
            temp: 12.0,
            feelsLike: 10.0,
            condition: "Rain",
            description: "light rain",
            humidity: 80,
            windSpeed: 4.0,
            icon: "10d"
        )
        return OutfitSuggestion(
            topItemId: nil,
            topItem: nil,
            bottomItemId: nil,
            bottomItem: nil,
            fullbodyItemId: "dress-1",
            fullbodyItem: OutfitItemDetail(
                id: "dress-1",
                category: "dress",
                colorPrimary: "maroon",
                pattern: "solid",
                imageUrl: nil,
                thumbnailUrl: nil
            ),
            footwearItemId: "boot-1",
            footwearItem: OutfitItemDetail(
                id: "boot-1",
                category: "boot",
                colorPrimary: "black",
                pattern: nil,
                imageUrl: nil,
                thumbnailUrl: nil
            ),
            outerwearItemId: nil,
            outerwearItem: nil,
            accessoryItem: nil,
            scores: OutfitScores(
                colorHarmony: 0.4,
                formality: 0.5,
                preferenceBonus: 0.0,
                styleDna: nil,
                behaviour: nil,
                total: 0.4
            ),
            weatherContext: weather,
            occasionContext: "Casual",
            outfitIndex: 1,
            explanation: "Experimental pick — tell us what you think.",
            confidence: "low",
            rediscovery: true,
            rediscoveryItemId: "dress-1"
        )
    }
}

// MARK: - Previews

#Preview("Reco card") {
    ScrollView {
        VStack(spacing: 14) {
            RecommendationCard(
                suggestion: .previewFixture,
                lookNumber: 1,
                title: "The Long Walk",
                isWearing: false,
                isSubmittingFeedback: false,
                onWear: {},
                onSkip: {},
                onLove: {},
                onDismiss: {}
            )
            RecommendationCard(
                suggestion: .previewFixture,
                lookNumber: 2,
                title: "Quiet Hours",
                isWearing: true,
                isSubmittingFeedback: false,
                onWear: {},
                onSkip: {},
                onLove: {},
                onDismiss: {}
            )
            RecommendationCard(
                suggestion: .previewFullbodyRediscoveryFixture,
                lookNumber: 3,
                title: "Not Worn In A While",
                isWearing: false,
                isSubmittingFeedback: false,
                onWear: {},
                onSkip: {},
                onLove: {},
                onDismiss: {}
            )
        }
        .padding(24)
    }
    .background(Theme.bg)
}
