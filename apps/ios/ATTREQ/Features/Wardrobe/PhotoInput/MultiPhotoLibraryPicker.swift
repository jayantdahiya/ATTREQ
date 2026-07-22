//
//  MultiPhotoLibraryPicker.swift
//  ATTREQ
//
//  Multi-photo library picker for Style DNA onboarding (M3-WP2), mirroring
//  the RN app's `launchImageLibraryAsync({ allowsMultipleSelection: true,
//  selectionLimit })` flow. Same shape as the single-photo
//  `PhotoLibraryPicker`: wraps SwiftUI's `.photosPicker` and pipes every
//  selection through `ImageProcessor.jpegDataForUpload` off the main actor
//  before delivering upload-ready data on the main actor.
//

import PhotosUI
import SwiftUI

extension View {
    /// Presents the system photo library picker for multiple images.
    ///
    /// - Parameters:
    ///   - isPresented: controls picker presentation; reset to `false` by the
    ///     system when the user confirms or cancels.
    ///   - maxSelectionCount: selection cap for this presentation (e.g. the
    ///     remaining Style DNA slots); clamped to at least 1.
    ///   - onImagesData: called once on the main actor with downscaled JPEG
    ///     data for every image that loaded and decoded successfully, in
    ///     selection order. Not called if nothing usable was picked.
    func multiPhotoLibraryPicker(
        isPresented: Binding<Bool>,
        maxSelectionCount: Int,
        onImagesData: @escaping ([Data]) -> Void
    ) -> some View {
        modifier(
            MultiPhotoLibraryPickerModifier(
                isPresented: isPresented,
                maxSelectionCount: max(1, maxSelectionCount),
                onImagesData: onImagesData
            )
        )
    }
}

private struct MultiPhotoLibraryPickerModifier: ViewModifier {
    let isPresented: Binding<Bool>
    let maxSelectionCount: Int
    let onImagesData: ([Data]) -> Void

    @State private var selection: [PhotosPickerItem] = []

    func body(content: Content) -> some View {
        content
            .photosPicker(
                isPresented: isPresented,
                selection: $selection,
                maxSelectionCount: maxSelectionCount,
                matching: .images
            )
            .onChange(of: selection) { _, newValue in
                guard !newValue.isEmpty else { return }
                Task { await handleSelection(newValue) }
            }
    }

    @MainActor
    private func handleSelection(_ items: [PhotosPickerItem]) async {
        // Clear the selection once handled so picking the same photos again
        // still triggers `onChange`.
        defer { selection = [] }

        var processed: [Data] = []
        for item in items {
            guard let rawData = try? await item.loadTransferable(type: Data.self) else {
                continue
            }
            // Decode/downscale/encode off the main actor; large photos take
            // a moment each (same policy as `PhotoLibraryPickerModifier`).
            let jpeg = await Task.detached(priority: .userInitiated) {
                ImageProcessor.jpegDataForUpload(rawData: rawData)
            }.value
            if let jpeg {
                processed.append(jpeg)
            }
        }
        guard !processed.isEmpty else { return }
        onImagesData(processed)
    }
}

#Preview("Multi photo library picker") {
    @Previewable @State var isPresented = false
    @Previewable @State var pickedCount: Int?

    VStack(spacing: 16) {
        Button("Pick up to 5 photos") {
            isPresented = true
        }
        if let pickedCount {
            Text("Picked \(pickedCount) JPEGs")
                .font(.footnote)
                .foregroundStyle(.secondary)
        }
    }
    .multiPhotoLibraryPicker(isPresented: $isPresented, maxSelectionCount: 5) { data in
        pickedCount = data.count
    }
}
