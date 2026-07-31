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
///
/// **Custom `init(from:)` is required, not incidental.** A `let` (or `var`)
/// stored property declared with an inline default value (`let x: T = y`) is
/// silently EXCLUDED from the compiler-synthesized `Decodable` conformance —
/// the Swift compiler even warns "will not be decoded because it is declared
/// with an initial value which cannot be overwritten." Synthesized Codable
/// would therefore always keep the Swift-side default and NEVER pick up the
/// backend's actual `status`/`purchase_price`/`brand`/`photos`/v2-attribute
/// values (verified in `WardrobeItemV2Tests.swift`) — those fields would look
/// permanently "active"/`nil`/unset regardless of what the server returns.
/// The explicit `init(from:)` below uses `decodeIfPresent(...) ?? default`
/// per field instead, which is the only way to get both behaviors at once:
/// decode the real value when the key is present, fall back to a default
/// (for old/legacy rows) when it's missing.
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
    let status: WardrobeItemStatus
    /// User-entered purchase price, for cost-per-wear stats. `nil` means not entered.
    let purchasePrice: Double?
    /// User-entered brand. `nil` means not entered (shown as "Unbranded" in stats).
    let brand: String?
    let wearCount: Int
    /// Date-only string, e.g. `"2026-07-10"` (backend `date | None` — not a timestamp).
    let lastWorn: String?
    /// Only populated on single-item GET and the PATCH-status response; `nil`
    /// (never an empty array) on the paginated list, which omits the key.
    /// Fetch the full set via `WardrobeRepository.photos(itemId:)`.
    let photos: WardrobeItemPhoto.CodableList?
    let createdAt: Date
    let updatedAt: Date

    // MARK: Classifier schema v2 (RI-2)
    //
    // All optional/defaulted so pre-RI-2 rows (`schemaVersion == 1`, every
    // field below `null`) decode without crashing — see
    // `WardrobeEnums.swift` (generated) for the vocabularies.

    let texture: Texture?
    let silhouette: Silhouette?
    let neckline: Neckline?
    let sleeveLength: SleeveLength?
    let statementLevel: StatementLevel?
    /// The LLM's 1-4 formality judgment. System-derived — not user-correctable.
    let llmFormality: Int?
    /// Derived server-side from `category` (dress/jumpsuit/romper) — not an
    /// independent LLM guess. User-correctable (e.g. a poncho misread as a top).
    let isFullbody: Bool
    /// Deterministic CIELAB palette, dominant color first. `nil` until pixel
    /// extraction runs (or on `llm_fallback`).
    let colorPalette: [PaletteColor]?
    /// `"pixel"` | `"llm_fallback"`.
    let colorExtractionSource: String?
    /// Per-attribute 0-1 confidence for the 9 keys the v2 prompt asks about
    /// (category, color_primary, pattern, season, occasion, texture,
    /// silhouette, neckline, sleeve_length). Drives the "tap to confirm"
    /// low-confidence flag in `WardrobeItemDetailView` (threshold < 0.6).
    let attributeConfidence: [String: Double]?
    /// `1` = pre-RI-2 row, `2` = v2 attributes present.
    let schemaVersion: Int

    /// Explicit memberwise initializer — required because a custom
    /// `init(from:)` (see below) suppresses the compiler-synthesized one.
    /// Keeps the same defaultable fields optional/defaulted that call sites
    /// (previews, `WardrobeViewModel.pendingPlaceholder`) already relied on.
    init(
        id: String,
        userId: String,
        originalImageUrl: String,
        processedImageUrl: String?,
        thumbnailUrl: String?,
        category: String?,
        colorPrimary: String?,
        colorSecondary: String?,
        pattern: String?,
        season: [String]?,
        occasion: [String]?,
        detectionConfidence: Double?,
        classificationSource: String?,
        processingStatus: ProcessingStatus,
        status: WardrobeItemStatus = .active,
        purchasePrice: Double? = nil,
        brand: String? = nil,
        wearCount: Int,
        lastWorn: String?,
        photos: WardrobeItemPhoto.CodableList? = nil,
        createdAt: Date,
        updatedAt: Date,
        texture: Texture? = nil,
        silhouette: Silhouette? = nil,
        neckline: Neckline? = nil,
        sleeveLength: SleeveLength? = nil,
        statementLevel: StatementLevel? = nil,
        llmFormality: Int? = nil,
        isFullbody: Bool = false,
        colorPalette: [PaletteColor]? = nil,
        colorExtractionSource: String? = nil,
        attributeConfidence: [String: Double]? = nil,
        schemaVersion: Int = 1
    ) {
        self.id = id
        self.userId = userId
        self.originalImageUrl = originalImageUrl
        self.processedImageUrl = processedImageUrl
        self.thumbnailUrl = thumbnailUrl
        self.category = category
        self.colorPrimary = colorPrimary
        self.colorSecondary = colorSecondary
        self.pattern = pattern
        self.season = season
        self.occasion = occasion
        self.detectionConfidence = detectionConfidence
        self.classificationSource = classificationSource
        self.processingStatus = processingStatus
        self.status = status
        self.purchasePrice = purchasePrice
        self.brand = brand
        self.wearCount = wearCount
        self.lastWorn = lastWorn
        self.photos = photos
        self.createdAt = createdAt
        self.updatedAt = updatedAt
        self.texture = texture
        self.silhouette = silhouette
        self.neckline = neckline
        self.sleeveLength = sleeveLength
        self.statementLevel = statementLevel
        self.llmFormality = llmFormality
        self.isFullbody = isFullbody
        self.colorPalette = colorPalette
        self.colorExtractionSource = colorExtractionSource
        self.attributeConfidence = attributeConfidence
        self.schemaVersion = schemaVersion
    }

    private enum CodingKeys: String, CodingKey {
        case id, userId, originalImageUrl, processedImageUrl, thumbnailUrl, category
        case colorPrimary, colorSecondary, pattern, season, occasion, detectionConfidence
        case classificationSource, processingStatus, status, purchasePrice, brand
        case wearCount, lastWorn, photos, createdAt, updatedAt
        case texture, silhouette, neckline, sleeveLength, statementLevel, llmFormality
        case isFullbody, colorPalette, colorExtractionSource, attributeConfidence, schemaVersion
    }

    init(from decoder: any Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        id = try container.decode(String.self, forKey: .id)
        userId = try container.decode(String.self, forKey: .userId)
        originalImageUrl = try container.decode(String.self, forKey: .originalImageUrl)
        processedImageUrl = try container.decodeIfPresent(String.self, forKey: .processedImageUrl)
        thumbnailUrl = try container.decodeIfPresent(String.self, forKey: .thumbnailUrl)
        category = try container.decodeIfPresent(String.self, forKey: .category)
        colorPrimary = try container.decodeIfPresent(String.self, forKey: .colorPrimary)
        colorSecondary = try container.decodeIfPresent(String.self, forKey: .colorSecondary)
        pattern = try container.decodeIfPresent(String.self, forKey: .pattern)
        season = try container.decodeIfPresent([String].self, forKey: .season)
        occasion = try container.decodeIfPresent([String].self, forKey: .occasion)
        detectionConfidence = try container.decodeIfPresent(Double.self, forKey: .detectionConfidence)
        classificationSource = try container.decodeIfPresent(String.self, forKey: .classificationSource)
        processingStatus = try container.decode(ProcessingStatus.self, forKey: .processingStatus)
        status = try container.decodeIfPresent(WardrobeItemStatus.self, forKey: .status) ?? .active
        purchasePrice = try container.decodeIfPresent(Double.self, forKey: .purchasePrice)
        brand = try container.decodeIfPresent(String.self, forKey: .brand)
        wearCount = try container.decode(Int.self, forKey: .wearCount)
        lastWorn = try container.decodeIfPresent(String.self, forKey: .lastWorn)
        photos = try container.decodeIfPresent(WardrobeItemPhoto.CodableList.self, forKey: .photos)
        createdAt = try container.decode(Date.self, forKey: .createdAt)
        updatedAt = try container.decode(Date.self, forKey: .updatedAt)
        texture = try container.decodeIfPresent(Texture.self, forKey: .texture)
        silhouette = try container.decodeIfPresent(Silhouette.self, forKey: .silhouette)
        neckline = try container.decodeIfPresent(Neckline.self, forKey: .neckline)
        sleeveLength = try container.decodeIfPresent(SleeveLength.self, forKey: .sleeveLength)
        statementLevel = try container.decodeIfPresent(StatementLevel.self, forKey: .statementLevel)
        llmFormality = try container.decodeIfPresent(Int.self, forKey: .llmFormality)
        isFullbody = try container.decodeIfPresent(Bool.self, forKey: .isFullbody) ?? false
        colorPalette = try container.decodeIfPresent([PaletteColor].self, forKey: .colorPalette)
        colorExtractionSource = try container.decodeIfPresent(String.self, forKey: .colorExtractionSource)
        attributeConfidence = try container.decodeIfPresent([String: Double].self, forKey: .attributeConfidence)
        schemaVersion = try container.decodeIfPresent(Int.self, forKey: .schemaVersion) ?? 1
    }
}

