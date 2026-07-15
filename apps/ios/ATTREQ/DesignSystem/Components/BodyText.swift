//
//  BodyText.swift
//  ATTREQ
//
//  Body copy — port of `ATTREQBody` from attreq-shared.jsx.
//  DM Sans 14, line-height 1.5, color t2.
//

import SwiftUI

/// Standard body copy with relaxed line height.
struct BodyText: View {
    let text: String
    var size: CGFloat = 14
    var color: Color?

    init(_ text: String, size: CGFloat = 14, color: Color? = nil) {
        self.text = text
        self.size = size
        self.color = color
    }

    var body: some View {
        Text(text)
            .font(.attreqBody(size))
            .foregroundStyle(color ?? Theme.t2)
            // CSS line-height 1.5 ≈ intrinsic (~1.25) + extra 0.25em between lines.
            .lineSpacing(size * 0.25)
    }
}

#Preview {
    VStack(alignment: .leading, spacing: 16) {
        BodyText("A quiet layer for a bright morning. Wool over linen keeps the chill honest without losing the drape.")
        BodyText("Smaller supporting copy at thirteen points.", size: 13)
        BodyText("Primary-colored body copy.", color: Theme.text)
    }
    .padding()
    .background(Theme.bg)
}
