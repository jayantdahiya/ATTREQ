"""Pydantic schemas for outfit-related operations."""

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field


class OutfitBase(BaseModel):
    """Base outfit schema with common fields."""

    top_item_id: UUID | None = None
    bottom_item_id: UUID | None = None
    accessory_ids: list[UUID] | None = None
    occasion_context: str | None = Field(None, max_length=100)


class OutfitCreate(OutfitBase):
    """Schema for creating an outfit."""

    pass


class OutfitResponse(OutfitBase):
    """Schema for outfit response with all data."""

    id: UUID
    user_id: UUID
    worn_date: date | None = None
    feedback_score: int | None = None
    weather_context: dict | None = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class OutfitWithItems(OutfitResponse):
    """Schema for outfit response with full item details."""

    top_item: dict | None = None
    bottom_item: dict | None = None
    # Note: accessory items would need to be fetched separately


class OutfitFeedback(BaseModel):
    """Schema for submitting feedback on an outfit."""

    feedback_score: int = Field(
        ..., ge=-1, le=1, description="Feedback: -1 (dislike), 0 (neutral), 1 (like)"
    )


class OutfitWear(BaseModel):
    """Schema for marking an outfit as worn."""

    worn_date: date = Field(default_factory=date.today)


class OutfitList(BaseModel):
    """Schema for paginated list of outfits."""

    items: list[OutfitResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
