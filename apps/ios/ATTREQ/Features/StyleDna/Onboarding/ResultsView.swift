//
//  ResultsView.swift
//  ATTREQ
//
//  Style DNA onboarding step 2 (M3). No artboard exists for this screen —
//  composed in the design language (serif italic headline, cards, mono
//  labels, pills) per the M3 doc. Content mirrors the RN screen
//  `apps/mobile/app/(onboarding)/results.tsx` + StyleDnaCard/FoundItemsCard:
//  aesthetic, palette swatches, patterns, silhouette, formality, occasions,
//  plus the "N wardrobe items found" card.
//

import SwiftUI

struct ResultsView: View {
    let model: OnboardingViewModel
    /// Advances to review when items were detected; otherwise the flow shell
    /// completes onboarding directly (RN's "Looks right →").
    let onContinue: () -> Void

    private var response: StyleDnaUploadResponse? { model.uploadResponse }

    var body: some View {
        VStack(alignment: .leading, spacing: 0) {
            MonoLabel("Step 02 — Results", color: Theme.accent)
                .padding(.bottom, 8)

            headline
                .padding(.bottom, 8)

            if let response {
                BodyText(subtitle(for: response))
                    .padding(.bottom, 20)

                if let dna = response.styleDna {
                    dnaCard(dna)
                        .padding(.bottom, 14)
                } else {
                    extractionFailedCard
                        .padding(.bottom, 14)
                }

                if !model.detectedItems.isEmpty {
                    foundItemsCard
                        .padding(.bottom, 14)
                }
            }

            if let message = model.completionError {
                BodyText(message, size: 13, color: Theme.clay)
                    .padding(.bottom, 12)
            }

            Spacer(minLength: 16)

            AttreqPrimaryButton(
                model.detectedItems.isEmpty ? "Looks right →" : "Review items →",
                role: .accent,
                isLoading: model.isCompleting,
                action: onContinue
            )
        }
    }

    // MARK: - Header

    private var headline: some View {
        (
            Text("Your\n").foregroundStyle(Theme.text)
                + Text("Style DNA.")
                .font(.attreqDisplay(34, italic: true))
                .foregroundStyle(Theme.accent)
        )
        .font(.attreqDisplay(34))
    }

    private func subtitle(for response: StyleDnaUploadResponse) -> String {
        var text = "Based on \(response.photosProcessed) photo\(response.photosProcessed == 1 ? "" : "s")."
        if response.photosSkipped > 0 {
            text += " \(response.photosSkipped) skipped (low quality)."
        }
        return text
    }

    // MARK: - DNA card

    private func dnaCard(_ dna: StyleDna) -> some View {
        VStack(alignment: .leading, spacing: 0) {
            // Aesthetic — primary as serif italic, secondary as pills.
            HStack(alignment: .firstTextBaseline) {
                MonoLabel("Aesthetic")
                Spacer()
                confidencePill(dna.aesthetic.confidence)
            }
            .padding(.bottom, 7)
            Text(dna.aesthetic.primary.capitalized)
                .font(.attreqDisplay(24, italic: true))
                .foregroundStyle(Theme.text)
                .padding(.bottom, dna.aesthetic.secondary.isEmpty ? 0 : 8)
            if !dna.aesthetic.secondary.isEmpty {
                PillFlowLayout(spacing: 6) {
                    ForEach(dna.aesthetic.secondary, id: \.self) { name in
                        AttreqPill(name)
                    }
                }
            }

            divider

            // Color palette — dominant / accent / avoids swatch rows.
            HStack(alignment: .firstTextBaseline) {
                MonoLabel("Palette")
                Spacer()
                confidencePill(dna.colorPalette.confidence)
            }
            .padding(.bottom, 10)
            VStack(alignment: .leading, spacing: 10) {
                paletteRow("Dominant", colors: dna.colorPalette.dominant)
                paletteRow("Accent", colors: dna.colorPalette.accent)
                paletteRow("Avoids", colors: dna.colorPalette.avoids)
            }

            divider

            // Patterns / silhouette / formality / occasions.
            VStack(alignment: .leading, spacing: 12) {
                pillRow(
                    "Patterns",
                    pills: dna.patterns.preferred.isEmpty ? ["Solid"] : dna.patterns.preferred,
                    confidence: dna.patterns.confidence
                )
                pillRow("Silhouette", pills: [dna.silhouette.preference], confidence: dna.silhouette.confidence)
                formalityRow(dna.formalityBias)
                pillRow("Occasions", pills: dna.occasions.primary, confidence: dna.occasions.confidence)
            }
        }
        .attreqCard(padding: 18)
    }

