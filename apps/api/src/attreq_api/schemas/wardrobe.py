"""Pydantic schemas for wardrobe-related operations."""

from datetime import date, datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, field_serializer

from attreq_api.services.storage import resolve_image_url


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
    purchase_price: float | None = Field(None, ge=0)
    brand: str | None = Field(None, max_length=100)


class WardrobeItemStatusUpdate(BaseModel):
    """Schema for archiving/unarchiving a wardrobe item."""

    status: Literal["active", "archived"]


class WardrobeItemPhotoResponse(BaseModel):
    """Schema for a single wardrobe item photo."""

    id: UUID
    original_image_url: str
    processed_image_url: str | None = None
    thumbnail_url: str | None = None
    is_primary: bool
    created_at: datetime

    class Config:
        from_attributes = True


class WardrobeItemPhotoUploadResponse(BaseModel):
    """Schema for the response to adding a photo to an item."""

    id: UUID
    status: str
    message: str


class WardrobeItemResponse(WardrobeItemBase):
    """Schema for a single wardrobe item response, including photos.

    Only constructed from ORM objects where `photos` was eager-loaded via
    `selectinload` (single-item GET, PATCH status) — never from the paginated
    list query, to avoid async lazy-load crashes. See `WardrobeItemListEntry`
    for the list-response shape (no `photos`).
    """

    id: UUID
    user_id: UUID
    original_image_url: str
    processed_image_url: str | None = None
    thumbnail_url: str | None = None
    detection_confidence: float | None = None
    classification_source: str | None = None
    processing_status: str
    status: str
    purchase_price: float | None = None
    brand: str | None = None
    wear_count: int
    last_worn: date | None = None
    photos: list[WardrobeItemPhotoResponse] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class WardrobeItemListEntry(WardrobeItemBase):
    """Schema for a wardrobe item as it appears in the paginated list.

    Deliberately omits `photos` — the list query does not eager-load the
    photos relationship (avoids N+1 queries and the async lazy-load crash
    that would occur if `from_attributes` touched an unloaded collection).
    """

    id: UUID
    user_id: UUID
    original_image_url: str
    processed_image_url: str | None = None
    thumbnail_url: str | None = None
    detection_confidence: float | None = None
    classification_source: str | None = None
    processing_status: str
    status: str
    purchase_price: float | None = None
    brand: str | None = None
    wear_count: int
    last_worn: date | None = None
    created_at: datetime
    updated_at: datetime

    @field_serializer("original_image_url", "processed_image_url", "thumbnail_url")
    def _resolve_image_urls(self, value: str | None) -> str | None:
        return resolve_image_url(value)

    class Config:
        from_attributes = True


class WardrobeItemList(BaseModel):
    """Schema for paginated list of wardrobe items."""

    items: list[WardrobeItemListEntry]
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

    @field_serializer("original_image_url")
    def _resolve_image_urls(self, value: str) -> str:
        return resolve_image_url(value)
