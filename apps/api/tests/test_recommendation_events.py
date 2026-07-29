"""Real-DB tests for RI-1 telemetry: recommendation_events, user_events, feedback endpoint.

Unlike the rest of the suite (DummyDB + dependency_overrides), these tests use the
`db_session`/`real_user` fixtures against a real Postgres instance, because the new
CRUD methods commit internally and their durability (finding #1 in the RI-1 plan —
`get_db` never commits) is exactly what several of these tests guard against.
"""

from __future__ import annotations

import uuid

import pytest
from sqlalchemy import delete, select

from attreq_api.api.v1 import deps
from attreq_api.api.v1.endpoints import recommendations
from attreq_api.config.database import AsyncSessionLocal, get_db
from attreq_api.crud.recommendation_event import recommendation_event_crud
from attreq_api.crud.user_event import UserEventCRUD
from attreq_api.main import app
from attreq_api.models.recommendation_event import RecommendationEvent
from attreq_api.models.user import User
from attreq_api.models.wardrobe import WardrobeItem
from tests.conftest import build_user, build_wardrobe_item


def _candidate(top_id: str, bottom_id: str, accessory_id: str | None = None) -> dict:
    """Build a raw candidate dict matching services.recommendation.algorithm's shape."""
    return {
        "top_item_id": top_id,
        "top_item": {"id": top_id, "category": "top", "color_primary": "blue"},
        "bottom_item_id": bottom_id,
        "bottom_item": {"id": bottom_id, "category": "bottom", "color_primary": "black"},
        "accessory_item": {"id": accessory_id} if accessory_id else None,
        "scores": {
            "color_harmony": 0.7,
            "formality": 0.8,
            "preference_bonus": 0.1,
            "style_dna": 0.55,
            "behaviour": 0.65,
            "total": 0.9,
        },
        "weather_context": {"temp": 22},
        "occasion_context": "casual",
    }


async def _persist_user(db_session) -> User:
    user = build_user(email=f"ri1-extra-{uuid.uuid4()}@example.com")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


async def _delete_user(db_session, user_id) -> None:
    await db_session.execute(delete(User).where(User.id == user_id))
    await db_session.commit()


# ---------------------------------------------------------------------------
# 1. bulk_create_shown
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_bulk_create_shown_writes_one_row_per_candidate(db_session, real_user):
    recommendation_id = uuid.uuid4()
    candidates = [_candidate("top-1", "bottom-1"), _candidate("top-2", "bottom-2"), _candidate("top-3", "bottom-3")]

    events = await recommendation_event_crud.bulk_create_shown(
        db_session,
        user_id=real_user.id,
        recommendation_id=recommendation_id,
        candidates=candidates,
        context={"weather": {"temp": 22}, "occasion": "casual", "date": "2026-07-22"},
    )

    assert len(events) == 3
    assert sorted(e.outfit_index for e in events) == [0, 1, 2]

    for event in events:
        assert event.event_type == "shown"
        scores = event.outfit_payload["scores"]
        assert set(scores.keys()) == {
            "color_harmony",
            "formality",
            "preference_bonus",
            "style_dna",
            "behaviour",
            "total",
        }


# ---------------------------------------------------------------------------
# 2. Full HTTP path — durable shown events
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_generate_daily_endpoint_writes_shown_events(monkeypatch, client, db_session, real_user):
    tops = [
        build_wardrobe_item(
            user_id=real_user.id, category="top", color_primary="blue", season=["all"], occasion=["casual"]
        )
        for _ in range(3)
    ]
    bottoms = [
        build_wardrobe_item(
            user_id=real_user.id, category="bottom", color_primary="black", season=["all"], occasion=["casual"]
        )
        for _ in range(3)
    ]
    for item in [*tops, *bottoms]:
        db_session.add(item)
    await db_session.commit()

    async def override_get_db():
        yield db_session

    async def fake_get_weather(lat, lon):
        return {
            "temp": 22.0,
            "feels_like": 22.0,
            "condition": "Clear",
            "description": "clear sky",
            "humidity": 50,
            "wind_speed": 1.0,
            "icon": "01d",
        }

    async def fake_cache_get(key):
        return None

    async def fake_cache_set(key, value, ttl):
        return True

    monkeypatch.setattr(recommendations.weather_service, "get_current_weather", fake_get_weather)
    monkeypatch.setattr(recommendations.redis_cache, "get", fake_cache_get)
    monkeypatch.setattr(recommendations.redis_cache, "set", fake_cache_set)
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[deps.get_current_active_user] = lambda: real_user

    try:
        response = await client.get("/api/v1/recommendations/daily")
        assert response.status_code == 200
        body = response.json()
        recommendation_id = body["recommendation_id"]
        num_suggestions = len(body["suggestions"])
        assert num_suggestions > 0
    finally:
        app.dependency_overrides.clear()
        for item in [*tops, *bottoms]:
            await db_session.execute(delete(WardrobeItem).where(WardrobeItem.id == item.id))
        await db_session.commit()

    # Guard finding #1: query through a *fresh* connection, not the request-scoped
    # session, to prove the shown batch actually persisted (was committed), not just
    # pending in the session that happened to serve the request.
    async with AsyncSessionLocal() as fresh_session:
        result = await fresh_session.execute(
            select(RecommendationEvent).where(
                RecommendationEvent.recommendation_id == uuid.UUID(recommendation_id)
            )
        )
        rows = result.scalars().all()
        assert len(rows) == num_suggestions
        assert all(row.event_type == "shown" for row in rows)


