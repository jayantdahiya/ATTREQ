//
//  StyleDnaProfileView.swift
//  ATTREQ
//
//  Style DNA profile screen (M3-WP3). No artboard exists — composed in the
//  redesign-v2 language (back circle + mono header per artboard 09, serif
//  italic headline, card, mono labels, pills, swatches). Behavioral
//  reference: RN `app/(protected)/style-dna/profile.tsx` + `StyleDnaCard`.
//
//  Backend truth (see StyleDnaRepository): there is no per-photo delete —
//  DELETE /users/style-dna/photos removes ALL seed photos, so the grid
//  carries a single "Remove all photos" action instead of per-tile deletes.
//

import SwiftUI

struct StyleDnaProfileView: View {
    @Environment(AppSession.self) private var session
    @Environment(\.dismiss) private var dismiss

    @State private var viewModel: StyleDnaProfileViewModel?
    @State private var showRegenerateConfirm = false
    @State private var showDeletePhotosConfirm = false

    /// `viewModel` is normally built on first appearance from the session's
    /// API client (same pattern as `MainTabsView`); previews inject one.
    init(viewModel: StyleDnaProfileViewModel? = nil) {
        _viewModel = State(initialValue: viewModel)
    }

    var body: some View {
        ZStack {
            Theme.bg.ignoresSafeArea()

            VStack(spacing: 0) {
                header
                    .padding(.horizontal, 28)
                    .padding(.top, 8)
                    .padding(.bottom, 18)

                if let viewModel {
                    content(viewModel)
                } else {
                    Spacer()
                }
            }
        }
        .task {
            if viewModel == nil {
                viewModel = StyleDnaProfileViewModel(
                    repository: StyleDnaRepository(apiClient: session.api)
                )
            }
            await viewModel?.load()
        }
        .confirmationDialog(
            "Regenerate Style DNA",
            isPresented: $showRegenerateConfirm,
            titleVisibility: .visible
        ) {
            Button("Regenerate") {
                Task { await viewModel?.regenerate() }
            }
            Button("Cancel", role: .cancel) {}
        } message: {
            Text("Re-run synthesis from your existing photos?")
        }
        .confirmationDialog(
            "Remove all photos",
            isPresented: $showDeletePhotosConfirm,
            titleVisibility: .visible
        ) {
            Button("Remove All", role: .destructive) {
                Task { await viewModel?.deleteAllPhotos() }
            }
            Button("Cancel", role: .cancel) {}
        } message: {
            Text("Seed photos are stored as a set — this removes all of them. Your current Style DNA stays until you upload new photos.")
        }
    }

    // MARK: - Header (artboard-09 pattern: back circle + mono label)

    private var header: some View {
        HStack(spacing: 10) {
            Button {
                dismiss()
            } label: {
                Circle()
                    .strokeBorder(Theme.border, lineWidth: 1)
                    .frame(width: 30, height: 30)
                    .overlay(AttreqIcon.back.view(size: 14, color: Theme.t2))
                    .contentShape(Circle())
            }
            .buttonStyle(.plain)
            .accessibilityLabel("Back")
            .accessibilityIdentifier("button-back")

            MonoLabel("Style DNA")

            Spacer()
        }
    }

    // MARK: - States

    @ViewBuilder
    private func content(_ viewModel: StyleDnaProfileViewModel) -> some View {
        switch viewModel.state {
        case .loading:
            loadingState
        case .failed(let message):
            errorState(message, viewModel: viewModel)
        case .loaded(let profile):
            if let dna = profile.styleDna {
                loadedState(dna: dna, photos: profile.photos, viewModel: viewModel)
            } else {
                emptyState(viewModel, photos: profile.photos)
            }
        }
    }

    private var loadingState: some View {
        VStack(spacing: 14) {
            Spacer()
            ProgressView()
                .tint(Theme.t2)
            MonoLabel("Loading your style profile")
            Spacer()
        }
        .frame(maxWidth: .infinity)
    }

    /// Clay error treatment with a retry CTA (initial load failed).
    private func errorState(_ message: String, viewModel: StyleDnaProfileViewModel) -> some View {
        VStack(spacing: 18) {
            Spacer()
            MonoLabel("Something went wrong", size: 11, color: Theme.clay)
            errorBanner(message)
            AttreqPrimaryButton("Try Again") {
                Task { await viewModel.load() }
            }
            .padding(.horizontal, 36)
            Spacer()
        }
        .padding(.horizontal, 28)
    }

