//
//  OnboardingViewModel.swift
//  ATTREQ
//
//  State + actions for the M3 Style DNA onboarding flow
//  (upload → results → review). Mirrors the RN screens in
//  `apps/mobile/app/(onboarding)/{upload-style,results,review-items}.tsx`.
//

import Foundation
import Observation

@MainActor
@Observable
final class OnboardingViewModel {
    static let minPhotos = 3
    static let maxPhotos = 8

    /// Lifecycle of the multipart Style DNA upload (`POST /users/style-dna`).
    enum UploadState {
        case idle
        case uploading
        case failed(String)
        case done(StyleDnaUploadResponse)
    }

    /// Upload-ready JPEG data for the 3–8 selected outfit photos.
    private(set) var photos: [Data] = []
    private(set) var uploadState: UploadState = .idle

    /// Items the extraction pipeline detected across all photos, flattened from
    /// each photo's `per_photo_extraction.wardrobe_items_detected` (the same
    /// collection RN's results.tsx builds before pushing review-items).
    private(set) var detectedItems: [DetectedWardrobeItem] = []
    /// Indices into `detectedItems` the user keeps on the review screen.
    /// Everything is kept by default.
    ///
    /// NOTE: mirrors RN review-items.tsx semantics exactly — the backend
    /// already seeded ALL detected items during upload
    /// (`_bulk_seed_wardrobe`, `classification_source="style_dna_seed"`), and
    /// the RN client neither bulk-adds kept items nor deletes rejected ones.
    /// The selection is client-side review state only.
    var reviewSelection: Set<Int> = []

    /// Error from onboarding completion (confirm or skip), shown inline.
    private(set) var completionError: String?
    /// True while `POST /users/onboarding/complete` is in flight.
    private(set) var isCompleting = false

    var isUploading: Bool {
        if case .uploading = uploadState { return true }
        return false
    }

    var uploadResponse: StyleDnaUploadResponse? {
        if case let .done(response) = uploadState { return response }
        return nil
    }

    var canBuild: Bool { photos.count >= Self.minPhotos }

    var keptItemCount: Int { reviewSelection.count }

    // MARK: - Photo selection

    /// Appends picked photos, capping the total at `maxPhotos` (mirrors RN's
    /// `slice(0, MAX_PHOTOS)`).
    func addPhotos(_ newPhotos: [Data]) {
        let remaining = Self.maxPhotos - photos.count
        guard remaining > 0 else { return }
        photos.append(contentsOf: newPhotos.prefix(remaining))
    }

    func removePhoto(at index: Int) {
        guard photos.indices.contains(index) else { return }
        photos.remove(at: index)
    }

    // MARK: - Upload

    /// Multipart-uploads the selected photos and extracts the detected
    /// wardrobe items from the response. On success `uploadState` is `.done`
    /// and the flow shell advances to results.
    ///
    /// Any attempt after the first (retry after `.failed`, or a rebuild after
    /// `.done`) first best-effort deletes the stored seed-photo set
    /// (`DELETE /users/style-dna/photos`) so re-uploads REPLACE the previous
    /// photos server-side instead of accumulating duplicates (the upload
    /// endpoint always appends).
    func buildStyleDna(using repository: StyleDnaRepository) async {
        guard canBuild, !isUploading else { return }
        let isFirstAttempt: Bool = if case .idle = uploadState { true } else { false }
        uploadState = .uploading
        if !isFirstAttempt {
            // Best-effort: if the delete fails the upload still proceeds
            // (worst case is the pre-fix duplicate behavior, not a new error).
            try? await repository.deletePhotos()
        }
        do {
            let response = try await repository.uploadPhotos(photos)
            detectedItems = Self.extractDetectedItems(from: response)
            reviewSelection = Set(detectedItems.indices)
            uploadState = .done(response)
        } catch {
            uploadState = .failed(AuthErrorMessage.describe(error))
        }
    }

    // MARK: - Review

    func toggleReviewItem(_ index: Int) {
        guard detectedItems.indices.contains(index) else { return }
        if reviewSelection.contains(index) {
            reviewSelection.remove(index)
        } else {
            reviewSelection.insert(index)
        }
    }

