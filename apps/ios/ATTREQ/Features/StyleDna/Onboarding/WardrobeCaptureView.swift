//
//  WardrobeCaptureView.swift
//  ATTREQ
//
//  Style DNA onboarding step 4 (RI-7, no artboard — composed in the design
//  language, same approach as `ResultsView`/`ReviewItemsView`). Seeds the
//  wardrobe directly with individual garment photos via
//  `POST /wardrobe/batch-upload`, independent of the Style DNA outfit photos
//  from step 1 — this runs whether the user built a Style DNA or skipped it,
//  since recommendations need actual wardrobe items either way.
//
//  Camera path: no custom `AVCaptureSession` — a dismiss/re-present loop over
//  the existing `CameraPicker` (same component `WardrobeScreen` uses for its
//  single-shot upload), with a running thumbnail tray and a "Done" button to
//  stop the loop. Library path: `MultiPhotoLibraryPicker` verbatim, capped to
//  the RI-7 batch-upload range (10–20).
//

import SwiftUI
import UIKit

struct WardrobeCaptureView: View {
    let model: OnboardingViewModel
    let wardrobeRepository: WardrobeRepository
    let recommendationsRepository: RecommendationsRepository
    /// "Continue" → finish onboarding (owned by the flow shell, same call as
    /// the pre-RI-7 skip/confirm paths — see `OnboardingViewModel.skip(session:)`).
    let onFinish: () -> Void

    /// Library selection floor/ceiling per the RI-7 plan (server cap is 20).
    private static let libraryMinSelection = 10
    private static let libraryMaxSelection = 20

    @State private var showCamera = false
    @State private var isCaptureLoopActive = false
    @State private var showLibrary = false

    private static let tileShape = RoundedRectangle(cornerRadius: 14, style: .continuous)

    var body: some View {
        VStack(alignment: .leading, spacing: 0) {
            MonoLabel("Step 04 — Wardrobe", color: Theme.accent)
                .padding(.bottom, 8)

            headline
                .padding(.bottom, 8)

            factsCard
                .padding(.bottom, 20)

            if !model.capturePhotos.isEmpty {
                photoTray
                    .padding(.bottom, 16)
            }

            captureButtons
                .padding(.bottom, 16)

            progressLine
                .padding(.bottom, 12)

            if case let .failed(message) = model.captureUploadState {
                errorBanner(message)
                    .padding(.bottom, 12)
            }

            recommendationStatus
                .padding(.bottom, 16)

            Spacer(minLength: 16)

            footer
        }
        .task {
            await model.refreshWardrobeCount(using: wardrobeRepository)
        }
        .onChange(of: showCamera) { wasShowing, isShowing in
            // The camera sheet just dismissed itself (capture or cancel). If
            // the user hasn't tapped "Done" and there's still room, re-present
            // it — the "dismiss/re-show loop" that stands in for a persistent
            // capture session.
            guard wasShowing, !isShowing, isCaptureLoopActive,
                  model.capturePhotos.count < OnboardingViewModel.maxCapturePhotos
            else { return }
            Task {
                try? await Task.sleep(for: .milliseconds(250))
                showCamera = true
            }
        }
        .fullScreenCover(isPresented: $showCamera) {
            CameraPicker { image in
                Task {
                    let data = await Task.detached(priority: .userInitiated) {
                        ImageProcessor.jpegDataForUpload(image)
                    }.value
                    guard let data else { return }
                    model.addCapturePhotos([data])
                }
            }
            .ignoresSafeArea()
        }
        .multiPhotoLibraryPicker(
            isPresented: $showLibrary,
            maxSelectionCount: min(
                Self.libraryMaxSelection,
                OnboardingViewModel.maxCapturePhotos - model.capturePhotos.count
            )
        ) { images in
            model.addCapturePhotos(images)
        }
    }

    // MARK: - Headline & facts

    private var headline: some View {
        (
            Text("Build your\n").foregroundStyle(Theme.text)
                + Text("wardrobe.")
                .font(.attreqDisplay(34, italic: true))
                .foregroundStyle(Theme.accent)
        )
        .font(.attreqDisplay(34))
    }

    private var factsCard: some View {
        VStack(alignment: .leading, spacing: 8) {
            factLine("Roughly a quarter of the average closet is never worn.")
            factLine("We only ever recommend outfits from clothes you already own — no ads, no affiliate picks.")
        }
        .padding(14)
        .background(Theme.accentSoft, in: RoundedRectangle(cornerRadius: 16, style: .continuous))
    }

    private func factLine(_ text: String) -> some View {
        HStack(alignment: .top, spacing: 8) {
            AttreqIcon.sparkles.view(size: 12, color: Theme.accent)
            BodyText(text, size: 13, color: Theme.text)
        }
    }

    // MARK: - Photo tray

    private var photoTray: some View {
        VStack(alignment: .leading, spacing: 8) {
            MonoLabel("\(model.capturePhotos.count) piece\(model.capturePhotos.count == 1 ? "" : "s") captured")
            ScrollView(.horizontal, showsIndicators: false) {
                HStack(spacing: 8) {
                    ForEach(Array(model.capturePhotos.enumerated()), id: \.offset) { index, data in
                        trayTile(data, index: index)
                    }
                }
            }
        }
    }

