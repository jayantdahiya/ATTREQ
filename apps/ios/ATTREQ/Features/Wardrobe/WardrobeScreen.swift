//
//  WardrobeScreen.swift
//  ATTREQ
//
//  Wardrobe screen (M2, artboard 06). Pixel source:
//  assets/design/ios-redesign-v2/attreq-app.jsx → ATTREQWardrobe.
//  Header "Closet / *Wardrobe*" + search circle, piece-count line, category
//  chips, two dashed upload tiles, two-column staggered grid.
//

import SwiftUI

struct WardrobeScreen: View {
    /// Owned by `MainTabsView` so state survives tab switches.
    let viewModel: WardrobeViewModel

    @State private var showCamera = false
    @State private var showLibrary = false

    /// Width/height ratios cycled across the grid to echo the design's
    /// staggered masonry heights (col1 208/174/146, col2 172/190/186 at
    /// ~160pt-wide tiles).
    private static let tileAspectRatios: [CGFloat] = [0.77, 0.93, 0.92, 0.84, 1.10, 0.86]

    var body: some View {
        ZStack {
            Theme.bg.ignoresSafeArea()

            ScrollView(showsIndicators: false) {
                VStack(alignment: .leading, spacing: 0) {
                    header
                    countLine
                        .padding(.bottom, 12)
                    chipsRow
                        .padding(.bottom, 12)
                    uploadTiles
                        .padding(.bottom, 14)
                    if let message = viewModel.errorMessage {
                        errorBanner(message)
                            .padding(.bottom, 12)
                    }
                    gridSection
                }
                .padding(.horizontal, 24)
                .padding(.top, 10)
                // Clearance for the floating tab bar.
                .padding(.bottom, 110)
            }
            .refreshable { await viewModel.refresh() }
        }
        .task {
            await viewModel.loadInitial()
            // The task is cancelled when the screen disappears mid-load —
            // don't kick off a poll loop for a screen that's gone.
            guard !Task.isCancelled else { return }
            viewModel.startPollingIfNeeded()
        }
        .onDisappear { viewModel.stopPolling() }
        // Full-screen: UIImagePickerController's camera source is documented
        // to require full-screen presentation (a sheet misbehaves).
        .fullScreenCover(isPresented: $showCamera) {
            CameraPicker { image in
                Task {
                    // Downscale/encode off the main actor, mirroring the
                    // library path in `PhotoLibraryPickerModifier`.
                    let data = await Task.detached(priority: .userInitiated) {
                        ImageProcessor.jpegDataForUpload(image)
                    }.value
                    guard let data else { return }
                    await viewModel.upload(imageData: data)
                }
            }
            .ignoresSafeArea()
        }
        .photoLibraryPicker(isPresented: $showLibrary) { data in
            Task { await viewModel.upload(imageData: data) }
        }
    }

    // MARK: - Header

    private var header: some View {
        HStack(alignment: .top) {
            VStack(alignment: .leading, spacing: 5) {
                MonoLabel("Closet")
                Text("Wardrobe")
                    .font(.attreqDisplay(28, weight: .semiBold, italic: true))
                    .foregroundStyle(Theme.text)
            }
            Spacer()
            // Inert for now — search ships post-M2.
            Circle()
                .strokeBorder(Theme.border, lineWidth: 1)
                .frame(width: 34, height: 34)
                .overlay(AttreqIcon.search.view(size: 14, color: Theme.t2))
                .padding(.top, 16)
        }
        .padding(.bottom, 3)
    }

    private var countLine: some View {
        let noun = viewModel.totalCount == 1 ? "piece" : "pieces"
        var line = Text("\(viewModel.totalCount) \(noun)")
            .font(.attreqBody(13, weight: .medium))
            .foregroundStyle(Theme.accent)
        if let relative = viewModel.lastAddedRelative {
            line = line + Text(" — last added \(relative)")
                .font(.attreqBody(13))
                .foregroundStyle(Theme.t3)
        }
        return line
    }

    // MARK: - Category chips

