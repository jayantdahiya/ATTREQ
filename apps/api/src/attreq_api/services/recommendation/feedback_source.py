"""Adapters that surface recent user like/dislike signal for RI-6
thumbs-propagation (`services/recommendation/similarity.py::compute_propagation_penalties`).

Two sources, in preference order:

1. `recommendation_events` (RI-1, merged) — the real per-generation
   telemetry. A `rejected` row with `rejection_reason == "dislike_item"` is
   the dislike signal; `accepted`/`worn` rows are the like signal. Both
   `top_item_id`/`bottom_item_id`/`fullbody_item_id` from the row's
   `outfit_payload` are treated as (weak, outfit-level — not item-level)
   dislike/like candidates: RI-1 does not record *which* item in a rejected
   outfit was disliked, only that the whole outfit was rejected for that
   reason. This is the PRIMARY source.

2. `Outfit.feedback_score` — the older per-outfit like/dislike column. Used
   only as a FALLBACK when the `recommendation_events` query returns nothing
   (e.g. a user who only ever rates saved outfits via
   `POST /outfits/{id}/feedback` and never goes through
   `/recommendations/daily`, or a fresh install with no telemetry yet).
"""

import logging
from datetime import datetime, timedelta
from uuid import UUID

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from attreq_api.models.outfit import Outfit
from attreq_api.models.recommendation_event import RecommendationEvent

logger = logging.getLogger(__name__)

# Matches schemas.telemetry.RejectionReason.DISLIKE_ITEM.value — a plain
# string here (not an import) to keep this module import-light.
_DISLIKE_ITEM_REASON = "dislike_item"
_POSITIVE_EVENT_TYPES = ("accepted", "worn")
_PAYLOAD_ITEM_KEYS = ("top_item_id", "bottom_item_id", "fullbody_item_id")


def _item_ids_from_payloads(rows: list[RecommendationEvent]) -> list[UUID]:
    item_ids: set[UUID] = set()
    for row in rows:
        payload = row.outfit_payload or {}
        for key in _PAYLOAD_ITEM_KEYS:
            raw = payload.get(key)
            if not raw:
                continue
            try:
                item_ids.add(raw if isinstance(raw, UUID) else UUID(str(raw)))
            except (ValueError, TypeError):
                continue
    return list(item_ids)


async def _dislikes_from_recommendation_events(
    db: AsyncSession, user_id: UUID, cutoff: datetime
) -> list[UUID]:
    query = select(RecommendationEvent).where(
        and_(
            RecommendationEvent.user_id == user_id,
            RecommendationEvent.event_type == "rejected",
            RecommendationEvent.rejection_reason == _DISLIKE_ITEM_REASON,
            RecommendationEvent.created_at >= cutoff,
        )
    )
    result = await db.execute(query)
    return _item_ids_from_payloads(list(result.scalars().all()))


async def _likes_from_recommendation_events(
    db: AsyncSession, user_id: UUID, cutoff: datetime
) -> list[UUID]:
    query = select(RecommendationEvent).where(
        and_(
            RecommendationEvent.user_id == user_id,
            RecommendationEvent.event_type.in_(_POSITIVE_EVENT_TYPES),
            RecommendationEvent.created_at >= cutoff,
        )
    )
    result = await db.execute(query)
    return _item_ids_from_payloads(list(result.scalars().all()))


def _item_ids_from_outfits(outfits: list[Outfit]) -> list[UUID]:
    item_ids: set[UUID] = set()
    for outfit in outfits:
        if outfit.top_item_id:
            item_ids.add(outfit.top_item_id)
        if outfit.bottom_item_id:
            item_ids.add(outfit.bottom_item_id)
        if outfit.fullbody_item_id:
            item_ids.add(outfit.fullbody_item_id)
    return list(item_ids)


async def _dislikes_from_outfit_adapter(
    db: AsyncSession, user_id: UUID, cutoff: datetime
) -> list[UUID]:
    """Fallback adapter (pre-RI-1 mechanism): `Outfit.feedback_score == -1`."""
    query = select(Outfit).where(
        and_(
            Outfit.user_id == user_id,
            Outfit.feedback_score == -1,
            Outfit.created_at >= cutoff,
        )
    )
    result = await db.execute(query)
    return _item_ids_from_outfits(list(result.scalars().all()))


async def _likes_from_outfit_adapter(
    db: AsyncSession, user_id: UUID, cutoff: datetime
) -> list[UUID]:
    query = select(Outfit).where(
        and_(
            Outfit.user_id == user_id,
            Outfit.feedback_score == 1,
            Outfit.created_at >= cutoff,
        )
    )
    result = await db.execute(query)
    return _item_ids_from_outfits(list(result.scalars().all()))


async def get_recent_dislikes(db: AsyncSession, user_id: UUID, days: int = 30) -> list[UUID]:
    """Item IDs the user recently signaled disliking.

    Prefers real `recommendation_events` rejections tagged `dislike_item`
    (RI-1). Falls back to the older `Outfit.feedback_score == -1` adapter
    only when the events-based query returns nothing.
    """
    cutoff = datetime.utcnow() - timedelta(days=days)
    item_ids = await _dislikes_from_recommendation_events(db, user_id, cutoff)
    if item_ids:
        return item_ids
    return await _dislikes_from_outfit_adapter(db, user_id, cutoff)


async def get_recent_likes(db: AsyncSession, user_id: UUID, days: int = 30) -> list[UUID]:
    """Item IDs the user recently signaled liking — see `get_recent_dislikes`."""
    cutoff = datetime.utcnow() - timedelta(days=days)
    item_ids = await _likes_from_recommendation_events(db, user_id, cutoff)
    if item_ids:
        return item_ids
    return await _likes_from_outfit_adapter(db, user_id, cutoff)
