//
//  WardrobeStats.swift
//  ATTREQ
//
//  Wardrobe stats & forgotten-items retention surfaces (RI-7). Backend
//  contract: apps/api/src/attreq_api/schemas/stats.py
//  - GET /stats/wardrobe?force_refresh=   → WardrobeStatsResponse
//  - GET /stats/forgotten?force_refresh=&days_threshold= → ForgottenItemsResponse
//
//  Both payloads are computed over ACTIVE items only — archived items keep
//  their outfit history but leave the dashboard. `generated_at` is a plain
//  date string (backend emits `date.today().isoformat()`), not a timestamp,
//  so it's decoded as `String` rather than `Date`.
//

import Foundation

/// Item count for a single garment category (`by_category`).
struct CategoryBreakdown: Codable, Sendable, Equatable {
    let category: String
    let count: Int
}

/// Item count for a color-family bucket — neutral/warm/cool/other/unknown (`by_color_family`).
struct ColorFamilyBreakdown: Codable, Sendable, Equatable {
    let family: String
    let count: Int
}

/// Item count for a brand ("Unbranded" when the item has no brand set) (`by_brand`).
struct BrandBreakdown: Codable, Sendable, Equatable {
    let brand: String
    let count: Int
}

/// A single entry in the most/least-worn lists. "Wear count" here means
/// "number of distinct worn outfits containing the item" — copy referencing
/// this should say "worn in N outfits", not imply a raw wear-event counter.
struct WornItemEntry: Codable, Sendable, Equatable, Identifiable {
    let itemId: String
    let category: String?
    let colorPrimary: String?
    let thumbnailUrl: String?
    let wearCount: Int
    /// Date-only string (`"yyyy-MM-dd"`), `nil` if never worn.
    let lastWorn: String?

    var id: String { itemId }
}

/// Cost-per-wear entry. Only present for items with a purchase price entered
/// at all — items with no price are omitted here entirely and counted only
/// in `items_missing_price`. `costPerWear` is `nil` when the item has a price
/// but has never been worn ("not worn yet", never "$0" or an error).
struct CostPerWearEntry: Codable, Sendable, Equatable, Identifiable {
    let itemId: String
    let category: String?
    let colorPrimary: String?
    let thumbnailUrl: String?
    let purchasePrice: Double
    let wearCount: Int
    let costPerWear: Double?

    var id: String { itemId }
}

/// Mirrors backend `WardrobeStatsResponse` (`schemas/stats.py`).
struct WardrobeStatsResponse: Codable, Sendable, Equatable {
    let totalActiveItems: Int
    let byCategory: [CategoryBreakdown]
    let byColorFamily: [ColorFamilyBreakdown]
    let byBrand: [BrandBreakdown]
    let closetValue: Double
    let itemsMissingPrice: Int
    let neverWornCount: Int
    let neverWornPercent: Double
    /// Highest wear_count first. Never includes zero-wear items.
    let mostWorn: [WornItemEntry]
    /// Lowest wear_count first, ascending. Never includes zero-wear items
    /// (those surface only via `neverWornCount` and the forgotten-items endpoint).
    let leastWorn: [WornItemEntry]
    let costPerWear: [CostPerWearEntry]
    let wornLast30Days: Int
    let wornLast90Days: Int
    /// Date-only string (backend `date.today().isoformat()`), not a timestamp.
    let generatedAt: String
    let cached: Bool
}

/// Suggested pairing partner for a forgotten item ("wear it with…").
struct ForgottenPartner: Codable, Sendable, Equatable, Identifiable {
    let itemId: String
    let category: String?
    let colorPrimary: String?
    let thumbnailUrl: String?
    let score: Double

    var id: String { itemId }
}

/// A single forgotten (never-worn or stale) wardrobe item.
struct ForgottenItemEntry: Codable, Sendable, Equatable, Identifiable {
    let itemId: String
    let category: String?
    let colorPrimary: String?
    let thumbnailUrl: String?
    let wearCount: Int
    let lastWorn: String?
    /// `nil` for never-worn items (there is no "last worn" to measure from).
    let daysSinceWorn: Int?
    /// `nil` when the algorithm found no good pairing candidate.
    let bestPartner: ForgottenPartner?

    var id: String { itemId }
}

/// Mirrors backend `ForgottenItemsResponse` (`schemas/stats.py`).
struct ForgottenItemsResponse: Codable, Sendable, Equatable {
    let items: [ForgottenItemEntry]
    let count: Int
    let generatedAt: String
    let cached: Bool
}
