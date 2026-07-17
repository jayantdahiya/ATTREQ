//
//  StyleDnaEditSheet.swift
//  ATTREQ
//
//  Style DNA correction sheet (M5-WP2, deferred from M3). No artboard and no
//  RN precedent exist — composed in the redesign-v2 language (mono header,
//  serif italic headline, card with hairline-separated sections, chips,
//  accent CTA).
//
//  Scope is deliberately narrow: the three facets a user can meaningfully
//  correct by hand — aesthetic primary (single-select), aesthetic secondary
//  (multi-select), and formality (three-step). Colors/patterns/silhouette
//  stay synthesis-owned.
//
//  Backend truth (endpoints/style_dna.py): PATCH /users/style-dna takes
//  {"corrections": {...}} and DEEP-MERGES it into the stored profile, so only
//  changed subtrees are sent and confidence values are never included — the
//  stored ones survive the merge untouched.
//

import SwiftUI

// MARK: - Formality choice

/// The edit sheet's three-step formality control, mapped onto the backend's
/// `formality_bias` shape (`level` 0–3 Double + `label` string; vocabulary
/// `athletic|casual|smart-casual|business|formal` — see `StyleDnaFormalityBias`).
enum StyleDnaFormalityChoice: CaseIterable, Equatable {
    case casual
    case smartCasual
    case formal

    /// Backend `formality_bias.label` value.
    var label: String {
        switch self {
        case .casual: "casual"
        case .smartCasual: "smart-casual"
        case .formal: "formal"
        }
    }

    /// Backend `formality_bias.level` value. The numeric anchors are
    /// 0 = athletic, 1 = casual, 2 = business, 3 = formal (see
    /// `services/style_dna/prompts.py`; `scoring.py` reads `level` as the
    /// numeric formality target) — so smart-casual sits midway between
    /// casual (1) and business (2).
    var level: Double {
        switch self {
        case .casual: 1
        case .smartCasual: 1.5
        case .formal: 3
        }
    }

    /// Chip title.
    var display: String {
        switch self {
        case .casual: "Casual"
        case .smartCasual: "Smart-casual"
        case .formal: "Formal"
        }
    }

    /// Pre-selection from the profile's current label; labels outside the
    /// three-step vocabulary ("athletic", "business") map to no selection —
    /// the facet then only counts as changed once the user picks a step.
    init?(label: String) {
        guard let match = Self.allCases.first(where: { $0.label == label }) else { return nil }
        self = match
    }
}

// MARK: - Corrections builder

/// Pure diff → corrections-payload builder, kept off the view so the payload
/// contract is unit-testable. Produces snake_case keys (dictionary keys pass
/// through `JSONEncoder` verbatim — see `StyleDnaCorrection`), only for
/// facets that actually changed, and never includes confidence values.
enum StyleDnaCorrectionsBuilder {
    /// - Parameters:
    ///   - original: the profile the sheet was opened with.
    ///   - primary: currently selected primary aesthetic.
    ///   - secondary: currently selected secondary aesthetics; compared as a
    ///     SET, so a pure reorder is not a change.
    ///   - formality: current three-step selection, `nil` when the profile's
    ///     label sits outside the vocabulary and the user hasn't picked one.
    ///     Compared by LABEL — reselecting the current label is not a change
    ///     even though the stored level may be fractional (e.g. 1.8).
    static func build(
        original: StyleDna,
        primary: String,
        secondary: [String],
        formality: StyleDnaFormalityChoice?
    ) -> [String: JSONValue] {
        var corrections: [String: JSONValue] = [:]

        var aesthetic: [String: JSONValue] = [:]
        if primary != original.aesthetic.primary {
            aesthetic["primary"] = .string(primary)
        }
        if Set(secondary) != Set(original.aesthetic.secondary) {
            aesthetic["secondary"] = .array(secondary.map(JSONValue.string))
        }
        if !aesthetic.isEmpty {
            corrections["aesthetic"] = .object(aesthetic)
        }

        if let formality, formality.label != original.formalityBias.label {
            corrections["formality_bias"] = .object([
                "level": .number(formality.level),
                "label": .string(formality.label),
            ])
        }

        return corrections
    }
}

// MARK: - Sheet

/// Full-height sheet for correcting the three editable Style DNA facets.
/// Presented from `StyleDnaProfileView`'s DNA-card "Edit" affordance; saving
/// goes through `StyleDnaProfileViewModel.applyCorrections`, which replaces
/// the profile state with the server's echo — success dismisses, failure
/// keeps the sheet open with an inline clay banner.
struct StyleDnaEditSheet: View {
    @Environment(\.dismiss) private var dismiss

