//
//  AttreqChip.swift
//  ATTREQ
//
//  Selectable chip — port of `ATTREQChip` from attreq-shared.jsx.
//  Capsule, DM Sans 13 medium, padding 6v 14h.
//

import SwiftUI

/// Toggleable filter/selection chip.
struct AttreqChip: View {
    let label: String
    let selected: Bool
    let action: () -> Void

    init(_ label: String, selected: Bool, action: @escaping () -> Void) {
        self.label = label
        self.selected = selected
        self.action = action
    }

    var body: some View {
        Button(action: action) {
            Text(label)
                .font(.attreqBody(13, weight: .medium))
                .foregroundStyle(selected ? Theme.bg : Theme.t2)
                .padding(.vertical, 6)
                .padding(.horizontal, 14)
                .background {
                    if selected {
                        Capsule().fill(Theme.text)
                    } else {
                        Capsule().strokeBorder(Theme.border, lineWidth: 1)
                    }
                }
                // Extend the tappable area to >=44pt tall without growing the
                // visible capsule; the negative outer padding below cancels the
                // extra space so surrounding layout is unchanged.
                .padding(.vertical, 8)
                .contentShape(Rectangle())
        }
        .buttonStyle(.plain)
        .padding(.vertical, -8)
        .accessibilityAddTraits(selected ? [.isSelected] : [])
        .accessibilityIdentifier("chip-\(label)")
    }
}

#Preview {
    @Previewable @State var selection = "Casual"
    let options = ["Casual", "Smart", "Formal", "Athletic"]

    return HStack(spacing: 8) {
        ForEach(options, id: \.self) { option in
            AttreqChip(option, selected: selection == option) {
                selection = option
            }
        }
    }
    .padding()
    .background(Theme.bg)
}