    private var chipsRow: some View {
        ScrollView(.horizontal, showsIndicators: false) {
            HStack(spacing: 6) {
                ForEach(WardrobeFilter.allCases, id: \.self) { filter in
                    WardrobeFilterChip(
                        filter.label,
                        selected: viewModel.selectedCategory == filter
                    ) {
                        viewModel.selectedCategory = filter
                    }
                }
            }
        }
        // Let chips scroll edge-to-edge while content stays on the 24pt grid.
        .padding(.horizontal, -24)
        .contentMargins(.horizontal, 24, for: .scrollContent)
    }

    // MARK: - Upload tiles

    private var uploadTiles: some View {
        HStack(spacing: 9) {
            UploadTile(
                icon: .camera,
                label: "Camera",
                sublabel: "Capture a piece",
                isEnabled: CameraPicker.isAvailable && !viewModel.isUploading
            ) {
                showCamera = true
            }
            .accessibilityIdentifier("tile-camera")

            UploadTile(
                icon: .image,
                label: "Library",
                sublabel: "From photos",
                isEnabled: !viewModel.isUploading
            ) {
                // UI-test hook: PHPicker's remote view doesn't reliably accept
                // synthesized taps, so `-uitest-autopick-photo` bypasses the
                // system picker and feeds a synthetic JPEG through the exact
                // same upload path the picker callback uses.
                if ProcessInfo.processInfo.arguments.contains("-uitest-autopick-photo") {
                    Task {
                        if let data = Self.syntheticTestPhotoJPEG() {
                            await viewModel.upload(imageData: data)
                        }
                    }
                } else {
                    showLibrary = true
                }
            }
            .accessibilityIdentifier("tile-library")
        }
    }

    // MARK: - Error banner

    private func errorBanner(_ message: String) -> some View {
        BodyText(message, size: 13, color: Theme.clay)
            .frame(maxWidth: .infinity, alignment: .leading)
            .padding(.vertical, 10)
            .padding(.horizontal, 13)
            .background(Theme.claySoft, in: RoundedRectangle(cornerRadius: 12, style: .continuous))
    }

    // MARK: - Grid

    @ViewBuilder
    private var gridSection: some View {
        let items = viewModel.filteredItems
        if viewModel.isUploading {
            HStack(spacing: 8) {
                ProgressView()
                    .controlSize(.small)
                    .tint(Theme.t3)
                MonoLabel("Uploading")
            }
            .padding(.bottom, 12)
        }
        if items.isEmpty {
            if viewModel.isLoading {
                loadingState
            } else {
                emptyState
            }
        } else {
            masonryGrid(items)
        }
    }

    private func masonryGrid(_ items: [WardrobeItem]) -> some View {
        // Alternate items across the two columns to keep visual order
        // left-to-right, matching the design's staggered layout.
        let indexed = Array(items.enumerated())
        let left = indexed.filter { $0.offset.isMultiple(of: 2) }
        let right = indexed.filter { !$0.offset.isMultiple(of: 2) }
        return HStack(alignment: .top, spacing: 10) {
            column(left)
            column(right)
        }
    }

    private func column(_ entries: [(offset: Int, element: WardrobeItem)]) -> some View {
        LazyVStack(alignment: .leading, spacing: 10) {
            ForEach(entries, id: \.element.id) { entry in
                WardrobeItemCard(
                    item: entry.element,
                    imageAspectRatio: Self.tileAspectRatios[entry.offset % Self.tileAspectRatios.count]
                )
                .onAppear {
                    Task { await viewModel.loadMoreIfNeeded(currentItem: entry.element) }
                }
            }
        }
        .frame(maxWidth: .infinity)
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
            MonoLabel("Nothing here yet", size: 11)
            BodyText(
                viewModel.selectedCategory == .all
                    ? "Capture a piece with the camera or add one from your photo library to start your closet."
                    : "No pieces in this category yet. Add one, or browse All.",
                size: 13
            )
            .multilineTextAlignment(.center)
        }
        .frame(maxWidth: .infinity)
        .padding(.top, 48)
        .padding(.horizontal, 16)
    }

    /// Deterministic stand-in photo for `-uitest-autopick-photo`: a plain
    /// garment-like color block, valid JPEG, well under the upload cap.
    private static func syntheticTestPhotoJPEG() -> Data? {
        let size = CGSize(width: 800, height: 1000)
        let format = UIGraphicsImageRendererFormat()
        format.scale = 1
        format.opaque = true
        let image = UIGraphicsImageRenderer(size: size, format: format).image { context in
            UIColor(red: 0.35, green: 0.45, blue: 0.65, alpha: 1).setFill()
            context.fill(CGRect(origin: .zero, size: size))
            UIColor(white: 0.95, alpha: 1).setFill()
            context.fill(CGRect(x: 120, y: 150, width: 560, height: 700))
        }
        return image.jpegData(compressionQuality: 0.85)
    }
}

