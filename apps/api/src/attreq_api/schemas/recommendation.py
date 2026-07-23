"""Pydantic schemas for recommendation system."""

from typing import Any, Literal

from pydantic import BaseModel, Field, field_serializer

from attreq_api.services.storage import resolve_image_url


class WeatherData(BaseModel):
    """Weather information schema."""

    temp: float = Field(..., description="Temperature in Celsius")
    feels_like: float = Field(..., description="Feels like temperature in Celsius")
    condition: str = Field(..., description="Weather condition (e.g., Clear, Rain)")
    description: str = Field(..., description="Detailed weather description")
    humidity: int = Field(..., description="Humidity percentage")
    wind_speed: float = Field(..., description="Wind speed in m/s")
    icon: str = Field(..., description="Weather icon code")


class OutfitItemDetail(BaseModel):
    """Detailed information about a wardrobe item in an outfit."""

    id: str = Field(..., description="Item UUID")
    category: str | None = Field(None, description="Item category")
    color_primary: str | None = Field(None, description="Primary color")
    pattern: str | None = Field(None, description="Pattern type")
    image_url: str | None = Field(None, description="Full image URL")
    thumbnail_url: str | None = Field(None, description="Thumbnail URL")

    @field_serializer("image_url", "thumbnail_url")
    def _resolve_image_urls(self, value: str | None) -> str | None:
        return resolve_image_url(value)


class OutfitScores(BaseModel):
    """Scoring breakdown for an outfit suggestion."""

    color_harmony: float = Field(..., description="Color compatibility score (0-1)")
    color_harmony_branch: str | None = Field(
        None,
        description=(
            "RI-3: winning color-harmony branch — 'tonal' | 'neutral_contrast' | "
            "'hue_rule' | 'none'. Consumed by RI-4 explanations."
        ),
    )
    formality: float = Field(
        ...,
        description=(
            "RI-3: context score (0.55*occasion_fit + 0.35*weather_score + "
            "0.10*time_score) occupying the original formality slot — see "
            "services/recommendation/context_scoring.py"
        ),
    )
    preference_bonus: float = Field(..., description="User preference bonus (0-1)")
    style_dna: float | None = Field(None, description="Style DNA affinity score (0-1)")
    behaviour: float | None = Field(None, description="Learned behaviour-weight score (0-1)")
    # RI-4: additive score-composition contract (section 5.5) — all default to
    # 0.0 (never required), so fullbody candidates (which populate every key,
    # 0.0 where a term doesn't apply) and any legacy payload still validate.
    base_compatibility: float = Field(
        0.0,
        description=(
            "RI-4: the pre-adjustment weighted color/context/style_dna/behaviour "
            "sum the confidence hedge is calibrated against — NOT the "
            "rotation-penalized total."
        ),
    )
    cold_start_bonus: float = Field(0.0, description="RI-4: content-similarity prior for genuinely-new items")
    rediscovery_bonus: float = Field(0.0, description="RI-4: grey-inventory promotion, capped at +0.05")
    rotation_penalty: float = Field(0.0, description="RI-4: anti-repetition decay, always <= 0")
    # RI-6: additive score-composition keys. Both default to `None` so
    # candidates generated with EMBEDDINGS_ENABLED=false (no vectors
    # available at all) still validate without silently dropping data.
    centroid: float | None = Field(
        None,
        description=(
            "RI-6: mean FashionCLIP cosine similarity (mapped to [0,1]) between "
            "the outfit's core items and the user's style centroid. Hand-tuned "
            "0.10 weight, provisional pending RI-5's fitted weights."
        ),
    )
    propagation_adjustment: float | None = Field(
        None,
        description=(
            "RI-6: thumbs-propagation adjustment from recent like/dislike "
            "neighbors, clamped to [-0.05, +0.05] per item."
        ),
    )
    total: float = Field(..., description="Total combined score, clamped to [0, 1]")

    @field_serializer("total")
    def _clamp_total(self, value: float) -> float:
        return max(0.0, min(1.0, value))