    /// No Style DNA yet (mirrors RN's `!data?.style_dna` branch). The
    /// regenerate CTA only renders with >= 3 stored seed photos — the backend
    /// 422s regenerate below that, and this screen has no photo upload until
    /// the Profile wiring lands in M5.
    private func emptyState(_ viewModel: StyleDnaProfileViewModel, photos: [StyleDnaPhoto]) -> some View {
        VStack(spacing: 12) {
            Spacer()
            MonoLabel("No Style DNA yet", size: 11)
            BodyText(
                "No Style DNA profile yet. Upload some outfit photos to get started — we'll read your aesthetic and build your profile.",
                size: 13
            )
            .multilineTextAlignment(.center)
            if let actionError = viewModel.actionError {
                errorBanner(actionError)
            }
            if photos.count >= OnboardingViewModel.minPhotos {
                AttreqPrimaryButton(
                    "Regenerate Style DNA",
                    role: .accent,
                    isLoading: viewModel.isRegenerating
                ) {
                    showRegenerateConfirm = true
                }
                .padding(.top, 12)
            } else {
                MonoLabel("Regenerate needs 3+ stored photos", size: 9)
                    .padding(.top, 12)
                BodyText(
                    "Photo upload returns here with the Profile wiring in M5. Until then, Style DNA is built from the photos you add during onboarding.",
                    size: 12
                )
                .multilineTextAlignment(.center)
            }
            Spacer()
        }
        .padding(.horizontal, 28)
    }

    // MARK: - Loaded

    private func loadedState(
        dna: StyleDna,
        photos: [StyleDnaPhoto],
        viewModel: StyleDnaProfileViewModel
    ) -> some View {
        ScrollView(showsIndicators: false) {
            VStack(alignment: .leading, spacing: 0) {
                headline
                    .padding(.bottom, 18)

                if let actionError = viewModel.actionError {
                    errorBanner(actionError)
                        .padding(.bottom, 14)
                }

                dnaCard(dna)
                    .padding(.bottom, 24)

                photosSection(photos, viewModel: viewModel)

                AttreqPrimaryButton(
                    "Regenerate Style DNA",
                    role: .accent,
                    isLoading: viewModel.isRegenerating
                ) {
                    showRegenerateConfirm = true
                }
                .padding(.top, 26)
            }
            .padding(.horizontal, 28)
            .padding(.bottom, 40)
        }
        .refreshable { await viewModel.load() }
    }

    /// Serif display headline in the artboard-09 voice
    /// ("Show us / *your style.*" → "Your style, / *decoded.*").
    private var headline: some View {
        VStack(alignment: .leading, spacing: 0) {
            Text("Your style,")
                .font(.attreqDisplay(34, weight: .semiBold))
                .foregroundStyle(Theme.text)
            Text("decoded.")
                .font(.attreqDisplay(34, weight: .semiBold, italic: true))
                .foregroundStyle(Theme.accent)
        }
    }

    // MARK: - DNA card

    private func dnaCard(_ dna: StyleDna) -> some View {
        VStack(alignment: .leading, spacing: 14) {
            aestheticSection(dna.aesthetic)
            hairline
            paletteSection(dna.colorPalette)
            hairline
            patternsSection(dna.patterns)
            hairline
            silhouetteSection(dna.silhouette)
            hairline
            formalitySection(dna.formalityBias)
            hairline
            occasionsSection(dna.occasions)
        }
        .attreqCard(padding: 18)
    }

    private var hairline: some View {
        Rectangle()
            .fill(Theme.borderSoft)
            .frame(height: 1)
    }

