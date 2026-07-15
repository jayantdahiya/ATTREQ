//
//  MainTabsView.swift
//  ATTREQ
//
//  Real authenticated tab shell (M2), replacing MainTabsPlaceholderView.
//  Floating `AttreqTabBar` over a switch of the four root tabs; Wardrobe is
//  the first real tab, Today/History land in M4 and Profile in M5.
//

import SwiftUI

struct MainTabsView: View {
    @Environment(AppSession.self) private var session

    @State private var activeTab: AttreqTab

    init(initialTab: AttreqTab = .today) {
        _activeTab = State(initialValue: initialTab)
    }
    /// Created once from the session's API client on first appearance and
    /// kept alive across tab switches so wardrobe state (items, filter,
    /// polling) survives leaving and re-entering the tab.
    @State private var wardrobeViewModel: WardrobeViewModel?
    @State private var isLoggingOut = false

    var body: some View {
        ZStack(alignment: .bottom) {
            Theme.bg.ignoresSafeArea()

            content
                .frame(maxWidth: .infinity, maxHeight: .infinity)

            AttreqTabBar(active: activeTab) { activeTab = $0 }
                .padding(.horizontal, 16)
                .padding(.bottom, 20)
        }
        .onAppear {
            if wardrobeViewModel == nil {
                wardrobeViewModel = WardrobeViewModel(
                    repository: WardrobeRepository(apiClient: session.api)
                )
            }
        }
    }

    @ViewBuilder
    private var content: some View {
        switch activeTab {
        case .today:
            MonoLabel("TODAY — M4", size: 12)

        case .wardrobe:
            if let wardrobeViewModel {
                WardrobeScreen(viewModel: wardrobeViewModel)
            }

        case .history:
            MonoLabel("HISTORY — M4", size: 12)

        case .profile:
            profileStub
        }
    }

    /// Temporary Profile tab: real profile ships in M5, but logout must work
    /// now so the register → logout → login loop stays testable end-to-end.
    private var profileStub: some View {
        VStack(spacing: 28) {
            MonoLabel("PROFILE — M5", size: 12)
            AttreqPrimaryButton("Log out", isLoading: isLoggingOut) {
                guard !isLoggingOut else { return }
                isLoggingOut = true
                Task {
                    await session.logout()
                    isLoggingOut = false
                }
            }
            .padding(.horizontal, 64)
        }
    }
}

// MARK: - Previews

#Preview("Main tabs") {
    MainTabsView()
        .environment(AppSession())
}
