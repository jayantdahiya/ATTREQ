//
//  StyleStepView.swift
//  ATTREQ
//
//  Artboard 03 — registration step 2 (style keywords + occasions).
//  Design: assets/design/ios-redesign-v2/attreq-auth.jsx (ATTREQRegisterStyle).
//

import SwiftUI

struct StyleStepView: View {
    @Bindable var model: RegisterViewModel
    let onContinue: () -> Void

    var body: some View {
        VStack(alignment: .leading, spacing: 0) {
            MonoLabel("Step 02 — Style", color: Theme.accent)
                .padding(.bottom, 8)

            headline
                .padding(.bottom, 6)

            BodyText("Tell us how you dress. We'll learn the rest.")
                .padding(.bottom, 20)

            styleCard
                .frame(maxWidth: .infinity, maxHeight: .infinity)

            AttreqPrimaryButton("Continue →", action: onContinue)
                .padding(.top, 16)
        }
    }

    private var headline: some View {
        (
            Text("Define your\n").foregroundStyle(Theme.text)
                + Text("aesthetic.")
                .font(.attreqDisplay(36, italic: true))
                .foregroundStyle(Theme.accent)
        )
        .font(.attreqDisplay(36))
    }

    private var styleCard: some View {
        VStack(alignment: .leading, spacing: 0) {
            MonoLabel("Style keywords")
                .padding(.bottom, 14)

            ChipFlowLayout(spacing: 7) {
                ForEach(RegisterViewModel.styleOptions, id: \.self) { keyword in
                    AttreqChip(keyword, selected: model.selectedKeywords.contains(keyword)) {
                        model.toggleKeyword(keyword)
                    }
                }
            }
            .padding(.bottom, 20)

            Rectangle()
                .fill(Theme.borderSoft)
                .frame(height: 1)
                .padding(.bottom, 20)

            AttreqUnderlineInput(label: "Occasions (optional)", text: $model.occasions)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .top)
        .padding(.vertical, 22)
        .padding(.horizontal, 20)
        .attreqCard(padding: 0)
    }
}

// MARK: - Flow layout

/// Left-aligned wrapping layout for the style chips (CSS `flex-wrap` with a
/// uniform gap, per the handoff's chip grid).
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

#Preview {
    StyleStepView(model: RegisterViewModel(), onContinue: {})
        .padding(28)
        .background(Theme.bg)
}