    private func aestheticSection(_ aesthetic: StyleDnaAesthetic) -> some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                MonoLabel("Aesthetic")
                Spacer()
                ConfidenceBadge(confidence: aesthetic.confidence)
            }
            Text(aesthetic.primary.isEmpty ? "—" : aesthetic.primary.capitalized)
                .font(.attreqDisplay(24, weight: .semiBold, italic: true))
                .foregroundStyle(Theme.text)
            if !aesthetic.secondary.isEmpty {
                FlowLayout(spacing: 6) {
                    ForEach(aesthetic.secondary, id: \.self) { label in
                        StaticChip(label.capitalized)
                    }
                }
            }
        }
    }

    private func paletteSection(_ palette: StyleDnaColorPalette) -> some View {
        VStack(alignment: .leading, spacing: 10) {
            MonoLabel("Color Palette")
            swatchRow("Dominant", names: palette.dominant)
            if !palette.accent.isEmpty {
                swatchRow("Accent", names: palette.accent)
            }
            if !palette.avoids.isEmpty {
                swatchRow("Avoids", names: palette.avoids, dimmed: true)
            }
        }
    }

    private func swatchRow(_ label: String, names: [String], dimmed: Bool = false) -> some View {
        VStack(alignment: .leading, spacing: 5) {
            MonoLabel(label, size: 8.5)
            if names.isEmpty {
                MonoLabel("—", size: 9)
            } else {
                FlowLayout(spacing: 9, rowSpacing: 6) {
                    ForEach(names, id: \.self) { name in
                        ColorSwatch(name: name, dimmed: dimmed)
                    }
                }
            }
        }
    }

    private func patternsSection(_ patterns: StyleDnaPatterns) -> some View {
        VStack(alignment: .leading, spacing: 8) {
            MonoLabel("Patterns")
            FlowLayout(spacing: 6) {
                // "Solid" fallback mirrors RN's StyleDnaCard.
                ForEach(patterns.preferred.isEmpty ? ["solid"] : patterns.preferred, id: \.self) { pattern in
                    AttreqPill(pattern)
                }
            }
        }
    }

    private func silhouetteSection(_ silhouette: StyleDnaSilhouette) -> some View {
        VStack(alignment: .leading, spacing: 5) {
            MonoLabel("Silhouette")
            BodyText(silhouette.preference.isEmpty ? "—" : silhouette.preference.capitalized, color: Theme.text)
        }
    }

    private func formalitySection(_ formality: StyleDnaFormalityBias) -> some View {
        VStack(alignment: .leading, spacing: 5) {
            MonoLabel("Formality")
            HStack(spacing: 8) {
                BodyText(formality.label.capitalized, color: Theme.text)
                // RN renders "label (1.8/3)"; the level becomes a pill here.
                AttreqPill(String(format: "%.1f / 3", formality.level), variant: .gold)
            }
        }
    }

    private func occasionsSection(_ occasions: StyleDnaOccasions) -> some View {
        VStack(alignment: .leading, spacing: 8) {
            MonoLabel("Occasions")
            if occasions.primary.isEmpty {
                MonoLabel("—", size: 9)
            } else {
                FlowLayout(spacing: 6) {
                    ForEach(occasions.primary, id: \.self) { occasion in
                        AttreqPill(occasion)
                    }
                }
            }
        }
    }

    // MARK: - Photos

    @ViewBuilder
    private func photosSection(_ photos: [StyleDnaPhoto], viewModel: StyleDnaProfileViewModel) -> some View {
        VStack(alignment: .leading, spacing: 10) {
            MonoLabel("Seed Photos")
            // Mirrors RN's "Based on N seed photo(s)." caption.
            BodyText("Based on \(photos.count) seed photo\(photos.count == 1 ? "" : "s").", size: 13)

            if !photos.isEmpty {
                LazyVGrid(
                    columns: Array(repeating: GridItem(.flexible(), spacing: 9), count: 3),
                    spacing: 9
                ) {
                    ForEach(photos) { photo in
                        photoTile(photo)
                            .opacity(viewModel.isDeletingPhotos ? 0.45 : 1)
                    }
                }

                removeAllPhotosButton(viewModel)
                    .padding(.top, 4)
            }
        }
    }

    /// 3:4 tile, radius 14 — the artboard-09 photo-grid geometry.
    private func photoTile(_ photo: StyleDnaPhoto) -> some View {
        let shape = RoundedRectangle(cornerRadius: 14, style: .continuous)
        return Color.clear
            .aspectRatio(3.0 / 4.0, contentMode: .fit)
            .overlay {
                AsyncImage(url: AppConfig.absoluteMediaURL(photo.fileUrl)) { phase in
                    switch phase {
                    case .success(let image):
                        image
                            .resizable()
                            .scaledToFill()
                    case .failure:
                        AttreqIcon.image.view(size: 16, color: Theme.t3)
                    default:
                        ProgressView()
                            .controlSize(.small)
                            .tint(Theme.t3)
                    }
                }
            }
            .background(Theme.surface)
            .clipShape(shape)
            .overlay(shape.strokeBorder(Theme.border, lineWidth: 1))
            .accessibilityIdentifier("dna-photo-\(photo.id)")
    }

    /// The backend deletes seed photos only as a full set (no per-photo
    /// endpoint), so a single destructive action replaces per-tile deletes.
    private func removeAllPhotosButton(_ viewModel: StyleDnaProfileViewModel) -> some View {
        Button {
            showDeletePhotosConfirm = true
        } label: {
            HStack(spacing: 6) {
                if viewModel.isDeletingPhotos {
                    ProgressView()
                        .controlSize(.small)
                        .tint(Theme.clay)
                } else {
                    AttreqIcon.x.view(size: 12, color: Theme.clay)
                }
                Text("Remove all photos")
                    .font(.attreqBody(13, weight: .medium))
                    .foregroundStyle(Theme.clay)
            }
            .frame(maxWidth: .infinity)
            .padding(.vertical, 11)
            .background(Capsule().strokeBorder(Theme.border, lineWidth: 1))
            .contentShape(Capsule())
        }
        .buttonStyle(.plain)
        .disabled(viewModel.isDeletingPhotos)
        .accessibilityIdentifier("button-Remove all photos")
    }

    // MARK: - Error banner (wardrobe treatment)

    private func errorBanner(_ message: String) -> some View {
        BodyText(message, size: 13, color: Theme.clay)
            .frame(maxWidth: .infinity, alignment: .leading)
            .padding(.vertical, 10)
            .padding(.horizontal, 13)
            .background(Theme.claySoft, in: RoundedRectangle(cornerRadius: 12, style: .continuous))
    }
}

