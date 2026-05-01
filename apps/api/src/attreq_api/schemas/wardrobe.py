"""Pydantic schemas for wardrobe-related operations."""

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field


class WardrobeItemBase(BaseModel):
    """Base wardrobe item schema with common fields."""

    category: str | None = Field(None, max_length=100)
    color_primary: str | None = Field(None, max_length=50)
    color_secondary: str | None = Field(None, max_length=50)
    pattern: str | None = Field(None, max_length=50)
    season: list[str] | None = None
    occasion: list[str] | None = None


class WardrobeItemCreate(BaseModel):
    """Schema for creating a wardrobe item (minimal - most fields set by AI)."""

    # Most fields will be set by the AI processing pipeline
    # User can optionally provide initial tags
    category: str | None = Field(None, max_length=100)
    season: list[str] | None = None
    occasion: list[str] | None = None


class WardrobeItemUpdate(BaseModel):
    """Schema for manually updating wardrobe item tags."""

    category: str | None = Field(None, max_length=100)
    color_primary: str | None = Field(None, max_length=50)
    color_secondary: str | None = Field(None, max_length=50)
    pattern: str | None = Field(None, max_length=50)
    season: list[str] | None = None
    occasion: list[str] | None = None


class WardrobeItemResponse(WardrobeItemBase):
    """Schema for wardrobe item response with all data."""

    id: UUID
    user_id: UUID
    original_image_url: str
    processed_image_url: str | None = None
    thumbnail_url: str | None = None
    detection_confidence: float | None = None
    classification_source: str | None = None
    processing_status: str
    wear_count: int
    last_worn: date | None = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class WardrobeItemList(BaseModel):
    """Schema for paginated list of wardrobe items."""

    items: list[WardrobeItemResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class WardrobeItemUploadResponse(BaseModel):
    """Schema for upload response."""

    id: UUID
    status: str
    message: str
    original_image_url: str
