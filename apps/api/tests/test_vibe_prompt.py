"""Tests for RI-5 Task 5.4 — the morning vibe prompt.

Backend portion: `services/recommendation/vibe.py`'s hint->bias mapping,
`context_scoring.calculate_context_score`'s soft formality nudge, the
`/daily` endpoint's cache-key partitioning by hint, and `vibe_answered`
event recording.
"""

from __future__ import annotations

from datetime import date, datetime

import pytest
from sqlalchemy import delete

from attreq_api.api.v1 import deps
from attreq_api.api.v1.endpoints import recommendations
from attreq_api.config.database import get_db
from attreq_api.crud.user_event import user_event_crud
from attreq_api.main import app
from attreq_api.models.wardrobe import WardrobeItem
from attreq_api.services.recommendation.context_scoring import calculate_context_score
from attreq_api.services.recommendation.vibe import (
    VALID_OCCASION_HINTS,
    VIBE_FORMALITY_BIAS,
    formality_bias_for_hint,
)
from tests.conftest import build_wardrobe_item

# ---------------------------------------------------------------------------
# formality_bias_for_hint
# ---------------------------------------------------------------------------


def test_formality_bias_for_known_hints():
    assert formality_bias_for_hint("sharp") == 0.6
    assert formality_bias_for_hint("relaxed") == -0.6
    assert formality_bias_for_hint("bold") == 0.1


def test_formality_bias_for_hint_case_insensitive():
    assert formality_bias_for_hint("SHARP") == 0.6
    assert formality_bias_for_hint(" relaxed ") == -0.6


def test_formality_bias_for_none_or_unknown_is_zero():
    assert formality_bias_for_hint(None) == 0.0
    assert formality_bias_for_hint("") == 0.0
    assert formality_bias_for_hint("garbage") == 0.0


def test_bold_is_recorded_but_mapped_near_neutral():
    """Correction 4: bold has no natural formality axis — mapped weak."""
    assert abs(VIBE_FORMALITY_BIAS["bold"]) < abs(VIBE_FORMALITY_BIAS["sharp"])
    assert abs(VIBE_FORMALITY_BIAS["bold"]) < abs(VIBE_FORMALITY_BIAS["relaxed"])


def test_valid_occasion_hints_match_vibe_formality_bias_keys():
    assert frozenset(VIBE_FORMALITY_BIAS) == VALID_OCCASION_HINTS


# ---------------------------------------------------------------------------
# calculate_context_score's soft formality nudge
# ---------------------------------------------------------------------------


def _item(**overrides):
    import uuid

    return build_wardrobe_item(user_id=uuid.uuid4(), **overrides)


def test_absent_hint_is_byte_identical_to_prior_behavior():
    top = _item(category="dress shirt", occasion=["formal"])
    bottom = _item(category="dress pants", occasion=["formal"])
    weather = {"temp": 20.0, "condition": "Clear"}
    now = datetime(2026, 7, 22, 14, 0, 0)

    default_call = calculate_context_score([top, bottom], "formal", weather, now=now)
    explicit_zero = calculate_context_score([top, bottom], "formal", weather, now=now, formality_bias=0.0)

    assert default_call == explicit_zero


def test_sharp_hint_raises_formality_target_for_formal_items():
    """For a formal-leaning outfit (occasion tag `"all"`, so the base
    occasion_fit isn't already ceilinged at 1.0), a 'sharp' hint (higher
    formality target) must score its occasion_fit measurably higher than a
    'relaxed' hint (lower target) does — the hint is a real, directional
    lever on the formality target, not a no-op."""
    top = _item(category="dress shirt", occasion=["all"])
    bottom = _item(category="dress pants", occasion=["all"])
    weather = {"temp": 20.0, "condition": "Clear"}
    now = datetime(2026, 7, 22, 14, 0, 0)

    _, sharp_detail = calculate_context_score(
        [top, bottom], "formal", weather, now=now, formality_bias=formality_bias_for_hint("sharp")
    )
    _, relaxed_detail = calculate_context_score(
        [top, bottom], "formal", weather, now=now, formality_bias=formality_bias_for_hint("relaxed")
    )

    assert sharp_detail["occasion_fit"] > relaxed_detail["occasion_fit"]


