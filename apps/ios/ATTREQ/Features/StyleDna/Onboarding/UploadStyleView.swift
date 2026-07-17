//
//  UploadStyleView.swift
//  ATTREQ
//
//  Style DNA onboarding step 1 (M3, artboard 09). Pixel source:
//  assets/design/ios-redesign-v2/attreq-onboarding.jsx → ATTREQStyleDNA.
//  "Step 01 — Upload" accent mono, "Show us / *your style.*" display 34,
//  3-column 3:4 photo grid (radius 14, dashed empties), 3pt progress bar,
//  accent CTA, "Skip for now" mono link. Behavior mirrors the RN screen
//  `apps/mobile/app/(onboarding)/upload-style.tsx` (pick 3–8 → upload).
//
//  The header row (back circle 30 + "Style DNA Setup" mono) lives in
//  `OnboardingFlowView`, shared by all three steps — same split as
//  `RegisterFlowView` hosting `AttreqStepNav` above its step views.
//

import SwiftUI
import UIKit

struct UploadStyleView: View {
    let model: OnboardingViewModel
    /// Uploads and, on success, advances to results (owned by the flow shell).
    let onBuild: () -> Void
    /// "Skip for now" → complete onboarding directly.
    let onSkip: () -> Void

    @State private var showLibrary = false

    private static let tileShape = RoundedRectangle(cornerRadius: 14, style: .continuous)

    var body: some View {
        VStack(alignment: .leading, spacing: 0) {
            MonoLabel("Step 01 — Upload", color: Theme.accent)
                .padding(.bottom, 8)

            headline
                .padding(.bottom, 8)

            BodyText("Upload 3–8 outfit photos you love. We'll read your aesthetic and pre-fill your wardrobe.")
                .padding(.bottom, 24)

            photoGrid
                .padding(.bottom, 16)

            progressRow
                .padding(.bottom, 28)

            if case let .failed(message) = model.uploadState {
                errorBanner(message)
                    .padding(.bottom, 12)
            }
            if let message = model.completionError {
                errorBanner(message)
                    .padding(.bottom, 12)
            }

            Spacer(minLength: 0)

            footer
        }
        .multiPhotoLibraryPicker(
            isPresented: $showLibrary,
            maxSelectionCount: OnboardingViewModel.maxPhotos - model.photos.count
        ) { images in
            model.addPhotos(images)
        }
    }

    // MARK: - Headline

    private var headline: some View {
        (
            Text("Show us\n").foregroundStyle(Theme.text)
                + Text("your style.")
                .font(.attreqDisplay(34, italic: true))
                .foregroundStyle(Theme.accent)
        )
        .font(.attreqDisplay(34))
    }

    // MARK: - Photo grid

    /// 6 tiles minimum; once 6+ photos are picked the grid grows to keep one
    /// empty "add" tile visible, capping at 8.
    private var tileCount: Int {
        max(6, min(OnboardingViewModel.maxPhotos, model.photos.count + 1))
    }

    private var photoGrid: some View {
        let columns = Array(repeating: GridItem(.flexible(), spacing: 9), count: 3)
        return LazyVGrid(columns: columns, spacing: 9) {
            ForEach(0..<tileCount, id: \.self) { index in
                tile(at: index)
                    .accessibilityIdentifier("styledna-tile-\(index)")
            }
        }
    }

    @ViewBuilder
    private func tile(at index: Int) -> some View {
        if index < model.photos.count {
            filledTile(at: index)
        } else {
            emptyTile
        }
    }

    private func filledTile(at index: Int) -> some View {
        Color.clear
            .aspectRatio(3.0 / 4.0, contentMode: .fit)
            .overlay {
                if let image = UIImage(data: model.photos[index]) {
                    Image(uiImage: image)
                        .resizable()
                        .scaledToFill()
                } else {
                    Self.tileShape.fill(Theme.surface)
                }
            }
            .clipShape(Self.tileShape)
            .overlay(alignment: .topTrailing) {
                Button {
                    model.removePhoto(at: index)
                } label: {
                    // Fixed black scrim + white glyph by design: this sits on
                    // top of arbitrary photo content, so it must not follow
                    // the light/dark theme.
                    Circle()
                        .fill(Color.black.opacity(0.45))
                        .frame(width: 22, height: 22)
                        .overlay {
                            Image(systemName: "xmark")
                                .font(.system(size: 9, weight: .medium))
                                .foregroundStyle(.white)
                        }
                        // Grow the tap target beyond the 22pt visual circle.
                        .frame(width: 34, height: 34)
                        .contentShape(Rectangle())
                }
                .buttonStyle(.plain)
                // Mutating the photo set mid-upload can't affect the in-flight
                // request; freeze the grid until the upload settles.
                .disabled(model.isUploading)
                .accessibilityLabel("Remove photo \(index + 1)")
            }
            .accessibilityLabel("Photo \(index + 1)")
    }

