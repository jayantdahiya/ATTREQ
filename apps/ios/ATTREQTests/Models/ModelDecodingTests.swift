import Foundation
import Testing
@testable import ATTREQ

/// Decoding tests for the Core/Models Codable mirrors, using JSON fixtures that
/// copy the exact shapes the backend Pydantic schemas serialize.
struct ModelDecodingTests {
    // MARK: - Decoder (mirrors WP1 APIClient configuration)

    /// Same configuration the networking layer uses: `.convertFromSnakeCase` keys and
    /// ISO8601-with-fractional-seconds dates. The date strategy additionally accepts
    /// timezone-NAIVE stamps (interpreted as UTC) because the backend emits
    /// `datetime.utcnow().isoformat()` for `DailySuggestionsResponse.generated_at`,
    /// which carries no `Z`/offset. WP1's decoder must do the same.
    static func makeDecoder() -> JSONDecoder {
        let decoder = JSONDecoder()
        decoder.keyDecodingStrategy = .convertFromSnakeCase
        decoder.dateDecodingStrategy = .custom { decoder in
            let container = try decoder.singleValueContainer()
            let raw = try container.decode(String.self)
            if let date = Self.parseISO8601(raw) ?? Self.parseISO8601(raw + "Z") {
                return date
            }
            throw DecodingError.dataCorruptedError(
                in: container,
                debugDescription: "Unrecognized date format: \(raw)"
            )
        }
        return decoder
    }

    static func parseISO8601(_ string: String) -> Date? {
        let fractional = ISO8601DateFormatter()
        fractional.formatOptions = [.withInternetDateTime, .withFractionalSeconds]
        if let date = fractional.date(from: string) { return date }
        let plain = ISO8601DateFormatter()
        plain.formatOptions = [.withInternetDateTime]
        return plain.date(from: string)
    }

    func decode<T: Decodable>(_ type: T.Type, from json: String) throws -> T {
        try Self.makeDecoder().decode(T.self, from: Data(json.utf8))
    }

    // MARK: - User / register response (POST /auth/register returns UserResponse only)

    @Test func decodesRegisterResponseUser() throws {
        let json = """
        {
          "email": "ada@example.com",
          "full_name": "Ada Lovelace",
          "location": null,
          "saved_latitude": 28.6139,
          "saved_longitude": 77.209,
          "saved_city": "New Delhi",
          "id": "b7c1a5e2-4f5d-4a4b-9d0f-2a51c3f8e901",
          "is_active": true,
          "is_verified": false,
          "created_at": "2026-07-15T09:31:22.123456Z",
          "updated_at": "2026-07-15T09:31:22.123456Z",
          "last_login": null,
          "oauth_provider": null,
          "style_preferences": null,
          "onboarding_completed": false,
          "onboarding_step": "pending"
        }
        """
        let user = try decode(User.self, from: json)
        #expect(user.id == "b7c1a5e2-4f5d-4a4b-9d0f-2a51c3f8e901")
        #expect(user.email == "ada@example.com")
        #expect(user.fullName == "Ada Lovelace")
        #expect(user.location == nil)
        #expect(user.savedLatitude == 28.6139)
        #expect(user.savedCity == "New Delhi")
        #expect(user.isActive)
        #expect(!user.isVerified)
        #expect(user.createdAt == Self.parseISO8601("2026-07-15T09:31:22.123456Z"))
        #expect(user.lastLogin == nil)
        #expect(user.oauthProvider == nil)
        #expect(user.stylePreferences == nil)
        #expect(!user.onboardingCompleted)
        #expect(user.onboardingStep == "pending")
    }

    // MARK: - AuthResponse (POST /auth/login LoginResponse)

