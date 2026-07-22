//
//  RejectionReasonSheet.swift
//  ATTREQ
//
//  Rejection-reason sheet (RI-1). Presented from `TodayScreen` — bound to
//  `TodayViewModel.isPresentingRejectionSheet` — whenever the user skips or
//  dismisses a suggestion. Captures WHY as a first-class, optional signal for
//  the recommendation-events preference-pair pipeline
//  (`POST /recommendations/{id}/feedback`, action=rejected); see
//  docs/07-recommendation-intelligence/01-milestone-1-telemetry-eval-harness.md.
//
//  No artboard and no RN precedent exist — composed in the redesign-v2
//  language (mono header, serif italic headline, card with a chip row + note
//  field), matching `StyleDnaEditSheet`'s structure.
//
//  Deliberately "skippable" end-to-end: tapping "Skip" (header) — or
//  swiping the sheet away without picking anything — still calls `onSubmit`
//  with `reason: nil`. A bare rejection is still a valid preference-pair
//  signal, so nothing here silently drops the event. `onSubmit` fires
//  exactly once per presentation (`hasSubmitted` guards the two exit paths:
//  an explicit button tap, and the `onDisappear` swipe-away fallback).
//
//  Only 6 of the 7 backend `RejectionReason` values get a chip; `.other` has
//  no explicit chip and is sent implicitly when the user types a note
//  without selecting one of the six (see `submit(reason:note:)`).
//

import SwiftUI

struct RejectionReasonSheet: View {
    @Environment(\.dismiss) private var dismiss

    /// Called exactly once, right before the sheet closes, with the chosen
    /// reason/note (both `nil` for a bare "Skip" or swipe-away).
    let onSubmit: (RejectionReason?, String?) -> Void

    @State private var selectedReason: RejectionReason?
    @State private var note: String = ""
    @State private var hasSubmitted = false

    private static let chipReasons = RejectionReason.allCases.filter { $0 != .other }

    var body: some View {
        VStack(spacing: 0) {
            header
                .padding(.horizontal, 28)
                .padding(.top, 22)
                .padding(.bottom, 16)

            ScrollView(showsIndicators: false) {
                VStack(alignment: .leading, spacing: 0) {
                    headline
                        .padding(.bottom, 18)

                    reasonCard
                        .padding(.bottom, 20)

                    AttreqPrimaryButton("Submit", role: .accent) {
                        submit(reason: selectedReason ?? impliedOtherReason)
                    }
                }
                .padding(.horizontal, 28)
                .padding(.bottom, 40)
            }
        }
        .background(Theme.bg.ignoresSafeArea())
        .presentationDetents([.medium, .large])
        .onDisappear {
            // Covers interactive swipe-away: neither button was tapped, but
            // the user already committed to skipping/dismissing the look
            // before this sheet ever opened — that signal must not be lost.
            if !hasSubmitted {
                submit(reason: nil, note: nil)
            }
        }
    }

    /// `.other` only when the user wrote something but picked no explicit
    /// chip — an unlabeled reason is better than none, but we never invent
    /// a specific one the user didn't choose.
    private var impliedOtherReason: RejectionReason? {
        note.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty ? nil : .other
    }

    // MARK: Header

    private var header: some View {
        HStack {
            MonoLabel("Why skip this?")
            Spacer()
            Button {
                submit(reason: nil, note: nil)
            } label: {
                Text("Skip")
                    .font(.attreqBody(13, weight: .medium))
                    .foregroundStyle(Theme.t2)
                    .contentShape(Rectangle())
            }
            .buttonStyle(.plain)
            .accessibilityIdentifier("button-Skip")
        }
    }

    /// Serif display headline, matching `StyleDnaEditSheet`'s voice.
    private var headline: some View {
        VStack(alignment: .leading, spacing: 0) {
            Text("Help us")
                .font(.attreqDisplay(30, weight: .semiBold))
                .foregroundStyle(Theme.text)
            Text("weave better.")
                .font(.attreqDisplay(30, weight: .semiBold, italic: true))
                .foregroundStyle(Theme.accent)
        }
    }

    // MARK: Reason card

    private var reasonCard: some View {
        VStack(alignment: .leading, spacing: 16) {
            VStack(alignment: .leading, spacing: 10) {
                MonoLabel("Reason (optional)")
                ChipFlowLayout(spacing: 6) {
                    ForEach(Self.chipReasons, id: \.self) { reason in
                        AttreqChip(reason.display, selected: selectedReason == reason) {
                            selectedReason = (selectedReason == reason) ? nil : reason
                        }
                    }
                }
            }
            Rectangle()
                .fill(Theme.borderSoft)
                .frame(height: 1)
            AttreqUnderlineInput(label: "Add a note (optional)", text: $note)
        }
        .attreqCard(padding: 18)
    }

    // MARK: Submit

    /// - Parameters:
    ///   - reason: `nil` for a bare rejection.
    ///   - note: pass `nil` explicitly (as the header "Skip" button and the
    ///     swipe-away fallback do) to discard any typed note along with the
    ///     reason; omit it to use whatever is currently in the note field
    ///     (the primary "Submit" button's path).
    private func submit(reason: RejectionReason?, note: String? = nil) {
        guard !hasSubmitted else { return }
        hasSubmitted = true
        let trimmedNote = (note ?? self.note).trimmingCharacters(in: .whitespacesAndNewlines)
        onSubmit(reason, trimmedNote.isEmpty ? nil : trimmedNote)
        dismiss()
    }
}

// MARK: - Flow layout

/// Minimal leading-aligned wrap layout for the chip row (private twin of
/// `StyleDnaEditSheet`'s `ChipFlowLayout`, which is itself file-private — no
/// shared flow layout exists in `DesignSystem/Components` to reuse).
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

#Preview("Rejection sheet") {
    Color.clear
        .sheet(isPresented: .constant(true)) {
            RejectionReasonSheet { reason, note in
                print("reason=\(String(describing: reason)) note=\(String(describing: note))")
            }
        }
}
