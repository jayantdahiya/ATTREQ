"""Pydantic schemas for wardrobe-related operations."""

from datetime import date, datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, field_serializer, field_validator

from attreq_api.schemas.wardrobe_enums import (
    NECKLINE_VALUES,
    SILHOUETTE_VALUES,
    SLEEVE_LENGTH_VALUES,
    STATEMENT_LEVEL_VALUES,
    TEXTURE_VALUES,
)
from attreq_api.services.storage import resolve_image_url


def _validate_enum_value(value: str | None, allowed: list[str], field_name: str) -> str | None:
    """Reject an out-of-vocabulary enum string with a clear 422 message.

    Used only on the *user-correctable* enum fields in `WardrobeItemUpdate` —
    the response schemas accept whatever the (already-coerced-by-the-mapper)
    stored value is, never re-validating LLM output on the way out.
    """
    if value is not None and value not in allowed:
        raise ValueError(f"{field_name} must be one of {allowed}, got {value!r}")
    return value


class PaletteColorSchema(BaseModel):
    """One color in a deterministic CIELAB `color_palette` (RI-2)."""

    lab: tuple[float, float, float]
    hex: str
    share: float
    is_neutral: bool
    name: str


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
    """Schema for manually updating wardrobe item tags.

    RI-2 adds the user-correctable v2 attribute fields (texture, silhouette,
    neckline, sleeve_length, statement_level, is_fullbody) — deliberately
    NOT `llm_formality`, `color_palette`, `color_extraction_source`,
    `attribute_confidence`, or `schema_version`, which are system-derived and
    not user-editable.
    """

    category: str | None = Field(None, max_length=100)
    color_primary: str | None = Field(None, max_length=50)
    color_secondary: str | None = Field(None, max_length=50)
    pattern: str | None = Field(None, max_length=50)
    season: list[str] | None = None
    occasion: list[str] | None = None
    purchase_price: float | None = Field(None, ge=0)
    brand: str | None = Field(None, max_length=100)

    texture: str | None = Field(None, max_length=20)
    silhouette: str | None = Field(None, max_length=20)
    neckline: str | None = Field(None, max_length=20)
    sleeve_length: str | None = Field(None, max_length=20)
    statement_level: str | None = Field(None, max_length=20)
    is_fullbody: bool | None = None

    @field_validator("texture")
    @classmethod
    def _validate_texture(cls, v: str | None) -> str | None:
        return _validate_enum_value(v, TEXTURE_VALUES, "texture")

    @field_validator("silhouette")
    @classmethod
    def _validate_silhouette(cls, v: str | None) -> str | None:
        return _validate_enum_value(v, SILHOUETTE_VALUES, "silhouette")

    @field_validator("neckline")
    @classmethod
    def _validate_neckline(cls, v: str | None) -> str | None:
        return _validate_enum_value(v, NECKLINE_VALUES, "neckline")

    @field_validator("sleeve_length")
    @classmethod
    def _validate_sleeve_length(cls, v: str | None) -> str | None:
        return _validate_enum_value(v, SLEEVE_LENGTH_VALUES, "sleeve_length")

    @field_validator("statement_level")
    @classmethod
    def _validate_statement_level(cls, v: str | None) -> str | None:
        return _validate_enum_value(v, STATEMENT_LEVEL_VALUES, "statement_level")


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

    # Classifier schema v2 (RI-2). All optional so pre-RI-2 (`schema_version=1`)
    # rows — which have `null` for every field below — still serialize cleanly.
    texture: str | None = None
    silhouette: str | None = None
    neckline: str | None = None
    sleeve_length: str | None = None
    statement_level: str | None = None
    llm_formality: int | None = None
    is_fullbody: bool = False
    color_palette: list[PaletteColorSchema] | None = None
    color_extraction_source: str | None = None
    attribute_confidence: dict[str, float] | None = None
    schema_version: int = 1

    # RI-6: near-duplicate detection is async (upload returns before the
    # embedding exists), so the warning is a stored field surfaced via this
    # GET response rather than the upload response. `None` when no
    # near-duplicate (>= 0.97 cosine similarity) was found, embeddings are
    # disabled, or the item hasn't finished processing yet.
    possible_duplicate_of: UUID | None = None
    needs_review: bool = False
    review_reason: str | None = None

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
