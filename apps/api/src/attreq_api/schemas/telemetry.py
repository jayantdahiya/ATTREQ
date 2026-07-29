"""Pydantic schemas for recommendation/user event telemetry (RI-1)."""

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class RejectionReason(StrEnum):
    """Fixed enum of rejection reasons — directly usable as labeled features."""

    TOO_FORMAL = "too_formal"
    TOO_CASUAL = "too_casual"
    DONT_LIKE_COMBO = "dont_like_combo"
    WEATHER_WRONG = "weather_wrong"
    WORE_RECENTLY = "wore_recently"
    DISLIKE_ITEM = "dislike_item"
    OTHER = "other"


class RecommendationFeedbackAction(StrEnum):
    """Actions a user can take on a shown outfit suggestion."""

    ACCEPTED = "accepted"
    REJECTED = "rejected"
    SWAPPED = "swapped"


class RecommendationFeedbackRequest(BaseModel):
    """Body for POST /recommendations/{recommendation_id}/feedback.

    Forgiving by design: rejection_reason/rejection_note are only meaningful when
    action == REJECTED. If sent with another action they are ignored, not rejected —
    the rejection UI "must be skippable" (a bare `rejected` with no reason is still
    a valid pair).
    """

    outfit_index: int = Field(..., ge=0, description="0-based position within the shown batch")
    action: RecommendationFeedbackAction
    rejection_reason: RejectionReason | None = None
    rejection_note: str | None = Field(None, max_length=500)
    swapped_item_ids: list[str] | None = Field(
        None, description="Schema-only for now — no swap UI ships in RI-1 (see RI-4/RI-5)."
    )


class RecommendationFeedbackResponse(BaseModel):
    """Response confirming a feedback event was recorded."""

    recommendation_id: str
    outfit_index: int
    event_type: str
    created_at: datetime
