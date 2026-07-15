//
//  AttreqPill.swift
//  ATTREQ
//
//  Status pill — port of `ATTREQPill` from attreq-shared.jsx.
//  Mono 8.5 uppercase, tracking 0.9, padding 3v 9h, tinted capsule.
//

import SwiftUI

/// Tint variants for `AttreqPill`.
enum PillVariant {
    case muted
    case gold
    case moss
    case clay
}

/// Small uppercase status/metadata pill.
struct AttreqPill: View {
    let text: String
    var variant: PillVariant = .muted

    init(_ text: String, variant: PillVariant = .muted) {
        self.text = text
        self.variant = variant
    }

    private var background: Color {
        switch variant {
        case .muted: Color(red: 128 / 255, green: 120 / 255, blue: 112 / 255).opacity(0.10)
        case .gold: Theme.accentSoft
        case .moss: Theme.mossSoft
        case .clay: Theme.claySoft
        }
    }

    private var foreground: Color {
        switch variant {
        case .muted: Theme.t2
        case .gold: Theme.accent
        case .moss: Theme.moss
        case .clay: Theme.clay
        }
    }

    var body: some View {
        Text(text.uppercased())
            .font(.attreqMono(8.5))
            .tracking(0.9)
            .foregroundStyle(foreground)
            .lineLimit(1)
            .padding(.vertical, 3)
            .padding(.horizontal, 9)
            .background(Capsule().fill(background))
    }
}

#Preview {
    HStack(spacing: 8) {
        AttreqPill("Archive")
        AttreqPill("Gold Hour", variant: .gold)
        AttreqPill("Fresh", variant: .moss)
        AttreqPill("Worn 3x", variant: .clay)
    }
    .padding()
    .background(Theme.bg)
}
