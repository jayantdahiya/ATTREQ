import Foundation

/// AI-pipeline processing state of a wardrobe item.
enum ProcessingStatus: String, Codable, Sendable, CaseIterable {
    case pending
    case processing
    case completed
    case failed
}

/// Mirrors backend `WardrobeItemResponse` (`schemas/wardrobe.py`) / TS `WardrobeItem`.
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
    let wearCount: Int
    /// Date-only string, e.g. `"2026-07-10"` (backend `date | None` — not a timestamp).
    let lastWorn: String?
    let createdAt: Date
    let updatedAt: Date
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

/// Request body for `PUT /wardrobe/{id}` manual tag edits (backend `WardrobeItemUpdate`).
struct WardrobeItemUpdateRequest: Codable, Sendable, Equatable {
    var category: String?
    var colorPrimary: String?
    var colorSecondary: String?
    var pattern: String?
    var season: [String]?
    var occasion: [String]?
}
