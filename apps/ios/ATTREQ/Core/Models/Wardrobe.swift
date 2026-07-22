import Foundation

/// AI-pipeline processing state of a wardrobe item.
enum ProcessingStatus: String, Codable, Sendable, CaseIterable {
    case pending
    case processing
    case completed
    case failed
}

/// Active-vs-archived lifecycle state of a wardrobe item (RI-7). Archiving
/// keeps outfit history but removes the item from Today and the active
/// wardrobe/stats surfaces (server-side; see `schemas/wardrobe.py
/// WardrobeItemStatusUpdate`).
enum WardrobeItemStatus: String, Codable, Sendable, CaseIterable {
    case active
    case archived
}

/// Mirrors backend `WardrobeItemResponse` (`schemas/wardrobe.py`) / TS `WardrobeItem`.
///
/// Also doubles as the paginated-list shape (`WardrobeItemListEntry` on the
/// backend): the two Pydantic schemas differ only in `photos` (list entries
/// omit it entirely to avoid an N+1 / async lazy-load crash), so `photos` is
/// optional here and simply decodes to `nil` when the key is absent — one
/// Swift model instead of two, matching how this file already served both
/// shapes before RI-7.
struct WardrobeItem: Codable, Sendable, Equatable, Identifiable {
    let id: String
    let userId: String
    let originalImageUrl: String
    let processedImageUrl: String?
    let thumbnailUrl: String?
    let category: String?
    let colorPrimary: String?
    let colorSecondary: String?
    let pattern: String?
    let season: [String]?
    let occasion: [String]?
    let detectionConfidence: Double?
    /// Backend-only field (which classifier tagged the item); absent from the TS types.
    let classificationSource: String?
    let processingStatus: ProcessingStatus
    /// "active" | "archived" — defaults to `.active` for older decode call
    /// sites/fixtures that predate this field.
    let status: WardrobeItemStatus = .active
    /// User-entered purchase price, for cost-per-wear stats. `nil` means not entered.
    let purchasePrice: Double? = nil
    /// User-entered brand. `nil` means not entered (shown as "Unbranded" in stats).
    let brand: String? = nil
    let wearCount: Int
    /// Date-only string, e.g. `"2026-07-10"` (backend `date | None` — not a timestamp).
    let lastWorn: String?
    /// Only populated on single-item GET and the PATCH-status response; `nil`
    /// (never an empty array) on the paginated list, which omits the key.
    /// Fetch the full set via `WardrobeRepository.photos(itemId:)`.
    let photos: WardrobeItemPhoto.CodableList? = nil
    let createdAt: Date
    let updatedAt: Date
}

/// One additional (or primary) photo attached to a wardrobe item (RI-7).
/// Mirrors backend `WardrobeItemPhotoResponse` (`schemas/wardrobe.py`).
struct WardrobeItemPhoto: Codable, Sendable, Equatable, Identifiable {
    let id: String
    let originalImageUrl: String
    /// `nil` until the background-removal worker finishes.
    let processedImageUrl: String?
    /// `nil` until the thumbnail worker finishes.
    let thumbnailUrl: String?
    let isPrimary: Bool
    let createdAt: Date

    /// Named alias so `WardrobeItem.photos`'s doc comment reads naturally;
    /// plain `[WardrobeItemPhoto]` underneath.
    typealias CodableList = [WardrobeItemPhoto]
}

/// Response body for `POST /wardrobe/items/{id}/photos` (backend
/// `WardrobeItemPhotoUploadResponse`) — same shape as `WardrobeUploadResponse`
/// but without `original_image_url` (the caller already has the bytes it sent).
struct WardrobeItemPhotoUploadResponse: Codable, Sendable, Equatable, Identifiable {
    let id: String
    let status: String
    let message: String
}

/// Mirrors backend `WardrobeItemList` / TS `WardrobeListResponse`.
struct WardrobeListResponse: Codable, Sendable, Equatable {
    let items: [WardrobeItem]
    let total: Int
    let page: Int
    let pageSize: Int
    let totalPages: Int
}

/// Mirrors backend `WardrobeItemUploadResponse` / TS `WardrobeUploadResponse`.
struct WardrobeUploadResponse: Codable, Sendable, Equatable, Identifiable {
    let id: String
    let status: String
    let message: String
    let originalImageUrl: String
}

/// Mirrors TS `DetectedWardrobeItem` — a clothing item detected in a Style DNA
/// photo by the extraction pipeline (`services/style_dna/prompts.py`).
struct DetectedWardrobeItem: Codable, Sendable, Equatable {
    let category: String
    let subcategory: String
    let colorPrimary: String?
    let colorSecondary: String?
    let pattern: String?
    let occasion: [String]
    let season: [String]
    let confidence: Double
    let boundingRegion: String
}

/// Request body for `PUT /wardrobe/items/{id}` manual tag edits (backend `WardrobeItemUpdate`).
/// Does NOT accept `status` — archiving/unarchiving is a separate call
/// (`WardrobeItemStatusUpdateRequest` via `PATCH /wardrobe/items/{id}/status`).
struct WardrobeItemUpdateRequest: Codable, Sendable, Equatable {
    var category: String?
    var colorPrimary: String?
    var colorSecondary: String?
    var pattern: String?
    var season: [String]?
    var occasion: [String]?
    /// RI-7: user-entered purchase price (for cost-per-wear stats).
    var purchasePrice: Double?
    /// RI-7: user-entered brand.
    var brand: String?
}

/// Request body for `PATCH /wardrobe/items/{id}/status` (backend
/// `WardrobeItemStatusUpdate`) — `"active"` or `"archived"`.
struct WardrobeItemStatusUpdateRequest: Codable, Sendable, Equatable {
    var status: String
}
