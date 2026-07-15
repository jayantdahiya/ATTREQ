import SwiftUI

/// Gradient garment placeholder tile (`ATTREQGarment` in the design handoff).
/// Fills its proposed frame with the tone's gradient; optionally shows a small
/// uppercase mono label pinned to the bottom-left corner.
struct GarmentPlaceholder: View {
    var tone: GarmentTone
    var label: String?
    var cornerRadius: CGFloat = 14

    init(tone: GarmentTone, label: String? = nil, cornerRadius: CGFloat = 14) {
        self.tone = tone
        self.label = label
        self.cornerRadius = cornerRadius
    }

    var body: some View {
        RoundedRectangle(cornerRadius: cornerRadius, style: .continuous)
            .fill(Theme.garmentGradient(tone))
            .overlay(alignment: .bottomLeading) {
                if let label {
                    Text(label.uppercased())
                        .font(.attreqMono(7.5))
                        .tracking(0.8)
                        .foregroundStyle(Theme.t3)
                        .lineLimit(1)
                        .padding(.leading, 8)
                        .padding(.bottom, 7)
                }
            }
            .clipShape(RoundedRectangle(cornerRadius: cornerRadius, style: .continuous))
    }
}

#Preview("Garment tones") {
    HStack(spacing: 8) {
        ForEach(GarmentTone.allCases, id: \.self) { tone in
            GarmentPlaceholder(tone: tone, label: String(describing: tone))
                .frame(height: 110)
        }
    }
    .padding(24)
    .background(Theme.bg)
}