    let viewModel: StyleDnaProfileViewModel
    /// Snapshot of the profile the sheet was opened with (diff baseline).
    let dna: StyleDna

    @State private var primary: String
    @State private var secondary: [String]
    @State private var formality: StyleDnaFormalityChoice?

    /// Chip vocabulary: the curated aesthetics plus whatever the profile
    /// currently holds (primary AND secondary), so every current value is
    /// representable and stays pre-selected even off-vocabulary
    /// (e.g. "quiet luxury").
    private let vocabulary: [String]

    private static let curatedAesthetics = [
        "minimalist", "classic", "casual", "streetwear",
        "formal", "bohemian", "sporty", "eclectic",
    ]

    init(viewModel: StyleDnaProfileViewModel, dna: StyleDna) {
        self.viewModel = viewModel
        self.dna = dna

        var vocabulary = Self.curatedAesthetics
        for extra in [dna.aesthetic.primary] + dna.aesthetic.secondary
        where !extra.isEmpty && !vocabulary.contains(extra) {
            vocabulary.append(extra)
        }
        self.vocabulary = vocabulary

        _primary = State(initialValue: dna.aesthetic.primary)
        _secondary = State(initialValue: dna.aesthetic.secondary)
        _formality = State(initialValue: StyleDnaFormalityChoice(label: dna.formalityBias.label))
    }

    var body: some View {
        ZStack {
            Theme.bg.ignoresSafeArea()

            VStack(spacing: 0) {
                header
                    .padding(.horizontal, 28)
                    .padding(.top, 22)
                    .padding(.bottom, 16)

                ScrollView(showsIndicators: false) {
                    VStack(alignment: .leading, spacing: 0) {
                        headline
                            .padding(.bottom, 18)

                        editCard
                            .padding(.bottom, 20)

                        if let saveError = viewModel.saveError {
                            errorBanner(saveError)
                                .padding(.bottom, 14)
                        }

                        AttreqPrimaryButton(
                            "Save changes",
                            role: .accent,
                            isLoading: viewModel.isSaving
                        ) {
                            save()
                        }
                    }
                    .padding(.horizontal, 28)
                    .padding(.bottom, 40)
                }
            }
        }
        .presentationDetents([.large])
        .interactiveDismissDisabled(viewModel.isSaving)
        .onAppear { viewModel.clearSaveError() }
    }

    // MARK: - Header

    private var header: some View {
        HStack {
            MonoLabel("Edit Style DNA")
            Spacer()
            Button {
                dismiss()
            } label: {
                Text("Cancel")
                    .font(.attreqBody(13, weight: .medium))
                    .foregroundStyle(Theme.t2)
                    .contentShape(Rectangle())
            }
            .buttonStyle(.plain)
            .disabled(viewModel.isSaving)
            .accessibilityIdentifier("button-Cancel")
        }
    }

    /// Serif display headline in the artboard-09 voice.
    private var headline: some View {
        VStack(alignment: .leading, spacing: 0) {
            Text("Refine")
                .font(.attreqDisplay(34, weight: .semiBold))
                .foregroundStyle(Theme.text)
            Text("your DNA.")
                .font(.attreqDisplay(34, weight: .semiBold, italic: true))
                .foregroundStyle(Theme.accent)
        }
    }

    // MARK: - Edit card

    private var editCard: some View {
        VStack(alignment: .leading, spacing: 16) {
            primarySection
            hairline
            secondarySection
            hairline
            formalitySection
        }
        .attreqCard(padding: 18)
    }

    private var hairline: some View {
        Rectangle()
            .fill(Theme.borderSoft)
            .frame(height: 1)
    }

    private var primarySection: some View {
        VStack(alignment: .leading, spacing: 10) {
            MonoLabel("Aesthetic — Primary")
            ChipFlowLayout(spacing: 6) {
                ForEach(vocabulary, id: \.self) { option in
                    AttreqChip(option.capitalized, selected: option == primary) {
                        selectPrimary(option)
                    }
                }
            }
        }
    }

    private var secondarySection: some View {
        VStack(alignment: .leading, spacing: 10) {
            MonoLabel("Aesthetic — Secondary")
            ChipFlowLayout(spacing: 6) {
                ForEach(vocabulary.filter { $0 != primary }, id: \.self) { option in
                    AttreqChip(option.capitalized, selected: secondary.contains(option)) {
                        toggleSecondary(option)
                    }
                }
            }
        }
    }

    private var formalitySection: some View {
        VStack(alignment: .leading, spacing: 10) {
            MonoLabel("Formality")
            ChipFlowLayout(spacing: 6) {
                ForEach(StyleDnaFormalityChoice.allCases, id: \.self) { choice in
                    AttreqChip(choice.display, selected: formality == choice) {
                        formality = choice
                    }
                }
            }
        }
    }

