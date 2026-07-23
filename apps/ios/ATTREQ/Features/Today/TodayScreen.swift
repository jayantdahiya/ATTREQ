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
//  RI-1: Skip/X on `RecommendationCard` now open `RejectionReasonSheet`
//  (bound to `viewModel.isPresentingRejectionSheet`) instead of acting
//  immediately — the sheet's confirmation is what actually records the
//  telemetry + (for dismiss) the existing outfit-level -1 call.
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

    /// RI-5 (Task 5.3): created lazily when the "Rate a few looks" entry is
    /// tapped, torn down on close (a fresh deck each time it's opened).
    @State private var swipeDeckViewModel: SwipeDeckViewModel?
    @State private var isPresentingSwipeDeck = false

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
        .task { await viewModel.loadSwipeDeckStatus() }
        .sheet(isPresented: rejectionSheetBinding) {
            RejectionReasonSheet { reason, note in
                recordThenNotify { await viewModel.confirmRejection(reason: reason, note: note) }
            }
        }
        .sheet(isPresented: $isPresentingSwipeDeck, onDismiss: {
            swipeDeckViewModel = nil
            Task { await viewModel.loadSwipeDeckStatus() }
        }) {
            if let swipeDeckViewModel {
                SwipeDeckView(viewModel: swipeDeckViewModel) {
                    isPresentingSwipeDeck = false
                }
            }
        }
    }

    private func presentSwipeDeck() {
        swipeDeckViewModel = viewModel.makeSwipeDeckViewModel()
        isPresentingSwipeDeck = true
    }

    /// Two-way bridge onto the view model's `isPresentingRejectionSheet` —
    /// SwiftUI needs a settable binding for `.sheet(isPresented:)`, including
    /// to flip it back to `false` on an interactive swipe-away.
    private var rejectionSheetBinding: Binding<Bool> {
        Binding(
            get: { viewModel.isPresentingRejectionSheet },
            set: { viewModel.isPresentingRejectionSheet = $0 }
        )
    }

    // MARK: - Scroll scaffold (header + weather strip + state content)

    private func scrollBody(@ViewBuilder content: () -> some View) -> some View {
        ScrollView(showsIndicators: false) {
            VStack(alignment: .leading, spacing: 0) {
                header
                    .padding(.bottom, 16)
                WeatherStrip(city: city, weather: viewModel.weather)
                    .padding(.bottom, 18)
                if !viewModel.hasAnsweredVibeToday {
                    vibePromptBlock
                        .padding(.bottom, 18)
                }
                content()
            }
            .padding(.horizontal, 24)
            .padding(.top, 10)
            // Clearance for the floating tab bar.
            .padding(.bottom, 110)
        }
        .refreshable { await viewModel.refresh() }
    }

    // MARK: - Morning vibe prompt (RI-5, Task 5.4)

    /// One-tap "Today's vibe: Sharp / Relaxed / Bold" chip row, shown once
    /// per day until answered or skipped. A soft formality nudge on
    /// generation — never blocks it (suggestions load regardless).
    private var vibePromptBlock: some View {
        VStack(alignment: .leading, spacing: 10) {
            MonoLabel("Today's vibe?", size: 10)
            HStack(spacing: 8) {
                vibeChip("Sharp", hint: "sharp")
                vibeChip("Relaxed", hint: "relaxed")
                vibeChip("Bold", hint: "bold")
                Spacer(minLength: 0)
                Button("Skip") { viewModel.skipVibe() }
                    .font(.attreqMono(10))
                    .foregroundStyle(Theme.t3)
                    .accessibilityIdentifier("vibe-skip")
            }
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .attreqCard(padding: 14)
    }

    private func vibeChip(_ title: String, hint: String) -> some View {
        Button {
            Task { await viewModel.selectVibe(hint) }
        } label: {
            Text(title.uppercased())
                .font(.attreqMono(10))
                .tracking(0.8)
                .foregroundStyle(Theme.text)
                .padding(.vertical, 7)
                .padding(.horizontal, 12)
                .background(Theme.surface, in: Capsule())
                .overlay(Capsule().strokeBorder(Theme.border, lineWidth: 1))
        }
        .buttonStyle(.plain)
        .accessibilityIdentifier("vibe-chip-\(hint)")
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
                onDismiss: { viewModel.dismiss(using: outfitsRepository) }
            )
        }

        hintCard
            .padding(.top, 11)

        if viewModel.showsSwipeDeckEntry {
            swipeDeckEntryCard
                .padding(.top, 11)
        }
    }

    /// RI-5 (Task 5.3) entry point — hidden once today's rating cap is
    /// reached (`showsSwipeDeckEntry`), never itself rate-limited to open.
    private var swipeDeckEntryCard: some View {
        Button(action: presentSwipeDeck) {
            HStack {
                VStack(alignment: .leading, spacing: 3) {
                    MonoLabel("A minute to spare?", size: 10)
                    Text("Rate a few looks")
                        .font(.attreqBody(14, weight: .medium))
                        .foregroundStyle(Theme.text)
                }
                Spacer()
                Image(systemName: "chevron.right")
                    .font(.system(size: 12, weight: .medium))
                    .foregroundStyle(Theme.t3)
            }
            .padding(.vertical, 13)
            .padding(.horizontal, 15)
        }
        .buttonStyle(.plain)
        .attreqCard(padding: 0)
        .accessibilityIdentifier("swipe-deck-entry")
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
