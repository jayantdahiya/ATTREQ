//
//  StylePreferencesSheet.swift
//  ATTREQ
//
//  Style-preferences editor sheet for the Profile preferences card (M5-WP1).
//  Same content language as the registration style step (artboard 03):
//  keyword chips + an occasions underline input, prefilled by splitting a
//  PLAIN `style_preferences` string on ", " (`StylePreferencesValue`) — parts
//  matching the keyword set select chips, the rest rejoin as the occasions
//  text. A DNA-owned value (see below) is never prefilled.
//
//  BACKEND OWNERSHIP — this field does NOT round-trip: the backend column
//  `users.style_preferences` is DNA-OWNED (the Style DNA service stores
//  `json.dumps(style_dna)` there and `GET /users/me` returns it verbatim).
//  Today `PUT /users/me` (backend `UserUpdate`,
//  apps/api/src/attreq_api/schemas/user.py) declares no `style_preferences`
//  field, so Pydantic silently drops the key — but if the backend ever
//  accepted it, a chip-string PUT would OVERWRITE the user's Style DNA blob;
//  accepting chip preferences server-side needs a separate column. Policy:
//  - loaded value was a plain chip string → best-effort PUT (same policy as
//    `AppSession.register`); failures never block dismissal,
//  - loaded value was the DNA JSON → the PUT is skipped entirely and the
//    sheet shows a local "Saved on this device only" echo instead.
//

import os
import SwiftUI

struct StylePreferencesSheet: View {
    @Environment(AppSession.self) private var session
    @Environment(\.dismiss) private var dismiss

    /// Kept in sync with `RegisterViewModel.styleOptions` (artboard 03).
    /// Duplicated locally so the sheet's nonisolated parsing needs no hop
    /// into the @MainActor register model.
    private static let styleOptions = [
        "Minimal", "Earthy", "Tailored", "Layered", "Casual", "Formal", "Streetwear", "Athleisure",
    ]

    @State private var selectedKeywords: [String]
    @State private var occasions: String
    @State private var isSaving = false
    /// "Saved on this device only" echo shown when the loaded value was the
    /// DNA JSON and the PUT is therefore skipped (see header).
    @State private var localOnlyHint: String?

    /// True when the loaded `style_preferences` was the Style DNA JSON — the
    /// save must never PUT over the DNA blob (see header).
    private let loadedValueIsDnaOwned: Bool

    private let logger = Logger(subsystem: "com.attreq.ios", category: "StylePreferencesSheet")

    /// Prefills from a PLAIN stored `style_preferences` string; a DNA-owned
    /// (JSON) value starts blank (see header).
    init(current: String?) {
        let value = StylePreferencesValue.parse(current)
        loadedValueIsDnaOwned = value.isDnaOwned
        let parts = value.prefillParts
        _selectedKeywords = State(initialValue: parts.filter { Self.styleOptions.contains($0) })
        _occasions = State(initialValue: parts.filter { !Self.styleOptions.contains($0) }
            .joined(separator: ", "))
    }

    var body: some View {
        ZStack {
            Theme.bg.ignoresSafeArea()

            ScrollView(showsIndicators: false) {
                VStack(alignment: .leading, spacing: 0) {
                    MonoLabel("Preferences — Style", color: Theme.accent)
                        .padding(.bottom, 8)

                    Text("Refine your aesthetic.")
                        .font(.attreqDisplay(26))
                        .foregroundStyle(Theme.text)
                        .padding(.bottom, 6)

                    BodyText("Keywords steer what we suggest each morning.", size: 13)
                        .padding(.bottom, 20)

                    styleCard

                    AttreqPrimaryButton(
                        "Save preferences",
                        role: .accent,
                        isLoading: isSaving,
                        action: save
                    )
                    .padding(.top, 16)

                    if let localOnlyHint {
                        BodyText(localOnlyHint, size: 12, color: Theme.t2)
                            .frame(maxWidth: .infinity, alignment: .center)
                            .padding(.top, 10)
                    }
                }
                .padding(.horizontal, 28)
                .padding(.top, 28)
                .padding(.bottom, 24)
            }
            .scrollBounceBehavior(.basedOnSize)
        }
        .presentationDetents([.medium, .large])
        .presentationDragIndicator(.visible)
    }

    // MARK: Card (chips + occasions, per StyleStepView)

    private var styleCard: some View {
        VStack(alignment: .leading, spacing: 0) {
            MonoLabel("Style keywords")
                .padding(.bottom, 14)

            ChipFlowLayout(spacing: 7) {
                ForEach(Self.styleOptions, id: \.self) { keyword in
                    AttreqChip(keyword, selected: selectedKeywords.contains(keyword)) {
                        toggleKeyword(keyword)
                    }
                }
            }
            .padding(.bottom, 20)

            Rectangle()
                .fill(Theme.borderSoft)
                .frame(height: 1)
                .padding(.bottom, 20)

            AttreqUnderlineInput(label: "Occasions (optional)", text: $occasions)
        }
        .attreqCard(padding: 20)
    }

    private func toggleKeyword(_ keyword: String) {
        if let index = selectedKeywords.firstIndex(of: keyword) {
            selectedKeywords.remove(at: index)
        } else {
            selectedKeywords.append(keyword)
        }
    }

    // MARK: Save

    /// Best-effort `PUT /users/me` (see the ownership note in the header):
    /// a failed PUT is logged, never surfaced, and the sheet still dismisses
    /// after a best-effort `refreshUser()`.
    ///
    /// When the loaded value was the Style DNA JSON the PUT is skipped
    /// entirely — simplest safe behavior, since a backend that accepted
    /// `style_preferences` would have this request overwrite the DNA blob —
    /// and a "Saved on this device only" echo is shown before dismissal.
    private func save() {
        guard !isSaving else { return }
        if loadedValueIsDnaOwned {
            isSaving = true
            localOnlyHint = "Saved on this device only"
            Task {
                defer { isSaving = false }
                // Brief pause so the echo is visible before the sheet goes.
                try? await Task.sleep(for: .seconds(1.2))
                dismiss()
            }
            return
        }
        isSaving = true
        Task {
            defer { isSaving = false }
            var parts = selectedKeywords
            let trimmedOccasions = occasions.trimmingCharacters(in: .whitespacesAndNewlines)
            if !trimmedOccasions.isEmpty {
                parts.append(trimmedOccasions)
            }
            let body = StylePreferencesBody(
                stylePreferences: parts.isEmpty ? nil : parts.joined(separator: ", ")
            )
            do {
                let _: User = try await session.api.request(
                    Endpoint(method: .put, path: "users/me", body: .json(body))
                )
            } catch {
                logger.error("save: PUT /users/me failed (best-effort): \(String(describing: error))")
            }
            try? await session.refreshUser()
            dismiss()
        }
    }
}

/// `PUT /users/me` body carrying only `style_preferences` (encoded snake_case
/// by `APIClient`). Nil is omitted per the endpoint's `exclude_unset` model.
private struct StylePreferencesBody: Encodable, Sendable {
    var stylePreferences: String?
}

// MARK: - Flow layout

/// Left-aligned wrapping chip layout — same arrangement as the registration
/// style step's private `ChipFlowLayout` (StyleStepView.swift).
private struct ChipFlowLayout: Layout {
    var spacing: CGFloat = 7

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

#Preview("Style preferences sheet") {
    Theme.bg.ignoresSafeArea()
        .sheet(isPresented: .constant(true)) {
            StylePreferencesSheet(current: "Minimal, Earthy, Layered, weekend dinners")
                .environment(AppSession())
        }
}
