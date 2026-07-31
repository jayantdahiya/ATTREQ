"""CRUD operations for recommendation_events.

Append-only: no update()/delete() methods are exposed here (and none should be added —
that's the code-level meaning of "append-only"). Every write method commits internally
because `get_db` (config/database.py) never commits on its own — it only rolls back on
exception and closes. Without an internal commit, every insert would be silently
discarded when the session closes at the end of the request.
"""

import uuid
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from attreq_api.models.recommendation_event import RecommendationEvent

# Positive signal event types for preference-pair derivation.
POSITIVE_EVENT_TYPES = ("accepted", "worn")


class RecommendationEventCRUD:
    """CRUD operations for recommendation_events."""

    async def bulk_create_shown(
        self,
        db: AsyncSession,
        *,
        user_id: UUID,
        recommendation_id: UUID,
        candidates: list[dict[str, Any]],
        context: dict[str, Any] | None = None,
    ) -> list[RecommendationEvent]:
        """Write one `shown` row per candidate outfit in a generation batch.

        `candidates` must be the raw candidate dicts produced by
        `generate_daily_outfits` (i.e. `scores` carries all 6 keys, including
        `style_dna`/`behaviour` — the serialized response schema historically
        dropped these, so this must NOT be built from the validated response).

        `outfit_index` is the candidate's position in `candidates` (enumerate order) —
        this is the single source of truth for index/recommendation_id, stamped by the
        caller before this is invoked.
        """
        events = []
        for index, candidate in enumerate(candidates):
            accessory_item = candidate.get("accessory_item") or {}
            outfit_payload = {
                "top_item_id": candidate.get("top_item_id"),
                "bottom_item_id": candidate.get("bottom_item_id"),
                # RI-4: fullbody/footwear/outerwear slots — `None` for
                # pre-RI-4-shaped candidate dicts (`.get` defaults), so this
                # stays backward compatible with any caller that hasn't been
                # updated to the new composition.OutfitCandidate shape.
                "fullbody_item_id": candidate.get("fullbody_item_id"),
                "footwear_item_id": candidate.get("footwear_item_id"),
                "outerwear_item_id": candidate.get("outerwear_item_id"),
                "accessory_item_id": accessory_item.get("id"),
                "scores": candidate.get("scores", {}),
            }
            event = RecommendationEvent(
                id=uuid.uuid4(),
                user_id=user_id,
                recommendation_id=recommendation_id,
                outfit_index=index,
                outfit_payload=outfit_payload,
                event_type="shown",
                context=context,
                # RI-4: the composed explanation/confidence hedge shown to
                # the user, captured on the same telemetry row as the score
                # breakdown. `None` for candidates that predate RI-4.
                explanation=candidate.get("explanation"),
                confidence=candidate.get("confidence"),
            )
            db.add(event)
            events.append(event)

        await db.commit()
        for event in events:
            await db.refresh(event)

        return events

    async def create_feedback_event(
        self,
        db: AsyncSession,
        *,
        user_id: UUID,
        recommendation_id: UUID,
        outfit_index: int,
        event_type: str,
        outfit_payload: dict[str, Any],
        context: dict[str, Any] | None = None,
        rejection_reason: str | None = None,
        rejection_note: str | None = None,
    ) -> RecommendationEvent:
        """Insert a new feedback row (accepted/rejected/swapped/worn).

        Never updates the original `shown` row — copies `outfit_index`,
        `outfit_payload`, `context` from it so every row is self-describing.
        """
        event = RecommendationEvent(
            id=uuid.uuid4(),
            user_id=user_id,
            recommendation_id=recommendation_id,
            outfit_index=outfit_index,
            outfit_payload=outfit_payload,
            event_type=event_type,
            rejection_reason=rejection_reason,
            rejection_note=rejection_note,
            context=context,
        )
        db.add(event)
        await db.commit()
        await db.refresh(event)

        return event

    async def get_shown(
        self,
        db: AsyncSession,
        *,
        recommendation_id: UUID,
        outfit_index: int,
        user_id: UUID | None = None,
    ) -> RecommendationEvent | None:
        """Look up the `shown` row for (recommendation_id, outfit_index).

        Pass `user_id` to scope by ownership (same discipline as `outfit_crud.get_by_id`).
        """
        query = select(RecommendationEvent).where(
            RecommendationEvent.recommendation_id == recommendation_id,
            RecommendationEvent.outfit_index == outfit_index,
            RecommendationEvent.event_type == "shown",
        )
        if user_id is not None:
            query = query.where(RecommendationEvent.user_id == user_id)

        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def get_preference_pairs(
        self,
        db: AsyncSession,
        *,
        recommendation_id: UUID | None = None,
        user_id: UUID | None = None,
    ) -> list[tuple[RecommendationEvent, RecommendationEvent]]:
        """Derive (positive, skipped) preference pairs.

        Logic:
        1. Positive signal per batch = events with event_type in {"accepted", "worn"}.
           Deduped by outfit_index (double-fires from best-effort, non-idempotent
           client calls produce duplicate rows for the same index).
        2. For each distinct positive outfit_index, pair it against every `shown` row
           in the same recommendation_id whose outfit_index differs.
        3. Batches with no positive event yield nothing.

        Implementation queries positives and shown rows in scope, then joins in
        Python — batch size is small (~3), so no self-join SQL is needed.
        """
        positive_query = select(RecommendationEvent).where(
            RecommendationEvent.event_type.in_(POSITIVE_EVENT_TYPES)
        )
        shown_query = select(RecommendationEvent).where(RecommendationEvent.event_type == "shown")

        if recommendation_id is not None:
            positive_query = positive_query.where(
                RecommendationEvent.recommendation_id == recommendation_id
            )
            shown_query = shown_query.where(RecommendationEvent.recommendation_id == recommendation_id)
        if user_id is not None:
            positive_query = positive_query.where(RecommendationEvent.user_id == user_id)
            shown_query = shown_query.where(RecommendationEvent.user_id == user_id)

        positive_result = await db.execute(positive_query)
        shown_result = await db.execute(shown_query)

        positives = list(positive_result.scalars().all())
        shown_rows = list(shown_result.scalars().all())

        # Dedupe positives by (recommendation_id, outfit_index) — first-seen wins.
        deduped_positives: dict[tuple[UUID, int], RecommendationEvent] = {}
        for positive in positives:
            key = (positive.recommendation_id, positive.outfit_index)
            deduped_positives.setdefault(key, positive)

        # Group shown rows by recommendation_id for the join.
        shown_by_batch: dict[UUID, list[RecommendationEvent]] = {}
        for shown in shown_rows:
            shown_by_batch.setdefault(shown.recommendation_id, []).append(shown)

        pairs: list[tuple[RecommendationEvent, RecommendationEvent]] = []
        for (batch_id, positive_index), positive in deduped_positives.items():
            for shown in shown_by_batch.get(batch_id, []):
                if shown.outfit_index != positive_index:
                    pairs.append((positive, shown))

        return pairs


# Global instance
recommendation_event_crud = RecommendationEventCRUD()
