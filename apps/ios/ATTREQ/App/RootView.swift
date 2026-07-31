//
//  RootView.swift
//  ATTREQ
//
//  Root routing gate (M1). Mirrors the RN gate in `apps/mobile/app/index.tsx`:
//  no token → auth screens; authenticated without onboarding → onboarding;
//  otherwise the main tabs.
//

import SwiftUI

struct RootView: View {
    @Environment(AppSession.self) private var session

    /// `-gallery` launch argument keeps the M0 design-system gallery reachable
    /// for design audits (Xcode scheme arguments / `XCUIApplication.launchArguments`).
    private var isGalleryMode: Bool {
        ProcessInfo.processInfo.arguments.contains("-gallery")
    }

    /// `-screen <name>` jumps straight to one screen for design audits:
    /// `register-account` / `register-style` / `register-location` /
    /// `wardrobe` / `today` / `history` / `profile` / `style-dna-upload` /
    /// `style-dna`.
    private var auditScreen: String? {
        let args = ProcessInfo.processInfo.arguments
        guard let index = args.firstIndex(of: "-screen"), args.indices.contains(index + 1) else { return nil }
        return args[index + 1]
    }

    var body: some View {
        if isGalleryMode {
            ComponentGalleryView()
        } else if let auditScreen {
            // Bootstrap here too so audit screenshots show the real
            // last-signed-in user (identity, stats) instead of fallbacks.
            auditDestination(auditScreen)
                .task { await session.bootstrap() }
        } else {
            gate
                .task { await session.bootstrap() }
        }
    }

    @ViewBuilder
    private func auditDestination(_ name: String) -> some View {
        switch name {
        case "register-account": RegisterFlowView(initialStep: 0)
        case "register-style": RegisterFlowView(initialStep: 1)
        case "register-location": RegisterFlowView(initialStep: 2)
        case "wardrobe": MainTabsView(initialTab: .wardrobe)
        case "today": MainTabsView(initialTab: .today)
        case "history": MainTabsView(initialTab: .history)
        case "profile": MainTabsView(initialTab: .profile)
        case "style-dna-upload": OnboardingFlowView()
        case "style-dna": StyleDnaProfileView()
        default: LoginView()
        }
    }

    @ViewBuilder
    private var gate: some View {
        switch session.authState {
        case .loading:
            ZStack {
                Theme.bg.ignoresSafeArea()
                ProgressView()
                    .tint(Theme.t2)
            }

        case .loggedOut:
            // LoginView owns its NavigationStack and pushes RegisterFlowView
            // itself (bottom "Create account" link).
            LoginView()

        case let .authenticated(user):
            if user.onboardingCompleted {
                MainTabsView()
            } else {
                OnboardingFlowView()
            }
        }
    }
}

#Preview {
    RootView()
        .environment(AppSession())
}
