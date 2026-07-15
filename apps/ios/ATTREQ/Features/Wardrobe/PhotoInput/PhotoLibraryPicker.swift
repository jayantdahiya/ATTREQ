//
//  PhotoLibraryPicker.swift
//  ATTREQ
//
//  Single-photo library picker for wardrobe upload (M2-WP3), mirroring the RN
//  app's `launchImageLibraryAsync({ mediaTypes: ['images'] })` flow. Wraps
//  SwiftUI's `.photosPicker` and pipes the selection through
//  `ImageProcessor.jpegDataForUpload` (decode → downscale → JPEG) off the main
//  actor before delivering upload-ready data on the main actor.
//

import PhotosUI
import SwiftUI

extension View {
    /// Presents the system photo library picker for a single image.
    ///
    /// - Parameters:
    ///   - isPresented: controls picker presentation; reset to `false` by the
    ///     system when the user picks or cancels.
    ///   - onImageData: called on the main actor with downscaled JPEG data
    ///     ready for `POST /wardrobe/upload`. Not called if loading or
    ///     decoding fails.
    func photoLibraryPicker(
        isPresented: Binding<Bool>,
        onImageData: @escaping (Data) -> Void
    ) -> some View {
        modifier(PhotoLibraryPickerModifier(isPresented: isPresented, onImageData: onImageData))
    }
}

private struct PhotoLibraryPickerModifier: ViewModifier {
    let isPresented: Binding<Bool>
    let onImageData: (Data) -> Void

    @State private var selection: PhotosPickerItem?

    func body(content: Content) -> some View {
        content
            .photosPicker(isPresented: isPresented, selection: $selection, matching: .images)
            .onChange(of: selection) { _, newValue in
                guard let item = newValue else { return }
                Task { await handleSelection(item) }
            }
    }

    @MainActor
    private func handleSelection(_ item: PhotosPickerItem) async {
        // Clear the selection once handled so picking the same photo again
        // still triggers `onChange`.
        defer { selection = nil }

        guard let rawData = try? await item.loadTransferable(type: Data.self) else {
            return
        }
        // Decode/downscale/encode off the main actor; it can take a moment
        // for large photos.
        let processed = await Task.detached(priority: .userInitiated) {
            ImageProcessor.jpegDataForUpload(rawData: rawData)
        }.value
        guard let processed else { return }
        onImageData(processed)
    }
}

#Preview("Photo library picker") {
    @Previewable @State var isPresented = false
    @Previewable @State var pickedBytes: Int?

    VStack(spacing: 16) {
        Button("Pick a photo") {
            isPresented = true
        }
        if let pickedBytes {
            Text("Picked JPEG: \(pickedBytes) bytes")
                .font(.footnote)
                .foregroundStyle(.secondary)
        }
    }
    .photoLibraryPicker(isPresented: $isPresented) { data in
        pickedBytes = data.count
    }
}
