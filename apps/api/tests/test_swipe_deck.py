"""Tests for RI-5 Task 5.3 — the swipe deck endpoints.

Real-DB tests (same `db_session`/`real_user` pattern as
`tests/test_recommendation_events.py`), since the feedback path's daily-cap
gate reads durable `user_events` rows.
"""

from __future__ import annotations

import uuid
from datetime import date

import pytest
from sqlalchemy import delete

from attreq_api.api.v1 import deps
from attreq_api.api.v1.endpoints import recommendations
from attreq_api.config.database import get_db
from attreq_api.crud.recommendation_event import recommendation_event_crud
from attreq_api.main import app
from attreq_api.models.wardrobe import WardrobeItem
from tests.conftest import build_wardrobe_item


@pytest.mark.asyncio
async def test_swipe_deck_returns_outfits_and_writes_swipe_deck_context(
    monkeypatch, client, db_session, real_user
):
    tops = [
        build_wardrobe_item(
            user_id=real_user.id,
            category="shirt",
            color_primary=color,
            season=["all"],
            occasion=["casual"],
        )
        for color in ["blue", "red", "green", "black", "white"]
    ]
    bottoms = [
        build_wardrobe_item(
            user_id=real_user.id, category="jeans", color_primary="navy", season=["all"], occasion=["casual"]
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

    monkeypatch.setattr(recommendations.weather_service, "get_current_weather", fake_get_weather)
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[deps.get_current_active_user] = lambda: real_user

    try:
        response = await client.get("/api/v1/recommendations/swipe-deck")
        assert response.status_code == 200
        body = response.json()
        assert 1 <= len(body["suggestions"]) <= recommendations.SWIPE_DECK_SIZE
        assert body["cached"] is False
        recommendation_id = body["recommendation_id"]
    finally:
        app.dependency_overrides.clear()
        for item in [*tops, *bottoms]:
            await db_session.execute(delete(WardrobeItem).where(WardrobeItem.id == item.id))
        await db_session.commit()

    shown = await recommendation_event_crud.get_shown(
        db_session, recommendation_id=uuid.UUID(recommendation_id), outfit_index=0, user_id=real_user.id
    )
    assert shown is not None
    assert shown.context["source"] == "swipe_deck"


@pytest.mark.asyncio
async def test_swipe_deck_status_reports_ratings_and_cap(client, db_session, real_user):
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[deps.get_current_active_user] = lambda: real_user
    try:
        response = await client.get("/api/v1/recommendations/swipe-deck/status")
        assert response.status_code == 200
        body = response.json()
        assert body == {"ratings_today": 0, "cap": recommendations.SWIPE_DECK_DAILY_CAP}
    finally:
        app.dependency_overrides.clear()


def _candidate(scores: dict | None = None) -> dict:
    return {
        "top_item_id": "top-1",
        "bottom_item_id": "bottom-1",
        "scores": scores or {"color_harmony": 0.7, "formality": 0.6},
    }


@pytest.mark.asyncio
async def test_sixth_swipe_rating_in_a_day_returns_429(client, db_session, real_user):
    """5 ratings on swipe-deck-sourced shown rows succeed; the 6th (same day)
    is refused with 429. The deck GENERATION itself is never rate-limited —
    only ratings are, so this seeds `shown` rows directly rather than calling
    the generation endpoint 6 times."""
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[deps.get_current_active_user] = lambda: real_user

    batches: list[tuple[uuid.UUID, int]] = []
    try:
        for _i in range(6):
            recommendation_id = uuid.uuid4()
            await recommendation_event_crud.bulk_create_shown(
                db_session,
                user_id=real_user.id,
                recommendation_id=recommendation_id,
                candidates=[_candidate()],
                context={"occasion": "casual", "date": date.today().isoformat(), "source": "swipe_deck"},
            )
            batches.append((recommendation_id, 0))

        statuses = []
        for recommendation_id, outfit_index in batches:
            response = await client.post(
                f"/api/v1/recommendations/{recommendation_id}/feedback",
                json={"outfit_index": outfit_index, "action": "accepted"},
            )
            statuses.append(response.status_code)

        assert statuses[:5] == [200] * 5
        assert statuses[5] == 429
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_swipe_deck_rating_writes_swipe_rated_user_event(client, db_session, real_user):
    from attreq_api.crud.user_event import user_event_crud

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[deps.get_current_active_user] = lambda: real_user

    recommendation_id = uuid.uuid4()
    try:
        await recommendation_event_crud.bulk_create_shown(
            db_session,
            user_id=real_user.id,
            recommendation_id=recommendation_id,
            candidates=[_candidate()],
            context={"occasion": "casual", "date": date.today().isoformat(), "source": "swipe_deck"},
        )
        response = await client.post(
            f"/api/v1/recommendations/{recommendation_id}/feedback",
            json={"outfit_index": 0, "action": "rejected"},
        )
        assert response.status_code == 200
    finally:
        app.dependency_overrides.clear()

    events = await user_event_crud.list_for_user(
        db_session, user_id=real_user.id, event_types=["swipe_rated"], limit=10
    )
    assert any(e.payload.get("recommendation_id") == str(recommendation_id) for e in events)


@pytest.mark.asyncio
async def test_non_swipe_deck_feedback_never_counts_against_cap(client, db_session, real_user):
    """A regular (non-swipe-deck) `shown` row's feedback must never be
    gated by the swipe-deck cap — `is_swipe_deck_rating` must be False when
    `context.source` isn't set."""
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[deps.get_current_active_user] = lambda: real_user

    try:
        for _ in range(6):
            recommendation_id = uuid.uuid4()
            await recommendation_event_crud.bulk_create_shown(
                db_session,
                user_id=real_user.id,
                recommendation_id=recommendation_id,
                candidates=[_candidate()],
                context={"occasion": "casual"},
            )
            response = await client.post(
                f"/api/v1/recommendations/{recommendation_id}/feedback",
                json={"outfit_index": 0, "action": "accepted"},
            )
            assert response.status_code == 200
    finally:
        app.dependency_overrides.clear()