    @Test func decodesAuthResponse() throws {
        let json = """
        {
          "access_token": "eyJhbGciOiJIUzI1NiJ9.access",
          "refresh_token": "eyJhbGciOiJIUzI1NiJ9.refresh",
          "token_type": "bearer",
          "user": {
            "email": "ada@example.com",
            "full_name": null,
            "location": null,
            "saved_latitude": null,
            "saved_longitude": null,
            "saved_city": null,
            "id": "b7c1a5e2-4f5d-4a4b-9d0f-2a51c3f8e901",
            "is_active": true,
            "is_verified": false,
            "created_at": "2026-07-15T09:31:22.123456+00:00",
            "updated_at": "2026-07-15T09:32:05.654321+00:00",
            "last_login": "2026-07-15T09:32:05.654321+00:00",
            "oauth_provider": null,
            "style_preferences": "{\\"aesthetic\\": {\\"primary\\": \\"minimalist\\"}}",
            "onboarding_completed": true,
            "onboarding_step": null
          }
        }
        """
        let response = try decode(AuthResponse.self, from: json)
        #expect(response.accessToken == "eyJhbGciOiJIUzI1NiJ9.access")
        #expect(response.refreshToken == "eyJhbGciOiJIUzI1NiJ9.refresh")
        #expect(response.tokenType == "bearer")
        #expect(response.user.id == "b7c1a5e2-4f5d-4a4b-9d0f-2a51c3f8e901")
        #expect(response.user.lastLogin == Self.parseISO8601("2026-07-15T09:32:05.654321Z"))
        #expect(response.user.onboardingCompleted)
        #expect(response.user.onboardingStep == nil)
    }

    @Test func decodesTokenRefreshResponse() throws {
        let json = """
        {"access_token": "eyJhbGciOiJIUzI1NiJ9.new", "token_type": "bearer"}
        """
        let response = try decode(TokenRefreshResponse.self, from: json)
        #expect(response.accessToken == "eyJhbGciOiJIUzI1NiJ9.new")
        #expect(response.tokenType == "bearer")
    }

    // MARK: - Wardrobe

    @Test func decodesWardrobeItemWithNulls() throws {
        let json = """
        {
          "category": null,
          "color_primary": null,
          "color_secondary": null,
          "pattern": null,
          "season": null,
          "occasion": null,
          "id": "0f8fad5b-d9cb-469f-a165-70867728950e",
          "user_id": "b7c1a5e2-4f5d-4a4b-9d0f-2a51c3f8e901",
          "original_image_url": "http://localhost:8001/uploads/wardrobe/raw.jpg",
          "processed_image_url": null,
          "thumbnail_url": null,
          "detection_confidence": null,
          "classification_source": null,
          "processing_status": "pending",
          "wear_count": 0,
          "last_worn": null,
          "created_at": "2026-07-15T10:00:00.000001Z",
          "updated_at": "2026-07-15T10:00:00.000001Z"
        }
        """
        let item = try decode(WardrobeItem.self, from: json)
        #expect(item.id == "0f8fad5b-d9cb-469f-a165-70867728950e")
        #expect(item.category == nil)
        #expect(item.season == nil)
        #expect(item.processedImageUrl == nil)
        #expect(item.detectionConfidence == nil)
        #expect(item.classificationSource == nil)
        #expect(item.processingStatus == .pending)
        #expect(item.wearCount == 0)
        #expect(item.lastWorn == nil)
    }