    private var emptyTile: some View {
        Button(action: addPhotosTapped) {
            Self.tileShape
                .strokeBorder(Theme.border, style: StrokeStyle(lineWidth: 1.5, dash: [5, 4]))
                .aspectRatio(3.0 / 4.0, contentMode: .fit)
                .overlay {
                    // Artboard: 18px plus glyph, 1.5 stroke, t3.
                    Image(systemName: "plus")
                        .font(.system(size: 16, weight: .light))
                        .foregroundStyle(Theme.t3)
                }
                .contentShape(Self.tileShape)
        }
        .buttonStyle(.plain)
        .disabled(model.isUploading)
        .accessibilityLabel("Add photos")
    }

    private func addPhotosTapped() {
        // UI-test hook: PHPicker's remote view doesn't reliably accept
        // synthesized taps, so `-uitest-autopick-photos` bypasses the system
        // picker and appends three synthetic JPEGs through the exact same
        // path the picker callback uses (same trick as WardrobeScreen's
        // `-uitest-autopick-photo`).
        if ProcessInfo.processInfo.arguments.contains("-uitest-autopick-photos") {
            model.addPhotos((0..<3).compactMap(Self.syntheticTestPhotoJPEG))
        } else {
            showLibrary = true
        }
    }

    // MARK: - Progress

    private var progressRow: some View {
        let fraction = CGFloat(model.photos.count) / CGFloat(OnboardingViewModel.maxPhotos)
        return HStack(spacing: 10) {
            GeometryReader { geometry in
                Capsule()
                    .fill(Theme.borderSoft)
                    .overlay(alignment: .leading) {
                        Capsule()
                            .fill(Theme.accent)
                            .frame(width: geometry.size.width * fraction)
                    }
            }
            .frame(height: 3)
            MonoLabel("\(model.photos.count) of \(OnboardingViewModel.maxPhotos) photos")
        }
    }

    // MARK: - Footer

    private var footer: some View {
        VStack(spacing: 13) {
            AttreqPrimaryButton(
                "Build my Style DNA →",
                role: .accent,
                isLoading: model.isUploading,
                action: onBuild
            )
            // Also disabled while "Skip for now" is completing onboarding —
            // starting an upload mid-completion would race the routing gate.
            .disabled(!model.canBuild || model.isCompleting)
            .opacity(model.canBuild || model.isUploading ? 1 : 0.45)

            if model.isUploading {
                BodyText("This takes 10–30 seconds. We're reading your aesthetic.", size: 12)
                    .frame(maxWidth: .infinity)
                    .multilineTextAlignment(.center)
            }

            Button(action: onSkip) {
                Text("Skip for now".uppercased())
                    .font(.attreqMono(9.5))
                    .tracking(1.2)
                    .foregroundStyle(Theme.t3)
                    // >=44pt tap target around the small mono link.
                    .padding(.vertical, 12)
                    .padding(.horizontal, 16)
                    .contentShape(Rectangle())
            }
            .buttonStyle(.plain)
            .padding(.vertical, -12)
            .frame(maxWidth: .infinity)
            .disabled(model.isUploading || model.isCompleting)
            .accessibilityIdentifier("link-skip-onboarding")
        }
    }

    private func errorBanner(_ message: String) -> some View {
        BodyText(message, size: 13, color: Theme.clay)
            .frame(maxWidth: .infinity, alignment: .leading)
            .padding(.vertical, 10)
            .padding(.horizontal, 13)
            .background(Theme.claySoft, in: RoundedRectangle(cornerRadius: 12, style: .continuous))
    }

    // MARK: - UI-test synthetic photo

    /// Deterministic stand-in photo for `-uitest-autopick-photos`: a plain
    /// garment-like color block, valid JPEG, well under the upload cap
    /// (mirrors `WardrobeScreen.syntheticTestPhotoJPEG`, tinted per index so
    /// the three tiles are visually distinct).
    private static func syntheticTestPhotoJPEG(index: Int) -> Data? {
        let fills: [UIColor] = [
            UIColor(red: 0.35, green: 0.45, blue: 0.65, alpha: 1),
            UIColor(red: 0.55, green: 0.42, blue: 0.32, alpha: 1),
            UIColor(red: 0.38, green: 0.52, blue: 0.42, alpha: 1),
        ]
        let size = CGSize(width: 800, height: 1000)
        let format = UIGraphicsImageRendererFormat()
        format.scale = 1
        format.opaque = true
        let image = UIGraphicsImageRenderer(size: size, format: format).image { context in
            fills[index % fills.count].setFill()
            context.fill(CGRect(origin: .zero, size: size))
            UIColor(white: 0.95, alpha: 1).setFill()
            context.fill(CGRect(x: 120, y: 150, width: 560, height: 700))
        }
        return image.jpegData(compressionQuality: 0.85)
    }
}

// MARK: - Previews

#Preview("Upload — empty") {
    ScrollView {
        UploadStyleView(model: OnboardingViewModel(), onBuild: {}, onSkip: {})
            .padding(28)
    }
    .background(Theme.bg)
}
