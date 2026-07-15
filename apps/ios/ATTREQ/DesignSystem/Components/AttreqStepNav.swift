import SwiftUI

/// Onboarding step navigation (`ATTREQStepNav` in the design handoff):
/// circular back button, centered segmented progress, mono "01/03" counter.
///
/// `step` is zero-based, matching the handoff (`step: 0` renders "01/03").
struct AttreqStepNav: View {
    let step: Int
    var total: Int = 3
    let onBack: () -> Void

    init(step: Int, total: Int = 3, onBack: @escaping () -> Void) {
        self.step = step
        self.total = total
        self.onBack = onBack
    }

    var body: some View {
        HStack {
            Button(action: onBack) {
                Circle()
                    .strokeBorder(Theme.border, lineWidth: 1)
                    .frame(width: 30, height: 30)
                    .overlay {
                        AttreqIcon.back.view(size: 14, color: Theme.t2)
                    }
                    // 44pt minimum tap target around the 30pt visual circle.
                    .frame(width: 44, height: 44)
                    .contentShape(Rectangle())
            }
            .buttonStyle(.plain)
            .accessibilityLabel("Back")

            Spacer()

            HStack(spacing: 5) {
                ForEach(0..<total, id: \.self) { index in
                    Capsule()
                        .fill(index <= step ? Theme.text : Theme.border)
                        .frame(width: index == step ? 22 : 8, height: 3)
                }
            }

            Spacer()

            MonoLabel(counterText)
        }
        .accessibilityElement(children: .contain)
        .accessibilityValue("Step \(step + 1) of \(total)")
    }

    private var counterText: String {
        String(format: "%02d/%02d", step + 1, total)
    }
}

#Preview("Step nav") {
    VStack(spacing: 32) {
        AttreqStepNav(step: 0) {}
        AttreqStepNav(step: 1) {}
        AttreqStepNav(step: 2) {}
    }
    .padding(28)
    .background(Theme.bg)
}
