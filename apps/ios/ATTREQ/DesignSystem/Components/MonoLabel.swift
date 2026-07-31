//
//  MonoLabel.swift
//  ATTREQ
//
//  Mono micro-label — port of `ATTREQML` from attreq-shared.jsx.
//  IBM Plex Mono 9.5, uppercase, letter-spacing 1.6, color t3.
//

import SwiftUI

/// Uppercase mono label used for section headers, field labels, and metadata.
struct MonoLabel: View {
    let text: String
    var size: CGFloat = 9.5
    var color: Color?

    init(_ text: String, size: CGFloat = 9.5, color: Color? = nil) {
        self.text = text
        self.size = size
        self.color = color
    }

    var body: some View {
        Text(text.uppercased())
            .font(.attreqMono(size))
            .tracking(1.6)
            .foregroundStyle(color ?? Theme.t3)
            .lineSpacing(size * 0.2) // ≈ CSS line-height 1.4
    }
}

#Preview {
    VStack(alignment: .leading, spacing: 12) {
        MonoLabel("Today's Forecast")
        MonoLabel("Wardrobe", size: 12)
        MonoLabel("Accent Label", color: Theme.accent)
    }
    .padding()
    .background(Theme.bg)
}
