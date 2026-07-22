"""Pydantic schemas for Style DNA operations."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, field_serializer

from attreq_api.services.storage import resolve_image_url


class StyleDnaPhotoResponse(BaseModel):
    id: UUID
    user_id: UUID
    file_path: str
    file_url: str
    quality_ok: bool
    quality_reason: str | None = None
    per_photo_extraction: dict[str, Any] | None = None
    created_at: datetime

    @field_serializer("file_url")
    def _resolve_image_urls(self, value: str) -> str:
        return resolve_image_url(value)

    class Config:
        from_attributes = True


class StyleDnaUploadResponse(BaseModel):
    photos_processed: int
    photos_skipped: int
    wardrobe_items_seeded: int
    style_dna: dict[str, Any] | None = None
    photos: list[StyleDnaPhotoResponse] = []


class StyleDnaProfileResponse(BaseModel):
    style_dna: dict[str, Any] | None = None
    photos: list[StyleDnaPhotoResponse] = []


class StyleDnaCorrection(BaseModel):
    """Partial corrections to Style DNA fields."""
    corrections: dict[str, Any]