    // MARK: - Error banner (wardrobe treatment)

    private func errorBanner(_ message: String) -> some View {
        BodyText(message, size: 13, color: Theme.clay)
            .frame(maxWidth: .infinity, alignment: .leading)
            .padding(.vertical, 10)
            .padding(.horizontal, 13)
            .background(Theme.claySoft, in: RoundedRectangle(cornerRadius: 12, style: .continuous))
    }

    // MARK: - Actions

    /// Primary is single-select; promoting a chip that is currently a
    /// secondary also removes it there (the two lists must stay disjoint —
    /// the secondary vocabulary excludes the primary).
    private func selectPrimary(_ option: String) {
        primary = option
        secondary.removeAll { $0 == option }
    }

    private func toggleSecondary(_ option: String) {
        if let index = secondary.firstIndex(of: option) {
            secondary.remove(at: index)
        } else {
            secondary.append(option)
        }
    }

    private func save() {
        guard !viewModel.isSaving else { return }
        let corrections = StyleDnaCorrectionsBuilder.build(
            original: dna,
            primary: primary,
            secondary: secondary,
            formality: formality
        )
        // Nothing changed — nothing to send; deep-merging an empty dict
        // would be harmless but is a pointless round trip.
        guard !corrections.isEmpty else {
            dismiss()
            return
        }
        Task {
            await viewModel.applyCorrections(corrections)
            if viewModel.saveError == nil {
                dismiss()
            }
        }
    }
}

// MARK: - Flow layout

/// Minimal leading-aligned wrap layout for the chip rows (private twin of the
/// profile screen's `FlowLayout`, which is file-private there).
private struct ChipFlowLayout: Layout {
    var spacing: CGFloat = 6
    var rowSpacing: CGFloat?

    func sizeThatFits(proposal: ProposedViewSize, subviews: Subviews, cache: inout ()) -> CGSize {
        let maxWidth = proposal.width ?? .infinity
        var x: CGFloat = 0
        var y: CGFloat = 0
        var rowHeight: CGFloat = 0
        var widest: CGFloat = 0
        for subview in subviews {
            let size = subview.sizeThatFits(.unspecified)
            if x > 0, x + size.width > maxWidth {
                x = 0
                y += rowHeight + (rowSpacing ?? spacing)
                rowHeight = 0
            }
            x += size.width + spacing
            widest = max(widest, x - spacing)
            rowHeight = max(rowHeight, size.height)
        }
        return CGSize(width: proposal.width ?? widest, height: y + rowHeight)
    }

    func placeSubviews(in bounds: CGRect, proposal: ProposedViewSize, subviews: Subviews, cache: inout ()) {
        var x = bounds.minX
        var y = bounds.minY
        var rowHeight: CGFloat = 0
        for subview in subviews {
            let size = subview.sizeThatFits(.unspecified)
            if x > bounds.minX, x + size.width > bounds.maxX {
                x = bounds.minX
                y += rowHeight + (rowSpacing ?? spacing)
                rowHeight = 0
            }
            subview.place(at: CGPoint(x: x, y: y), anchor: .topLeading, proposal: ProposedViewSize(size))
            x += size.width + spacing
            rowHeight = max(rowHeight, size.height)
        }
    }
}

// MARK: - Previews

private let previewDna = StyleDna(
    aesthetic: StyleDnaAesthetic(
        primary: "quiet luxury",
        secondary: ["minimalist", "classic"],
        confidence: 0.87
    ),
    colorPalette: StyleDnaColorPalette(
        dominant: ["cream", "camel"],
        accent: ["rust"],
        avoids: ["neon green"],
        confidence: 0.74
    ),
    patterns: StyleDnaPatterns(preferred: ["solid"], confidence: 0.66),
    silhouette: StyleDnaSilhouette(preference: "tailored", confidence: 0.71),
    formalityBias: StyleDnaFormalityBias(level: 1.8, label: "smart-casual", confidence: 0.79),
    occasions: StyleDnaOccasions(primary: ["office", "dinner"], confidence: 0.62),
    behaviourWeights: [:]
)

#Preview("Edit sheet") {
    let auth = AuthSession(keychain: KeychainStore(), baseURL: AppConfig.apiBaseURL)
    let client = APIClient(baseURL: AppConfig.apiBaseURL, authSession: auth)
    let viewModel = StyleDnaProfileViewModel(
        repository: StyleDnaRepository(apiClient: client),
        initialState: .loaded(StyleDnaProfileResponse(styleDna: previewDna, photos: []))
    )
    return Color.clear
        .sheet(isPresented: .constant(true)) {
            StyleDnaEditSheet(viewModel: viewModel, dna: previewDna)
        }
}
