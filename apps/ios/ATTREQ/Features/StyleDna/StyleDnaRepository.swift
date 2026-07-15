//
//  StyleDnaRepository.swift
//  ATTREQ
//
//  Style DNA API calls (M3-WP1). Backend contract:
//  apps/api/src/attreq_api/api/v1/endpoints/style_dna.py (router mounted at /users),
//  apps/api/src/attreq_api/api/v1/endpoints/wardrobe.py (bulk add),
//  apps/api/src/attreq_api/api/v1/endpoints/users.py (onboarding complete).
//
//  - POST   /users/style-dna/upload       multipart, repeated field name "files",
//    3–8 photos, each must be image/* with a jpg/jpeg/png extension. 201.
//    Server-side this ALSO auto-seeds the wardrobe (confidence >= 0.6,
//    classification_source "style_dna_seed") and returns only the seeded COUNT;
//    the detected items themselves live in
//    photos[].per_photo_extraction["wardrobe_items_detected"].
//  - GET    /users/style-dna              profile + seed photos.
//  - PATCH  /users/style-dna              {"corrections": {...}} deep-merged server-side.
//  - POST   /users/style-dna/regenerate   re-synthesize from stored photos; returns
//    StyleDnaUploadResponse (wardrobe_items_seeded is always 0 here).
//  - DELETE /users/style-dna/photos       deletes ALL seed photos (no per-photo delete
//    exists on the backend). 204.
//  - POST   /wardrobe/items/bulk          top-level JSON array of detected-item dicts
//    (snake_case keys), max 50; returns the created WardrobeItemResponse list. 201.
//  - POST   /users/onboarding/complete    marks onboarding done; returns UserResponse.
//

import Foundation

/// Stateless facade over the Style DNA endpoints. Mirrors RN
/// `apps/mobile/src/lib/api/style-dna.ts`.
final class StyleDnaRepository: Sendable {
    private let apiClient: APIClient

    init(apiClient: APIClient) {
        self.apiClient = apiClient
    }

    /// `POST /users/style-dna/upload` — multipart upload of 3–8 outfit photos.
    /// One part per photo, all under the repeated field name `files`
    /// (FastAPI `list[UploadFile] = File(...)`), filenames `photo-0.jpg`,
    /// `photo-1.jpg`, … Photos are JPEG data (the caller re-encodes HEIC etc.).
    func uploadPhotos(_ photos: [Data]) async throws -> StyleDnaUploadResponse {
        try await apiClient.request(
            Endpoint(
                method: .post,
                path: "users/style-dna/upload",
                body: .multipart(
                    photos.enumerated().map { index, data in
                        MultipartField(
                            name: "files",
                            filename: "photo-\(index).jpg",
                            contentType: "image/jpeg",
                            data: data
                        )
                    }
                )
            )
        )
    }

    /// `GET /users/style-dna` — current profile (nil until first upload) + seed photos.
    func profile() async throws -> StyleDnaProfileResponse {
        try await apiClient.request(
            Endpoint(method: .get, path: "users/style-dna")
        )
    }

    /// `PATCH /users/style-dna` — manual corrections, deep-merged into the stored
    /// profile server-side.
    ///
    /// IMPORTANT: `corrections` keys must be the backend's snake_case form
    /// (`"color_palette"`, `"formality_bias"`, …). Dictionary keys pass through
    /// `JSONEncoder` verbatim — `.convertToSnakeCase` only rewrites struct
    /// property keys, not `[String: JSONValue]` keys (verified on this runtime;
    /// the contrary note in `StyleDna.swift` describes pre-iOS-17 Foundation).
    func correct(_ corrections: [String: JSONValue]) async throws -> StyleDnaProfileResponse {
        try await apiClient.request(
            Endpoint(
                method: .patch,
                path: "users/style-dna",
                body: .json(StyleDnaCorrection(corrections: corrections))
            )
        )
    }

    /// `POST /users/style-dna/regenerate` — re-run synthesis from the stored photos
    /// (no new uploads). Returns `StyleDnaUploadResponse` (backend truth; NOT the
    /// profile response) with `wardrobeItemsSeeded == 0`.
    func regenerate() async throws -> StyleDnaUploadResponse {
        try await apiClient.request(
            Endpoint(method: .post, path: "users/style-dna/regenerate")
        )
    }

    /// `DELETE /users/style-dna/photos` — deletes ALL seed photos (used before a
    /// re-upload). The backend has no per-photo delete endpoint.
    func deletePhotos() async throws {
        try await apiClient.requestVoid(
            Endpoint(method: .delete, path: "users/style-dna/photos")
        )
    }

    /// `POST /wardrobe/items/bulk` — bulk-insert user-confirmed detected items
    /// (review screen). Body is a TOP-LEVEL JSON ARRAY of item dicts; struct
    /// properties encode to the snake_case keys the backend reads
    /// (`color_primary`, `season`, `occasion`, `confidence`, …). Max 50 items;
    /// an empty list is a backend 400, so callers should skip the call for it.
    ///
    /// Note: `uploadPhotos` already auto-seeds these items server-side — this
    /// endpoint is for adding items the seeding pass skipped (e.g. confidence
    /// < 0.6) or re-adding after edits, not for re-posting the whole detection list.
    func bulkAddItems(_ items: [DetectedWardrobeItem]) async throws -> [WardrobeItem] {
        try await apiClient.request(
            Endpoint(
                method: .post,
                path: "wardrobe/items/bulk",
                body: .json(items)
            )
        )
    }

    /// `POST /users/onboarding/complete` — mark onboarding finished after the user
    /// confirms Style DNA + wardrobe review; returns the updated user
    /// (`onboardingCompleted == true`, `onboardingStep == "complete"`).
    ///
    /// NOTE: production code path is `AppSession.completeOnboarding` (which also
    /// flips `authState` for the routing gate); this method documents/pins the
    /// endpoint contract and is exercised by StyleDnaRepositoryTests.
    func completeOnboarding() async throws -> User {
        try await apiClient.request(
            Endpoint(method: .post, path: "users/onboarding/complete")
        )
    }
}