def test_relaxed_hint_lowers_formality_target_for_casual_items():
    """Mirror check for a casual-leaning outfit: a 'relaxed' hint (lower
    formality target) must score higher than a 'sharp' hint (higher target)
    for items that are actually casual."""
    top = _item(category="t-shirt", occasion=["all"])
    bottom = _item(category="jeans", occasion=["all"])
    weather = {"temp": 20.0, "condition": "Clear"}
    now = datetime(2026, 7, 22, 14, 0, 0)

    _, relaxed_detail = calculate_context_score(
        [top, bottom], "casual", weather, now=now, formality_bias=formality_bias_for_hint("relaxed")
    )
    _, sharp_detail = calculate_context_score(
        [top, bottom], "casual", weather, now=now, formality_bias=formality_bias_for_hint("sharp")
    )

    assert relaxed_detail["occasion_fit"] > sharp_detail["occasion_fit"]


# ---------------------------------------------------------------------------
# Endpoint: cache key partitioning + vibe_answered recording
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_daily_cache_key_differs_by_occasion_hint(monkeypatch, client, db_session, real_user):
    tops = [
        build_wardrobe_item(user_id=real_user.id, category="shirt", color_primary="blue", season=["all"], occasion=["casual"])
        for _ in range(2)
    ]
    bottoms = [
        build_wardrobe_item(user_id=real_user.id, category="jeans", color_primary="black", season=["all"], occasion=["casual"])
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

    cache_keys_seen: list[str] = []

    async def fake_cache_get(key):
        cache_keys_seen.append(key)
        return

    async def fake_cache_set(key, value, ttl):
        return True

    monkeypatch.setattr(recommendations.weather_service, "get_current_weather", fake_get_weather)
    monkeypatch.setattr(recommendations.redis_cache, "get", fake_cache_get)
    monkeypatch.setattr(recommendations.redis_cache, "set", fake_cache_set)
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[deps.get_current_active_user] = lambda: real_user

    try:
        await client.get("/api/v1/recommendations/daily")
        await client.get("/api/v1/recommendations/daily", params={"occasion_hint": "sharp"})
    finally:
        app.dependency_overrides.clear()
        for item in [*tops, *bottoms]:
            await db_session.execute(delete(WardrobeItem).where(WardrobeItem.id == item.id))
        await db_session.commit()

    assert len(cache_keys_seen) == 2
    assert cache_keys_seen[0] != cache_keys_seen[1]
    assert cache_keys_seen[0].endswith(":none")
    assert cache_keys_seen[1].endswith(":sharp")


@pytest.mark.asyncio
async def test_vibe_answered_event_written_with_correct_payload(monkeypatch, client, db_session, real_user):
    from sqlalchemy import delete as sa_delete

    from attreq_api.models.user_event import UserEvent

    await db_session.execute(
        sa_delete(UserEvent).where(UserEvent.user_id == real_user.id, UserEvent.event_type == "vibe_answered")
    )
    await db_session.commit()

    tops = [
        build_wardrobe_item(user_id=real_user.id, category="shirt", color_primary="blue", season=["all"], occasion=["casual"])
        for _ in range(2)
    ]
    bottoms = [
        build_wardrobe_item(user_id=real_user.id, category="jeans", color_primary="black", season=["all"], occasion=["casual"])
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
        response = await client.get(
            "/api/v1/recommendations/daily", params={"occasion_hint": "relaxed"}
        )
        assert response.status_code == 200
    finally:
        app.dependency_overrides.clear()
        for item in [*tops, *bottoms]:
            await db_session.execute(delete(WardrobeItem).where(WardrobeItem.id == item.id))
        await db_session.commit()

    events = await user_event_crud.list_for_user(
        db_session, user_id=real_user.id, event_types=["vibe_answered"], limit=10
    )
    assert len(events) == 1
    assert events[0].payload == {"vibe": "relaxed", "date": date.today().isoformat()}


@pytest.mark.asyncio
async def test_unknown_occasion_hint_is_ignored_not_rejected(monkeypatch, client, db_session, real_user):
    """The vibe prompt is always skippable — an unrecognized hint value must
    behave exactly like no hint at all, never a 4xx."""
    tops = [
        build_wardrobe_item(user_id=real_user.id, category="shirt", color_primary="blue", season=["all"], occasion=["casual"])
        for _ in range(2)
    ]
    bottoms = [
        build_wardrobe_item(user_id=real_user.id, category="jeans", color_primary="black", season=["all"], occasion=["casual"])
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
        response = await client.get(
            "/api/v1/recommendations/daily", params={"occasion_hint": "extremely-fancy"}
        )
        assert response.status_code == 200
    finally:
        app.dependency_overrides.clear()
        for item in [*tops, *bottoms]:
            await db_session.execute(delete(WardrobeItem).where(WardrobeItem.id == item.id))
        await db_session.commit()