    private var divider: some View {
        Rectangle()
            .fill(Theme.borderSoft)
            .frame(height: 1)
            .padding(.vertical, 14)
    }

    /// Mirrors RN `ConfidenceBadge` (badge only when confidence < 0.6), but in
    /// pill form; a gold percentage pill is shown otherwise so every section
    /// carries its confidence, per the M3 composition spec.
    @ViewBuilder
    private func confidencePill(_ confidence: Double) -> some View {
        if confidence < 0.6 {
            AttreqPill("Limited data", variant: .clay)
        } else {
            AttreqPill("\(Int((confidence * 100).rounded()))% confident", variant: .gold)
        }
    }

    private func paletteRow(_ label: String, colors: [String]) -> some View {
        VStack(alignment: .leading, spacing: 6) {
            MonoLabel(label, size: 8.5)
            if colors.isEmpty {
                MonoLabel("—", size: 8.5, color: Theme.t2)
            } else {
                PillFlowLayout(spacing: 8) {
                    ForEach(colors, id: \.self) { name in
                        swatch(name)
                    }
                }
            }
        }
    }

    private func swatch(_ name: String) -> some View {
        HStack(spacing: 5) {
            RoundedRectangle(cornerRadius: 4, style: .continuous)
                .fill(Self.swatchColor(for: name) ?? Theme.surface)
                .frame(width: 14, height: 14)
                .overlay {
                    RoundedRectangle(cornerRadius: 4, style: .continuous)
                        .strokeBorder(Theme.border, lineWidth: 1)
                }
            Text(name.uppercased())
                .font(.attreqMono(8.5))
                .tracking(0.9)
                .foregroundStyle(Theme.t2)
        }
    }

    private func pillRow(_ label: String, pills: [String], confidence: Double) -> some View {
        VStack(alignment: .leading, spacing: 7) {
            HStack(alignment: .firstTextBaseline) {
                MonoLabel(label)
                Spacer()
                confidencePill(confidence)
            }
            if pills.isEmpty {
                MonoLabel("—", size: 8.5, color: Theme.t2)
            } else {
                PillFlowLayout(spacing: 6) {
                    ForEach(pills, id: \.self) { pill in
                        AttreqPill(pill)
                    }
                }
            }
        }
    }

    private func formalityRow(_ formality: StyleDnaFormalityBias) -> some View {
        VStack(alignment: .leading, spacing: 7) {
            HStack(alignment: .firstTextBaseline) {
                MonoLabel("Formality")
                Spacer()
                confidencePill(formality.confidence)
            }
            HStack(spacing: 8) {
                AttreqPill(formality.label, variant: .gold)
                MonoLabel(String(format: "%.1f / 3", formality.level), size: 8.5, color: Theme.t2)
            }
        }
    }

    // MARK: - Extraction failed (nil style_dna)