class OutfitSuggestion(BaseModel):
    """Single outfit suggestion with items and scoring.

    RI-4: `top_item_id`/`top_item`/`bottom_item_id`/`bottom_item` become
    optional — a fullbody-anchored outfit (`fullbody_item_id` set) has
    neither (see `services/recommendation/composition.py`'s fullbody branch:
    it never sets a phantom bottom).
    """

    top_item_id: str | None = Field(None, description="Top item UUID (null for a fullbody outfit)")
    top_item: OutfitItemDetail | None = Field(None, description="Top item details")
    bottom_item_id: str | None = Field(None, description="Bottom item UUID (null for a fullbody outfit)")
    bottom_item: OutfitItemDetail | None = Field(None, description="Bottom item details")
    fullbody_item_id: str | None = Field(None, description="RI-4: fullbody anchor item UUID")
    fullbody_item: OutfitItemDetail | None = Field(None, description="RI-4: fullbody anchor item details")
    footwear_item_id: str | None = Field(None, description="RI-4: footwear item UUID")
    footwear_item: OutfitItemDetail | None = Field(None, description="RI-4: footwear item details")
    outerwear_item_id: str | None = Field(None, description="RI-4: outerwear item UUID")
    outerwear_item: OutfitItemDetail | None = Field(None, description="RI-4: outerwear item details")
    accessory_item: OutfitItemDetail | None = Field(None, description="Optional accessory item")
    scores: OutfitScores = Field(..., description="Scoring breakdown")
    weather_context: dict[str, Any] = Field(..., description="Weather data used for generation")
    occasion_context: str = Field(..., description="Occasion type")
    outfit_index: int = Field(..., description="0-based position within the shown batch")
    explanation: str = Field("", description="RI-4: template-composed, one-line reason for this pick")
    confidence: Literal["low", "normal"] = Field(
        "normal", description="RI-4: 'low' hedges the explanation when base_compatibility is weak"
    )
    rediscovery: bool = Field(False, description="RI-4: at most one true per batch — a grey-inventory pick")
    rediscovery_item_id: str | None = Field(
        None, description="RI-4: the neglected item id driving the rediscovery bonus, when marked"
    )
    rationale: str | None = Field(
        None,
        description=(
            "RI-6: one-sentence LLM re-ranker rationale for this pick, only "
            "present when RERANKER_ENABLED and the LLM call validated."
        ),
    )


class DailySuggestionsResponse(BaseModel):
    """Response containing daily outfit suggestions."""

    recommendation_id: str = Field(..., description="Groups this generation batch for feedback/telemetry")
    suggestions: list[OutfitSuggestion] = Field(..., description="List of outfit suggestions")
    total_suggestions: int = Field(..., description="Number of suggestions returned")
    generated_at: str = Field(..., description="ISO timestamp when suggestions were generated")
    weather: WeatherData = Field(..., description="Weather data used")
    occasion: str = Field(..., description="Occasion type requested")
    cached: bool = Field(False, description="Whether results were served from cache")


class SwipeDeckStatusResponse(BaseModel):
    """RI-5 (Task 5.3): today's swipe-deck rating count + cap, so the client
    can show/hide the entry point without inferring state from a 429."""

    ratings_today: int = Field(..., description="Swipe-deck ratings submitted today")
    cap: int = Field(..., description="Daily rating cap")


class DailySuggestionRequest(BaseModel):
    """Request parameters for daily suggestions (for documentation)."""

    lat: float = Field(..., description="Latitude for weather lookup", ge=-90, le=90)
    lon: float = Field(..., description="Longitude for weather lookup", ge=-180, le=180)
    occasion: str = Field("casual", description="Occasion type (casual, formal, party, etc.)")
    force_refresh: bool = Field(False, description="Force regeneration, bypass cache")
