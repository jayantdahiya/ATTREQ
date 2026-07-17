//
//  TodayScreen.swift
//  ATTREQ
//
//  Today dashboard (M4, artboard 05). Pixel source:
//  assets/design/ios-redesign-v2/attreq-app.jsx → ATTREQDashboard.
//  Mono date + display-32 "Good morning, / *Name.*" header with menu circle,
//  weather strip (degrades keyless), "Today's looks" row, RecommendationCard
//  for the current suggestion, pull-to-refresh hint card.
//
//  States: loading (ProgressView), empty (no wardrobe → invite to upload),
//  failed (clay banner + retry), loaded. Pull-to-refresh in every scroll state
//  → `viewModel.refresh()` (GET /recommendations/daily?refresh=true).
//

import SwiftUI

struct TodayScreen: View {
    @Environment(AppSession.self) private var session

    /// Owned by `MainTabsView` (WP3 wiring) so state survives tab switches.
    let viewModel: TodayViewModel
    /// Records wears and feedback (POST /outfits) for the action callbacks.
    let outfitsRepository: OutfitsRepository
    /// Fired after a wear/love/dismiss successfully wrote an outfit, so
    /// `MainTabsView` can mark the History tab stale (its next `load()`
    /// refetches and the new entry appears without a manual pull-to-refresh).
    var onOutfitRecorded: (@MainActor () -> Void)? = nil

    var body: some View {
        ZStack {
            Theme.bg.ignoresSafeArea()

            switch viewModel.state {
            case .loading:
                ProgressView()
                    .tint(Theme.t2)
            case .empty:
                scrollBody { emptyBlock }
            case let .failed(message):
                scrollBody { failedBlock(message) }
            case .loaded:
                scrollBody { loadedBlock }
            }
        }
        .task { await viewModel.load() }
    }

    // MARK: - Scroll scaffold (header + weather strip + state content)

    private func scrollBody(@ViewBuilder content: () -> some View) -> some View {
        ScrollView(showsIndicators: false) {
            VStack(alignment: .leading, spacing: 0) {
                header
                    .padding(.bottom, 16)
                WeatherStrip(city: city, weather: viewModel.weather)
                    .padding(.bottom, 18)
                content()
            }
            .padding(.horizontal, 24)
            .padding(.top, 10)
            // Clearance for the floating tab bar.
            .padding(.bottom, 110)
        }
        .refreshable { await viewModel.refresh() }
    }

    // MARK: - Header

    private var header: some View {
        HStack(alignment: .top) {
            VStack(alignment: .leading, spacing: 5) {
                MonoLabel(TodayViewModel.dateLine())
                VStack(alignment: .leading, spacing: 0) {
                    Text("\(TodayViewModel.greeting()),")
                        .font(.attreqDisplay(32, weight: .semiBold))
                        .foregroundStyle(Theme.text)
                    Text("\(TodayViewModel.firstName(from: user)).")
                        .font(.attreqDisplay(32, weight: .semiBold, italic: true))
                        .foregroundStyle(Theme.accent)
                }
            }
            Spacer(minLength: 12)
            // Decorative menu circle per artboard 05 — deliberately inert
            // (no menu exists in the native port), so it's hidden from
            // assistive tech to avoid announcing a non-functional control.
            Circle()
                .strokeBorder(Theme.border, lineWidth: 1)
                .frame(width: 34, height: 34)
                .overlay(AttreqIcon.menu.view(size: 15, color: Theme.t2))
                .padding(.top, 22)
                .accessibilityHidden(true)
        }
    }

    // MARK: - Loaded