    /// Finishes the review step. Mirrors RN `review-items.tsx` exactly: the
    /// detected items were already seeded server-side during upload, so no
    /// `POST /wardrobe/items/bulk` happens here — confirming is just
    /// `POST /users/onboarding/complete`. (RN also never deletes items the
    /// user rejected; the review toggles are advisory, same as here.)
    func confirmReview(session: AppSession) async {
        await complete(session: session)
    }

    /// "Skip for now" — straight to `POST /users/onboarding/complete`,
    /// mirroring the RN skip semantics (no photos, no Style DNA).
    func skip(session: AppSession) async {
        await complete(session: session)
    }

    private func complete(session: AppSession) async {
        guard !isCompleting else { return }
        completionError = nil
        isCompleting = true
        defer { isCompleting = false }
        do {
            // On success `authState` flips to the refreshed user
            // (`onboardingCompleted == true`) and the RootView gate navigates
            // to the tabs — no manual routing here.
            try await session.completeOnboarding()
        } catch {
            completionError = AuthErrorMessage.describe(error)
        }
    }

    // MARK: - Detected-item extraction

    /// Flattens `wardrobe_items_detected` out of every photo's
    /// `per_photo_extraction` blob (RN results.tsx does the same flatMap).
    ///
    /// Keys are looked up in BOTH camelCase and snake_case: the decoder's
    /// `.convertFromSnakeCase` strategy may or may not rewrite `[String: JSONValue]`
    /// dictionary keys depending on the Foundation runtime (the codebase's own
    /// docs disagree — see `JSONValue` vs `StyleDna.behaviourWeights`), so this
    /// tolerates either form.
    static func extractDetectedItems(from response: StyleDnaUploadResponse) -> [DetectedWardrobeItem] {
        response.photos.flatMap { photo -> [DetectedWardrobeItem] in
            guard let extraction = photo.perPhotoExtraction,
                  case let .array(values) = field("wardrobeItemsDetected", in: extraction)
            else { return [] }
            return values.compactMap(detectedItem(from:))
        }
    }

    private static func detectedItem(from value: JSONValue) -> DetectedWardrobeItem? {
        guard case let .object(fields) = value,
              let category = string("category", in: fields)
        else { return nil }
        return DetectedWardrobeItem(
            category: category,
            subcategory: string("subcategory", in: fields) ?? "",
            colorPrimary: string("colorPrimary", in: fields),
            colorSecondary: string("colorSecondary", in: fields),
            pattern: string("pattern", in: fields),
            occasion: stringArray("occasion", in: fields),
            season: stringArray("season", in: fields),
            confidence: number("confidence", in: fields) ?? 0,
            boundingRegion: string("boundingRegion", in: fields) ?? ""
        )
    }

    /// Looks up `camelKey`, falling back to its snake_case spelling.
    private static func field(_ camelKey: String, in fields: [String: JSONValue]) -> JSONValue? {
        if let value = fields[camelKey] { return value }
        let snakeKey = camelKey.reduce(into: "") { result, character in
            if character.isUppercase {
                result.append("_")
                result.append(contentsOf: character.lowercased())
            } else {
                result.append(character)
            }
        }
        return fields[snakeKey]
    }

    private static func string(_ key: String, in fields: [String: JSONValue]) -> String? {
        guard case let .string(value) = field(key, in: fields) else { return nil }
        let trimmed = value.trimmingCharacters(in: .whitespaces)
        return trimmed.isEmpty ? nil : trimmed
    }

    private static func number(_ key: String, in fields: [String: JSONValue]) -> Double? {
        guard case let .number(value) = field(key, in: fields) else { return nil }
        return value
    }

    private static func stringArray(_ key: String, in fields: [String: JSONValue]) -> [String] {
        guard case let .array(values) = field(key, in: fields) else { return [] }
        return values.compactMap {
            if case let .string(value) = $0 { return value }
            return nil
        }
    }
}

// MARK: - Preview support

#if DEBUG
extension OnboardingViewModel {
    /// Preview-only factory: a model already in the `.done` state so results
    /// and review previews are constructible without a network round trip.
    static func previewCompleted(
        response: StyleDnaUploadResponse,
        items: [DetectedWardrobeItem]
    ) -> OnboardingViewModel {
        let model = OnboardingViewModel()
        model.detectedItems = items
        model.reviewSelection = Set(items.indices)
        model.uploadState = .done(response)
        return model
    }
}
#endif