# ---------------------------------------------------------------------------
# 3-6. Feedback endpoint
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_feedback_valid_reason(client, db_session, real_user):
    recommendation_id = uuid.uuid4()
    await recommendation_event_crud.bulk_create_shown(
        db_session,
        user_id=real_user.id,
        recommendation_id=recommendation_id,
        candidates=[_candidate("t1", "b1"), _candidate("t2", "b2")],
        context={"occasion": "casual"},
    )

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[deps.get_current_active_user] = lambda: real_user
    try:
        response = await client.post(
            f"/api/v1/recommendations/{recommendation_id}/feedback",
            json={"outfit_index": 0, "action": "rejected", "rejection_reason": "too_formal"},
        )
        assert response.status_code == 200
        body = response.json()
        assert body["outfit_index"] == 0
        assert body["event_type"] == "rejected"
    finally:
        app.dependency_overrides.clear()

    result = await db_session.execute(
        select(RecommendationEvent).where(
            RecommendationEvent.recommendation_id == recommendation_id,
            RecommendationEvent.event_type == "rejected",
        )
    )
    row = result.scalar_one()
    assert row.rejection_reason == "too_formal"


@pytest.mark.asyncio
async def test_feedback_rejects_invalid_reason(client, db_session, real_user):
    recommendation_id = uuid.uuid4()
    await recommendation_event_crud.bulk_create_shown(
        db_session,
        user_id=real_user.id,
        recommendation_id=recommendation_id,
        candidates=[_candidate("t1", "b1")],
        context=None,
    )

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[deps.get_current_active_user] = lambda: real_user
    try:
        response = await client.post(
            f"/api/v1/recommendations/{recommendation_id}/feedback",
            json={"outfit_index": 0, "action": "rejected", "rejection_reason": "bogus_reason"},
        )
        assert response.status_code == 422
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_feedback_unknown_recommendation_id(client, db_session, real_user):
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[deps.get_current_active_user] = lambda: real_user
    try:
        response = await client.post(
            f"/api/v1/recommendations/{uuid.uuid4()}/feedback",
            json={"outfit_index": 0, "action": "accepted"},
        )
        assert response.status_code == 404
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_feedback_wrong_user_cannot_address_others_batch(client, db_session, real_user):
    other_user = await _persist_user(db_session)
    try:
        recommendation_id = uuid.uuid4()
        await recommendation_event_crud.bulk_create_shown(
            db_session,
            user_id=other_user.id,
            recommendation_id=recommendation_id,
            candidates=[_candidate("t1", "b1")],
            context=None,
        )

        async def override_get_db():
            yield db_session

        # Authenticated as real_user, addressing other_user's batch.
        app.dependency_overrides[get_db] = override_get_db
        app.dependency_overrides[deps.get_current_active_user] = lambda: real_user
        try:
            response = await client.post(
                f"/api/v1/recommendations/{recommendation_id}/feedback",
                json={"outfit_index": 0, "action": "accepted"},
            )
            assert response.status_code == 404
        finally:
            app.dependency_overrides.clear()
    finally:
        await _delete_user(db_session, other_user.id)


# ---------------------------------------------------------------------------
# 7-10. Preference-pair derivation
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_preference_pairs_one_accepted_two_shown_returns_two_pairs(db_session, real_user):
    recommendation_id = uuid.uuid4()
    shown = await recommendation_event_crud.bulk_create_shown(
        db_session,
        user_id=real_user.id,
        recommendation_id=recommendation_id,
        candidates=[_candidate("t1", "b1"), _candidate("t2", "b2"), _candidate("t3", "b3")],
        context=None,
    )
    accepted_row = shown[0]
    await recommendation_event_crud.create_feedback_event(
        db_session,
        user_id=real_user.id,
        recommendation_id=recommendation_id,
        outfit_index=accepted_row.outfit_index,
        event_type="accepted",
        outfit_payload=accepted_row.outfit_payload,
        context=None,
    )

    pairs = await recommendation_event_crud.get_preference_pairs(
        db_session, recommendation_id=recommendation_id, user_id=real_user.id
    )

    assert len(pairs) == 2
    for positive, skipped in pairs:
        assert positive.outfit_index == 0
        assert skipped.outfit_index != 0
        assert skipped.event_type == "shown"


@pytest.mark.asyncio
async def test_preference_pairs_no_positive_returns_nothing(db_session, real_user):
    recommendation_id = uuid.uuid4()
    await recommendation_event_crud.bulk_create_shown(
        db_session,
        user_id=real_user.id,
        recommendation_id=recommendation_id,
        candidates=[_candidate("t1", "b1"), _candidate("t2", "b2")],
        context=None,
    )

    pairs = await recommendation_event_crud.get_preference_pairs(
        db_session, recommendation_id=recommendation_id, user_id=real_user.id
    )

    assert pairs == []


