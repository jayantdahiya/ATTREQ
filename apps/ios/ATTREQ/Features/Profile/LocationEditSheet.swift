//
//  LocationEditSheet.swift
//  ATTREQ
//
//  Location editor sheet for the Profile preferences card (M5-WP1).
//  Same content language as the registration location step (artboard 04):
//  device-location row via `LocationProvider` + manual city underline input.
//
//  Save routing (mirrors the RN registration/profile split):
//  - Device coordinates captured → `PATCH /users/me/location` with lat/lon
//    (+ the typed city as an override of the reverse-geocoded one).
//  - Manual city only → `PUT /users/me` (`location` + `saved_city`), since the
//    PATCH endpoint requires coordinates. Note this leaves any previously
//    saved coordinates in place (same as RN registration's city-only path).
//  Either way `session.refreshUser()` then updates the Profile rows.
//

import SwiftUI

struct LocationEditSheet: View {
    @Environment(AppSession.self) private var session
    @Environment(\.dismiss) private var dismiss

    @State private var provider = LocationProvider()
    @State private var manualCity: String
    @State private var deviceLocation: (latitude: Double, longitude: Double, city: String?)?
    @State private var isLocating = false
    @State private var locationErrorMessage: String?
    @State private var isSaving = false
    @State private var errorMessage: String?

    init(initialCity: String = "") {
        _manualCity = State(initialValue: initialCity)
    }

    var body: some View {
        ZStack {
            Theme.bg.ignoresSafeArea()

            ScrollView(showsIndicators: false) {
                VStack(alignment: .leading, spacing: 0) {
                    MonoLabel("Preferences — Location", color: Theme.accent)
                        .padding(.bottom, 8)

                    Text("Where mornings find you.")
                        .font(.attreqDisplay(26))
                        .foregroundStyle(Theme.text)
                        .padding(.bottom, 6)

                    BodyText("Your city keeps suggestions weather-aware.", size: 13)
                        .padding(.bottom, 20)

                    locationCard

                    if let errorMessage {
                        BodyText(errorMessage, size: 13, color: Theme.clay)
                            .padding(.top, 12)
                    }

                    AttreqPrimaryButton(
                        "Save location",
                        role: .accent,
                        isLoading: isSaving,
                        action: save
                    )
                    .padding(.top, 16)
                }
                .padding(.horizontal, 28)
                .padding(.top, 28)
                .padding(.bottom, 24)
            }
            .scrollBounceBehavior(.basedOnSize)
        }
        .presentationDetents([.medium, .large])
        .presentationDragIndicator(.visible)
    }

    // MARK: Card (device row + manual city, per LocationStepView)

    private var locationCard: some View {
        VStack(alignment: .leading, spacing: 0) {
            deviceLocationRow
                .padding(.bottom, 16)

            Rectangle()
                .fill(Theme.borderSoft)
                .frame(height: 1)
                .padding(.bottom, 18)

            AttreqUnderlineInput(label: "Or enter your city", text: $manualCity)
        }
        .attreqCard(padding: 20)
    }

    private var deviceLocationRow: some View {
        VStack(alignment: .leading, spacing: 8) {
            Button {
                Task { await requestDeviceLocation() }
            } label: {
                HStack(spacing: 12) {
                    Circle()
                        .fill(Theme.accentSoft)
                        .frame(width: 36, height: 36)
                        .overlay {
                            if isLocating {
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
                        if let resolvedCity {
                            MonoLabel(resolvedCity, color: Theme.accent)
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
            .disabled(isLocating)

            if let locationErrorMessage {
                BodyText(locationErrorMessage, size: 12, color: Theme.clay)
            }
        }
    }

    private var resolvedCity: String? {
        guard let deviceLocation else { return nil }
        return deviceLocation.city ?? "Location captured"
    }

    // MARK: Actions

    private func requestDeviceLocation() async {
        guard !isLocating else { return }
        locationErrorMessage = nil
        isLocating = true
        defer { isLocating = false }
        do {
            deviceLocation = try await provider.requestLocation()
        } catch {
            deviceLocation = nil
            locationErrorMessage = AuthErrorMessage.describe(error)
        }
    }

    private func save() {
        guard !isSaving else { return }
        errorMessage = nil
        let typedCity = manualCity.trimmingCharacters(in: .whitespacesAndNewlines)
        guard deviceLocation != nil || !typedCity.isEmpty else {
            errorMessage = "Use device location or enter your city."
            return
        }
        isSaving = true
        Task {
            defer { isSaving = false }
            do {
                if let deviceLocation {
                    // A typed city deliberately overrides the geocoded one.
                    let city = typedCity.isEmpty ? deviceLocation.city : typedCity
                    let _: User = try await session.api.request(
                        Endpoint(
                            method: .patch,
                            path: "users/me/location",
                            body: .json(LocationUpdateRequest(
                                lat: deviceLocation.latitude,
                                lon: deviceLocation.longitude,
                                city: city
                            ))
                        )
                    )
                } else {
                    // City-only path: PATCH requires coordinates, so update
                    // the profile fields instead (see header comment).
                    let _: User = try await session.api.request(
                        Endpoint(
                            method: .put,
                            path: "users/me",
                            body: .json(UserUpdateRequest(
                                fullName: nil,
                                location: typedCity,
                                savedLatitude: nil,
                                savedLongitude: nil,
                                savedCity: typedCity,
                                isActive: nil
                            ))
                        )
                    )
                }
                try? await session.refreshUser()
                dismiss()
            } catch {
                errorMessage = AuthErrorMessage.describe(error)
            }
        }
    }
}

// MARK: - Previews

#Preview("Location sheet") {
    Theme.bg.ignoresSafeArea()
        .sheet(isPresented: .constant(true)) {
            LocationEditSheet(initialCity: "Milan")
                .environment(AppSession())
        }
}
