// WardrobeEnums.swift
// ATTREQ
//
// GENERATED FILE — DO NOT EDIT BY HAND.
//
// Mirrors the fixed-vocabulary attribute enums in
// apps/api/src/attreq_api/schemas/wardrobe_enums.py (single source of truth).
// Regenerate with:
//     python apps/api/scripts/gen_swift_enums.py
// CI (`backend-ci.yml`) runs `--check` and fails the build if this file is
// stale relative to the Python enums (RI-2 plan finding #9 — generate, don't
// hand-mirror).

import Foundation

/// Fabric/material texture. `.other` is the coercion fallback.
enum Texture: String, Codable, Sendable, CaseIterable {
    case smooth
    case knit
    case denim
    case leather
    case lace
    case silkSatin = "silk_satin"
    case linen
    case corduroy
    case wool
    case fleece
    case sheer
    case other
}

/// Garment fit/cut.
enum Silhouette: String, Codable, Sendable, CaseIterable {
    case fitted
    case regular
    case relaxed
    case oversized
    case aLine = "a_line"
    case straight
    case skinny
    case wide
    case crop
    case longline
}

/// Neckline shape. Only meaningful for tops/fullbody garments — `.nA` is a legal, expected value for bottoms/footwear.
enum Neckline: String, Codable, Sendable, CaseIterable {
    case crew
    case vNeck = "v_neck"
    case scoop
    case collared
    case turtleneck
    case boat
    case square
    case offShoulder = "off_shoulder"
    case hooded
    case other
    case nA = "n_a"
}

/// Sleeve length. Only meaningful for tops/outerwear/fullbody garments — `.nA` is a legal, expected value for bottoms/footwear.
enum SleeveLength: String, Codable, Sendable, CaseIterable {
    case sleeveless
    case short
    case threeQuarter = "three_quarter"
    case long
    case nA = "n_a"
}

/// How much visual attention the item commands.
enum StatementLevel: String, Codable, Sendable, CaseIterable {
    case basic
    case standard
    case statement
}