    @ViewBuilder
    private var loadedBlock: some View {
        HStack(alignment: .center) {
            Text("Today's looks")
                .font(.attreqDisplay(20, weight: .semiBold, italic: true))
                .foregroundStyle(Theme.text)
            Spacer()
            MonoLabel(looksCountText)
        }
        .padding(.bottom, 13)

        if let message = viewModel.errorMessage {
            errorBanner(message)
                .padding(.bottom, 12)
        }

        // `.loaded` implies non-empty suggestions and `advance()` wraps, so
        // `current` is always present here — no exhausted branch exists (the
        // hint card's continuous-cycling design keeps a look on screen).
        if let current = viewModel.current {
            RecommendationCard(
                suggestion: current,
                lookNumber: viewModel.currentIndex + 1,
                title: viewModel.currentLookTitle,
                isWearing: viewModel.isWearing,
                isSubmittingFeedback: viewModel.isSubmittingFeedback,
                onWear: { recordThenNotify { await viewModel.wear(using: outfitsRepository) } },
                onSkip: { viewModel.skip() },
                onLove: { recordThenNotify { await viewModel.love(using: outfitsRepository) } },
                onDismiss: { recordThenNotify { await viewModel.dismiss(using: outfitsRepository) } }
            )
        }

        hintCard
            .padding(.top, 11)
    }

    /// Runs a wear/feedback action; when it succeeds (an outfit row was
    /// written), fires `onOutfitRecorded` so History refreshes on next entry.
    private func recordThenNotify(_ action: @escaping @MainActor () async -> Bool) {
        Task { @MainActor in
            if await action() {
                onOutfitRecorded?()
            }
        }
    }

    private var looksCountText: String {
        "\(viewModel.totalLooks) \(viewModel.totalLooks == 1 ? "look" : "looks")"
    }

    /// Pull-down hint card — mono with the artboard's looser 1.1 tracking
    /// (vs MonoLabel's 1.6), 11v/15h padding.
    private var hintCard: some View {
        Text("Pull down to weave new looks from weather, wardrobe and feedback.".uppercased())
            .font(.attreqMono(9.5))
            .tracking(1.1)
            .foregroundStyle(Theme.t3)
            .lineSpacing(9.5 * 0.2)
            .frame(maxWidth: .infinity, alignment: .leading)
            .padding(.vertical, 11)
            .padding(.horizontal, 15)
            .attreqCard(padding: 0)
    }

    // MARK: - Empty (no wardrobe items)

    private var emptyBlock: some View {
        VStack(alignment: .leading, spacing: 10) {
            MonoLabel("No looks yet", size: 11)
            BodyText(
                "Your closet is waiting. Add a top and a bottom in the Wardrobe tab and ATTREQ will weave your first looks from weather and style.",
                size: 13
            )
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .attreqCard(padding: 16)
    }

    // MARK: - Failed

    @ViewBuilder
    private func failedBlock(_ message: String) -> some View {
        errorBanner(message)
            .padding(.bottom, 14)
        AttreqPrimaryButton("Try again") {
            Task { await viewModel.load() }
        }
    }

    private func errorBanner(_ message: String) -> some View {
        BodyText(message, size: 13, color: Theme.clay)
            .frame(maxWidth: .infinity, alignment: .leading)
            .padding(.vertical, 10)
            .padding(.horizontal, 13)
            .background(Theme.claySoft, in: RoundedRectangle(cornerRadius: 12, style: .continuous))
    }

    // MARK: - Session-derived header data

    private var user: User? {
        if case let .authenticated(user) = session.authState { return user }
        return nil
    }

    /// Weather strip city comes from the user profile, not the weather payload.
    private var city: String? {
        let candidate = user?.savedCity ?? user?.location
        guard let candidate, !candidate.isEmpty else { return nil }
        return candidate
    }
}

// MARK: - Previews

#Preview("Today") {
    let auth = AuthSession(keychain: KeychainStore(), baseURL: AppConfig.apiBaseURL)
    let client = APIClient(baseURL: AppConfig.apiBaseURL, authSession: auth)
    TodayScreen(
        viewModel: TodayViewModel(repository: RecommendationsRepository(apiClient: client)),
        outfitsRepository: OutfitsRepository(apiClient: client)
    )
    .environment(AppSession())
}