/// One color in a deterministic CIELAB `colorPalette` (RI-2). Mirrors backend
/// `PaletteColorSchema` (`schemas/wardrobe.py`).
struct PaletteColor: Codable, Sendable, Equatable {
    /// `[L*, a*, b*]`.
    let lab: [Double]
    /// `"#rrggbb"`.
    let hex: String
    /// Fraction of foreground pixels in this cluster, `0...1`.
    let share: Double
    /// `true` when this color is perceptually achromatic (C* < 15) — NOT the
    /// same as a "fashion neutral" (navy has C* ~= 80 and `isNeutral == false`
    /// despite being wardrobe-neutral; see `color_extraction.py`).
    let isNeutral: Bool
    /// Nearest named color from the classifier's 16-color vocabulary.
    let name: String
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

    // RI-2: user-correctable v2 attribute fields only — NOT `llmFormality`,
    // `colorPalette`, `colorExtractionSource`, `attributeConfidence`, or
    // `schemaVersion`, which are system-derived. Sending any of these fields
    // makes the backend emit an `item_corrected` telemetry event per changed/
    // confirmed field (see `endpoints/wardrobe.py::update_wardrobe_item`).
    var texture: Texture?
    var silhouette: Silhouette?
    var neckline: Neckline?
    var sleeveLength: SleeveLength?
    var statementLevel: StatementLevel?
    var isFullbody: Bool?
}

/// Request body for `PATCH /wardrobe/items/{id}/status` (backend
/// `WardrobeItemStatusUpdate`) — `"active"` or `"archived"`.
struct WardrobeItemStatusUpdateRequest: Codable, Sendable, Equatable {
    var status: String
}
