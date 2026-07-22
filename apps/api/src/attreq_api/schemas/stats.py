"""Pydantic schemas for wardrobe stats & forgotten-items retention surfaces."""

from datetime import date
from typing import Any

from pydantic import BaseModel, Field


class CategoryBreakdown(BaseModel):
    """Item count for a single garment category."""

    category: str
    count: int


class ColorFamilyBreakdown(BaseModel):
    """Item count for a color family bucket (neutral/warm/cool/other/unknown)."""

    family: str
    count: int


class BrandBreakdown(BaseModel):
    """Item count for a brand ("Unbranded" when brand is null)."""

    brand: str
    count: int


class WornItemEntry(BaseModel):
    """A single item entry in the most/least-worn lists."""

    item_id: str
    category: str | None = None
    color_primary: str | None = None
    thumbnail_url: str | None = None
    wear_count: int
    last_worn: date | None = None


class CostPerWearEntry(BaseModel):
    """Cost-per-wear entry (only present for items with a purchase price set)."""

    item_id: str
    category: str | None = None
    color_primary: str | None = None
    thumbnail_url: str | None = None
    purchase_price: float
    wear_count: int
    cost_per_wear: float | None = Field(
        None, description="purchase_price / wear_count; null when never worn"
    )


class WardrobeStatsResponse(BaseModel):
    """Wardrobe stats dashboard payload (active items only)."""

    total_active_items: int
    by_category: list[CategoryBreakdown]
    by_color_family: list[ColorFamilyBreakdown]
    by_brand: list[BrandBreakdown]
    closet_value: float
    items_missing_price: int
    never_worn_count: int
    never_worn_percent: float
    most_worn: list[WornItemEntry]
    least_worn: list[WornItemEntry]
    cost_per_wear: list[CostPerWearEntry]
    worn_last_30_days: int
    worn_last_90_days: int
    generated_at: str
    cached: bool = False


class ForgottenPartner(BaseModel):
    """Suggested pairing partner for a forgotten item ("wear it with...")."""

    item_id: str
    category: str | None = None
    color_primary: str | None = None
    thumbnail_url: str | None = None
    score: float


class ForgottenItemEntry(BaseModel):
    """A single forgotten (never-worn or stale) wardrobe item."""

    item_id: str
    category: str | None = None
    color_primary: str | None = None
    thumbnail_url: str | None = None
    wear_count: int
    last_worn: date | None = None
    days_since_worn: int | None = None
    best_partner: ForgottenPartner | None = None


class ForgottenItemsResponse(BaseModel):
    """Forgotten-items surface payload."""

    items: list[ForgottenItemEntry]
    count: int
    generated_at: str
    cached: bool = False


def build_wardrobe_stats_response(data: dict[str, Any]) -> WardrobeStatsResponse:
    """Validate a raw (possibly cache-round-tripped) stats dict into the response model."""
    return WardrobeStatsResponse(**data)


def build_forgotten_items_response(data: dict[str, Any]) -> ForgottenItemsResponse:
    """Validate a raw (possibly cache-round-tripped) forgotten-items dict into the response model."""
    return ForgottenItemsResponse(**data)
