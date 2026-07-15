//
//  LocationProvider.swift
//  ATTREQ
//
//  Async wrapper over CLLocationManager: when-in-use permission,
//  a single location fix, and a reverse-geocoded city name.
//
//  Concurrency: the provider is @MainActor and creates its
//  CLLocationManager on the main thread, so delegate callbacks arrive on
//  the main thread too; the nonisolated delegate methods hop back onto the
//  actor with `MainActor.assumeIsolated`.
//

import CoreLocation
import Foundation

/// Errors surfaced by `LocationProvider`.
enum LocationProviderError: LocalizedError {
    /// The user denied (or previously denied) location permission.
    case permissionDenied
    /// Core Location returned no usable fix.
    case locationUnavailable
    /// A request is already in flight.
    case requestInProgress

    var errorDescription: String? {
        switch self {
        case .permissionDenied:
            "Location access is off. Enable it in Settings or enter your city below."
        case .locationUnavailable:
            "Couldn't determine your location. Try again or enter your city below."
        case .requestInProgress:
            "Already looking up your location."
        }
    }
}

/// One-shot async location lookup with reverse-geocoded city.
@MainActor
final class LocationProvider: NSObject {
    private var manager: CLLocationManager?
    private var locationContinuation: CheckedContinuation<CLLocation, Error>?
    private var authorizationContinuation: CheckedContinuation<CLAuthorizationStatus, Error>?

    /// Requests when-in-use permission (if undetermined), fetches a single
    /// location, and reverse-geocodes it. `city` is nil when geocoding fails —
    /// coordinates alone are still useful to callers.
    ///
    /// Cancellation-aware: if the surrounding task is cancelled while waiting on
    /// the permission prompt or the location fix, the pending continuation is
    /// resumed by throwing `CancellationError` and cleared, so the provider stays
    /// reusable for a later request.
    func requestLocation() async throws -> (latitude: Double, longitude: Double, city: String?) {
        guard locationContinuation == nil, authorizationContinuation == nil else {
            throw LocationProviderError.requestInProgress
        }

        let manager = self.manager ?? CLLocationManager()
        manager.delegate = self
        manager.desiredAccuracy = kCLLocationAccuracyKilometer
        self.manager = manager

        var status = manager.authorizationStatus
        if status == .notDetermined {
            status = try await withTaskCancellationHandler {
                try await withCheckedThrowingContinuation { continuation in
                    authorizationContinuation = continuation
                    manager.requestWhenInUseAuthorization()
                }
            } onCancel: {
                Task { @MainActor [weak self] in
                    self?.cancelPendingAuthorization()
                }
            }
        }
        guard status == .authorizedWhenInUse || status == .authorizedAlways else {
            throw LocationProviderError.permissionDenied
        }

        let location: CLLocation = try await withTaskCancellationHandler {
            try await withCheckedThrowingContinuation { continuation in
                locationContinuation = continuation
                manager.requestLocation()
            }
        } onCancel: {
            Task { @MainActor [weak self] in
                self?.cancelPendingLocation()
            }
        }

        let city = try? await Self.city(for: location)
        return (location.coordinate.latitude, location.coordinate.longitude, city)
    }

    /// Fails a pending permission wait with `CancellationError` and clears it.
    /// No-op when the continuation already resumed (e.g. the prompt was answered
    /// before the cancellation handler's hop onto the main actor ran).
    private func cancelPendingAuthorization() {
        guard let continuation = authorizationContinuation else { return }
        authorizationContinuation = nil
        continuation.resume(throwing: CancellationError())
    }

    /// Fails a pending location fix with `CancellationError` and clears it.
    private func cancelPendingLocation() {
        guard let continuation = locationContinuation else { return }
        locationContinuation = nil
        continuation.resume(throwing: CancellationError())
    }

    private static func city(for location: CLLocation) async throws -> String? {
        let placemarks = try await CLGeocoder().reverseGeocodeLocation(location)
        let placemark = placemarks.first
        return placemark?.locality ?? placemark?.subAdministrativeArea ?? placemark?.administrativeArea
    }
}

// MARK: - CLLocationManagerDelegate

extension LocationProvider: CLLocationManagerDelegate {
    nonisolated func locationManagerDidChangeAuthorization(_ manager: CLLocationManager) {
        let status = manager.authorizationStatus
        // Callbacks land on the thread that created the manager (main).
        MainActor.assumeIsolated {
            // Also fired when the delegate is first set; only resume once the
            // user has actually answered the prompt.
            guard status != .notDetermined, let continuation = authorizationContinuation else { return }
            authorizationContinuation = nil
            continuation.resume(returning: status)
        }
    }

    nonisolated func locationManager(_ manager: CLLocationManager, didUpdateLocations locations: [CLLocation]) {
        MainActor.assumeIsolated {
            guard let continuation = locationContinuation else { return }
            locationContinuation = nil
            if let location = locations.last {
                continuation.resume(returning: location)
            } else {
                continuation.resume(throwing: LocationProviderError.locationUnavailable)
            }
        }
    }

    nonisolated func locationManager(_ manager: CLLocationManager, didFailWithError error: Error) {
        MainActor.assumeIsolated {
            guard let continuation = locationContinuation else { return }
            locationContinuation = nil
            if let clError = error as? CLError, clError.code == .denied {
                continuation.resume(throwing: LocationProviderError.permissionDenied)
            } else {
                continuation.resume(throwing: LocationProviderError.locationUnavailable)
            }
        }
    }
}
