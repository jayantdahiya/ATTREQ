//
//  WardrobeItemDetailView.swift
//  ATTREQ
//
//  Wardrobe item detail (RI-7) — net-new screen; there was previously no
//  destination for tapping a wardrobe grid card. Pushed from `WardrobeScreen`
//  (main grid) and `ArchivedWardrobeView` (archived grid) via
//  `navigationDestination(for: String.self)`.
//
//  Backend contract: apps/api/src/attreq_api/api/v1/endpoints/wardrobe.py
//  - GET    /wardrobe/items/{id}                (full item incl. `photos`)
//  - PUT    /wardrobe/items/{id}                 (price/brand edits)
//  - PATCH  /wardrobe/items/{id}/status          (archive/unarchive)
//  - POST   /wardrobe/items/{id}/photos          (add a photo)
//  - GET    /wardrobe/items/{id}/photos          (poll for thumbnail)
//

import PhotosUI
import SwiftUI

// MARK: - View model

/// Drives `WardrobeItemDetailView`. Scoped to the screen's lifetime (not
/// shared across tab switches like the tab-root view models) — a fresh
/// instance is created each time the detail screen is pushed.
@MainActor
@Observable
final class WardrobeItemDetailViewModel {
    enum LoadState: Equatable {
        case loading
        case loaded
        case failed(String)
    }

    private(set) var state: LoadState = .loading
    private(set) var item: WardrobeItem?
    /// Additional photos (RI-7), fetched separately from the item itself —
    /// the item response's own `photos` field is populated too, but this
    /// list is the one polled after an upload, so it's kept as the source of
    /// truth for the gallery once the first load completes.
    private(set) var photos: [WardrobeItemPhoto] = []
    /// True while a new photo upload + poll is in flight (gallery shows a
    /// spinner tile instead of the "+ Add" tile).
    private(set) var isUploadingPhoto = false
    /// True while the archive/unarchive call is in flight.
    private(set) var isChangingStatus = false
    /// True while the price/brand edit save is in flight.
    private(set) var isSavingEdits = false
    /// Surfaced banner for any action failure (load, upload, archive, save).
    var errorMessage: String?

    private let itemId: String
    private let repository: WardrobeRepository
    @ObservationIgnored private var photoPollTask: Task<Void, Never>?

    init(itemId: String, repository: WardrobeRepository) {
        self.itemId = itemId
        self.repository = repository
    }

    deinit {
        photoPollTask?.cancel()
    }

    // MARK: Loading

    func load() async {
        state = .loading
        do {
            async let itemResult = repository.item(id: itemId)
            async let photosResult = repository.photos(itemId: itemId)
            let (loadedItem, loadedPhotos) = try await (itemResult, photosResult)
            item = loadedItem
            photos = loadedPhotos
            errorMessage = nil
            state = .loaded
        } catch {
            guard !Self.isCancellation(error) else { return }
            state = .failed(Self.message(for: error, fallback: "Couldn't load this item."))
        }
    }

    // MARK: Status (archive/unarchive)

    /// Toggles active <-> archived. Returns whether it succeeded so the
    /// screen can dismiss the confirmation UI and notify the tab shell (Today
    /// and Profile/Stats invalidate immediately on the server).
    @discardableResult
    func setStatus(_ newStatus: WardrobeItemStatus) async -> Bool {
        guard !isChangingStatus else { return false }
        isChangingStatus = true
        defer { isChangingStatus = false }
        do {
            let updated = try await repository.setStatus(itemId: itemId, status: newStatus)
            item = updated
            errorMessage = nil
            return true
        } catch {
            errorMessage = Self.message(
                for: error,
                fallback: newStatus == .archived ? "Couldn't archive this item." : "Couldn't unarchive this item."
            )
            return false
        }
    }

    // MARK: Edits (price / brand)

    func saveEdits(purchasePrice: Double?, brand: String?) async -> Bool {
        guard !isSavingEdits else { return false }
        isSavingEdits = true
        defer { isSavingEdits = false }
        do {
            let body = WardrobeItemUpdateRequest(
                purchasePrice: purchasePrice,
                brand: (brand?.trimmingCharacters(in: .whitespaces)).flatMap { $0.isEmpty ? nil : $0 }
            )
            let updated = try await repository.update(itemId: itemId, body: body)
            // The PUT response mirrors the list-entry shape (no `photos`),
            // but the gallery reads from `photos` (this view model's own
            // separately-polled array), never from `item.photos` — so there's
            // nothing to preserve by hand here.
            item = updated
            errorMessage = nil
            return true
        } catch {
            errorMessage = Self.message(for: error, fallback: "Couldn't save your changes.")
            return false
        }
    }

