//
//  OnboardingFlowView.swift
//  ATTREQ
//
//  Flow shell for M3 Style DNA onboarding: upload (artboard 09) → results →
//  review, crossfading between steps the way `RegisterFlowView` does. Hosts
//  the shared header row from artboard 09 (back circle 30 + "Style DNA
//  Setup" mono). Successful completion flips `AppSession.authState` (user
//  refreshed with `onboardingCompleted == true`), which navigates to the
//  tabs — no manual routing here.
//

import SwiftUI

struct OnboardingFlowView: View {
    private enum Step {
        case upload
        case results
        case review
        /// RI-7: seeds the wardrobe directly with garment photos, whether the
        /// user built a Style DNA or skipped it — reached from all three
        /// prior paths (skip / "Looks right" with no detected items /
        /// review confirm) instead of completing onboarding directly.
        case wardrobeCapture
    }

    @Environment(AppSession.self) private var session
    @State private var model = OnboardingViewModel()
    @State private var step: Step = .upload

    var body: some View {
        GeometryReader { geometry in
            ScrollView {
                VStack(alignment: .leading, spacing: 0) {
                    header
                        .padding(.bottom, 26)

                    stepContent
                        .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .top)
                        .transition(.opacity)
                }
                .padding(.top, 8)
                .padding(.horizontal, 28)
                .padding(.bottom, 36)
                .frame(minHeight: geometry.size.height, alignment: .top)
            }
            .scrollBounceBehavior(.basedOnSize)
        }
        .background(Theme.bg.ignoresSafeArea())
        .toolbar(.hidden, for: .navigationBar)
        .navigationBarBackButtonHidden(true)
    }

    // MARK: - Header (artboard 09)

    /// Back circle 30pt + "Style DNA Setup" mono. On the upload step there is
    /// nowhere to go back to (the onboarding gate has no previous screen, and
    /// RN's upload-style has no back at all), so the circle renders per the
    /// artboard but is disabled. After a successful build (results/review
    /// steps) it is ALSO disabled: the photos are uploaded and the wardrobe
    /// seeded, so returning to upload would only re-upload — RN has no back
    /// on those screens either. The wardrobe-capture step (RI-7) is reachable
    /// from a Style-DNA SKIP too (no `uploadResponse`), where "back to
    /// results" wouldn't have anything to show, so it's unconditionally disabled.
    private var header: some View {
        HStack(spacing: 10) {
            Button(action: goBack) {
                Circle()
                    .strokeBorder(Theme.border, lineWidth: 1)
                    .frame(width: 30, height: 30)
                    .overlay {
                        AttreqIcon.back.view(size: 14, color: Theme.t2)
                    }
                    // 44pt minimum tap target around the 30pt visual circle.
                    .frame(width: 44, height: 44)
                    .contentShape(Rectangle())
            }
            .buttonStyle(.plain)
            .padding(.horizontal, -7)
            .disabled(step == .upload || step == .wardrobeCapture || model.uploadResponse != nil || model.isCompleting)
            .accessibilityLabel("Back")

            MonoLabel("Style DNA Setup")
        }
    }

    // MARK: - Steps

    @ViewBuilder
    private var stepContent: some View {
        switch step {
        case .upload:
            UploadStyleView(
                model: model,
                onBuild: { Task { await build() } },
                // RI-7: skipping Style DNA no longer completes onboarding
                // directly — it still needs actual wardrobe items to recommend
                // from, so it lands on the wardrobe-capture step like every
                // other path.
                onSkip: { go(to: .wardrobeCapture) }
            )
        case .results:
            ResultsView(
                model: model,
                onContinue: advanceFromResults
            )
        case .review:
            ReviewItemsView(
                model: model,
                onConfirm: { go(to: .wardrobeCapture) }
            )
        case .wardrobeCapture:
            WardrobeCaptureView(
                model: model,
                wardrobeRepository: wardrobeRepository,
                recommendationsRepository: recommendationsRepository,
                onFinish: { Task { await model.skip(session: session) } }
            )
        }
    }

    private var repository: StyleDnaRepository {
        StyleDnaRepository(apiClient: session.api)
    }

    private var wardrobeRepository: WardrobeRepository {
        WardrobeRepository(apiClient: session.api)
    }

    private var recommendationsRepository: RecommendationsRepository {
        RecommendationsRepository(apiClient: session.api)
    }

    private func build() async {
        await model.buildStyleDna(using: repository)
        if model.uploadResponse != nil {
            go(to: .results)
        }
    }

    /// Continue from results: review detected items when there are any;
    /// otherwise mirror RN's "Looks right →" and move to the wardrobe-capture
    /// step (RI-7) instead of completing onboarding directly.
    private func advanceFromResults() {
        if model.detectedItems.isEmpty {
            go(to: .wardrobeCapture)
        } else {
            go(to: .review)
        }
    }

    /// Unreachable today (the back button is disabled on upload and, after a
    /// successful build, on every later step too), but kept so the header
    /// stays correct if a pre-build step is ever inserted.
    private func goBack() {
        switch step {
        case .upload:
            break // Disabled; nothing before the onboarding gate.
        case .results:
            go(to: .upload)
        case .review:
            go(to: .results)
        case .wardrobeCapture:
            go(to: .results)
        }
    }

    private func go(to newStep: Step) {
        withAnimation(.easeInOut(duration: 0.2)) {
            step = newStep
        }
    }
}

#Preview {
    OnboardingFlowView()
        .environment(AppSession())
}