// MARK: - Small filter chip (artboard-06 variant)

/// Wardrobe's compact chip — 12pt DM Sans medium, 5pt/12pt padding —
/// deliberately smaller than the design system's `AttreqChip` (13pt, 6/14),
/// per the `ATTREQWardrobe` artboard.
private struct WardrobeFilterChip: View {
    let label: String
    let selected: Bool
    let action: () -> Void

    init(_ label: String, selected: Bool, action: @escaping () -> Void) {
        self.label = label
        self.selected = selected
        self.action = action
    }

    var body: some View {
        Button(action: action) {
            Text(label)
                .font(.attreqBody(12, weight: .medium))
                .foregroundStyle(selected ? Theme.bg : Theme.t2)
                .padding(.vertical, 5)
                .padding(.horizontal, 12)
                .background {
                    if selected {
                        Capsule().fill(Theme.text)
                    } else {
                        Capsule().strokeBorder(Theme.border, lineWidth: 1)
                    }
                }
                // >=44pt tappable height without growing the visible capsule
                // (same trick as `AttreqChip`).
                .padding(.vertical, 9)
                .contentShape(Rectangle())
        }
        .buttonStyle(.plain)
        .padding(.vertical, -9)
        .accessibilityAddTraits(selected ? [.isSelected] : [])
        .accessibilityIdentifier("chip-\(label)")
    }
}

// MARK: - Upload tile

/// Dashed add-a-piece tile (Camera / Library) from artboard 06.
private struct UploadTile: View {
    let icon: AttreqIcon
    let label: String
    let sublabel: String
    var isEnabled: Bool = true
    let action: () -> Void

    private static let shape = RoundedRectangle(cornerRadius: 16, style: .continuous)

    var body: some View {
        Button(action: action) {
            VStack(alignment: .leading, spacing: 5) {
                Circle()
                    .fill(Theme.accentSoft)
                    .frame(width: 28, height: 28)
                    .overlay(icon.view(size: 13, color: Theme.t2))
                Text(label)
                    .font(.attreqBody(13, weight: .medium))
                    .foregroundStyle(Theme.text)
                MonoLabel(sublabel)
                    .lineLimit(1)
            }
            .frame(maxWidth: .infinity, alignment: .leading)
            .padding(.vertical, 12)
            .padding(.horizontal, 13)
            .background(Self.shape.fill(Theme.surface))
            .overlay {
                Self.shape.strokeBorder(
                    Theme.border,
                    style: StrokeStyle(lineWidth: 1.5, dash: [5, 4])
                )
            }
            .contentShape(Self.shape)
            .opacity(isEnabled ? 1 : 0.45)
        }
        .buttonStyle(.plain)
        .disabled(!isEnabled)
        .accessibilityLabel("\(label) — \(sublabel)")
    }
}

// MARK: - Previews

#Preview("Wardrobe") {
    let auth = AuthSession(keychain: KeychainStore(), baseURL: AppConfig.apiBaseURL)
    let client = APIClient(baseURL: AppConfig.apiBaseURL, authSession: auth)
    WardrobeScreen(
        viewModel: WardrobeViewModel(repository: WardrobeRepository(apiClient: client))
    )
}
