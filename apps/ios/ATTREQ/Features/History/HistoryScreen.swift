//
//  HistoryScreen.swift
//  ATTREQ
//
//  History screen (M4, artboard 07). Pixel source:
//  assets/design/ios-redesign-v2/attreq-app.jsx → ATTREQHistory.
//  Header "Diary / *History*" with baseline-aligned "N looks tracked" mono,
//  date-grouped sections (italic date label + hairline + ISO mono), stacked
//  outfit cards. Pull-to-refresh + infinite scroll via `loadMoreIfNeeded`.
//

import SwiftUI

struct HistoryScreen: View {
    /// Owned by `MainTabsView` so history state survives tab switches.
    let viewModel: HistoryViewModel

    var body: some View {
        ZStack {
            Theme.bg.ignoresSafeArea()

            ScrollView(showsIndicators: false) {
                VStack(alignment: .leading, spacing: 0) {
                    header
                        .padding(.bottom, 20)
                    content
                }
                .padding(.horizontal, 24)
                .padding(.top, 10)
                // Clearance for the floating tab bar.
                .padding(.bottom, 110)
            }
            .refreshable { await viewModel.refresh() }
        }
        .task { await viewModel.load() }
    }

    // MARK: - Header

    private var header: some View {
        VStack(alignment: .leading, spacing: 5) {
            MonoLabel("Diary")
            HStack(alignment: .firstTextBaseline) {
                Text("History")
                    .font(.attreqDisplay(28, weight: .semiBold, italic: true))
                    .foregroundStyle(Theme.text)
                Spacer()
                MonoLabel(trackedLine)
            }
        }
    }

    private var trackedLine: String {
        "\(viewModel.totalTracked) \(viewModel.totalTracked == 1 ? "look" : "looks") tracked"
    }

    // MARK: - States

    @ViewBuilder
    private var content: some View {
        switch viewModel.state {
        case .loading:
            loadingState
        case .empty:
            emptyState
        case let .failed(message):
            failedState(viewModel.errorMessage ?? message)
        case .loaded:
            // Refresh-over-content failures keep the list but must not be
            // silent — surface the clay banner (mirrors TodayScreen).
            if let message = viewModel.errorMessage {
                errorBanner(message)
                    .padding(.bottom, 14)
            }
            groupList
        }
    }

    private var loadingState: some View {
        HStack {
            Spacer()
            ProgressView()
                .tint(Theme.t2)
            Spacer()
        }
        .padding(.top, 64)
    }

    private var emptyState: some View {
        VStack(spacing: 10) {
            MonoLabel("No looks tracked yet", size: 11)
            BodyText(
                "Wear one of today's suggestions and it will be recorded here, day by day.",
                size: 13
            )
            .multilineTextAlignment(.center)
        }
        .frame(maxWidth: .infinity)
        .padding(.top, 48)
        .padding(.horizontal, 16)
    }

    private func errorBanner(_ message: String) -> some View {
        BodyText(message, size: 13, color: Theme.clay)
            .frame(maxWidth: .infinity, alignment: .leading)
            .padding(.vertical, 10)
            .padding(.horizontal, 13)
            .background(Theme.claySoft, in: RoundedRectangle(cornerRadius: 12, style: .continuous))
    }

    private func failedState(_ message: String) -> some View {
        VStack(alignment: .leading, spacing: 14) {
            errorBanner(message)

            Button {
                Task { await viewModel.load() }
            } label: {
                MonoLabel("Retry", size: 10, color: Theme.text)
                    .padding(.vertical, 9)
                    .padding(.horizontal, 18)
                    .overlay(Capsule().strokeBorder(Theme.border, lineWidth: 1))
                    .contentShape(Capsule())
            }
            .buttonStyle(.plain)
            .accessibilityIdentifier("history-retry")
        }
        .padding(.top, 4)
    }

    // MARK: - Date groups

    private var groupList: some View {
        LazyVStack(alignment: .leading, spacing: 20) {
            ForEach(viewModel.groups, id: \.isoLabel) { group in
                groupSection(group)
            }
        }
    }

    private func groupSection(_ group: HistoryGroup) -> some View {
        VStack(alignment: .leading, spacing: 10) {
            HStack(spacing: 10) {
                Text(group.dateLabel)
                    .font(.attreqDisplay(16, weight: .semiBold, italic: true))
                    .foregroundStyle(Theme.text)
                    .lineLimit(1)
                    .fixedSize()
                Rectangle()
                    .fill(Theme.borderSoft)
                    .frame(height: 1)
                    .frame(maxWidth: .infinity)
                MonoLabel(group.isoLabel)
            }

            VStack(spacing: 8) {
                ForEach(group.entries, id: \.outfit.id) { entry in
                    OutfitHistoryCard(
                        outfitID: entry.outfit.id,
                        title: entry.title,
                        piecesCount: entry.piecesCount,
                        pillLabel: entry.pill.label,
                        pillVariant: entry.pill.variant
                    )
                    .onAppear {
                        Task { await viewModel.loadMoreIfNeeded(currentEntry: entry) }
                    }
                }
            }
        }
    }
}

// MARK: - Previews

#Preview("History") {
    let auth = AuthSession(keychain: KeychainStore(), baseURL: AppConfig.apiBaseURL)
    let client = APIClient(baseURL: AppConfig.apiBaseURL, authSession: auth)
    HistoryScreen(
        viewModel: HistoryViewModel(repository: OutfitsRepository(apiClient: client))
    )
}
