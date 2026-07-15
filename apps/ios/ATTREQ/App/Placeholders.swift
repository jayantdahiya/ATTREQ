//
//  Placeholders.swift
//  ATTREQ
//
//  Temporary post-auth destinations for M1 so the routing gate is testable
//  end-to-end. Replaced by real screens in M2 (tabs) and M3 (Style DNA
//  onboarding).
//

import SwiftUI

// MARK: - Main tabs placeholder (M2+)

/// Stand-in for the authenticated tab shell. Includes a temporary logout
/// button so the full E2E loop (register → relaunch → logout → login) works.
struct MainTabsPlaceholderView: View {
    @Environment(AppSession.self) private var session

    @State private var activeTab: AttreqTab = .today
    @State private var isLoggingOut = false

    var body: some View {
        ZStack(alignment: .bottom) {
            Theme.bg.ignoresSafeArea()

            VStack(spacing: 28) {
                Spacer()
                MonoLabel("M2+ — coming soon", size: 12)
                // Temporary: real logout lives in the Profile tab (M4).
                AttreqPrimaryButton("Log out", isLoading: isLoggingOut) {
                    guard !isLoggingOut else { return }
                    isLoggingOut = true
                    Task {
                        await session.logout()
                        isLoggingOut = false
                    }
                }
                .padding(.horizontal, 64)
                Spacer()
            }

            AttreqTabBar(active: activeTab) { activeTab = $0 }
                .padding(.horizontal, 16)
                .padding(.bottom, 20)
        }
    }
}

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

#Preview("Main tabs placeholder") {
    MainTabsPlaceholderView()
        .environment(AppSession())
}

#Preview("Onboarding placeholder") {
    OnboardingPlaceholderView()
        .environment(AppSession())
}