    /// Graceful degradation per the M3 doc: upload succeeded but the LLM
    /// extraction failed (e.g. no classifier key) — clay body, flow continues.
    private var extractionFailedCard: some View {
        VStack(alignment: .leading, spacing: 6) {
            MonoLabel("Extraction failed", color: Theme.clay)
            BodyText(
                "We couldn't read your style from these photos this time. Your photos are saved — you can regenerate your Style DNA from your profile later.",
                size: 13,
                color: Theme.clay
            )
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding(14)
        .background(Theme.claySoft, in: RoundedRectangle(cornerRadius: 16, style: .continuous))
    }

    // MARK: - Found items card

    private var foundItemsCard: some View {
        let items = model.detectedItems
        return VStack(alignment: .leading, spacing: 5) {
            MonoLabel("Wardrobe", color: Theme.accent)
            Text("\(items.count) wardrobe item\(items.count == 1 ? "" : "s") found")
                .font(.attreqDisplay(20, italic: true))
                .foregroundStyle(Theme.text)
            BodyText(itemsPreview(items), size: 13)
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding(16)
        .background(Theme.accentSoft, in: RoundedRectangle(cornerRadius: 16, style: .continuous))
    }

    /// RN FoundItemsCard preview line: first three "color subcategory" names
    /// joined with " · ", then "+N more".
    private func itemsPreview(_ items: [DetectedWardrobeItem]) -> String {
        let names = items.prefix(3).map { item in
            let name = item.subcategory.isEmpty ? item.category : item.subcategory
            return [item.colorPrimary, name].compactMap(\.self).joined(separator: " ")
        }
        let remaining = items.count - 3
        return names.joined(separator: " · ") + (remaining > 0 ? " · +\(remaining) more" : "")
    }

    // MARK: - Swatch color mapping

    /// Best-effort mapping from the classifier's free-text color names to
    /// displayable swatches; unknown names fall back to a bordered neutral.
    private static func swatchColor(for name: String) -> Color? {
        let needle = name.lowercased()
        // Longest-first so "light blue" beats "blue", "off-white" beats "white".
        let table: [(String, Color)] = [
            ("light blue", Color(red: 0.68, green: 0.78, blue: 0.88)),
            ("off-white", Color(red: 0.95, green: 0.94, blue: 0.91)),
            ("charcoal", Color(red: 0.22, green: 0.22, blue: 0.23)),
            ("burgundy", Color(red: 0.45, green: 0.13, blue: 0.18)),
            ("lavender", Color(red: 0.71, green: 0.65, blue: 0.83)),
            ("mustard", Color(red: 0.80, green: 0.62, blue: 0.18)),
            ("maroon", Color(red: 0.42, green: 0.13, blue: 0.15)),
            ("orange", Color(red: 0.85, green: 0.50, blue: 0.20)),
            ("purple", Color(red: 0.48, green: 0.32, blue: 0.58)),
            ("silver", Color(red: 0.77, green: 0.78, blue: 0.79)),
            ("yellow", Color(red: 0.90, green: 0.78, blue: 0.30)),
            ("black", Color(red: 0.10, green: 0.10, blue: 0.10)),
            ("white", Color(red: 0.97, green: 0.97, blue: 0.96)),
            ("cream", Color(red: 0.94, green: 0.91, blue: 0.84)),
            ("ivory", Color(red: 0.96, green: 0.94, blue: 0.89)),
            ("beige", Color(red: 0.87, green: 0.82, blue: 0.72)),
            ("camel", Color(red: 0.76, green: 0.60, blue: 0.42)),
            ("taupe", Color(red: 0.60, green: 0.55, blue: 0.49)),
            ("brown", Color(red: 0.45, green: 0.33, blue: 0.24)),
            ("denim", Color(red: 0.29, green: 0.40, blue: 0.55)),
            ("khaki", Color(red: 0.66, green: 0.62, blue: 0.47)),
            ("olive", Color(red: 0.44, green: 0.45, blue: 0.28)),
            ("green", Color(red: 0.35, green: 0.52, blue: 0.39)),
            ("sage", Color(red: 0.62, green: 0.68, blue: 0.58)),
            ("navy", Color(red: 0.15, green: 0.20, blue: 0.33)),
            ("blue", Color(red: 0.31, green: 0.44, blue: 0.64)),
            ("teal", Color(red: 0.22, green: 0.48, blue: 0.48)),
            ("gray", Color(red: 0.58, green: 0.58, blue: 0.58)),
            ("grey", Color(red: 0.58, green: 0.58, blue: 0.58)),
            ("pink", Color(red: 0.88, green: 0.66, blue: 0.70)),
            ("rust", Color(red: 0.70, green: 0.36, blue: 0.22)),
            ("wine", Color(red: 0.44, green: 0.15, blue: 0.22)),
            ("gold", Color(red: 0.78, green: 0.63, blue: 0.30)),
            ("red", Color(red: 0.70, green: 0.22, blue: 0.20)),
            ("tan", Color(red: 0.80, green: 0.68, blue: 0.52)),
        ]
        return table.first { needle.contains($0.0) }?.1
    }
}

// MARK: - Flow layout

/// Left-aligned wrapping layout for pills/swatches (CSS `flex-wrap` with a
/// uniform gap — same arrangement as `ChipFlowLayout` in `StyleStepView`).
struct PillFlowLayout: Layout {
    var spacing: CGFloat = 6

    func sizeThatFits(proposal: ProposedViewSize, subviews: Subviews, cache: inout ()) -> CGSize {
        arrangement(proposal: proposal, subviews: subviews).size
    }

    func placeSubviews(in bounds: CGRect, proposal: ProposedViewSize, subviews: Subviews, cache: inout ()) {
        let positions = arrangement(proposal: proposal, subviews: subviews).positions
        for (subview, position) in zip(subviews, positions) {
            subview.place(
                at: CGPoint(x: bounds.minX + position.x, y: bounds.minY + position.y),
                proposal: .unspecified
            )
        }
    }

    private func arrangement(proposal: ProposedViewSize, subviews: Subviews) -> (size: CGSize, positions: [CGPoint]) {
        let maxWidth = proposal.width ?? .infinity
        var positions: [CGPoint] = []
        var x: CGFloat = 0
        var y: CGFloat = 0
        var rowHeight: CGFloat = 0
        var totalWidth: CGFloat = 0

        for subview in subviews {
            let size = subview.sizeThatFits(.unspecified)
            if x > 0, x + size.width > maxWidth {
                x = 0
                y += rowHeight + spacing
                rowHeight = 0
            }
            positions.append(CGPoint(x: x, y: y))
            rowHeight = max(rowHeight, size.height)
            totalWidth = max(totalWidth, x + size.width)
            x += size.width + spacing
        }

        return (CGSize(width: totalWidth, height: y + rowHeight), positions)
    }
}

// MARK: - Previews

#if DEBUG
extension StyleDna {
    /// Sample DNA for previews, matching the synthesis prompt's shape.
    static let previewSample = StyleDna(
        aesthetic: StyleDnaAesthetic(primary: "quiet luxury", secondary: ["minimal", "smart casual"], confidence: 0.82),
        colorPalette: StyleDnaColorPalette(
            dominant: ["navy", "cream", "charcoal"],
            accent: ["camel", "burgundy"],
            avoids: ["neon green"],
            confidence: 0.74
        ),
        patterns: StyleDnaPatterns(preferred: ["solid", "subtle stripe"], confidence: 0.55),
        silhouette: StyleDnaSilhouette(preference: "tailored", confidence: 0.68),
        formalityBias: StyleDnaFormalityBias(level: 1.8, label: "smart-casual", confidence: 0.71),
        occasions: StyleDnaOccasions(primary: ["work", "dinner"], confidence: 0.66),
        behaviourWeights: [:]
    )
}

extension [DetectedWardrobeItem] {
    static let previewSample: [DetectedWardrobeItem] = [
        DetectedWardrobeItem(
            category: "top", subcategory: "oxford shirt", colorPrimary: "white",
            colorSecondary: nil, pattern: "solid", occasion: ["work"],
            season: ["all"], confidence: 0.91, boundingRegion: "upper body"
        ),
        DetectedWardrobeItem(
            category: "bottom", subcategory: "chinos", colorPrimary: "navy",
            colorSecondary: nil, pattern: "solid", occasion: ["casual"],
            season: ["all"], confidence: 0.84, boundingRegion: "lower body"
        ),
        DetectedWardrobeItem(
            category: "outerwear", subcategory: "overcoat", colorPrimary: "camel",
            colorSecondary: "brown", pattern: "solid", occasion: ["work", "dinner"],
            season: ["fall", "winter"], confidence: 0.52, boundingRegion: "upper body"
        ),
        DetectedWardrobeItem(
            category: "shoes", subcategory: "loafers", colorPrimary: "brown",
            colorSecondary: nil, pattern: nil, occasion: ["work"],
            season: ["all"], confidence: 0.77, boundingRegion: "feet"
        ),
    ]
}

#Preview("Results") {
    let response = StyleDnaUploadResponse(
        photosProcessed: 4,
        photosSkipped: 1,
        wardrobeItemsSeeded: 4,
        styleDna: .previewSample,
        photos: []
    )
    ScrollView {
        ResultsView(
            model: .previewCompleted(response: response, items: .previewSample),
            onContinue: {}
        )
        .padding(28)
    }
    .background(Theme.bg)
}

#Preview("Results — extraction failed") {
    let response = StyleDnaUploadResponse(
        photosProcessed: 3,
        photosSkipped: 0,
        wardrobeItemsSeeded: 0,
        styleDna: nil,
        photos: []
    )
    ScrollView {
        ResultsView(
            model: .previewCompleted(response: response, items: []),
            onContinue: {}
        )
        .padding(28)
    }
    .background(Theme.bg)
}
#endif
