"""Real-DB tests for services/recommendation/feedback_source.py (RI-6).

Uses the `db_session`/`real_user` fixtures (see test_recommendation_events.py's
module docstring for why: `recommendation_event_crud` commits internally, so
`DummyDB` + rollback semantics don't apply here). `RecommendationEvent.
outfit_payload` is a free-form JSONB column (no FK), so the primary-source
tests use arbitrary UUID strings; the fallback-adapter tests use real
`WardrobeItem` rows since `Outfit.top_item_id`/`bottom_item_id` are real
foreign keys.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import delete

from attreq_api.crud.recommendation_event import recommendation_event_crud
from attreq_api.models.outfit import Outfit
from attreq_api.models.recommendation_event import RecommendationEvent
from attreq_api.models.wardrobe import WardrobeItem
from attreq_api.services.recommendation.feedback_source import get_recent_dislikes, get_recent_likes
from tests.conftest import build_outfit, build_wardrobe_item


def _shown_candidate(top_id: str, bottom_id: str) -> dict:
    return {
        "top_item_id": top_id,
        "bottom_item_id": bottom_id,
        "scores": {"total": 0.8},
    }


@pytest.mark.asyncio
async def test_get_recent_dislikes_reads_dislike_item_rejections(db_session, real_user):
    top_id = str(uuid.uuid4())
    bottom_id = str(uuid.uuid4())
    recommendation_id = uuid.uuid4()

    await recommendation_event_crud.bulk_create_shown(
        db_session,
        user_id=real_user.id,
        recommendation_id=recommendation_id,
        candidates=[_shown_candidate(top_id, bottom_id)],
        context={"occasion": "casual"},
    )
    shown = await recommendation_event_crud.get_shown(
        db_session, recommendation_id=recommendation_id, outfit_index=0, user_id=real_user.id
    )
    await recommendation_event_crud.create_feedback_event(
        db_session,
        user_id=real_user.id,
        recommendation_id=recommendation_id,
        outfit_index=0,
        event_type="rejected",
        outfit_payload=shown.outfit_payload,
        rejection_reason="dislike_item",
    )

    dislikes = await get_recent_dislikes(db_session, real_user.id, days=30)

    assert uuid.UUID(top_id) in dislikes
    assert uuid.UUID(bottom_id) in dislikes


@pytest.mark.asyncio
async def test_get_recent_dislikes_ignores_rejections_with_other_reasons(db_session, real_user):
    top_id = str(uuid.uuid4())
    bottom_id = str(uuid.uuid4())
    recommendation_id = uuid.uuid4()

    await recommendation_event_crud.bulk_create_shown(
        db_session,
        user_id=real_user.id,
        recommendation_id=recommendation_id,
        candidates=[_shown_candidate(top_id, bottom_id)],
    )
    shown = await recommendation_event_crud.get_shown(
        db_session, recommendation_id=recommendation_id, outfit_index=0, user_id=real_user.id
    )
    await recommendation_event_crud.create_feedback_event(
        db_session,
        user_id=real_user.id,
        recommendation_id=recommendation_id,
        outfit_index=0,
        event_type="rejected",
        outfit_payload=shown.outfit_payload,
        rejection_reason="too_formal",
    )

    dislikes = await get_recent_dislikes(db_session, real_user.id, days=30)

    assert uuid.UUID(top_id) not in dislikes
    assert uuid.UUID(bottom_id) not in dislikes


@pytest.mark.asyncio
async def test_get_recent_likes_reads_accepted_and_worn_events(db_session, real_user):
    top_id = str(uuid.uuid4())
    bottom_id = str(uuid.uuid4())
    recommendation_id = uuid.uuid4()

    await recommendation_event_crud.bulk_create_shown(
        db_session,
        user_id=real_user.id,
        recommendation_id=recommendation_id,
        candidates=[_shown_candidate(top_id, bottom_id)],
    )
    shown = await recommendation_event_crud.get_shown(
        db_session, recommendation_id=recommendation_id, outfit_index=0, user_id=real_user.id
    )
    await recommendation_event_crud.create_feedback_event(
        db_session,
        user_id=real_user.id,
        recommendation_id=recommendation_id,
        outfit_index=0,
        event_type="accepted",
        outfit_payload=shown.outfit_payload,
    )

    likes = await get_recent_likes(db_session, real_user.id, days=30)

    assert uuid.UUID(top_id) in likes
    assert uuid.UUID(bottom_id) in likes


@pytest.mark.asyncio
async def test_get_recent_dislikes_days_boundary_excludes_old_events(db_session, real_user):
    top_id = str(uuid.uuid4())
    bottom_id = str(uuid.uuid4())
    recommendation_id = uuid.uuid4()

    await recommendation_event_crud.bulk_create_shown(
        db_session,
        user_id=real_user.id,
        recommendation_id=recommendation_id,
        candidates=[_shown_candidate(top_id, bottom_id)],
    )
    shown = await recommendation_event_crud.get_shown(
        db_session, recommendation_id=recommendation_id, outfit_index=0, user_id=real_user.id
    )
    event = await recommendation_event_crud.create_feedback_event(
        db_session,
        user_id=real_user.id,
        recommendation_id=recommendation_id,
        outfit_index=0,
        event_type="rejected",
        outfit_payload=shown.outfit_payload,
        rejection_reason="dislike_item",
    )
    # Backdate the row past the lookback window.
    await db_session.execute(
        RecommendationEvent.__table__.update()
        .where(RecommendationEvent.id == event.id)
        .values(created_at=datetime.now(UTC) - timedelta(days=45))
    )
    await db_session.commit()

    dislikes = await get_recent_dislikes(db_session, real_user.id, days=30)

    assert uuid.UUID(top_id) not in dislikes
    assert uuid.UUID(bottom_id) not in dislikes


# ---------------------------------------------------------------------------
# Fallback adapter: Outfit.feedback_score (used only when the
# recommendation_events query returns nothing).
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_recent_dislikes_falls_back_to_outfit_feedback_score(db_session, real_user):
    top_item = build_wardrobe_item(user_id=real_user.id)
    bottom_item = build_wardrobe_item(user_id=real_user.id)
    db_session.add_all([top_item, bottom_item])
    await db_session.commit()

    outfit = build_outfit(
        user_id=real_user.id,
        top_item_id=top_item.id,
        bottom_item_id=bottom_item.id,
        feedback_score=-1,
    )
    db_session.add(outfit)
    await db_session.commit()

    dislikes = await get_recent_dislikes(db_session, real_user.id, days=30)

    assert top_item.id in dislikes
    assert bottom_item.id in dislikes

    await db_session.execute(delete(Outfit).where(Outfit.id == outfit.id))
    await db_session.execute(
        delete(WardrobeItem).where(WardrobeItem.id.in_([top_item.id, bottom_item.id]))
    )
    await db_session.commit()


@pytest.mark.asyncio
async def test_get_recent_likes_falls_back_to_outfit_feedback_score(db_session, real_user):
    top_item = build_wardrobe_item(user_id=real_user.id)
    db_session.add(top_item)
    await db_session.commit()

    outfit = build_outfit(user_id=real_user.id, top_item_id=top_item.id, feedback_score=1)
    db_session.add(outfit)
    await db_session.commit()

    likes = await get_recent_likes(db_session, real_user.id, days=30)

    assert top_item.id in likes

    await db_session.execute(delete(Outfit).where(Outfit.id == outfit.id))
    await db_session.execute(delete(WardrobeItem).where(WardrobeItem.id == top_item.id))
    await db_session.commit()


@pytest.mark.asyncio
async def test_get_recent_dislikes_prefers_recommendation_events_over_outfit_adapter(
    db_session, real_user
):
    """When BOTH sources have data, the recommendation_events result wins —
    the Outfit adapter is a fallback only for when events yield nothing."""
    events_top_id = str(uuid.uuid4())
    events_bottom_id = str(uuid.uuid4())
    recommendation_id = uuid.uuid4()
    await recommendation_event_crud.bulk_create_shown(
        db_session,
        user_id=real_user.id,
        recommendation_id=recommendation_id,
        candidates=[_shown_candidate(events_top_id, events_bottom_id)],
    )
    shown = await recommendation_event_crud.get_shown(
        db_session, recommendation_id=recommendation_id, outfit_index=0, user_id=real_user.id
    )
    await recommendation_event_crud.create_feedback_event(
        db_session,
        user_id=real_user.id,
        recommendation_id=recommendation_id,
        outfit_index=0,
        event_type="rejected",
        outfit_payload=shown.outfit_payload,
        rejection_reason="dislike_item",
    )

    outfit_item = build_wardrobe_item(user_id=real_user.id)
    db_session.add(outfit_item)
    await db_session.commit()
    outfit = build_outfit(user_id=real_user.id, top_item_id=outfit_item.id, feedback_score=-1)
    db_session.add(outfit)
    await db_session.commit()

    dislikes = await get_recent_dislikes(db_session, real_user.id, days=30)

    assert uuid.UUID(events_top_id) in dislikes
    assert outfit_item.id not in dislikes

    await db_session.execute(delete(Outfit).where(Outfit.id == outfit.id))
    await db_session.execute(delete(WardrobeItem).where(WardrobeItem.id == outfit_item.id))
    await db_session.commit()
