"""Pydantic schemas for recommendation system."""

from datetime import date
from typing import Any

from pydantic import BaseModel, Field


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


class OutfitScores(BaseModel):
    """Scoring breakdown for an outfit suggestion."""

    color_harmony: float = Field(..., description="Color compatibility score (0-1)")
    formality: float = Field(..., description="Formality matching score (0-1)")
    preference_bonus: float = Field(..., description="User preference bonus (0-1)")
    total: float = Field(..., description="Total combined score (0-1)")


class OutfitSuggestion(BaseModel):
    """Single outfit suggestion with items and scoring."""

    top_item_id: str = Field(..., description="Top item UUID")
    top_item: OutfitItemDetail = Field(..., description="Top item details")
    bottom_item_id: str = Field(..., description="Bottom item UUID")
    bottom_item: OutfitItemDetail = Field(..., description="Bottom item details")
    accessory_item: OutfitItemDetail | None = Field(None, description="Optional accessory item")
    scores: OutfitScores = Field(..., description="Scoring breakdown")
    weather_context: dict[str, Any] = Field(..., description="Weather data used for generation")
    occasion_context: str = Field(..., description="Occasion type")


class DailySuggestionsResponse(BaseModel):
    """Response containing daily outfit suggestions."""

    suggestions: list[OutfitSuggestion] = Field(..., description="List of outfit suggestions")
    total_suggestions: int = Field(..., description="Number of suggestions returned")
    generated_at: str = Field(..., description="ISO timestamp when suggestions were generated")
    weather: WeatherData = Field(..., description="Weather data used")
    occasion: str = Field(..., description="Occasion type requested")
    cached: bool = Field(False, description="Whether results were served from cache")


class DailySuggestionRequest(BaseModel):
    """Request parameters for daily suggestions (for documentation)."""

    lat: float = Field(..., description="Latitude for weather lookup", ge=-90, le=90)
    lon: float = Field(..., description="Longitude for weather lookup", ge=-180, le=180)
    occasion: str = Field("casual", description="Occasion type (casual, formal, party, etc.)")
    force_refresh: bool = Field(False, description="Force regeneration, bypass cache")

