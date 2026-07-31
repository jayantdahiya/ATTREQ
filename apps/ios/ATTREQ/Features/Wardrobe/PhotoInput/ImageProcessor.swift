//
//  ImageProcessor.swift
//  ATTREQ
//
//  Prepares picked/captured photos for wardrobe upload (M2-WP3):
//  decode → downscale (only when larger than `maxDimension`) → JPEG-encode.
//  Rendering through UIGraphicsImageRenderer also bakes in the EXIF
//  orientation, so the backend always receives an upright image.
//
//  The backend defines `MAX_UPLOAD_SIZE_MB=10` but does not enforce it, so
//  this client-side downscale is the effective size guard: a 1600 px-max
//  JPEG at quality 0.85 stays far below 10 MB.
//

import UIKit

/// Stateless image pipeline for wardrobe uploads.
enum ImageProcessor {
    /// Default longest-side cap, in pixels.
    static let defaultMaxDimension: CGFloat = 1600
    /// Default JPEG compression quality.
    static let defaultQuality: CGFloat = 0.85

    /// Downscales `image` so its longest side is at most `maxDimension` pixels
    /// (preserving aspect ratio; images already within bounds keep their size),
    /// strips orientation by re-rendering, and returns JPEG data.
    ///
    /// Safe to call off the main actor — `UIGraphicsImageRenderer`, `UIImage.draw`,
    /// and `jpegData` are thread-safe.
    static func jpegDataForUpload(
        _ image: UIImage,
        maxDimension: CGFloat = ImageProcessor.defaultMaxDimension,
        quality: CGFloat = ImageProcessor.defaultQuality
    ) -> Data? {
        // `size` is in points; multiply by `scale` for pixel dimensions.
        let pixelSize = CGSize(
            width: image.size.width * image.scale,
            height: image.size.height * image.scale
        )
        guard pixelSize.width >= 1, pixelSize.height >= 1, maxDimension >= 1 else {
            return nil
        }

        let longestSide = max(pixelSize.width, pixelSize.height)
        let ratio = longestSide > maxDimension ? maxDimension / longestSide : 1
        let targetSize = CGSize(
            width: max(1, (pixelSize.width * ratio).rounded()),
            height: max(1, (pixelSize.height * ratio).rounded())
        )

        // scale = 1 so the rendered bitmap's pixel size equals `targetSize`
        // regardless of the device's screen scale. Rendering always (even when
        // not downscaling) normalizes orientation, since `draw(in:)` applies it.
        let format = UIGraphicsImageRendererFormat()
        format.scale = 1
        // JPEG has no alpha channel; an opaque context avoids pointless
        // alpha compositing for transparent (e.g. PNG) sources.
        format.opaque = true
        let renderer = UIGraphicsImageRenderer(size: targetSize, format: format)
        let rendered = renderer.image { _ in
            image.draw(in: CGRect(origin: .zero, size: targetSize))
        }
        return rendered.jpegData(compressionQuality: quality)
    }

    /// Decodes raw image data (JPEG, PNG, HEIC, …) and runs it through
    /// ``jpegDataForUpload(_:maxDimension:quality:)``.
    static func jpegDataForUpload(
        rawData: Data,
        maxDimension: CGFloat = ImageProcessor.defaultMaxDimension,
        quality: CGFloat = ImageProcessor.defaultQuality
    ) -> Data? {
        guard let image = UIImage(data: rawData) else { return nil }
        return jpegDataForUpload(image, maxDimension: maxDimension, quality: quality)
    }
}
