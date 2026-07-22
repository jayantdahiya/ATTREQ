//
//  LocationStepView.swift
//  ATTREQ
//
//  Artboard 04 — registration step 3 (location + submit).
//  Design: assets/design/ios-redesign-v2/attreq-auth.jsx (ATTREQRegisterLocation).
//

import SwiftUI

struct LocationStepView: View {
    @Bindable var model: RegisterViewModel
    let onSubmit: () -> Void

    var body: some View {
        VStack(alignment: .leading, spacing: 0) {
            MonoLabel("Step 03 — Location", color: Theme.accent)
                .padding(.bottom, 8)

            headline
                .padding(.bottom, 6)

            BodyText("Share your city for weather-aware suggestions.")
                .padding(.bottom, 20)

            locationMotif
                .frame(maxWidth: .infinity)
                .padding(.bottom, 22)

            locationCard

            if let errorMessage = model.errorMessage {
                BodyText(errorMessage, size: 13, color: Theme.clay)
                    .padding(.top, 12)
            }

            AttreqPrimaryButton(
                "Create account →",
                role: .accent,
                isLoading: model.isLoading,
                action: onSubmit
            )
            .padding(.top, 16)

            Spacer(minLength: 0)
        }
    }

    private var headline: some View {
        (
            Text("The weather decides\n").foregroundStyle(Theme.text)
                + Text("before you do.")
                .font(.attreqDisplay(34, italic: true))
                .foregroundStyle(Theme.accent)
        )
        .font(.attreqDisplay(34))
    }

    // MARK: Concentric-circles motif

    private var locationMotif: some View {
        ZStack {
            Circle()
                .strokeBorder(Theme.border, lineWidth: 1)
                .frame(width: 116, height: 116)

            Circle()
                .fill(Theme.accentSoft)
                .overlay {
                    Circle()
                        .strokeBorder(Theme.accentSoft, style: StrokeStyle(lineWidth: 1.5, dash: [4, 4]))
                }
                .frame(width: 82, height: 82)

            Circle()
                .fill(Theme.text)
                .frame(width: 50, height: 50)
                .overlay {
                    AttreqIcon.location.view(size: 20, color: Theme.bg)
                }
        }
        .accessibilityHidden(true)
    }

    // MARK: Card

    private var locationCard: some View {
        VStack(alignment: .leading, spacing: 0) {
            deviceLocationRow
                .padding(.bottom, 16)

            Rectangle()
                .fill(Theme.borderSoft)
                .frame(height: 1)
                .padding(.bottom, 18)

            AttreqUnderlineInput(label: "Or enter your city", text: $model.manualCity)
        }
        .attreqCard(padding: 20)
    }

    private var deviceLocationRow: some View {
        VStack(alignment: .leading, spacing: 8) {
            Button {
                Task { await model.requestDeviceLocation() }
            } label: {
                HStack(spacing: 12) {
                    Circle()
                        .fill(Theme.accentSoft)
                        .frame(width: 36, height: 36)
                        .overlay {
                            if model.isLocating {
                                ProgressView()
                                    .controlSize(.small)
                                    .tint(Theme.accent)
                            } else {
                                AttreqIcon.location.view(size: 15, color: Theme.accent)
                            }
                        }

                    VStack(alignment: .leading, spacing: 2) {
                        Text("Use device location")
                            .font(.attreqBody(14, weight: .medium))
                            .foregroundStyle(Theme.text)
                        if let city = model.resolvedCity {
                            MonoLabel(city, color: Theme.accent)
                        } else {
                            MonoLabel("For weather-aware suggestions")
                        }
                    }

                    Spacer(minLength: 8)

                    AttreqIcon.chevron.view(size: 13, color: Theme.t3)
                }
                .contentShape(Rectangle())
            }
            .buttonStyle(.plain)
            .disabled(model.isLocating)

            if let locationError = model.locationErrorMessage {
                BodyText(locationError, size: 12, color: Theme.clay)
            }
        }
    }
}

#Preview {
    LocationStepView(model: RegisterViewModel(), onSubmit: {})
        .padding(28)
        .background(Theme.bg)
}