    @Test func decodesWardrobeListResponseWithCompletedItem() throws {
        let json = """
        {
          "items": [
            {
              "category": "top",
              "color_primary": "navy",
              "color_secondary": "white",
              "pattern": "striped",
              "season": ["summer", "spring"],
              "occasion": ["casual", "work"],
              "id": "0f8fad5b-d9cb-469f-a165-70867728950e",
              "user_id": "b7c1a5e2-4f5d-4a4b-9d0f-2a51c3f8e901",
              "original_image_url": "http://localhost:8001/uploads/wardrobe/raw.jpg",
              "processed_image_url": "http://localhost:8001/uploads/wardrobe/processed.png",
              "thumbnail_url": "http://localhost:8001/uploads/wardrobe/thumb.jpg",
              "detection_confidence": 0.93,
              "classification_source": "groq",
              "processing_status": "completed",
              "wear_count": 4,
              "last_worn": "2026-07-10",
              "created_at": "2026-06-01T08:15:30.500000Z",
              "updated_at": "2026-07-10T18:20:11.250000Z"
            }
          ],
          "total": 1,
          "page": 1,
          "page_size": 20,
          "total_pages": 1
        }
        """
        let list = try decode(WardrobeListResponse.self, from: json)
        #expect(list.total == 1)
        #expect(list.pageSize == 20)
        #expect(list.totalPages == 1)
        let item = try #require(list.items.first)
        #expect(item.processingStatus == .completed)
        #expect(item.season == ["summer", "spring"])
        #expect(item.detectionConfidence == 0.93)
        #expect(item.classificationSource == "groq")
        #expect(item.lastWorn == "2026-07-10")
        #expect(item.wearCount == 4)
    }

    @Test func decodesWardrobeUploadResponse() throws {
        let json = """
        {
          "id": "0f8fad5b-d9cb-469f-a165-70867728950e",
          "status": "pending",
          "message": "Image uploaded successfully. Processing started.",
          "original_image_url": "http://localhost:8001/uploads/wardrobe/raw.jpg"
        }
        """
        let response = try decode(WardrobeUploadResponse.self, from: json)
        #expect(response.id == "0f8fad5b-d9cb-469f-a165-70867728950e")
        #expect(response.status == "pending")
        #expect(response.originalImageUrl.hasSuffix("raw.jpg"))
    }

    // MARK: - Daily suggestions

    @Test func decodesDailySuggestionsResponse() throws {
        // NOTE: generated_at copies the backend's timezone-naive
        // `datetime.utcnow().isoformat()` output — no trailing Z. The scores
        // object omits style_dna/behaviour, exactly like the backend's
        // OutfitScores response schema (which drops those keys).
        let json = """
        {
          "recommendation_id": "33333333-3333-3333-3333-333333333333",
          "suggestions": [
            {
              "top_item_id": "11111111-1111-1111-1111-111111111111",
              "top_item": {
                "id": "11111111-1111-1111-1111-111111111111",
                "category": "top",
                "color_primary": "navy",
                "pattern": "solid",
                "image_url": "http://localhost:8001/uploads/wardrobe/top.png",
                "thumbnail_url": null
              },
              "bottom_item_id": "22222222-2222-2222-2222-222222222222",
              "bottom_item": {
                "id": "22222222-2222-2222-2222-222222222222",
                "category": "bottom",
                "color_primary": "beige",
                "pattern": null,
                "image_url": null,
                "thumbnail_url": "http://localhost:8001/uploads/wardrobe/bottom-thumb.jpg"
              },
              "accessory_item": null,
              "scores": {
                "color_harmony": 0.82,
                "formality": 0.7,
                "preference_bonus": 0.1,
                "total": 0.66
              },
              "weather_context": {
                "temp": 24.5,
                "feels_like": 25.1,
                "condition": "Clear",
                "description": "clear sky",
                "humidity": 40,
                "wind_speed": 3.2,
                "icon": "01d"
              },
              "occasion_context": "casual",
              "outfit_index": 0
            }
          ],
          "total_suggestions": 1,
          "generated_at": "2026-07-15T09:31:22.123456",
          "weather": {
            "temp": 24.5,
            "feels_like": 25.1,
            "condition": "Clear",
            "description": "clear sky",
            "humidity": 40,
            "wind_speed": 3.2,
            "icon": "01d"
          },
          "occasion": "casual",
          "cached": false
        }
        """
        let response = try decode(DailySuggestionsResponse.self, from: json)
        #expect(response.totalSuggestions == 1)
        #expect(response.occasion == "casual")
        #expect(!response.cached)
        // Naive timestamp is interpreted as UTC.
        #expect(response.generatedAt == Self.parseISO8601("2026-07-15T09:31:22.123456Z"))
        #expect(response.weather.temp == 24.5)
        #expect(response.weather.feelsLike == 25.1)
        #expect(response.weather.humidity == 40)
        #expect(response.weather.windSpeed == 3.2)
        #expect(response.weather.description == "clear sky")

        let suggestion = try #require(response.suggestions.first)
        #expect(suggestion.topItem.colorPrimary == "navy")
        #expect(suggestion.bottomItem.imageUrl == nil)
        #expect(suggestion.accessoryItem == nil)
        #expect(suggestion.scores.colorHarmony == 0.82)
        #expect(suggestion.scores.styleDna == nil)
        #expect(suggestion.scores.behaviour == nil)
        #expect(suggestion.scores.total == 0.66)
        #expect(suggestion.weatherContext == response.weather)
        #expect(suggestion.occasionContext == "casual")
    }

