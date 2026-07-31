//
//  PersonalColorSelfieView.swift
//  ATTREQ
//
//  Style DNA onboarding step 5 (RI-3, no artboard — composed in the design
//  language, same approach as `WardrobeCaptureView`). Optional, skippable
//  "estimate your coloring" step: a single face photo, analyzed once for a
//  warm<->cool undertone + light<->deep depth estimate, then discarded.
//
//  Backend contract: `POST /users/style-dna/selfie` (see
//  `StyleDnaRepository.estimatePersonalColor`). Feature-flagged OFF by
//  default server-side (404) and requires explicit `consent=true` (400
//  otherwise) — this view treats BOTH, and any other failure, as a soft
//  outcome: there is always a "Continue" forward, never a dead end.
//
//  PRIVACY (must stay visible in the copy below, not just in code comments):
//  the photo is sent once to a third-party vendor for analysis and is never
//  stored — no server-side copy, no re-use. Skipping this step costs the
//  user nothing; a low-confidence or absent estimate has ~zero influence on
//  recommendations either way.
//

import PhotosUI
import SwiftUI
import UIKit

struct PersonalColorSelfieView: View {
    let model: OnboardingViewModel
    let styleDnaRepository: StyleDnaRepository
    /// Advances past this step — completes onboarding (owned by the flow
    /// shell, same `model.skip(session:)` call every prior path already used).
    let onDone: () -> Void

    @State private var selfieData: Data?
    @State private var hasConsented = false
    @State private var showLibrary = false

    private static let tileShape = RoundedRectangle(cornerRadius: 20, style: .continuous)

    var body: some View {
        VStack(alignment: .leading, spacing: 0) {
            MonoLabel("Step 05 — Coloring", color: Theme.accent)
                .padding(.bottom, 8)

            headline
                .padding(.bottom, 8)

            BodyText("Optional. A single selfie lets us fine-tune color picks to your undertone — skip it any time with no downside.")
                .padding(.bottom, 20)

            privacyCard
                .padding(.bottom, 20)

            photoPicker
                .padding(.bottom, 16)

            if selfieData != nil {
                consentToggle
                    .padding(.bottom, 16)
            }

            if case let .failed(message) = model.personalColorState {
                errorBanner(message)
                    .padding(.bottom, 12)
            }
            if case .done = model.personalColorState {
                successBanner
                    .padding(.bottom, 12)
            }

            Spacer(minLength: 16)

            footer
        }
        .photoLibraryPicker(isPresented: $showLibrary) { data in
            selfieData = data
        }
    }

    // MARK: - Headline

    private var headline: some View {
        (
            Text("Fine-tune your\n").foregroundStyle(Theme.text)
                + Text("coloring.")
                .font(.attreqDisplay(34, italic: true))
                .foregroundStyle(Theme.accent)
        )
        .font(.attreqDisplay(34))
    }

    // MARK: - Privacy disclosure

    private var privacyCard: some View {
        VStack(alignment: .leading, spacing: 8) {
            privacyLine("Analyzed once by a third-party vendor for undertone and depth — never a season label.")
            privacyLine("Never stored. The photo isn't saved by us or the vendor once analysis finishes.")
            privacyLine("Optional and skippable. This has near-zero effect on your recommendations either way.")
        }
        .padding(14)
        .background(Theme.accentSoft, in: RoundedRectangle(cornerRadius: 16, style: .continuous))
    }

    private func privacyLine(_ text: String) -> some View {
        HStack(alignment: .top, spacing: 8) {
            AttreqIcon.sparkles.view(size: 12, color: Theme.accent)
            BodyText(text, size: 13, color: Theme.text)
        }
    }

    // MARK: - Photo picker

