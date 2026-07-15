//
//  Placeholders.swift
//  ATTREQ
//
//  Temporary post-auth destinations so the routing gate is testable
//  end-to-end. The M2 tab shell is real (`MainTabsView`); Style DNA
//  onboarding is replaced in M3.
//

import SwiftUI

// MARK: - Onboarding placeholder (M3)

/// Stand-in for the Style DNA onboarding flow. The temporary button calls
/// `POST /users/onboarding/complete` and refreshes the user, so the
/// onboarding gate is testable end-to-end before M3 lands.
struct OnboardingPlaceholderView: View {
    @Environment(AppSession.self) private var session

    @State private var isCompleting = false

    var body: some View {
        ZStack {
            Theme.bg.ignoresSafeArea()

            VStack(spacing: 28) {
                MonoLabel("Style DNA Onboarding — M3", size: 12)
                // Temporary: the real flow completes onboarding after Style DNA
                // + wardrobe review.
                AttreqPrimaryButton("Complete onboarding", role: .accent, isLoading: isCompleting) {
                    guard !isCompleting else { return }
                    isCompleting = true
                    Task {
                        do {
                            try await session.completeOnboarding()
                        } catch {
                            // Stay on this screen; the button re-enables for retry.
                        }
                        isCompleting = false
                    }
                }
                .padding(.horizontal, 64)
            }
        }
    }
}

// MARK: - Previews

#Preview("Onboarding placeholder") {
    OnboardingPlaceholderView()
        .environment(AppSession())
}