    @Test func decodesOutfitScoresWithStyleDnaFields() throws {
        // Shape the recommendation algorithm computes internally; tolerated in
        // case the backend response schema starts passing these through.
        let json = """
        {
          "color_harmony": 0.8,
          "formality": 0.6,
          "preference_bonus": 0.2,
          "style_dna": 0.75,
          "behaviour": 0.5,
          "total": 0.71
        }
        """
        let scores = try decode(OutfitScores.self, from: json)
        #expect(scores.styleDna == 0.75)
        #expect(scores.behaviour == 0.5)
    }

    // MARK: - Outfits

    @Test func decodesOutfitWithWeatherContextAndWornDate() throws {
        let json = """
        {
          "top_item_id": "11111111-1111-1111-1111-111111111111",
          "bottom_item_id": "22222222-2222-2222-2222-222222222222",
          "accessory_ids": ["33333333-3333-3333-3333-333333333333"],
          "occasion_context": "work",
          "id": "44444444-4444-4444-4444-444444444444",
          "user_id": "b7c1a5e2-4f5d-4a4b-9d0f-2a51c3f8e901",
          "worn_date": "2026-07-12",
          "feedback_score": 1,
          "weather_context": {"temp": 21.0, "feels_like": 20.4, "condition": "Clouds"},
          "created_at": "2026-07-12T07:45:00.100000Z",
          "updated_at": "2026-07-12T19:02:33.900000Z"
        }
        """
        let outfit = try decode(Outfit.self, from: json)
        #expect(outfit.accessoryIds == ["33333333-3333-3333-3333-333333333333"])
        #expect(outfit.wornDate == "2026-07-12")
        #expect(outfit.feedbackScore == 1)
        let weather = try #require(outfit.weatherContext)
        #expect(weather["temp"] == .number(21.0))
        // Dictionary String keys are NOT converted by .convertFromSnakeCase on
        // the modern Foundation JSON decoder — raw backend keys are preserved.
        #expect(weather["feels_like"] == .number(20.4))
        #expect(weather["feelsLike"] == nil)
    }

    // MARK: - Style DNA