    @ViewBuilder
    private var photoPicker: some View {
        if let data = selfieData, let image = UIImage(data: data) {
            HStack(spacing: 12) {
                Image(uiImage: image)
                    .resizable()
                    .scaledToFill()
                    .frame(width: 84, height: 84)
                    .clipShape(Circle())
                    .overlay(Circle().strokeBorder(Theme.border, lineWidth: 1))

                VStack(alignment: .leading, spacing: 6) {
                    Text("Selfie ready")
                        .font(.attreqBody(14, weight: .medium))
                        .foregroundStyle(Theme.text)
                    Button("Choose a different photo") {
                        selfieData = nil
                        hasConsented = false
                    }
                    .buttonStyle(.plain)
                    .font(.attreqBody(13))
                    .foregroundStyle(Theme.t2)
                    .disabled(model.isAnalyzingPersonalColor)
                }
                Spacer()
            }
            .padding(14)
            .background(Self.tileShape.fill(Theme.surface))
            .overlay(Self.tileShape.strokeBorder(Theme.border, lineWidth: 1))
        } else {
            Button {
                showLibrary = true
            } label: {
                VStack(alignment: .leading, spacing: 5) {
                    Circle()
                        .fill(Theme.accentSoft)
                        .frame(width: 28, height: 28)
                        .overlay(AttreqIcon.person.view(size: 13, color: Theme.t2))
                    Text("Pick a selfie")
                        .font(.attreqBody(13, weight: .medium))
                        .foregroundStyle(Theme.text)
                    MonoLabel("A single, clear, well-lit face photo")
                        .lineLimit(1)
                }
                .frame(maxWidth: .infinity, alignment: .leading)
                .padding(.vertical, 12)
                .padding(.horizontal, 13)
                .background(Self.tileShape.fill(Theme.surface))
                .overlay(Self.tileShape.strokeBorder(Theme.border, style: StrokeStyle(lineWidth: 1.5, dash: [5, 4])))
                .contentShape(Self.tileShape)
            }
            .buttonStyle(.plain)
            .accessibilityIdentifier("tile-personal-color-selfie")
        }
    }

    // MARK: - Consent

    private var consentToggle: some View {
        Button {
            hasConsented.toggle()
        } label: {
            HStack(alignment: .top, spacing: 10) {
                Image(systemName: hasConsented ? "checkmark.square.fill" : "square")
                    .font(.system(size: 18, weight: .regular))
                    .foregroundStyle(hasConsented ? Theme.accent : Theme.t3)
                BodyText(
                    "I consent to this one-time analysis by a third-party vendor. I understand my photo will not be stored.",
                    size: 13,
                    color: Theme.text
                )
            }
        }
        .buttonStyle(.plain)
        .disabled(model.isAnalyzingPersonalColor)
        .accessibilityIdentifier("toggle-selfie-consent")
    }

    // MARK: - Result banners

    private func errorBanner(_ message: String) -> some View {
        BodyText("Couldn't complete the analysis (\(message)) — no problem, continue anytime.", size: 13, color: Theme.clay)
            .frame(maxWidth: .infinity, alignment: .leading)
            .padding(.vertical, 10)
            .padding(.horizontal, 13)
            .background(Theme.claySoft, in: RoundedRectangle(cornerRadius: 12, style: .continuous))
    }

    private var successBanner: some View {
        HStack(spacing: 10) {
            AttreqIcon.check.view(size: 14, color: Theme.moss)
            BodyText("Got it — your color picks are fine-tuned.", size: 13, color: Theme.moss)
        }
        .padding(12)
        .background(Theme.mossSoft, in: RoundedRectangle(cornerRadius: 14, style: .continuous))
    }

    // MARK: - Footer

    private var footer: some View {
        VStack(spacing: 13) {
            if selfieData != nil, model.personalColorState != .done {
                AttreqPrimaryButton(
                    "Analyze →",
                    role: .accent,
                    isLoading: model.isAnalyzingPersonalColor,
                    action: analyze
                )
                .disabled(!hasConsented)
                .opacity(hasConsented ? 1 : 0.45)
                .accessibilityIdentifier("button-analyze-selfie")
            }

            AttreqPrimaryButton(
                model.personalColorState == .done ? "Continue →" : "Skip for now",
                isLoading: model.isCompleting,
                action: onDone
            )
            .disabled(model.isAnalyzingPersonalColor)
            .accessibilityIdentifier("button-skip-or-continue-selfie")
        }
    }

    private func analyze() {
        guard let selfieData, hasConsented else { return }
        Task {
            await model.estimatePersonalColor(
                imageData: selfieData,
                consent: true,
                using: styleDnaRepository
            )
        }
    }
}

// MARK: - Previews

#Preview("Personal color selfie") {
    let auth = AuthSession(keychain: KeychainStore(), baseURL: AppConfig.apiBaseURL)
    let client = APIClient(baseURL: AppConfig.apiBaseURL, authSession: auth)
    ScrollView {
        PersonalColorSelfieView(
            model: OnboardingViewModel(),
            styleDnaRepository: StyleDnaRepository(apiClient: client),
            onDone: {}
        )
        .padding(28)
    }
    .background(Theme.bg)
}
