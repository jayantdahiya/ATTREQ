//
//  ArchivedWardrobeView.swift
//  ATTREQ
//
//  Archived-items view (RI-7) — pushed from `WardrobeScreen`'s "Archived"
//  header link. Reuses `WardrobeItemCard` for visual consistency with the
//  main grid, but with its own screen-scoped `WardrobeViewModel` configured
//  for `status: .archived` (see `WardrobeViewModel.init(status:)`).
//
//  No per-row "Unarchive" affordance here by design — tapping a card pushes
//  `WardrobeItemDetailView`, which already has the Unarchive action; deep-
//  linking there avoids duplicating the archive/unarchive control inline.
//

import SwiftUI

struct ArchivedWardrobeView: View {
    @State private var viewModel: WardrobeViewModel

    init(repository: WardrobeRepository) {
        _viewModel = State(initialValue: WardrobeViewModel(repository: repository, status: .archived))
    }

    var body: some View {
        ZStack {
            Theme.bg.ignoresSafeArea()

            ScrollView(showsIndicators: false) {
                VStack(alignment: .leading, spacing: 0) {
                    header
                        .padding(.bottom, 12)
                    if let message = viewModel.errorMessage {
                        errorBanner(message)
                            .padding(.bottom, 12)
                    }
                    grid
                }
                .padding(.horizontal, 24)
                .padding(.top, 10)
                .padding(.bottom, 40)
            }
            .refreshable { await viewModel.refresh() }
        }
        .navigationTitle("Archived")
        .navigationBarTitleDisplayMode(.inline)
        .task {
            await viewModel.loadInitial()
        }
    }

    private var header: some View {
        VStack(alignment: .leading, spacing: 5) {
            MonoLabel("Closet")
            Text("Archived")
                .font(.attreqDisplay(24, weight: .semiBold, italic: true))
                .foregroundStyle(Theme.text)
            BodyText("Kept for outfit history, out of Today and the active wardrobe.", size: 12)
        }
    }

    @ViewBuilder
    private var grid: some View {
        let items = viewModel.filteredItems
        if items.isEmpty {
            if viewModel.isLoading {
                HStack {
                    Spacer()
                    ProgressView().tint(Theme.t2)
                    Spacer()
                }
                .padding(.top, 48)
            } else {
                VStack(spacing: 10) {
                    MonoLabel("Nothing archived", size: 11)
                    BodyText("Items you archive from the item detail screen show up here.", size: 13)
                        .multilineTextAlignment(.center)
                }
                .frame(maxWidth: .infinity)
                .padding(.top, 48)
                .padding(.horizontal, 16)
            }
        } else {
            let columns = [GridItem(.flexible(), spacing: 10), GridItem(.flexible(), spacing: 10)]
            LazyVGrid(columns: columns, spacing: 10) {
                ForEach(items) { item in
                    NavigationLink(value: item.id) {
                        WardrobeItemCard(item: item, imageAspectRatio: 0.9)
                    }
                    .buttonStyle(.plain)
                    .onAppear {
                        Task { await viewModel.loadMoreIfNeeded(currentItem: item) }
                    }
                }
            }
        }
    }

    private func errorBanner(_ message: String) -> some View {
        BodyText(message, size: 13, color: Theme.clay)
            .frame(maxWidth: .infinity, alignment: .leading)
            .padding(.vertical, 10)
            .padding(.horizontal, 13)
            .background(Theme.claySoft, in: RoundedRectangle(cornerRadius: 12, style: .continuous))
    }
}

// MARK: - Previews

#Preview("Archived") {
    let auth = AuthSession(keychain: KeychainStore(), baseURL: AppConfig.apiBaseURL)
    let client = APIClient(baseURL: AppConfig.apiBaseURL, authSession: auth)
    NavigationStack {
        ArchivedWardrobeView(repository: WardrobeRepository(apiClient: client))
    }
}