    @Test func decodesStyleDnaProfileResponse() throws {
        let json = """
        {
          "style_dna": {
            "aesthetic": {
              "primary": "minimalist",
              "secondary": ["smart-casual", "classic"],
              "confidence": 0.85
            },
            "color_palette": {
              "dominant": ["navy", "white", "grey"],
              "accent": ["olive"],
              "avoids": ["neon"],
              "confidence": 0.9
            },
            "patterns": {"preferred": ["solid", "striped"], "confidence": 0.8},
            "silhouette": {"preference": "tailored", "confidence": 0.7},
            "formality_bias": {"level": 1.6, "label": "smart-casual", "confidence": 0.75},
            "occasions": {"primary": ["casual", "work"], "confidence": 0.8},
            "behaviour_weights": {
              "category_likes": {"top": 1.5, "bottom": 0.5},
              "color_likes": {"navy": 2.0}
            }
          },
          "photos": [
            {
              "id": "55555555-5555-5555-5555-555555555555",
              "user_id": "b7c1a5e2-4f5d-4a4b-9d0f-2a51c3f8e901",
              "file_path": "uploads/style_dna/photo1.jpg",
              "file_url": "http://localhost:8001/uploads/style_dna/photo1.jpg",
              "quality_ok": true,
              "quality_reason": null,
              "per_photo_extraction": {
                "usable": true,
                "quality_reason": null,
                "style_signals": {
                  "formality_level": 1,
                  "colors": {"primary": ["navy"], "secondary": ["white"]}
                }
              },
              "created_at": "2026-07-14T16:40:12.345678Z"
            },
            {
              "id": "66666666-6666-6666-6666-666666666666",
              "user_id": "b7c1a5e2-4f5d-4a4b-9d0f-2a51c3f8e901",
              "file_path": "uploads/style_dna/photo2.jpg",
              "file_url": "http://localhost:8001/uploads/style_dna/photo2.jpg",
              "quality_ok": false,
              "quality_reason": "Photo too blurry",
              "per_photo_extraction": null,
              "created_at": "2026-07-14T16:40:13.000001Z"
            }
          ]
        }
        """
        let response = try decode(StyleDnaProfileResponse.self, from: json)
        let dna = try #require(response.styleDna)
        #expect(dna.aesthetic.primary == "minimalist")
        #expect(dna.aesthetic.secondary == ["smart-casual", "classic"])
        #expect(dna.colorPalette.dominant == ["navy", "white", "grey"])
        #expect(dna.patterns.preferred == ["solid", "striped"])
        #expect(dna.silhouette.preference == "tailored")
        #expect(dna.formalityBias.level == 1.6)
        #expect(dna.formalityBias.label == "smart-casual")
        #expect(dna.occasions.primary == ["casual", "work"])
        // Dictionary String keys keep their raw backend snake_case form.
        #expect(dna.behaviourWeights["category_likes"]?["top"] == 1.5)
        #expect(dna.behaviourWeights["color_likes"]?["navy"] == 2.0)
        #expect(dna.behaviourWeights["categoryLikes"] == nil)

        #expect(response.photos.count == 2)
        let usable = response.photos[0]
        #expect(usable.qualityOk)
        #expect(usable.qualityReason == nil)
        let extraction = try #require(usable.perPhotoExtraction)
        #expect(extraction["usable"] == .bool(true))
        #expect(extraction["quality_reason"] == .null)
        guard case .object(let signals)? = extraction["style_signals"] else {
            Issue.record("style_signals should decode as an object")
            return
        }
        #expect(signals["formality_level"] == .number(1))

        let skipped = response.photos[1]
        #expect(!skipped.qualityOk)
        #expect(skipped.qualityReason == "Photo too blurry")
        #expect(skipped.perPhotoExtraction == nil)
    }

    @Test func decodesStyleDnaUploadResponseWithNullDna() throws {
        let json = """
        {
          "photos_processed": 0,
          "photos_skipped": 3,
          "wardrobe_items_seeded": 0,
          "style_dna": null,
          "photos": []
        }
        """
        let response = try decode(StyleDnaUploadResponse.self, from: json)
        #expect(response.photosProcessed == 0)
        #expect(response.photosSkipped == 3)
        #expect(response.wardrobeItemsSeeded == 0)
        #expect(response.styleDna == nil)
        #expect(response.photos.isEmpty)
    }

