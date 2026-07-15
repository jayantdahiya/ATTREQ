//
//  CameraPicker.swift
//  ATTREQ
//
//  UIImagePickerController(.camera) wrapped for SwiftUI (M2-WP3). Present it
//  from a sheet/fullScreenCover; it dismisses itself on capture or cancel.
//  The camera is unavailable in the simulator — gate presentation on
//  `CameraPicker.isAvailable` and disable the camera tile when false.
//
//  No #Preview: UIImagePickerController's camera cannot render in previews.
//

import SwiftUI
import UIKit

/// SwiftUI wrapper around the system camera capture UI.
struct CameraPicker: UIViewControllerRepresentable {
    /// Whether a camera source exists on this device (false in the simulator).
    @MainActor
    static var isAvailable: Bool {
        UIImagePickerController.isSourceTypeAvailable(.camera)
    }

    private let onImage: (UIImage) -> Void

    /// - Parameter onImage: called with the captured photo before dismissal.
    init(onImage: @escaping (UIImage) -> Void) {
        self.onImage = onImage
    }

    func makeUIViewController(context: Context) -> UIImagePickerController {
        let picker = UIImagePickerController()
        picker.sourceType = .camera
        picker.cameraCaptureMode = .photo
        picker.delegate = context.coordinator
        context.coordinator.dismiss = context.environment.dismiss
        return picker
    }

    func updateUIViewController(_ uiViewController: UIImagePickerController, context: Context) {
        context.coordinator.onImage = onImage
        // `dismiss` must come from `context.environment` — reading an
        // `@Environment` property wrapper outside body/update contexts
        // returns a default (no-op) action.
        context.coordinator.dismiss = context.environment.dismiss
    }

    func makeCoordinator() -> Coordinator {
        Coordinator(onImage: onImage)
    }

    /// UIKit delegate bridge. MainActor-isolated: UIImagePickerController only
    /// calls its delegate on the main thread.
    @MainActor
    final class Coordinator: NSObject, UIImagePickerControllerDelegate, UINavigationControllerDelegate {
        var onImage: (UIImage) -> Void
        /// Set from `context.environment` in make/update; nil only before the
        /// first `makeUIViewController`.
        var dismiss: DismissAction?

        init(onImage: @escaping (UIImage) -> Void) {
            self.onImage = onImage
        }

        func imagePickerController(
            _ picker: UIImagePickerController,
            didFinishPickingMediaWithInfo info: [UIImagePickerController.InfoKey: Any]
        ) {
            let image = (info[.editedImage] as? UIImage) ?? (info[.originalImage] as? UIImage)
            if let image {
                onImage(image)
            }
            dismiss?()
        }

        func imagePickerControllerDidCancel(_ picker: UIImagePickerController) {
            dismiss?()
        }
    }
}
