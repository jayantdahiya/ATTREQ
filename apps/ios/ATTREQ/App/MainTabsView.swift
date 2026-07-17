//
//  MainTabsView.swift
//  ATTREQ
//
//  Real authenticated tab shell (M2), replacing MainTabsPlaceholderView.
//  Floating `AttreqTabBar` over a switch of the four root tabs; all four are
//  live (Today/Wardrobe M2, History M4, Profile M5).
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
    /// Same lifecycle as `wardrobeViewModel` — suggestions/paging survive tab switches.
    @State private var todayViewModel: TodayViewModel?
    @State private var historyViewModel: HistoryViewModel?
    /// Shared by Today (wear/feedback writes) and History (reads) so both
    /// tabs hit the same store.
    @State private var outfitsRepository: OutfitsRepository?
    /// Same lifecycle as the other tab models — profile stats survive tab
    /// switches. Shares `outfitsRepository` so the Worn/Streak stats read the
    /// same store the Today tab writes to.
    @State private var profileViewModel: ProfileViewModel?

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
            if todayViewModel == nil || historyViewModel == nil || profileViewModel == nil {
                let outfits = outfitsRepository ?? OutfitsRepository(apiClient: session.api)
                outfitsRepository = outfits
                if todayViewModel == nil {
                    todayViewModel = TodayViewModel(
                        repository: RecommendationsRepository(apiClient: session.api)
                    )
                }
                if historyViewModel == nil {
                    historyViewModel = HistoryViewModel(repository: outfits)
                }
                if profileViewModel == nil {
                    profileViewModel = ProfileViewModel(
                        wardrobeRepository: WardrobeRepository(apiClient: session.api),
                        outfitsRepository: outfits
                    )
                }
            }
        }
    }

    @ViewBuilder
    private var content: some View {
        switch activeTab {
        case .today:
            if let todayViewModel, let outfitsRepository {
                TodayScreen(
                    viewModel: todayViewModel,
                    outfitsRepository: outfitsRepository,
                    // A recorded wear/love/dismiss makes the History list and
                    // the Profile stats (Worn/Streak) stale; each refetches on
                    // next tab entry.
                    onOutfitRecorded: {
                        historyViewModel?.markStale()
                        profileViewModel?.markStale()
                    }
                )
            }

        case .wardrobe:
            if let wardrobeViewModel {
                // A successful upload changes the Pieces stat.
                WardrobeScreen(
                    viewModel: wardrobeViewModel,
                    onItemUploaded: { profileViewModel?.markStale() }
                )
            }

        case .history:
            if let historyViewModel {
                HistoryScreen(viewModel: historyViewModel)
            }

        case .profile:
            if let profileViewModel {
                ProfileScreen(viewModel: profileViewModel)
            }
        }
    }
}

// MARK: - Previews

#Preview("Main tabs") {
    MainTabsView()
        .environment(AppSession())
}
