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

    // MARK: - Wardrobe capture (RI-7, onboarding step 4)
    //
    // Distinct from `photos` above (the 3–8 Style DNA OUTFIT photos used for
    // aesthetic extraction): these are individual GARMENT shots for
    // `POST /wardrobe/batch-upload`, seeding the wardrobe directly so
    // recommendations have something to draw from even when Style DNA is
    // skipped entirely.

    /// Server-enforced batch cap (`wardrobe_batch_upload_max_files`, raised to
    /// 20 in RI-7). Kept as a client-side ceiling too so the capture loop and
    /// library picker never assemble a batch the server would reject.
    static let maxCapturePhotos = 20

    private(set) var capturePhotos: [Data] = []

    enum CaptureUploadState: Equatable {
        case idle
        case uploading
        case failed(String)
        case done
    }

    private(set) var captureUploadState: CaptureUploadState = .idle
    var isCaptureUploading: Bool {
        if case .uploading = captureUploadState { return true }
        return false
    }

    /// Best-known total wardrobe size (Style DNA seed + this step's uploads +
    /// anything already there), for the "N items added" progress copy. Refreshed
    /// via `refreshWardrobeCount(using:)`.
    private(set) var wardrobeItemCount = 0
    /// Items still needed to reach `recommendedItemTarget` — the "M more
    /// unlocks better matches" half of the progress copy. Never negative.
    var itemsRemainingForBetterMatches: Int { max(0, Self.recommendedItemTarget - wardrobeItemCount) }
    /// Rough product target for "enough variety to mix and match" — not a
    /// hard gate (the recommendations endpoint itself decides sufficiency;
    /// see `pollForFirstRecommendation`), just the progress copy's headline number.
    static let recommendedItemTarget = 10

    /// True once the daily-recommendations endpoint has returned a non-empty
    /// `suggestions` array for the first time — triggers the celebratory
    /// "first recommendation unlocked" moment. Sticky: never resets to false.
    private(set) var firstRecommendationUnlocked = false
    /// True while `pollForFirstRecommendation` is actively polling.
    private(set) var isCheckingForRecommendation = false

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
    /// mirroring the RN skip semantics (no photos, no Style DNA). Also used
    /// by the wardrobe-capture step's "Continue" action (RI-7) — completion
    /// is the same call regardless of which prior steps ran.
    func skip(session: AppSession) async {
        await complete(session: session)
    }

    // MARK: - Wardrobe capture (RI-7, onboarding step 4)

    /// Appends captured/picked garment photos, capping at `maxCapturePhotos`.
    func addCapturePhotos(_ newPhotos: [Data]) {
        let remaining = Self.maxCapturePhotos - capturePhotos.count
        guard remaining > 0 else { return }
        capturePhotos.append(contentsOf: newPhotos.prefix(remaining))
    }

    func removeCapturePhoto(at index: Int) {
        guard capturePhotos.indices.contains(index) else { return }
        capturePhotos.remove(at: index)
    }

    /// `POST /wardrobe/batch-upload` for every captured/picked photo.
    ///
    /// TODO(RI-6): duplicate-upload detection isn't available yet — this is
    /// the natural pre-upload call site for it once it ships.
    func uploadCapturePhotos(using repository: WardrobeRepository) async {
        guard !capturePhotos.isEmpty, !isCaptureUploading else { return }
        captureUploadState = .uploading
        do {
            _ = try await repository.batchUpload(imagesData: capturePhotos)
            capturePhotos = []
            captureUploadState = .done
            await refreshWardrobeCount(using: repository)
        } catch {
            captureUploadState = .failed(AuthErrorMessage.describe(error))
        }
    }

    /// Refreshes `wardrobeItemCount` from the server's page-1 total (cheap —
    /// `page_size: 1` transfers no item payload). Silent on failure; the
    /// progress copy just keeps showing the last known count.
    func refreshWardrobeCount(using repository: WardrobeRepository) async {
        guard let response = try? await repository.list(page: 1, pageSize: 1) else { return }
        wardrobeItemCount = response.total
    }

    /// Polls `GET /wardrobe/items` for items reaching `processing_status ==
    /// "completed"`, then calls `GET /recommendations/daily` once at least 2
    /// are done; any 200 with a non-empty `suggestions` array is the unlock.
    /// A 404 ("insufficient wardrobe items") means keep waiting — NOT an
    /// error — since `category` values are garment names ("shirt", "jeans"),
    /// never literal "top"/"bottom" roles, this deliberately never inspects
    /// categories client-side to decide readiness (per the RI-7 gating note).
    func pollForFirstRecommendation(
        wardrobeRepository: WardrobeRepository,
        recommendationsRepository: RecommendationsRepository
    ) async {
        guard !firstRecommendationUnlocked, !isCheckingForRecommendation else { return }
        isCheckingForRecommendation = true
        defer { isCheckingForRecommendation = false }
        let clock = ContinuousClock()
        let deadline = clock.now.advanced(by: .seconds(60))
        while !Task.isCancelled {
            do {
                let list = try await wardrobeRepository.list(page: 1, pageSize: 50, status: "active")
                let completedCount = list.items.filter { $0.processingStatus == .completed }.count
                if completedCount >= 2 {
                    let daily = try await recommendationsRepository.daily()
                    if !daily.suggestions.isEmpty {
                        firstRecommendationUnlocked = true
                        return
                    }
                }
            } catch {
                // 404 "insufficient items" and any other transient failure:
                // keep polling until the deadline rather than surfacing an error.
            }
            guard clock.now < deadline else { return }
            try? await clock.sleep(for: .seconds(3))
        }
    }

    // MARK: - Personal-color selfie (RI-3, optional final onboarding step)
    //
    // `POST /users/style-dna/selfie` — opt-in, feature-flagged, and NEVER
    // allowed to block onboarding. The endpoint 404s when the server-side
    // flag is off and 400s if consent wasn't true; both, along with any
    // other failure (network, 500, decoding), land in `.failed` here rather
    // than throwing — the flow shell always has a "Continue" path forward
    // regardless of outcome (see `PersonalColorSelfieView`).

    enum PersonalColorState: Equatable {
        case idle
        case analyzing
        case done
        case failed(String)
    }

    private(set) var personalColorState: PersonalColorState = .idle
    var isAnalyzingPersonalColor: Bool {
        if case .analyzing = personalColorState { return true }
        return false
    }

    /// Submits the selfie for personal-color estimation. `consent` must be
    /// `true` when the caller has the user's explicit opt-in (the only way
    /// this should ever be invoked) — sending `false` is a defensive
    /// impossibility, not a supported "silent" path.
    func estimatePersonalColor(
        imageData: Data,
        consent: Bool,
        using repository: StyleDnaRepository
    ) async {
        guard !isAnalyzingPersonalColor else { return }
        personalColorState = .analyzing
        do {
            _ = try await repository.estimatePersonalColor(imageData: imageData, consent: consent)
            personalColorState = .done
        } catch {
            // Graceful degradation: this is a soft failure, not a hard stop —
            // 404 (feature disabled), 400 (consent), or anything else all
            // just mean "no personal-color estimate this time."
            personalColorState = .failed(AuthErrorMessage.describe(error))
        }
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