    // MARK: Photos

    /// Uploads a new photo, then polls `GET /photos` until it shows up with a
    /// non-nil `thumbnailUrl` (mirrors `WardrobeViewModel`'s
    /// pending/processing poll: ~2s interval, ~90s cap) or the cap expires —
    /// whichever comes first, the tile just stops spinning either way.
    ///
    /// TODO(RI-6): duplicate-upload detection isn't available yet — this is
    /// the natural pre-upload call site for it once it ships.
    func addPhoto(imageData: Data) async {
        guard !isUploadingPhoto else { return }
        isUploadingPhoto = true
        photoPollTask?.cancel()
        do {
            let response = try await repository.addPhoto(itemId: itemId, imageData: imageData)
            errorMessage = nil
            await refreshPhotos()
            startPolling(forPhotoId: response.id)
        } catch {
            isUploadingPhoto = false
            errorMessage = Self.message(for: error, fallback: "Couldn't add that photo.")
        }
    }

    private func startPolling(forPhotoId photoId: String) {
        photoPollTask = Task { [weak self] in
            guard let self else { return }
            let clock = ContinuousClock()
            let deadline = clock.now.advanced(by: .seconds(90))
            defer { self.isUploadingPhoto = false }
            while !Task.isCancelled {
                try? await clock.sleep(for: .seconds(2))
                guard !Task.isCancelled else { return }
                await self.refreshPhotos()
                let isReady = self.photos.first { $0.id == photoId }?.thumbnailUrl != nil
                if isReady || clock.now >= deadline { return }
            }
        }
    }

    private func refreshPhotos() async {
        guard let refreshed = try? await repository.photos(itemId: itemId) else { return }
        photos = refreshed
    }

    func deletePhoto(_ photoId: String) async {
        do {
            try await repository.deletePhoto(itemId: itemId, photoId: photoId)
            photos.removeAll { $0.id == photoId }
        } catch {
            errorMessage = Self.message(for: error, fallback: "Couldn't remove that photo.")
        }
    }

    func stopPolling() {
        photoPollTask?.cancel()
        photoPollTask = nil
    }

    // MARK: Errors

    private static func isCancellation(_ error: any Error) -> Bool {
        if error is CancellationError { return true }
        if (error as? URLError)?.code == .cancelled { return true }
        if case let APIError.network(underlying) = error {
            return isCancellation(underlying)
        }
        return false
    }

    private static func message(for error: any Error, fallback: String) -> String {
        switch error {
        case APIError.network:
            return "Can't reach ATTREQ. Check your connection."
        case let APIError.http(_, body):
            if let object = try? JSONSerialization.jsonObject(with: body) as? [String: Any],
               let detail = object["detail"] as? String,
               !detail.isEmpty {
                return detail
            }
            return fallback
        default:
            return fallback
        }
    }
}

// MARK: - View

struct WardrobeItemDetailView: View {
    let itemId: String
    let repository: WardrobeRepository
    /// Fired after a successful archive/unarchive so the tab shell can
    /// invalidate Today/Profile/Stats (RI-7).
    var onStatusChanged: (() -> Void)?

    @State private var model: WardrobeItemDetailViewModel
    @State private var showLibrary = false
    @State private var showArchiveConfirm = false
    @State private var priceText: String = ""
    @State private var brandText: String = ""
    @FocusState private var isPriceFocused: Bool
    @FocusState private var isBrandFocused: Bool

    init(itemId: String, repository: WardrobeRepository, onStatusChanged: (() -> Void)? = nil) {
        self.itemId = itemId
        self.repository = repository
        self.onStatusChanged = onStatusChanged
        _model = State(initialValue: WardrobeItemDetailViewModel(itemId: itemId, repository: repository))
    }