// MARK: - Static chip

/// Non-interactive twin of `AttreqChip`'s unselected look, for read-only
/// metadata (secondary aesthetics) where a toggle button would be wrong.
private struct StaticChip: View {
    let label: String

    init(_ label: String) {
        self.label = label
    }

    var body: some View {
        Text(label)
            .font(.attreqBody(13, weight: .medium))
            .foregroundStyle(Theme.t2)
            .padding(.vertical, 6)
            .padding(.horizontal, 14)
            .background(Capsule().strokeBorder(Theme.border, lineWidth: 1))
    }
}

// MARK: - Color swatch

/// Small rounded color square + mono name, resolved from the synthesis
/// palette's color NAME (e.g. "camel", "light blue").
private struct ColorSwatch: View {
    let name: String
    var dimmed = false

    var body: some View {
        HStack(spacing: 5) {
            RoundedRectangle(cornerRadius: 5, style: .continuous)
                .fill(SwatchPalette.color(named: name))
                .frame(width: 16, height: 16)
                .overlay(
                    RoundedRectangle(cornerRadius: 5, style: .continuous)
                        .strokeBorder(Theme.border, lineWidth: 1)
                )
                .opacity(dimmed ? 0.45 : 1)
            Text(name.lowercased())
                .font(.attreqMono(9))
                .foregroundStyle(Theme.t2)
        }
        .accessibilityElement(children: .combine)
        .accessibilityLabel(name)
    }
}

/// Name → display-color table for palette swatches. Longest matching key
/// wins ("light blue" beats "blue"); unknown names fall back to a neutral
/// stone so the swatch never renders invisibly.
private enum SwatchPalette {
    static func color(named name: String) -> Color {
        let key = name.lowercased().trimmingCharacters(in: .whitespacesAndNewlines)
        if let exact = table.first(where: { $0.key == key }) {
            return exact.color
        }
        let best = table
            .filter { key.contains($0.key) }
            .max { $0.key.count < $1.key.count }
        return best?.color ?? fallback
    }

    private static let fallback = rgb(0xA19A91)

