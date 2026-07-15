//
//  Theme.swift
//  ATTREQ
//
//  Semantic design tokens for the ATTREQ Redesign v2 handoff.
//  Source of truth: assets/design/ios-redesign-v2/attreq-shared.jsx
//  (ATTREQ_C light tokens / ATTREQ_DARK_C dark tokens).
//
//  Every color resolves through the asset catalog, so the system
//  appearance switch drives light/dark theming automatically.
//

import SwiftUI

// MARK: - Theme

/// Namespace mirroring the handoff token names (`bg`, `surface`, `t2`, `accent`, ...).
enum Theme {
    /// Screen background — light `#F5F2EE`, dark `#181512`.
    static let bg = Color("bg")
    /// Card / elevated surface — light `#FFFFFF`, dark `#231F1B`.
    static let surface = Color("surface")
    /// Deepest ink — light `#1C1917`, dark `#EDE9E3`.
    static let deep = Color("deep")
    /// Primary text — light `#1C1917`, dark `#EDE9E3`.
    static let text = Color("textPrimary")
    /// Secondary text — light `#78716C`, dark `#9A9088`.
    static let t2 = Color("textSecondary")
    /// Tertiary text — light `#A8A29E`, dark `#6E6862`.
    static let t3 = Color("textTertiary")
    /// Camel accent — light `#9B7B5A`, dark `#BA9272`.
    static let accent = Color("accent")
    /// Accent tint background — light 10%, dark 13% of accent.
    static let accentSoft = Color("accentSoft")
    /// Clay (destructive / skip) — light `#BF5C45`, dark `#D4705A`.
    static let clay = Color("clay")
    /// Clay tint background — light 10%, dark 12% of clay.
    static let claySoft = Color("claySoft")
    /// Moss (positive / worn) — light `#5A8A6A`, dark `#72AA86`.
    static let moss = Color("moss")
    /// Moss tint background — light 12%, dark 14% of moss.
    static let mossSoft = Color("mossSoft")
    /// Hairline border — 8% of ink.
    static let border = Color("border")
    /// Softer hairline border — 5% of ink.
    static let borderSoft = Color("borderSoft")
}

// MARK: - Garment placeholder gradients

/// The five garment-placeholder tones from the handoff's `garmentGrads`.
enum GarmentTone: CaseIterable {
    case top, bottom, outer, accent, shoes
}

extension Theme {
    /// Unit points approximating the CSS `linear-gradient(155deg, ...)` direction
    /// (CSS angles run clockwise from north; 155° points down and slightly right).
    private static let gradientStart = UnitPoint(x: 0.267, y: 0.0)
    private static let gradientEnd = UnitPoint(x: 0.733, y: 1.0)

    /// Two-stop placeholder gradient for a garment tone, matching
    /// `garmentGrads` in both appearances via the asset catalog.
    static func garmentGradient(_ tone: GarmentTone) -> LinearGradient {
        let name: String
        switch tone {
        case .top: name = "garmentTop"
        case .bottom: name = "garmentBottom"
        case .outer: name = "garmentOuter"
        case .accent: name = "garmentAccent"
        case .shoes: name = "garmentShoes"
        }
        return LinearGradient(
            colors: [Color("\(name)Start"), Color("\(name)End")],
            startPoint: gradientStart,
            endPoint: gradientEnd
        )
    }

    /// Card shadow from the handoff's `cardStyle` box-shadow:
    /// dark `0 2px 12px rgba(0,0,0,0.28)`, light `0 2px 8px rgba(0,0,0,0.04)`.
    /// CSS blur is twice the SwiftUI shadow radius, so 8px/12px blur maps to 4pt/6pt.
    static func cardShadow(isDark: Bool) -> (color: Color, radius: CGFloat, y: CGFloat) {
        isDark
            ? (color: Color.black.opacity(0.28), radius: 6, y: 2)
            : (color: Color.black.opacity(0.04), radius: 4, y: 2)
    }
}

// MARK: - Card background modifier

/// Applies the signature ATTREQ card treatment: surface background,
/// 20pt continuous corner radius, 1pt hairline border, and the
/// appearance-appropriate soft shadow.
struct AttreqCardBackground: ViewModifier {
    @Environment(\.colorScheme) private var colorScheme

    var padding: CGFloat = 16

    func body(content: Content) -> some View {
        let shape = RoundedRectangle(cornerRadius: 20, style: .continuous)
        let shadow = Theme.cardShadow(isDark: colorScheme == .dark)
        content
            .padding(padding)
            .background(Theme.surface, in: shape)
            .overlay(shape.strokeBorder(Theme.border, lineWidth: 1))
            .overlay {
                // Dark-mode inner top highlight from the handoff's `cardStyle`:
                // `inset 0 1px 0 rgba(255,255,255,0.04)` (same rim technique as
                // the tab bar's inner glow).
                if colorScheme == .dark {
                    RoundedRectangle(cornerRadius: 19, style: .continuous)
                        .strokeBorder(
                            LinearGradient(
                                colors: [Color.white.opacity(0.04), Color.white.opacity(0)],
                                startPoint: .top,
                                endPoint: .bottom
                            ),
                            lineWidth: 1
                        )
                        .padding(1)
                }
            }
            .shadow(color: shadow.color, radius: shadow.radius, x: 0, y: shadow.y)
    }
}

extension View {
    /// Wraps the view in the standard ATTREQ card style (see `AttreqCardBackground`).
    func attreqCard(padding: CGFloat = 16) -> some View {
        modifier(AttreqCardBackground(padding: padding))
    }
}