@pytest.mark.asyncio
async def test_preference_pairs_dedupes_duplicate_accepted(db_session, real_user):
    recommendation_id = uuid.uuid4()
    shown = await recommendation_event_crud.bulk_create_shown(
        db_session,
        user_id=real_user.id,
        recommendation_id=recommendation_id,
        candidates=[_candidate("t1", "b1"), _candidate("t2", "b2"), _candidate("t3", "b3")],
        context=None,
    )
    accepted_row = shown[0]

    # Simulate a best-effort double-tap: two identical `accepted` rows at the same index.
    for _ in range(2):
        await recommendation_event_crud.create_feedback_event(
            db_session,
            user_id=real_user.id,
            recommendation_id=recommendation_id,
            outfit_index=accepted_row.outfit_index,
            event_type="accepted",
            outfit_payload=accepted_row.outfit_payload,
            context=None,
        )

    pairs = await recommendation_event_crud.get_preference_pairs(
        db_session, recommendation_id=recommendation_id, user_id=real_user.id
    )

    assert len(pairs) == 2  # not 4


@pytest.mark.asyncio
async def test_worn_counts_as_positive_signal(db_session, real_user):
    recommendation_id = uuid.uuid4()
    shown = await recommendation_event_crud.bulk_create_shown(
        db_session,
        user_id=real_user.id,
        recommendation_id=recommendation_id,
        candidates=[_candidate("t1", "b1"), _candidate("t2", "b2"), _candidate("t3", "b3")],
        context=None,
    )
    worn_row = shown[1]
    await recommendation_event_crud.create_feedback_event(
        db_session,
        user_id=real_user.id,
        recommendation_id=recommendation_id,
        outfit_index=worn_row.outfit_index,
        event_type="worn",
        outfit_payload=worn_row.outfit_payload,
        context=None,
    )

    pairs = await recommendation_event_crud.get_preference_pairs(
        db_session, recommendation_id=recommendation_id, user_id=real_user.id
    )

    assert len(pairs) == 2
    assert all(positive.outfit_index == 1 for positive, _ in pairs)


# ---------------------------------------------------------------------------
# 11. Append-only guarantee
# ---------------------------------------------------------------------------


def test_append_only_no_update_method():
    from attreq_api.crud.recommendation_event import RecommendationEventCRUD

    assert not hasattr(RecommendationEventCRUD, "update")
    assert not hasattr(RecommendationEventCRUD, "delete")
    assert not hasattr(UserEventCRUD, "update")
    assert not hasattr(UserEventCRUD, "delete")

    import inspect

    recs_source = inspect.getsource(recommendations)
    assert "router.put" not in recs_source
    assert "router.patch" not in recs_source


# ---------------------------------------------------------------------------
# 12. Stale-cache regeneration guard
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_cache_hit_without_recommendation_id_regenerates(monkeypatch, client, db_session, real_user):
    tops = [
        build_wardrobe_item(
            user_id=real_user.id, category="top", color_primary="blue", season=["all"], occasion=["casual"]
        )
        for _ in range(2)
    ]
    bottoms = [
        build_wardrobe_item(
            user_id=real_user.id, category="bottom", color_primary="black", season=["all"], occasion=["casual"]
        )
        for _ in range(2)
    ]
    for item in [*tops, *bottoms]:
        db_session.add(item)
    await db_session.commit()

    async def override_get_db():
        yield db_session

    async def fake_get_weather(lat, lon):
        return {
            "temp": 22.0,
            "feels_like": 22.0,
            "condition": "Clear",
            "description": "clear sky",
            "humidity": 50,
            "wind_speed": 1.0,
            "icon": "01d",
        }

    # Simulate a pre-deploy cache entry that lacks `recommendation_id`.
    async def fake_cache_get(key):
        return {
            "suggestions": [],
            "total_suggestions": 0,
            "generated_at": "2026-01-01T00:00:00",
            "weather": {
                "temp": 20.0,
                "feels_like": 20.0,
                "condition": "Clear",
                "description": "clear",
                "humidity": 40,
                "wind_speed": 1.0,
                "icon": "01d",
            },
            "occasion": "casual",
            "cached": False,
        }

    async def fake_cache_set(key, value, ttl):
        return True

    monkeypatch.setattr(recommendations.weather_service, "get_current_weather", fake_get_weather)
    monkeypatch.setattr(recommendations.redis_cache, "get", fake_cache_get)
    monkeypatch.setattr(recommendations.redis_cache, "set", fake_cache_set)
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[deps.get_current_active_user] = lambda: real_user

    try:
        response = await client.get("/api/v1/recommendations/daily")
        assert response.status_code == 200
        body = response.json()
        # Regenerated, not the stale cached payload: has a recommendation_id and
        # actual suggestions (the stale payload had 0 suggestions and no key).
        assert "recommendation_id" in body
        assert body["cached"] is False
    finally:
        app.dependency_overrides.clear()
        for item in [*tops, *bottoms]:
            await db_session.execute(delete(WardrobeItem).where(WardrobeItem.id == item.id))
        await db_session.commit()