    private func trayTile(_ data: Data, index: Int) -> some View {
        Color.clear
            .frame(width: 72, height: 90)
            .overlay {
                if let image = UIImage(data: data) {
                    Image(uiImage: image).resizable().scaledToFill()
                } else {
                    Self.tileShape.fill(Theme.surface)
                }
            }
            .clipShape(Self.tileShape)
            .overlay(alignment: .topTrailing) {
                Button {
                    model.removeCapturePhoto(at: index)
                } label: {
                    Circle()
                        .fill(Color.black.opacity(0.45))
                        .frame(width: 18, height: 18)
                        .overlay { Image(systemName: "xmark").font(.system(size: 8, weight: .medium)).foregroundStyle(.white) }
                        .frame(width: 30, height: 30)
                        .contentShape(Rectangle())
                }
                .buttonStyle(.plain)
                .disabled(model.isCaptureUploading)
                .accessibilityLabel("Remove photo \(index + 1)")
            }
    }

    // MARK: - Capture entry points

    private var captureButtons: some View {
        HStack(spacing: 9) {
            if isCaptureLoopActive {
                AttreqPrimaryButton("Done capturing") {
                    isCaptureLoopActive = false
                }
                .accessibilityIdentifier("button-done-capturing")
            } else {
                captureTile(
                    icon: .camera,
                    label: "Camera",
                    sublabel: "One piece at a time",
                    isEnabled: CameraPicker.isAvailable && model.capturePhotos.count < OnboardingViewModel.maxCapturePhotos
                ) {
                    isCaptureLoopActive = true
                    showCamera = true
                }
                .accessibilityIdentifier("tile-onboarding-camera")

                captureTile(
                    icon: .image,
                    label: "Library",
                    sublabel: "Pick \(Self.libraryMinSelection)–\(Self.libraryMaxSelection) at once",
                    isEnabled: model.capturePhotos.count < OnboardingViewModel.maxCapturePhotos
                ) {
                    showLibrary = true
                }
                .accessibilityIdentifier("tile-onboarding-library")
            }
        }
    }

    private func captureTile(
        icon: AttreqIcon,
        label: String,
        sublabel: String,
        isEnabled: Bool,
        action: @escaping () -> Void
    ) -> some View {
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
            .background(Self.tileShape.fill(Theme.surface))
            .overlay(Self.tileShape.strokeBorder(Theme.border, style: StrokeStyle(lineWidth: 1.5, dash: [5, 4])))
            .contentShape(Self.tileShape)
            .opacity(isEnabled ? 1 : 0.45)
        }
        .buttonStyle(.plain)
        .disabled(!isEnabled)
    }

    // MARK: - Progress copy

    /// "N items added — M more unlocks better matches" — facts-only, no
    /// percentage bar, no streak mechanics (per the RI-7 plan).
    private var progressLine: some View {
        let remaining = model.itemsRemainingForBetterMatches
        return MonoLabel(
            remaining > 0
                ? "\(model.wardrobeItemCount) items added — \(remaining) more unlocks better matches"
                : "\(model.wardrobeItemCount) items added — plenty for great matches",
            size: 9
        )
    }

    // MARK: - Recommendation unlock status

    @ViewBuilder
    private var recommendationStatus: some View {
        if model.firstRecommendationUnlocked {
            HStack(spacing: 10) {
                AttreqIcon.check.view(size: 14, color: Theme.moss)
                BodyText("Your first recommendation is ready — find it on Today.", size: 13, color: Theme.moss)
            }
            .padding(12)
            .background(Theme.mossSoft, in: RoundedRectangle(cornerRadius: 14, style: .continuous))
        } else if model.isCheckingForRecommendation {
            HStack(spacing: 8) {
                ProgressView().controlSize(.small).tint(Theme.t3)
                MonoLabel("Checking if your first look is ready")
            }
        }
    }

    // MARK: - Footer

    private var footer: some View {
        VStack(spacing: 13) {
            if !model.capturePhotos.isEmpty, model.captureUploadState != .done {
                AttreqPrimaryButton(
                    "Add \(model.capturePhotos.count) to wardrobe",
                    role: .accent,
                    isLoading: model.isCaptureUploading,
                    action: uploadCaptures
                )
                .accessibilityIdentifier("button-upload-capture-photos")
            }

            AttreqPrimaryButton("Continue →", isLoading: model.isCompleting, action: onFinish)
                .disabled(model.isCaptureUploading)
                .accessibilityIdentifier("button-continue-onboarding")
        }
    }

    private func uploadCaptures() {
        Task {
            await model.uploadCapturePhotos(using: wardrobeRepository)
            if case .done = model.captureUploadState {
                await model.pollForFirstRecommendation(
                    wardrobeRepository: wardrobeRepository,
                    recommendationsRepository: recommendationsRepository
                )
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

#Preview("Wardrobe capture") {
    let auth = AuthSession(keychain: KeychainStore(), baseURL: AppConfig.apiBaseURL)
    let client = APIClient(baseURL: AppConfig.apiBaseURL, authSession: auth)
    ScrollView {
        WardrobeCaptureView(
            model: OnboardingViewModel(),
            wardrobeRepository: WardrobeRepository(apiClient: client),
            recommendationsRepository: RecommendationsRepository(apiClient: client),
            onFinish: {}
        )
        .padding(28)
    }
    .background(Theme.bg)
}
