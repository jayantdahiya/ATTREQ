//
//  StyleDnaProfileViewModel.swift
//  ATTREQ
//
//  Style DNA profile screen state (M3-WP3). Mirrors RN
//  `app/(protected)/style-dna/profile.tsx` + `use-style-dna.ts` hooks:
//  fetch the profile, regenerate from existing seed photos, manage photos.
//
//  Backend-truth reconciliation (see StyleDnaRepository):
//  - regenerate returns `StyleDnaUploadResponse`, mapped to the profile
//    shape here so the view only ever renders `StyleDnaProfileResponse`.
//  - there is NO per-photo delete endpoint — only DELETE
//    /users/style-dna/photos, which removes ALL seed photos. The screen
//    therefore offers a single "Remove all photos" action.
//

import Foundation
import Observation

@MainActor
@Observable
final class StyleDnaProfileViewModel {
    enum LoadState {
        case loading
        case loaded(StyleDnaProfileResponse)
        case failed(String)
    }

    private(set) var state: LoadState = .loading
    private(set) var isRegenerating = false
    private(set) var isDeletingPhotos = false
    /// Non-fatal action failure (regenerate / delete) shown as a banner over
    /// otherwise-valid content. Cleared on the next action or successful load.
    private(set) var actionError: String?

    private let repository: StyleDnaRepository

    init(repository: StyleDnaRepository, initialState: LoadState = .loading) {
        self.repository = repository
        state = initialState
    }

    /// `GET /users/style-dna`. The first load drives the full-screen
    /// loading/failed states; once content is on screen this refreshes
    /// silently (stale data beats a flash — mirrors RN query refetch).
    func load() async {
        let hadContent = if case .loaded = state { true } else { false }
        if !hadContent {
            state = .loading
        }
        do {
            state = .loaded(try await repository.profile())
            actionError = nil
        } catch {
            if !hadContent {
                state = .failed(Self.message(for: error, fallback: "Couldn't load your style profile."))
            }
        }
    }

    /// `POST /users/style-dna/regenerate` — re-run synthesis from the stored
    /// seed photos. The endpoint returns `StyleDnaUploadResponse`
    /// (`wardrobeItemsSeeded` always 0 here); mapped to the profile shape.
    func regenerate() async {
        guard !isRegenerating else { return }
        isRegenerating = true
        actionError = nil
        defer { isRegenerating = false }
        do {
            let response = try await repository.regenerate()
            state = .loaded(
                StyleDnaProfileResponse(styleDna: response.styleDna, photos: response.photos)
            )
        } catch {
            actionError = Self.message(for: error, fallback: "Couldn't regenerate your Style DNA.")
        }
    }

    /// `DELETE /users/style-dna/photos` — removes ALL seed photos (the
    /// backend stores them as a set; the profile itself is kept until the
    /// next upload/regenerate). Refetches afterwards; falls back to clearing
    /// the photo list locally if the refetch fails.
    func deleteAllPhotos() async {
        guard case .loaded(let current) = state, !isDeletingPhotos else { return }
        isDeletingPhotos = true
        actionError = nil
        defer { isDeletingPhotos = false }
        do {
            try await repository.deletePhotos()
            if let refreshed = try? await repository.profile() {
                state = .loaded(refreshed)
            } else {
                state = .loaded(StyleDnaProfileResponse(styleDna: current.styleDna, photos: []))
            }
        } catch {
            actionError = Self.message(for: error, fallback: "Couldn't remove your photos.")
        }
    }

    // MARK: - Errors

    /// Same policy as `WardrobeViewModel`: connectivity gets a friendly line,
    /// FastAPI `detail` strings pass through, everything else falls back.
    private static func message(for error: any Error, fallback: String) -> String {
        switch error {
        case APIError.network:
            return "Can't reach ATTREQ. Check your connection."
        case let APIError.http(_, body):
            // FastAPI error bodies carry a human-readable string `detail`
            // (e.g. "Only 2 usable photos stored. Upload new photos first.").
            if let object = try? JSONSerialization.jsonObject(with: body) as? [String: Any],
               let detail = object["detail"] as? String,
               !detail.isEmpty {
                return detail
            }
            return fallback
        default:
            return fallback
        }
    }
}
