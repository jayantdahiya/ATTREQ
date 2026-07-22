//
//  ImageProcessorTests.swift
//  ATTREQTests
//
//  M2-WP3: unit tests for the wardrobe photo upload pipeline
//  (decode → downscale → orientation-normalizing JPEG encode).
//

import UIKit
import Testing
@testable import ATTREQ

// MARK: - Fixtures

/// Renders a synthetic image of exactly `width`×`height` pixels.
///
/// - Parameter noisy: when true, fills the image with random-colored blocks so
///   the JPEG encoder cannot compress it well (worst-case size testing);
///   otherwise a flat two-tone fill (cheap, highly compressible).
private func makeImage(width: Int, height: Int, noisy: Bool = false) -> UIImage {
    let size = CGSize(width: width, height: height)
    let format = UIGraphicsImageRendererFormat()
    format.scale = 1
    format.opaque = true
    return UIGraphicsImageRenderer(size: size, format: format).image { context in
        UIColor.systemIndigo.setFill()
        context.fill(CGRect(origin: .zero, size: size))
        if noisy {
            // 8 px random-colored blocks: dense high-frequency content that
            // defeats JPEG compression, while keeping fill-count manageable.
            var rng = SystemRandomNumberGenerator()
            let block = 8
            for y in stride(from: 0, to: height, by: block) {
                for x in stride(from: 0, to: width, by: block) {
                    UIColor(
                        red: CGFloat(UInt8.random(in: 0...255, using: &rng)) / 255,
                        green: CGFloat(UInt8.random(in: 0...255, using: &rng)) / 255,
                        blue: CGFloat(UInt8.random(in: 0...255, using: &rng)) / 255,
                        alpha: 1
                    ).setFill()
                    context.fill(CGRect(x: x, y: y, width: block, height: block))
                }
            }
        } else {
            UIColor.systemOrange.setFill()
            context.fill(CGRect(x: 0, y: 0, width: width / 2, height: height / 2))
        }
    }
}

/// Pixel dimensions of an encoded image, decoded via UIImage.
/// `UIImage(data:)` always has `scale == 1`, so `size` is the pixel size.
private func decodedPixelSize(of data: Data) -> CGSize? {
    guard let image = UIImage(data: data) else { return nil }
    return CGSize(width: image.size.width * image.scale, height: image.size.height * image.scale)
}

// MARK: - Tests

@Suite("ImageProcessor upload pipeline")
struct ImageProcessorTests {
    @Test("4000×3000 downscales to a 1600 longest side, preserving aspect ratio")
    func downscalesOversizedImagePreservingRatio() throws {
        let source = makeImage(width: 4000, height: 3000)

        let data = try #require(ImageProcessor.jpegDataForUpload(source))
        let size = try #require(decodedPixelSize(of: data))

        #expect(max(size.width, size.height) == 1600)
        // 4:3 preserved: 4000×3000 → 1600×1200.
        #expect(size.width == 1600)
        #expect(size.height == 1200)
    }

    @Test("800×600 within bounds keeps its pixel dimensions")
    func keepsSmallImageDimensionsUntouched() throws {
        let source = makeImage(width: 800, height: 600)

        let data = try #require(ImageProcessor.jpegDataForUpload(source))
        let size = try #require(decodedPixelSize(of: data))

        #expect(size.width == 800)
        #expect(size.height == 600)
    }

    @Test("Output data round-trips through UIImage decoding")
    func outputDecodesAsUIImage() throws {
        let source = makeImage(width: 1200, height: 900)

        let data = try #require(ImageProcessor.jpegDataForUpload(source))

        #expect(UIImage(data: data) != nil)
        // JPEG magic bytes (SOI marker) — the backend expects image/jpeg.
        #expect(data.prefix(2) == Data([0xFF, 0xD8]))
    }

    @Test("Worst-case noisy 4000×3000 input stays under the backend's 10 MB cap")
    func largeNoisyInputStaysUnderUploadCap() throws {
        let source = makeImage(width: 4000, height: 3000, noisy: true)

        let data = try #require(ImageProcessor.jpegDataForUpload(source))

        #expect(data.count < 10 * 1024 * 1024)
    }

    @Test("rawData path decodes PNG input and re-encodes as JPEG")
    func rawDataPathHandlesPNGInput() throws {
        let source = makeImage(width: 2400, height: 1000)
        let pngData = try #require(source.pngData())

        let data = try #require(ImageProcessor.jpegDataForUpload(rawData: pngData))
        let size = try #require(decodedPixelSize(of: data))

        #expect(data.prefix(2) == Data([0xFF, 0xD8]))
        // 2400×1000 → longest side capped at 1600 → 1600×667 (rounded).
        #expect(size.width == 1600)
        #expect(abs(size.height - 1000.0 * 1600.0 / 2400.0) <= 1)
    }
}
