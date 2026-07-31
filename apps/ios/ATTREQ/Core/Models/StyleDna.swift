import Foundation

/// Mirrors TS `StyleDnaAesthetic`.
struct StyleDnaAesthetic: Codable, Sendable, Equatable {
    let primary: String
    let secondary: [String]
    let confidence: Double
}

/// Mirrors TS `StyleDnaColorPalette`.
struct StyleDnaColorPalette: Codable, Sendable, Equatable {
    let dominant: [String]
    let accent: [String]
    let avoids: [String]
    let confidence: Double
}

/// Mirrors TS `StyleDna.patterns`.
struct StyleDnaPatterns: Codable, Sendable, Equatable {
    let preferred: [String]
    let confidence: Double
}

/// Mirrors TS `StyleDna.silhouette`.
struct StyleDnaSilhouette: Codable, Sendable, Equatable {
    /// One of `slim-fitted|relaxed-fitted|oversized|structured|draped|tailored|mixed`.
    let preference: String
    let confidence: Double
}

/// Mirrors TS `StyleDna.formality_bias`.
struct StyleDnaFormalityBias: Codable, Sendable, Equatable {
    /// 0.0–3.0 weighted average (0 = athletic … 3 = formal).
    let level: Double
    /// One of `athletic|casual|smart-casual|business|formal`.
    let label: String
    let confidence: Double
}

/// Mirrors TS `StyleDna.occasions`.
struct StyleDnaOccasions: Codable, Sendable, Equatable {
    let primary: [String]
    let confidence: Double
}

/// Mirrors backend `personal_color` key (RI-3, `services/style_dna/personal_color.py`):
/// two continuous axes estimated from an optional, opt-in selfie — NEVER a
/// self-declared "season" label. `undertoneWarmCool`/`depthLightDeep` are
/// `[-1, 1]` (+1 = deep/warm, -1 = light/cool per the backend's convention);
/// `confidence` is `[0, 1]`. Absent entirely until the user completes
/// `POST /users/style-dna/selfie` at least once.
struct PersonalColor: Codable, Sendable, Equatable {
    let undertoneWarmCool: Double
    let depthLightDeep: Double
    let confidence: Double
}

/// Mirrors TS `StyleDna`. The backend types this as `dict[str, Any]`; the
/// concrete shape comes from the synthesis prompt in
/// `services/style_dna/prompts.py`, which matches the TS interface exactly.
struct StyleDna: Codable, Sendable, Equatable {
    let aesthetic: StyleDnaAesthetic
    let colorPalette: StyleDnaColorPalette
    let patterns: StyleDnaPatterns
    let silhouette: StyleDnaSilhouette
    let formalityBias: StyleDnaFormalityBias
    let occasions: StyleDnaOccasions
    /// Feedback-derived weights, e.g. `{"category_likes": {"top": 1.5}}`.
    /// Dictionary String keys keep their raw backend snake_case form —
    /// `.convertFromSnakeCase` does not rewrite dictionary keys on this runtime.
    let behaviourWeights: [String: [String: Double]]
    /// Optional (RI-3): present only after a selfie estimation call. An
    /// `Optional` synthesized property decodes as `nil` when the key is
    /// absent — unlike the required fields above, its absence does NOT fail
    /// the whole `StyleDna` decode.
    let personalColor: PersonalColor?

    init(
        aesthetic: StyleDnaAesthetic,
        colorPalette: StyleDnaColorPalette,
        patterns: StyleDnaPatterns,
        silhouette: StyleDnaSilhouette,
        formalityBias: StyleDnaFormalityBias,
        occasions: StyleDnaOccasions,
        behaviourWeights: [String: [String: Double]],
        personalColor: PersonalColor? = nil
    ) {
        self.aesthetic = aesthetic
        self.colorPalette = colorPalette
        self.patterns = patterns
        self.silhouette = silhouette
        self.formalityBias = formalityBias
        self.occasions = occasions
        self.behaviourWeights = behaviourWeights
        self.personalColor = personalColor
    }
}

/// Mirrors backend `StyleDnaPhotoResponse` (`schemas/style_dna.py`) / TS `StyleDnaPhoto`.
struct StyleDnaPhoto: Codable, Sendable, Equatable, Identifiable {
    let id: String
    let userId: String
    let filePath: String
    let fileUrl: String
    let qualityOk: Bool
    let qualityReason: String?
    /// Arbitrary per-photo extraction JSON (backend `dict[str, Any] | None`).
    /// Dictionary keys keep their raw backend snake_case form.
    let perPhotoExtraction: [String: JSONValue]?
    let createdAt: Date
}

/// Mirrors backend `StyleDnaUploadResponse` / TS `StyleDnaUploadResponse`.
///
/// `styleDna` decodes LENIENTLY: the backend stores the synthesis LLM's output
/// as an untyped `dict[str, Any]`, so a shape-drifted blob (wrong types,
/// missing subfields) must not fail the whole response — it degrades to the
/// same `nil` the backend sends when synthesis is skipped, and the UI shows
/// its existing no-DNA state. `StyleDna` itself stays strict.
struct StyleDnaUploadResponse: Codable, Sendable, Equatable {
    let photosProcessed: Int
    let photosSkipped: Int
    let wardrobeItemsSeeded: Int
    let styleDna: StyleDna?
    let photos: [StyleDnaPhoto]

    init(
        photosProcessed: Int,
        photosSkipped: Int,
        wardrobeItemsSeeded: Int,
        styleDna: StyleDna?,
        photos: [StyleDnaPhoto]
    ) {
        self.photosProcessed = photosProcessed
        self.photosSkipped = photosSkipped
        self.wardrobeItemsSeeded = wardrobeItemsSeeded
        self.styleDna = styleDna
        self.photos = photos
    }

    init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        photosProcessed = try container.decode(Int.self, forKey: .photosProcessed)
        photosSkipped = try container.decode(Int.self, forKey: .photosSkipped)
        wardrobeItemsSeeded = try container.decode(Int.self, forKey: .wardrobeItemsSeeded)
        styleDna = (try? container.decodeIfPresent(StyleDna.self, forKey: .styleDna)) ?? nil
        photos = try container.decode([StyleDnaPhoto].self, forKey: .photos)
    }
}

/// Mirrors backend `StyleDnaProfileResponse` / TS `StyleDnaProfileResponse`.
///
/// `styleDna` decodes LENIENTLY — see `StyleDnaUploadResponse`: malformed LLM
/// output degrades to `nil` (the existing no-DNA UX) instead of failing the
/// response; the photos still decode.
struct StyleDnaProfileResponse: Codable, Sendable, Equatable {
    let styleDna: StyleDna?
    let photos: [StyleDnaPhoto]

    init(styleDna: StyleDna?, photos: [StyleDnaPhoto]) {
        self.styleDna = styleDna
        self.photos = photos
    }

    init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        styleDna = (try? container.decodeIfPresent(StyleDna.self, forKey: .styleDna)) ?? nil
        photos = try container.decode([StyleDnaPhoto].self, forKey: .photos)
    }
}

/// Mirrors backend `StyleDnaCorrection` / TS `StyleDnaCorrection`.
///
/// TS types this as `Partial<StyleDna>`, which has no direct Swift analogue;
/// the backend accepts `dict[str, Any]`, so corrections are sent as arbitrary
/// JSON. Build keys in the backend's snake_case form (`"color_palette"`, …) —
/// the encoder's `.convertToSnakeCase` strategy does NOT rewrite dictionary
/// String keys on this runtime; they pass through verbatim.
struct StyleDnaCorrection: Codable, Sendable, Equatable {
    var corrections: [String: JSONValue]
}