    /// The backend stores the synthesis LLM's output as an untyped dict, so a
    /// shape-drifted style_dna ("secondary": null, string confidence) must
    /// degrade to `styleDna == nil` — the existing no-DNA UX — instead of
    /// failing the whole response. Everything else still decodes.
    private static let malformedStyleDnaJSON = """
    {
      "aesthetic": {"primary": "minimalist", "secondary": null, "confidence": "high"},
      "color_palette": {"dominant": ["navy"], "accent": [], "avoids": [], "confidence": 0.8},
      "patterns": {"preferred": ["solid"], "confidence": 0.7},
      "silhouette": {"preference": "tailored", "confidence": 0.6},
      "formality_bias": {"level": 1.5, "label": "smart-casual", "confidence": 0.7},
      "occasions": {"primary": ["casual"], "confidence": 0.7},
      "behaviour_weights": {}
    }
    """

    private static let styleDnaPhotoJSON = """
    {
      "id": "55555555-5555-5555-5555-555555555555",
      "user_id": "b7c1a5e2-4f5d-4a4b-9d0f-2a51c3f8e901",
      "file_path": "uploads/style_dna/photo1.jpg",
      "file_url": "http://localhost:8001/uploads/style_dna/photo1.jpg",
      "quality_ok": true,
      "quality_reason": null,
      "per_photo_extraction": {"usable": true},
      "created_at": "2026-07-14T16:40:12.345678Z"
    }
    """

    @Test func malformedStyleDnaDegradesToNilInUploadResponse() throws {
        let json = """
        {
          "photos_processed": 3,
          "photos_skipped": 0,
          "wardrobe_items_seeded": 2,
          "style_dna": \(Self.malformedStyleDnaJSON),
          "photos": [\(Self.styleDnaPhotoJSON)]
        }
        """
        let response = try decode(StyleDnaUploadResponse.self, from: json)
        #expect(response.styleDna == nil)
        #expect(response.photosProcessed == 3)
        #expect(response.photosSkipped == 0)
        #expect(response.wardrobeItemsSeeded == 2)
        #expect(response.photos.count == 1)
        #expect(response.photos.first?.id == "55555555-5555-5555-5555-555555555555")
        #expect(response.photos.first?.perPhotoExtraction?["usable"] == .bool(true))
    }

    @Test func malformedStyleDnaDegradesToNilInProfileResponse() throws {
        let json = """
        {
          "style_dna": \(Self.malformedStyleDnaJSON),
          "photos": [\(Self.styleDnaPhotoJSON)]
        }
        """
        let response = try decode(StyleDnaProfileResponse.self, from: json)
        #expect(response.styleDna == nil)
        #expect(response.photos.count == 1)
        #expect(response.photos.first?.fileUrl.hasSuffix("photo1.jpg") == true)
    }

    /// The leniency lives ONLY on the response wrappers — `StyleDna` itself
    /// stays strict, so direct decodes of a malformed blob still throw.
    @Test func styleDnaItselfStaysStrict() {
        #expect(throws: DecodingError.self) {
            _ = try Self.makeDecoder().decode(StyleDna.self, from: Data(Self.malformedStyleDnaJSON.utf8))
        }
    }

    // MARK: - Request encoding (round-trip through .convertToSnakeCase)

    @Test func encodesRegisterRequestWithSnakeCaseKeys() throws {
        let encoder = JSONEncoder()
        encoder.keyEncodingStrategy = .convertToSnakeCase
        let request = RegisterRequest(email: "ada@example.com", password: "Sup3rSecret", fullName: "Ada Lovelace")
        let data = try encoder.encode(request)
        let object = try #require(try JSONSerialization.jsonObject(with: data) as? [String: Any])
        #expect(object["email"] as? String == "ada@example.com")
        #expect(object["full_name"] as? String == "Ada Lovelace")
        #expect(object["fullName"] == nil)
    }

    @Test func encodesTokenRefreshRequestWithSnakeCaseKeys() throws {
        let encoder = JSONEncoder()
        encoder.keyEncodingStrategy = .convertToSnakeCase
        let data = try encoder.encode(TokenRefreshRequest(refreshToken: "abc"))
        let object = try #require(try JSONSerialization.jsonObject(with: data) as? [String: Any])
        #expect(object["refresh_token"] as? String == "abc")
    }
}