    private static let table: [(key: String, color: Color)] = [
        ("black", rgb(0x1C1917)), ("charcoal", rgb(0x3A3733)),
        ("grey", rgb(0x8A857E)), ("gray", rgb(0x8A857E)), ("silver", rgb(0xB9B6B0)),
        ("white", rgb(0xFAF8F5)), ("off-white", rgb(0xF5F2EA)), ("off white", rgb(0xF5F2EA)),
        ("cream", rgb(0xF1E8D8)), ("ivory", rgb(0xF6F0E1)), ("ecru", rgb(0xEADFC8)),
        ("oatmeal", rgb(0xE4DCC9)), ("stone", rgb(0xC9C2B6)), ("beige", rgb(0xD9C9AF)),
        ("sand", rgb(0xD9C39A)), ("tan", rgb(0xC8A97D)), ("camel", rgb(0xB98F62)),
        ("caramel", rgb(0xB07B4F)), ("khaki", rgb(0xA79A6E)), ("taupe", rgb(0xA99C8F)),
        ("brown", rgb(0x7A5C43)), ("chocolate", rgb(0x5A4232)), ("coffee", rgb(0x6B4F3B)),
        ("espresso", rgb(0x4A362A)),
        ("olive", rgb(0x6E6F45)), ("sage", rgb(0xA3B29A)), ("mint", rgb(0xA9D3B5)),
        ("forest", rgb(0x3C5941)), ("emerald", rgb(0x2E7D5B)), ("green", rgb(0x567A5B)),
        ("teal", rgb(0x3D7A78)), ("turquoise", rgb(0x53B0AE)),
        ("navy", rgb(0x27364D)), ("light blue", rgb(0xA3C2DC)), ("sky blue", rgb(0xA3C2DC)),
        ("denim", rgb(0x5D7A9B)), ("cobalt", rgb(0x2E5AA8)), ("indigo", rgb(0x3F4470)),
        ("blue", rgb(0x4A6FA5)),
        ("lavender", rgb(0xA99BC6)), ("lilac", rgb(0xC1AED4)), ("purple", rgb(0x6F5A93)),
        ("plum", rgb(0x6E4560)), ("mauve", rgb(0xA8848E)),
        ("burgundy", rgb(0x6E2B33)), ("maroon", rgb(0x6B2B36)), ("wine", rgb(0x703043)),
        ("red", rgb(0xB03A2E)), ("crimson", rgb(0xA5273B)),
        ("rust", rgb(0xA65432)), ("terracotta", rgb(0xC2664A)), ("coral", rgb(0xE0796A)),
        ("salmon", rgb(0xE8927C)), ("peach", rgb(0xEFC4A6)), ("apricot", rgb(0xE8A96B)),
        ("orange", rgb(0xD08434)),
        ("mustard", rgb(0xC99A34)), ("gold", rgb(0xC4A24E)), ("yellow", rgb(0xE4C24E)),
        ("blush", rgb(0xE7B9B4)), ("pink", rgb(0xD998A7)), ("rose", rgb(0xC97A85)),
        ("fuchsia", rgb(0xB74A8C)), ("magenta", rgb(0xB0368C)),
    ]

    private static func rgb(_ hex: UInt32) -> Color {
        Color(
            red: Double((hex >> 16) & 0xFF) / 255,
            green: Double((hex >> 8) & 0xFF) / 255,
            blue: Double(hex & 0xFF) / 255
        )
    }
}

// MARK: - Flow layout

/// Minimal leading-aligned wrap layout for chips/pills/swatches.
private struct FlowLayout: Layout {
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

private extension StyleDnaProfileResponse {
    static let fixture = StyleDnaProfileResponse(
        styleDna: StyleDna(
            aesthetic: StyleDnaAesthetic(
                primary: "quiet luxury",
                secondary: ["minimalist", "smart casual"],
                confidence: 0.87
            ),
            colorPalette: StyleDnaColorPalette(
                dominant: ["cream", "camel", "charcoal", "navy"],
                accent: ["rust", "sage"],
                avoids: ["neon green", "fuchsia"],
                confidence: 0.74
            ),
            patterns: StyleDnaPatterns(preferred: ["solid", "subtle stripe"], confidence: 0.66),
            silhouette: StyleDnaSilhouette(preference: "tailored", confidence: 0.71),
            formalityBias: StyleDnaFormalityBias(level: 1.8, label: "smart-casual", confidence: 0.79),
            occasions: StyleDnaOccasions(primary: ["office", "dinner", "weekend"], confidence: 0.62),
            behaviourWeights: [:]
        ),
        photos: (1...4).map { index in
            StyleDnaPhoto(
                id: "photo-\(index)",
                userId: "user-1",
                filePath: "uploads/style_dna/photo-\(index).jpg",
                fileUrl: "/uploads/style_dna/photo-\(index).jpg",
                qualityOk: true,
                qualityReason: nil,
                perPhotoExtraction: nil,
                createdAt: .now
            )
        }
    )
}

@MainActor
private func previewViewModel(_ state: StyleDnaProfileViewModel.LoadState) -> StyleDnaProfileViewModel {
    let auth = AuthSession(keychain: KeychainStore(), baseURL: AppConfig.apiBaseURL)
    let client = APIClient(baseURL: AppConfig.apiBaseURL, authSession: auth)
    return StyleDnaProfileViewModel(
        repository: StyleDnaRepository(apiClient: client),
        initialState: state
    )
}

#Preview("Loaded") {
    StyleDnaProfileView(viewModel: previewViewModel(.loaded(.fixture)))
        .environment(AppSession())
}

#Preview("Empty") {
    StyleDnaProfileView(
        viewModel: previewViewModel(.loaded(StyleDnaProfileResponse(styleDna: nil, photos: [])))
    )
    .environment(AppSession())
}

#Preview("Error") {
    StyleDnaProfileView(
        viewModel: previewViewModel(.failed("Can't reach ATTREQ. Check your connection."))
    )
    .environment(AppSession())
}
