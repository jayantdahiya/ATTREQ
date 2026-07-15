//
//  AttreqPrimaryButton.swift
//  ATTREQ
//
//  Full-width capsule button — port of `ATTREQBtn` from attreq-shared.jsx.
//  DM Sans 14 medium, 13pt vertical padding, letter-spacing 0.2.
//

import SwiftUI

/// Visual role for `AttreqPrimaryButton`.
enum AttreqButtonRole {
    /// Ink background, paper foreground (default CTA).
    case primary
    /// Accent (bronze) background, paper foreground.
    case accent
}

/// Full-width primary call-to-action button.
struct AttreqPrimaryButton: View {
    let title: String
    var role: AttreqButtonRole = .primary
    var systemImage: String? = nil
    var isLoading: Bool = false
    let action: () -> Void

    init(
        _ title: String,
        role: AttreqButtonRole = .primary,
        systemImage: String? = nil,
        isLoading: Bool = false,
        action: @escaping () -> Void
    ) {
        self.title = title
        self.role = role
        self.systemImage = systemImage
        self.isLoading = isLoading
        self.action = action
    }

    private var background: Color {
        switch role {
        case .primary: Theme.text
        case .accent: Theme.accent
        }
    }

    var body: some View {
        Button(action: action) {
            HStack(spacing: 6) {
                if isLoading {
                    ProgressView()
                        .controlSize(.small)
                        .tint(Theme.bg)
                } else {
                    if let systemImage {
                        // Fixed-metric by design, consistent with `AttreqIcon.view`:
                        // icon sizes are pinned to the handoff's pixel values and
                        // intentionally do not scale with Dynamic Type.
                        Image(systemName: systemImage)
                            .font(.system(size: 14, weight: .medium))
                    }
                    Text(title)
                        .font(.attreqBody(14, weight: .medium))
                        .tracking(0.2)
                }
            }
            .foregroundStyle(Theme.bg)
            .frame(maxWidth: .infinity)
            .padding(.vertical, 13)
            .background(Capsule().fill(background))
        }
        .buttonStyle(AttreqPressableButtonStyle())
        .disabled(isLoading)
    }
}

/// Subtle press feedback: dims the button while pressed.
private struct AttreqPressableButtonStyle: ButtonStyle {
    func makeBody(configuration: Configuration) -> some View {
        configuration.label
            .opacity(configuration.isPressed ? 0.82 : 1)
            .animation(.easeOut(duration: 0.12), value: configuration.isPressed)
    }
}

#Preview {
    VStack(spacing: 14) {
        AttreqPrimaryButton("Continue") {}
        AttreqPrimaryButton("Generate Outfit", role: .accent, systemImage: "sparkles") {}
        AttreqPrimaryButton("Saving…", isLoading: true) {}
    }
    .padding(24)
    .background(Theme.bg)
}