    var body: some View {
        ZStack {
            Theme.bg.ignoresSafeArea()

            ScrollView(showsIndicators: false) {
                VStack(alignment: .leading, spacing: 0) {
                    switch model.state {
                    case .loading:
                        loadingState
                    case let .failed(message):
                        failedState(message)
                    case .loaded:
                        if let item = model.item {
                            content(for: item)
                        }
                    }
                }
                .padding(.horizontal, 24)
                .padding(.top, 10)
                .padding(.bottom, 40)
            }
        }
        .navigationTitle("Item")
        .navigationBarTitleDisplayMode(.inline)
        .task {
            await model.load()
            guard !Task.isCancelled else { return }
            if let item = model.item {
                priceText = item.purchasePrice.map { String(format: "%.2f", $0) } ?? ""
                brandText = item.brand ?? ""
            }
        }
        .onDisappear { model.stopPolling() }
        .photoLibraryPicker(isPresented: $showLibrary) { data in
            Task { await model.addPhoto(imageData: data) }
        }
        .confirmationDialog(
            model.item?.status == .archived ? "Unarchive item" : "Archive item",
            isPresented: $showArchiveConfirm,
            titleVisibility: .visible
        ) {
            Button(model.item?.status == .archived ? "Unarchive" : "Archive", role: model.item?.status == .archived ? nil : .destructive) {
                Task {
                    let newStatus: WardrobeItemStatus = model.item?.status == .archived ? .active : .archived
                    if await model.setStatus(newStatus) {
                        onStatusChanged?()
                    }
                }
            }
            Button("Cancel", role: .cancel) {}
        } message: {
            Text(
                model.item?.status == .archived
                    ? "This brings the item back into Today and your active wardrobe."
                    : "Archiving keeps this item's outfit history but removes it from Today and your active wardrobe — for items you've sold, donated, or put away."
            )
        }
    }

    // MARK: - States

    private var loadingState: some View {
        HStack {
            Spacer()
            ProgressView().tint(Theme.t2)
            Spacer()
        }
        .padding(.top, 80)
    }

    private func failedState(_ message: String) -> some View {
        VStack(alignment: .leading, spacing: 12) {
            errorBanner(message)
            Button {
                Task { await model.load() }
            } label: {
                MonoLabel("Retry", size: 10, color: Theme.text)
                    .padding(.vertical, 9)
                    .padding(.horizontal, 18)
                    .overlay(Capsule().strokeBorder(Theme.border, lineWidth: 1))
            }
            .buttonStyle(.plain)
        }
        .padding(.top, 40)
    }

    // MARK: - Loaded content

    @ViewBuilder
    private func content(for item: WardrobeItem) -> some View {
        header(for: item)
            .padding(.bottom, 16)

        if let message = model.errorMessage {
            errorBanner(message)
                .padding(.bottom, 12)
        }

        gallery
            .padding(.bottom, 20)

        detailsCard(for: item)
            .padding(.bottom, 16)

        editCard
            .padding(.bottom, 20)

        archiveButton(for: item)
    }

    private func header(for item: WardrobeItem) -> some View {
        VStack(alignment: .leading, spacing: 5) {
            HStack(spacing: 8) {
                MonoLabel("Piece")
                if item.status == .archived {
                    AttreqPill("Archived", variant: .muted)
                }
            }
            Text(item.category?.capitalized ?? "Piece")
                .font(.attreqDisplay(28, weight: .semiBold, italic: true))
                .foregroundStyle(Theme.text)
        }
    }

    // MARK: - Gallery

    /// All photos for the item: the fetched `photos` list (already includes
    /// the primary/original upload — see `DELETE .../photos/{id}` rejecting
    /// deletion of the primary, which only makes sense if it's IN this list)
    /// sorted primary-first. Falls back to a single tile built from the
    /// item's own image fields if the endpoint ever returns nothing (e.g. a
    /// legacy item predating the photos table).
    private var galleryPhotos: [GalleryTile] {
        if !model.photos.isEmpty {
            return model.photos
                .sorted { $0.isPrimary && !$1.isPrimary }
                .map { GalleryTile(id: $0.id, imageURL: $0.thumbnailUrl ?? $0.processedImageUrl ?? $0.originalImageUrl, isDeletable: !$0.isPrimary) }
        }
        guard let item = model.item else { return [] }
        let fallbackURL = item.thumbnailUrl ?? item.processedImageUrl ?? item.originalImageUrl
        return [GalleryTile(id: "primary", imageURL: fallbackURL, isDeletable: false)]
    }

    private struct GalleryTile: Identifiable {
        let id: String
        let imageURL: String
        let isDeletable: Bool
    }

    private var gallery: some View {
        ScrollView(.horizontal, showsIndicators: false) {
            HStack(spacing: 10) {
                ForEach(galleryPhotos) { tile in
                    galleryTile(tile)
                }
                addPhotoTile
            }
        }
    }

    private func galleryTile(_ tile: GalleryTile) -> some View {
        let shape = RoundedRectangle(cornerRadius: 16, style: .continuous)
        return AsyncImage(url: AppConfig.absoluteMediaURL(tile.imageURL)) { phase in
            switch phase {
            case let .success(image):
                image.resizable().scaledToFill()
            default:
                shape.fill(Theme.surface).overlay {
                    if phase.error == nil {
                        ProgressView().controlSize(.small).tint(Theme.t3)
                    } else {
                        AttreqIcon.image.view(size: 18, color: Theme.t3)
                    }
                }
            }
        }
        .frame(width: 130, height: 160)
        .clipShape(shape)
        .overlay(shape.strokeBorder(Theme.border, lineWidth: 1))
        .overlay(alignment: .topTrailing) {
            if tile.isDeletable {
                Button {
                    Task { await model.deletePhoto(tile.id) }
                } label: {
                    Circle()
                        .fill(Color.black.opacity(0.45))
                        .frame(width: 22, height: 22)
                        .overlay { Image(systemName: "xmark").font(.system(size: 9, weight: .medium)).foregroundStyle(.white) }
                        .frame(width: 34, height: 34)
                        .contentShape(Rectangle())
                }
                .buttonStyle(.plain)
                .accessibilityLabel("Remove photo")
            }
        }
    }

    private var addPhotoTile: some View {
        let shape = RoundedRectangle(cornerRadius: 16, style: .continuous)
        return Button {
            showLibrary = true
        } label: {
            shape
                .strokeBorder(Theme.border, style: StrokeStyle(lineWidth: 1.5, dash: [5, 4]))
                .overlay {
                    if model.isUploadingPhoto {
                        ProgressView().controlSize(.small).tint(Theme.t3)
                    } else {
                        VStack(spacing: 6) {
                            AttreqIcon.plus.view(size: 16, color: Theme.t3)
                            MonoLabel("Add photo", size: 8)
                        }
                    }
                }
        }
        .buttonStyle(.plain)
        .frame(width: 130, height: 160)
        .disabled(model.isUploadingPhoto)
        .accessibilityLabel("Add photo")
        .accessibilityIdentifier("button-add-photo")
    }

    // MARK: - Details card

    private func detailsCard(for item: WardrobeItem) -> some View {
        VStack(alignment: .leading, spacing: 10) {
            detailRow("Color", value: item.colorPrimary ?? "—")
            if let pattern = item.pattern {
                divider
                detailRow("Pattern", value: pattern)
            }
            divider
            detailRow("Worn in", value: "\(item.wearCount) outfit\(item.wearCount == 1 ? "" : "s")")
        }
        .attreqCard(padding: 16)
    }

    private func detailRow(_ label: String, value: String) -> some View {
        HStack {
            MonoLabel(label)
            Spacer()
            Text(value.capitalized)
                .font(.attreqBody(13, weight: .medium))
                .foregroundStyle(Theme.text)
        }
    }

    private var divider: some View {
        Rectangle().fill(Theme.borderSoft).frame(height: 1)
    }

    // MARK: - Editable price / brand

    private var editCard: some View {
        VStack(alignment: .leading, spacing: 16) {
            AttreqUnderlineInput(
                label: "Brand",
                text: $brandText,
                focus: $isBrandFocused
            )
            AttreqUnderlineInput(
                label: "Purchase price ($)",
                text: $priceText,
                keyboard: .decimalPad,
                focus: $isPriceFocused
            )
            AttreqPrimaryButton(
                "Save",
                isLoading: model.isSavingEdits,
                action: saveEdits
            )
            .accessibilityIdentifier("button-save-item-details")
        }
    }

    private func saveEdits() {
        isPriceFocused = false
        isBrandFocused = false
        let trimmedPrice = priceText.trimmingCharacters(in: .whitespaces)
        let price = trimmedPrice.isEmpty ? nil : Double(trimmedPrice)
        Task { _ = await model.saveEdits(purchasePrice: price, brand: brandText) }
    }

    // MARK: - Archive / unarchive

    private func archiveButton(for item: WardrobeItem) -> some View {
        Button {
            showArchiveConfirm = true
        } label: {
            HStack(spacing: 8) {
                if model.isChangingStatus {
                    ProgressView().controlSize(.small).tint(Theme.clay)
                } else {
                    AttreqIcon.archive.view(size: 14, color: Theme.clay)
                }
                MonoLabel(item.status == .archived ? "Unarchive" : "Archive", size: 10, color: Theme.clay)
            }
            .frame(maxWidth: .infinity)
            .padding(.vertical, 13)
            .overlay(Capsule().strokeBorder(Theme.clay.opacity(0.4), lineWidth: 1))
        }
        .buttonStyle(.plain)
        .disabled(model.isChangingStatus)
        .accessibilityIdentifier("button-archive-item")
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

#Preview("Item detail") {
    let auth = AuthSession(keychain: KeychainStore(), baseURL: AppConfig.apiBaseURL)
    let client = APIClient(baseURL: AppConfig.apiBaseURL, authSession: auth)
    NavigationStack {
        WardrobeItemDetailView(itemId: "preview-1", repository: WardrobeRepository(apiClient: client))
    }
}
