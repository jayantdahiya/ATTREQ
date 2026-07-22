from __future__ import annotations

import uuid
from datetime import date

import pytest
from fastapi import HTTPException

from attreq_api.api.v1 import deps
from attreq_api.api.v1.endpoints import auth, outfits, recommendations, stats, users, wardrobe
from attreq_api.config import security
from attreq_api.config.database import get_db
from attreq_api.main import app
from attreq_api.services.recommendation import algorithm
from attreq_api.workers import batch_image_processor, image_processor
from tests.conftest import DummyDB, build_outfit, build_user, build_wardrobe_item


@pytest.mark.asyncio
async def test_login_returns_tokens_and_user(monkeypatch, client, dummy_db):
    user = build_user()

    async def override_get_db():
        yield dummy_db

    async def fake_authenticate(db, email, password):
        assert email == "test@example.com"
        assert password == "Password123"
        return user

    async def fake_update_last_login(db, current_user):
        return current_user

    monkeypatch.setattr(auth.user_crud, "authenticate", fake_authenticate)
    monkeypatch.setattr(auth.user_crud, "update_last_login", fake_update_last_login)
    monkeypatch.setattr(
        auth,
        "create_tokens",
        lambda subject: {
            "access_token": "access-token",
            "refresh_token": "refresh-token",
            "token_type": "bearer",
        },
    )
    app.dependency_overrides[get_db] = override_get_db

    response = await client.post(
        "/api/v1/auth/login",
        data={"username": "test@example.com", "password": "Password123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["access_token"] == "access-token"
    assert payload["refresh_token"] == "refresh-token"
    assert payload["token_type"] == "bearer"
    assert payload["user"]["id"] == str(user.id)
    assert payload["user"]["email"] == user.email
    assert payload["user"]["saved_city"] == user.saved_city

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_login_rejects_invalid_credentials(monkeypatch, client, dummy_db):
    async def override_get_db():
        yield dummy_db

    async def fake_authenticate(db, email, password):
        return None

    monkeypatch.setattr(auth.user_crud, "authenticate", fake_authenticate)
    app.dependency_overrides[get_db] = override_get_db

    response = await client.post(
        "/api/v1/auth/login",
        data={"username": "bad@example.com", "password": "wrong-password"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect email or password"

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_refresh_uses_json_body_contract(monkeypatch, client, dummy_db):
    user = build_user()

    async def override_get_db():
        yield dummy_db

    monkeypatch.setattr(auth, "verify_token", lambda token, token_type="refresh": {"sub": str(user.id)})
    async def fake_get_user_by_id(db, user_id):
        return user

    monkeypatch.setattr(auth.user_crud, "get_by_id", fake_get_user_by_id)
    monkeypatch.setattr(security, "create_access_token", lambda subject: "new-access-token")
    app.dependency_overrides[get_db] = override_get_db

    response = await client.post("/api/v1/auth/refresh", json={"refresh_token": "refresh-token"})

    assert response.status_code == 200
    assert response.json() == {"access_token": "new-access-token", "token_type": "bearer"}

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_refresh_rejects_invalid_token(monkeypatch, client, dummy_db):
    async def override_get_db():
        yield dummy_db

    def fake_verify_token(token, token_type="refresh"):
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    monkeypatch.setattr(auth, "verify_token", fake_verify_token)
    app.dependency_overrides[get_db] = override_get_db

    response = await client.post("/api/v1/auth/refresh", json={"refresh_token": "bad-token"})

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid refresh token"

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_get_current_user_returns_profile(client):
    user = build_user()
    app.dependency_overrides[users.get_current_user] = lambda: user

    response = await client.get("/api/v1/users/me")

    assert response.status_code == 200
    assert response.json()["id"] == str(user.id)
    assert response.json()["email"] == user.email
    assert response.json()["saved_city"] == user.saved_city

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_update_location_uses_lat_lon_city_contract(monkeypatch, client, dummy_db):
    user = build_user(saved_latitude=None, saved_longitude=None, saved_city=None)

    async def override_get_db():
        yield dummy_db

    async def fake_update_user_location(db, current_user, location_data):
        current_user.saved_latitude = location_data.lat
        current_user.saved_longitude = location_data.lon
        current_user.saved_city = location_data.city
        return current_user

    monkeypatch.setattr(users.user_crud, "update_user_location", fake_update_user_location)
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[users.get_current_user] = lambda: user

    response = await client.patch(
        "/api/v1/users/me/location",
        json={"lat": 28.6139, "lon": 77.2090, "city": "Delhi"},
    )

    assert response.status_code == 200
    assert response.json()["saved_latitude"] == pytest.approx(28.6139)
    assert response.json()["saved_longitude"] == pytest.approx(77.2090)
    assert response.json()["saved_city"] == "Delhi"

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_daily_recommendations_accept_explicit_coordinates(monkeypatch, client, dummy_db):
    user = build_user(saved_latitude=None, saved_longitude=None)
    weather_calls: list[tuple[float, float]] = []

    async def override_get_db():
        yield dummy_db

    async def fake_get_weather(lat, lon):
        weather_calls.append((lat, lon))
        return {
            "temp": 29,
            "feels_like": 31,
            "condition": "Sunny",
            "description": "clear sky",
            "humidity": 60,
            "wind_speed": 4.2,
            "icon": "01d",
        }

    async def fake_cache_get(key):
        return None

    async def fake_cache_set(key, value, ttl):
        return None

    top_item = build_wardrobe_item(user_id=user.id)
    bottom_item = build_wardrobe_item(user_id=user.id, category="jeans", color_primary="black")

    async def fake_generate_daily_outfits(db, user_id, weather, occasion, num_suggestions):
        return [
            {
                "top_item_id": str(top_item.id),
                "top_item": {
                    "id": str(top_item.id),
                    "category": top_item.category,
                    "color_primary": top_item.color_primary,
                    "pattern": top_item.pattern,
                    "image_url": top_item.processed_image_url,
                    "thumbnail_url": top_item.thumbnail_url,
                },
                "bottom_item_id": str(bottom_item.id),
                "bottom_item": {
                    "id": str(bottom_item.id),
                    "category": bottom_item.category,
                    "color_primary": bottom_item.color_primary,
                    "pattern": bottom_item.pattern,
                    "image_url": bottom_item.processed_image_url,
                    "thumbnail_url": bottom_item.thumbnail_url,
                },
                "accessory_item_id": None,
                "accessory_item": None,
                "scores": {
                    "color_harmony": 0.9,
                    "formality": 0.6,
                    "weather_appropriateness": 0.8,
                    "versatility": 0.7,
                    "preference_bonus": 0.2,
                    "total": 3.2,
                },
                "weather_context": {
                    "temp": 29,
                    "feels_like": 31,
                    "condition": "Sunny",
                    "description": "clear sky",
                    "humidity": 60,
                    "wind_speed": 4.2,
                    "icon": "01d",
                },
                "occasion_context": "casual",
            }
        ]

    monkeypatch.setattr(recommendations.weather_service, "get_current_weather", fake_get_weather)
    monkeypatch.setattr(recommendations.redis_cache, "get", fake_cache_get)
    monkeypatch.setattr(recommendations.redis_cache, "set", fake_cache_set)
    monkeypatch.setattr(recommendations, "generate_daily_outfits", fake_generate_daily_outfits)
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[deps.get_current_active_user] = lambda: user

    response = await client.get(
        "/api/v1/recommendations/daily",
        params={"lat": 12.9716, "lon": 77.5946, "occasion": "casual"},
    )

    assert response.status_code == 200
    assert weather_calls == [(12.9716, 77.5946)]
    assert response.json()["occasion"] == "casual"
    assert response.json()["cached"] is False

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_daily_recommendations_fallback_to_saved_coordinates(monkeypatch, client, dummy_db):
    user = build_user(saved_latitude=13.0827, saved_longitude=80.2707, saved_city="Chennai")
    weather_calls: list[tuple[float, float]] = []

    async def override_get_db():
        yield dummy_db

    async def fake_get_weather(lat, lon):
        weather_calls.append((lat, lon))
        return {
            "temp": 32,
            "feels_like": 36,
            "condition": "Humid",
            "description": "humid",
            "humidity": 78,
            "wind_speed": 2.5,
            "icon": "02d",
        }

    async def fake_cache_get(key):
        return None

    async def fake_cache_set(key, value, ttl):
        return None

    async def fake_generate_daily_outfits(db, user_id, weather, occasion, num_suggestions):
        return []

    monkeypatch.setattr(recommendations.weather_service, "get_current_weather", fake_get_weather)
    monkeypatch.setattr(recommendations.redis_cache, "get", fake_cache_get)
    monkeypatch.setattr(recommendations.redis_cache, "set", fake_cache_set)
    monkeypatch.setattr(recommendations, "generate_daily_outfits", fake_generate_daily_outfits)
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[deps.get_current_active_user] = lambda: user

    response = await client.get("/api/v1/recommendations/daily")

    assert response.status_code == 404
    assert weather_calls == [(13.0827, 80.2707)]

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_mark_outfit_worn_updates_outfit_and_items(monkeypatch, client, dummy_db):
    user = build_user()
    top_item = build_wardrobe_item(user_id=user.id)
    bottom_item = build_wardrobe_item(user_id=user.id, category="jeans")
    outfit_record = build_outfit(user_id=user.id, top_item_id=top_item.id, bottom_item_id=bottom_item.id)
    update_calls: list[tuple[uuid.UUID, dict]] = []

    async def override_get_db():
        yield dummy_db

    async def fake_get_outfit(db, outfit_id, user_id=None, load_items=False):
        return outfit_record

    async def fake_mark_as_worn(db, outfit_id, worn_date):
        outfit_record.worn_date = worn_date
        return outfit_record

    async def fake_get_item(db, item_id, user_id=None):
        if item_id == top_item.id:
            return top_item
        if item_id == bottom_item.id:
            return bottom_item
        return None

    async def fake_update_item(db, item_id, data):
        update_calls.append((item_id, data))
        return

    monkeypatch.setattr(outfits.outfit_crud, "get_by_id", fake_get_outfit)
    monkeypatch.setattr(outfits.outfit_crud, "mark_as_worn", fake_mark_as_worn)
    monkeypatch.setattr(outfits.wardrobe_crud, "get_by_id", fake_get_item)
    monkeypatch.setattr(outfits.wardrobe_crud, "update", fake_update_item)
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[deps.get_current_active_user] = lambda: user

    response = await client.post(
        f"/api/v1/outfits/{outfit_record.id}/wear",
        json={"worn_date": str(date(2026, 4, 18))},
    )

    assert response.status_code == 200
    assert response.json()["worn_date"] == "2026-04-18"
    assert len(update_calls) == 2

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_submit_outfit_feedback_uses_feedback_score_contract(monkeypatch, client, dummy_db):
    user = build_user()
    outfit_record = build_outfit(user_id=user.id)

    async def override_get_db():
        yield dummy_db

    async def fake_get_outfit(db, outfit_id, user_id=None, load_items=False):
        return outfit_record

    async def fake_update_feedback(db, outfit_id, feedback_score):
        outfit_record.feedback_score = feedback_score
        return outfit_record

    monkeypatch.setattr(outfits.outfit_crud, "get_by_id", fake_get_outfit)
    monkeypatch.setattr(outfits.outfit_crud, "update_feedback", fake_update_feedback)
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[deps.get_current_active_user] = lambda: user

    response = await client.post(
        f"/api/v1/outfits/{outfit_record.id}/feedback",
        json={"feedback_score": 1},
    )

    assert response.status_code == 200
    assert response.json()["feedback_score"] == 1

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_wear_emits_worn_and_style_dna_events(monkeypatch, client, dummy_db):
    user = build_user()
    top_item = build_wardrobe_item(user_id=user.id)
    bottom_item = build_wardrobe_item(user_id=user.id, category="jeans")
    outfit_record = build_outfit(user_id=user.id, top_item_id=top_item.id, bottom_item_id=bottom_item.id)

    user_events_created: list[tuple[str, dict]] = []

    async def override_get_db():
        yield dummy_db

    async def fake_get_outfit(db, outfit_id, user_id=None, load_items=False):
        return outfit_record

    async def fake_mark_as_worn(db, outfit_id, worn_date):
        outfit_record.worn_date = worn_date
        return outfit_record

    async def fake_get_item(db, item_id, user_id=None):
        if item_id == top_item.id:
            return top_item
        if item_id == bottom_item.id:
            return bottom_item
        return None

    async def fake_update_item(db, item_id, data):
        return None

    async def fake_user_event_create(db, *, user_id, event_type, payload=None):
        user_events_created.append((event_type, payload or {}))

    async def fake_update_behaviour_weights(db, user_id, outfit_id, signal):
        return True  # simulate a real mutation

    monkeypatch.setattr(outfits.outfit_crud, "get_by_id", fake_get_outfit)
    monkeypatch.setattr(outfits.outfit_crud, "mark_as_worn", fake_mark_as_worn)
    monkeypatch.setattr(outfits.wardrobe_crud, "get_by_id", fake_get_item)
    monkeypatch.setattr(outfits.wardrobe_crud, "update", fake_update_item)
    monkeypatch.setattr(outfits.user_event_crud, "create", fake_user_event_create)
    monkeypatch.setattr(
        "attreq_api.services.style_dna.style_dna_service.update_behaviour_weights",
        fake_update_behaviour_weights,
    )
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[deps.get_current_active_user] = lambda: user

    response = await client.post(
        f"/api/v1/outfits/{outfit_record.id}/wear",
        json={"worn_date": str(date(2026, 4, 18))},
    )

    assert response.status_code == 200

    event_types = [event_type for event_type, _ in user_events_created]
    assert "outfit_worn" in event_types
    assert "style_dna_updated" in event_types

    worn_payload = next(payload for event_type, payload in user_events_created if event_type == "outfit_worn")
    assert worn_payload["outfit_id"] == str(outfit_record.id)

    style_dna_payload = next(
        payload for event_type, payload in user_events_created if event_type == "style_dna_updated"
    )
    assert style_dna_payload["signal"] == "worn"

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_wear_skips_style_dna_event_when_not_mutated(monkeypatch, client, dummy_db):
    user = build_user()
    top_item = build_wardrobe_item(user_id=user.id)
    bottom_item = build_wardrobe_item(user_id=user.id, category="jeans")
    outfit_record = build_outfit(user_id=user.id, top_item_id=top_item.id, bottom_item_id=bottom_item.id)

    user_events_created: list[tuple[str, dict]] = []

    async def override_get_db():
        yield dummy_db

    async def fake_get_outfit(db, outfit_id, user_id=None, load_items=False):
        return outfit_record

    async def fake_mark_as_worn(db, outfit_id, worn_date):
        outfit_record.worn_date = worn_date
        return outfit_record

    async def fake_get_item(db, item_id, user_id=None):
        if item_id == top_item.id:
            return top_item
        if item_id == bottom_item.id:
            return bottom_item
        return None

    async def fake_update_item(db, item_id, data):
        return None

    async def fake_user_event_create(db, *, user_id, event_type, payload=None):
        user_events_created.append((event_type, payload or {}))

    async def fake_update_behaviour_weights(db, user_id, outfit_id, signal):
        return False  # no style_preferences set for this user — no mutation

    monkeypatch.setattr(outfits.outfit_crud, "get_by_id", fake_get_outfit)
    monkeypatch.setattr(outfits.outfit_crud, "mark_as_worn", fake_mark_as_worn)
    monkeypatch.setattr(outfits.wardrobe_crud, "get_by_id", fake_get_item)
    monkeypatch.setattr(outfits.wardrobe_crud, "update", fake_update_item)
    monkeypatch.setattr(outfits.user_event_crud, "create", fake_user_event_create)
    monkeypatch.setattr(
        "attreq_api.services.style_dna.style_dna_service.update_behaviour_weights",
        fake_update_behaviour_weights,
    )
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[deps.get_current_active_user] = lambda: user

    response = await client.post(
        f"/api/v1/outfits/{outfit_record.id}/wear",
        json={"worn_date": str(date(2026, 4, 18))},
    )

    assert response.status_code == 200

    event_types = [event_type for event_type, _ in user_events_created]
    assert "outfit_worn" in event_types
    assert "style_dna_updated" not in event_types

    app.dependency_overrides.clear()


# ============================================================================
# RI-7: Stats endpoints
# ============================================================================


@pytest.mark.asyncio
async def test_get_wardrobe_stats_endpoint_returns_mocked_payload(monkeypatch, client, dummy_db):
    user = build_user()

    async def override_get_db():
        yield dummy_db

    payload = {
        "total_active_items": 3,
        "by_category": [{"category": "shirt", "count": 2}, {"category": "jeans", "count": 1}],
        "by_color_family": [{"family": "cool", "count": 2}, {"family": "neutral", "count": 1}],
        "by_brand": [{"brand": "Unbranded", "count": 3}],
        "closet_value": 150.0,
        "items_missing_price": 0,
        "never_worn_count": 1,
        "never_worn_percent": 33.3,
        "most_worn": [],
        "least_worn": [],
        "cost_per_wear": [],
        "worn_last_30_days": 1,
        "worn_last_90_days": 2,
        "generated_at": "2026-07-22",
        "cached": False,
    }

    async def fake_get_wardrobe_stats(db, user_id, force_refresh=False):
        return payload

    monkeypatch.setattr(stats, "get_wardrobe_stats", fake_get_wardrobe_stats)
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[deps.get_current_active_user] = lambda: user

    response = await client.get("/api/v1/stats/wardrobe")

    assert response.status_code == 200
    body = response.json()
    assert body["total_active_items"] == 3
    assert body["closet_value"] == 150.0
    assert body["never_worn_percent"] == 33.3

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_get_forgotten_items_endpoint_returns_mocked_payload(monkeypatch, client, dummy_db):
    user = build_user()

    async def override_get_db():
        yield dummy_db

    payload = {
        "items": [
            {
                "item_id": str(uuid.uuid4()),
                "category": "hat",
                "color_primary": "yellow",
                "thumbnail_url": None,
                "wear_count": 0,
                "last_worn": None,
                "days_since_worn": None,
                "best_partner": None,
            }
        ],
        "count": 1,
        "generated_at": "2026-07-22",
        "cached": False,
    }

    async def fake_get_forgotten_items(db, user_id, days_threshold=60, force_refresh=False):
        return payload

    monkeypatch.setattr(stats, "get_forgotten_items", fake_get_forgotten_items)
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[deps.get_current_active_user] = lambda: user

    response = await client.get("/api/v1/stats/forgotten")

    assert response.status_code == 200
    body = response.json()
    assert body["count"] == 1
    assert body["items"][0]["category"] == "hat"

    app.dependency_overrides.clear()


# ============================================================================
# RI-7: Archive / unarchive endpoint
# ============================================================================


@pytest.mark.asyncio
async def test_archive_wardrobe_item_success(monkeypatch, client, dummy_db):
    user = build_user()
    item = build_wardrobe_item(user_id=user.id, status="active")
    weaviate_calls: list[tuple[str, uuid.UUID]] = []
    invalidate_stats_calls: list[uuid.UUID] = []
    invalidate_daily_calls: list[uuid.UUID] = []

    async def override_get_db():
        yield dummy_db

    async def fake_get_by_id(db, item_id, user_id=None):
        return item

    async def fake_update(db, item_id, update_data):
        for field, value in update_data.items():
            setattr(item, field, value)
        return item

    async def fake_invalidate_stats(user_id):
        invalidate_stats_calls.append(user_id)

    async def fake_invalidate_daily(user_id):
        invalidate_daily_calls.append(user_id)

    monkeypatch.setattr(wardrobe.wardrobe_crud, "get_by_id", fake_get_by_id)
    monkeypatch.setattr(wardrobe.wardrobe_crud, "update", fake_update)
    monkeypatch.setattr(wardrobe.weaviate_service, "is_connected", lambda: True)
    monkeypatch.setattr(
        wardrobe.weaviate_service,
        "delete_item",
        lambda item_id: weaviate_calls.append(("delete", item_id)),
    )
    monkeypatch.setattr(wardrobe, "invalidate_wardrobe_stats_cache", fake_invalidate_stats)
    monkeypatch.setattr(wardrobe, "invalidate_daily_suggestions", fake_invalidate_daily)
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[deps.get_current_active_user] = lambda: user

    response = await client.patch(
        f"/api/v1/wardrobe/items/{item.id}/status", json={"status": "archived"}
    )

    assert response.status_code == 200
    assert response.json()["status"] == "archived"
    assert ("delete", item.id) in weaviate_calls
    assert invalidate_stats_calls == [user.id]
    assert invalidate_daily_calls == [user.id]

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_archive_wardrobe_item_unowned_returns_404(monkeypatch, client, dummy_db):
    user = build_user()

    async def override_get_db():
        yield dummy_db

    async def fake_get_by_id(db, item_id, user_id=None):
        return None

    monkeypatch.setattr(wardrobe.wardrobe_crud, "get_by_id", fake_get_by_id)
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[deps.get_current_active_user] = lambda: user

    response = await client.patch(
        f"/api/v1/wardrobe/items/{uuid.uuid4()}/status", json={"status": "archived"}
    )

    assert response.status_code == 404

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_archive_wardrobe_item_bad_status_returns_422(client, dummy_db):
    user = build_user()

    async def override_get_db():
        yield dummy_db

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[deps.get_current_active_user] = lambda: user

    response = await client.patch(
        f"/api/v1/wardrobe/items/{uuid.uuid4()}/status", json={"status": "deleted"}
    )

    assert response.status_code == 422

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_list_wardrobe_items_archived_status_passed_to_crud(monkeypatch, client, dummy_db):
    user = build_user()
    captured_kwargs: dict = {}

    async def override_get_db():
        yield dummy_db

    async def fake_get_by_user(db, user_id, **kwargs):
        captured_kwargs.update(kwargs)
        return [], 0

    monkeypatch.setattr(wardrobe.wardrobe_crud, "get_by_user", fake_get_by_user)
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[deps.get_current_active_user] = lambda: user

    response = await client.get("/api/v1/wardrobe/items", params={"status": "archived"})

    assert response.status_code == 200
    assert captured_kwargs["status"] == "archived"

    app.dependency_overrides.clear()


# ============================================================================
# RI-7: Additional-photo endpoints
# ============================================================================


@pytest.mark.asyncio
async def test_add_wardrobe_item_photo_returns_201_and_schedules_processing(
    monkeypatch, client, dummy_db
):
    user = build_user()
    item = build_wardrobe_item(user_id=user.id)
    photo_id = uuid.uuid4()
    processing_calls: list[uuid.UUID] = []

    async def override_get_db():
        yield dummy_db

    async def fake_get_by_id(db, item_id, user_id=None):
        return item

    async def fake_save_upload_file(file, user_id, subdirectory):
        return ("/tmp/originals/photo.jpg", "/uploads/originals/photo.jpg")

    class FakePhoto:
        id = photo_id

    async def fake_create(db, item_id, original_image_url):
        return FakePhoto()

    async def fake_process_photo(photo_id, user_id, original_image_path):
        processing_calls.append(photo_id)

    monkeypatch.setattr(wardrobe.wardrobe_crud, "get_by_id", fake_get_by_id)
    monkeypatch.setattr(wardrobe.get_storage(), "save_upload_file", fake_save_upload_file)
    monkeypatch.setattr(wardrobe.wardrobe_photo_crud, "create", fake_create)
    monkeypatch.setattr(wardrobe, "process_wardrobe_item_photo", fake_process_photo)
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[deps.get_current_active_user] = lambda: user

    response = await client.post(
        f"/api/v1/wardrobe/items/{item.id}/photos",
        files={"file": ("photo.jpg", b"fake-image-bytes", "image/jpeg")},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["id"] == str(photo_id)
    assert body["status"] == "processing"
    # Background task must have been scheduled and executed with the new photo id.
    assert processing_calls == [photo_id]

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_delete_wardrobe_item_photo_204(monkeypatch, client, dummy_db):
    from attreq_api.models.wardrobe_photo import WardrobeItemPhoto

    user = build_user()
    item = build_wardrobe_item(user_id=user.id)
    photo = WardrobeItemPhoto(
        id=uuid.uuid4(),
        item_id=item.id,
        original_image_url="/uploads/originals/p.jpg",
        is_primary=False,
    )
    delete_calls: list[uuid.UUID] = []

    async def override_get_db():
        yield dummy_db

    async def fake_get_by_id(db, item_id, user_id=None):
        return item

    async def fake_get_photo_by_id(db, photo_id, item_id=None):
        return photo

    async def fake_delete(db, photo_id):
        delete_calls.append(photo_id)
        return True

    monkeypatch.setattr(wardrobe.wardrobe_crud, "get_by_id", fake_get_by_id)
    monkeypatch.setattr(wardrobe.wardrobe_photo_crud, "get_by_id", fake_get_photo_by_id)
    monkeypatch.setattr(wardrobe.wardrobe_photo_crud, "delete", fake_delete)
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[deps.get_current_active_user] = lambda: user

    response = await client.delete(f"/api/v1/wardrobe/items/{item.id}/photos/{photo.id}")

    assert response.status_code == 204
    assert delete_calls == [photo.id]

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_delete_primary_photo_returns_400(monkeypatch, client, dummy_db):
    from attreq_api.models.wardrobe_photo import WardrobeItemPhoto

    user = build_user()
    item = build_wardrobe_item(user_id=user.id)
    photo = WardrobeItemPhoto(
        id=uuid.uuid4(),
        item_id=item.id,
        original_image_url="/uploads/originals/p.jpg",
        is_primary=True,
    )

    async def override_get_db():
        yield dummy_db

    async def fake_get_by_id(db, item_id, user_id=None):
        return item

    async def fake_get_photo_by_id(db, photo_id, item_id=None):
        return photo

    monkeypatch.setattr(wardrobe.wardrobe_crud, "get_by_id", fake_get_by_id)
    monkeypatch.setattr(wardrobe.wardrobe_photo_crud, "get_by_id", fake_get_photo_by_id)
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[deps.get_current_active_user] = lambda: user

    response = await client.delete(f"/api/v1/wardrobe/items/{item.id}/photos/{photo.id}")

    assert response.status_code == 400

    app.dependency_overrides.clear()


# ============================================================================
# RI-7: Archived items excluded from recommendation pools
# ============================================================================


@pytest.mark.asyncio
async def test_generate_daily_outfits_query_filters_to_active_status():
    class QueryCapturingDB:
        def __init__(self):
            self.queries = []

        async def execute(self, query):
            self.queries.append(query)

            class FakeScalars:
                def all(self_inner):
                    return []

            class FakeResult:
                def scalars(self_inner):
                    return FakeScalars()

            return FakeResult()

    db = QueryCapturingDB()
    user_id = uuid.uuid4()

    result = await algorithm.generate_daily_outfits(
        db, user_id, weather={"temp": 22, "condition": "Clear"}, occasion="casual"
    )

    assert result == []
    assert len(db.queries) == 1
    compiled = str(db.queries[0].compile(compile_kwargs={"literal_binds": True}))
    assert "wardrobe_items.status" in compiled
    assert "'active'" in compiled


# ============================================================================
# RI-7: Batch upload concurrency (bounded, per-task session)
# ============================================================================


@pytest.mark.asyncio
async def test_batch_upload_of_20_all_reach_terminal_status_no_cross_item_swap(monkeypatch):
    """20 images processed concurrently must all complete, each with its OWN
    classification result — proving no cross-item state corruption from the
    per-task-session + bounded-semaphore fix (RI-7 shared-AsyncSession bug).
    """

    class FakeSessionCM:
        def __init__(self):
            self.db = DummyDB()

        async def __aenter__(self):
            return self.db

        async def __aexit__(self, *exc_info):
            return False

    def fake_async_session_local():
        return FakeSessionCM()

    updates: dict[uuid.UUID, dict] = {}

    async def fake_update(db, item_id, update_data):
        updates.setdefault(item_id, {}).update(update_data)

    async def fake_generate_processed_and_thumbnail(image_path, user_id, log_ref=None):
        return image_path, f"processed:{image_path}", f"thumb:{image_path}"

    FAILING_INDEX = 7

    async def fake_detect_clothing(image_path):
        if image_path == f"/tmp/img_{FAILING_INDEX}.jpg":
            raise RuntimeError("simulated classifier failure for one image")
        return {
            "category": f"category-for-{image_path}",
            "color_primary": "blue",
            "color_secondary": None,
            "pattern": "solid",
            "season": ["all"],
            "occasion": ["casual"],
            "detection_confidence": 0.9,
            "classification_source": "fallback",
            "processing_status": "completed",
        }

    async def fake_invalidate_stats(user_id):
        return None

    monkeypatch.setattr(batch_image_processor, "AsyncSessionLocal", fake_async_session_local)
    monkeypatch.setattr(batch_image_processor.wardrobe_crud, "update", fake_update)
    monkeypatch.setattr(
        batch_image_processor,
        "generate_processed_and_thumbnail",
        fake_generate_processed_and_thumbnail,
    )
    monkeypatch.setattr(
        batch_image_processor.clothing_detection_service, "detect_clothing", fake_detect_clothing
    )
    monkeypatch.setattr(
        batch_image_processor.weaviate_service, "is_connected", lambda: False
    )
    monkeypatch.setattr(
        batch_image_processor, "invalidate_wardrobe_stats_cache", fake_invalidate_stats
    )

    item_ids = [uuid.uuid4() for _ in range(20)]
    image_paths = [f"/tmp/img_{i}.jpg" for i in range(20)]

    await batch_image_processor.process_batch_wardrobe_images(
        item_ids=item_ids,
        user_id=uuid.uuid4(),
        image_refs=image_paths,
        image_urls=image_paths,
    )

    # All 20 items reached a terminal state — none stuck pending/processing.
    assert len(updates) == 20
    for item_id in item_ids:
        assert updates[item_id]["processing_status"] == "completed"

    # No cross-item classification swap: each item's category matches its OWN
    # image path, except the one whose detection intentionally failed (falls
    # back to None but still completes — one bad image never fails the batch).
    for i, item_id in enumerate(item_ids):
        expected_path = image_paths[i]
        if i == FAILING_INDEX:
            assert updates[item_id]["category"] is None
        else:
            assert updates[item_id]["category"] == f"category-for-{expected_path}"


# ============================================================================
# RI-2: Classifier schema v2 — response contracts, correction validation,
# item_corrected telemetry, and worker BG-removal-failure color fallback.
# ============================================================================


@pytest.mark.asyncio
async def test_get_wardrobe_item_round_trips_color_palette_and_attribute_confidence(
    monkeypatch, client, dummy_db
):
    user = build_user()
    item = build_wardrobe_item(
        user_id=user.id,
        texture="knit",
        silhouette="oversized",
        neckline="crew",
        sleeve_length="long",
        statement_level="statement",
        llm_formality=2,
        is_fullbody=False,
        color_palette=[
            {"lab": [50.0, 1.0, 2.0], "hex": "#808080", "share": 0.7, "is_neutral": True, "name": "gray"}
        ],
        color_extraction_source="pixel",
        attribute_confidence={"category": 0.9, "texture": 0.4},
        schema_version=2,
    )

    async def override_get_db():
        yield dummy_db

    async def fake_get_by_id(db, item_id, user_id=None):
        return item

    monkeypatch.setattr(wardrobe.wardrobe_crud, "get_by_id", fake_get_by_id)
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[deps.get_current_active_user] = lambda: user

    response = await client.get(f"/api/v1/wardrobe/items/{item.id}")

    assert response.status_code == 200
    body = response.json()
    assert body["texture"] == "knit"
    assert body["silhouette"] == "oversized"
    assert body["schema_version"] == 2
    assert body["color_palette"] == [
        {"lab": [50.0, 1.0, 2.0], "hex": "#808080", "share": 0.7, "is_neutral": True, "name": "gray"}
    ]
    assert body["attribute_confidence"] == {"category": 0.9, "texture": 0.4}

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_get_wardrobe_item_v1_row_serializes_with_null_v2_fields(monkeypatch, client, dummy_db):
    user = build_user()
    item = build_wardrobe_item(user_id=user.id)  # defaults: schema_version=1, all v2 fields None

    async def override_get_db():
        yield dummy_db

    async def fake_get_by_id(db, item_id, user_id=None):
        return item

    monkeypatch.setattr(wardrobe.wardrobe_crud, "get_by_id", fake_get_by_id)
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[deps.get_current_active_user] = lambda: user

    response = await client.get(f"/api/v1/wardrobe/items/{item.id}")

    assert response.status_code == 200
    body = response.json()
    assert body["schema_version"] == 1
    assert body["texture"] is None
    assert body["color_palette"] is None
    assert body["attribute_confidence"] is None
    assert body["is_fullbody"] is False

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_update_wardrobe_item_rejects_out_of_vocabulary_enum_with_422(client, dummy_db):
    user = build_user()

    async def override_get_db():
        yield dummy_db

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[deps.get_current_active_user] = lambda: user

    response = await client.put(
        f"/api/v1/wardrobe/items/{uuid.uuid4()}", json={"texture": "fur"}
    )

    assert response.status_code == 422

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_update_wardrobe_item_emits_item_corrected_event_on_attribute_change(
    monkeypatch, client, dummy_db
):
    user = build_user()
    item = build_wardrobe_item(user_id=user.id, texture="smooth", schema_version=2)
    emitted: list[dict] = []

    async def override_get_db():
        yield dummy_db

    async def fake_get_by_id(db, item_id, user_id=None):
        return item

    async def fake_update(db, item_id, update_data):
        for field, value in update_data.items():
            setattr(item, field, value)
        return item

    async def fake_create_event(db, *, user_id, event_type, payload=None):
        emitted.append({"user_id": user_id, "event_type": event_type, "payload": payload})

    monkeypatch.setattr(wardrobe.wardrobe_crud, "get_by_id", fake_get_by_id)
    monkeypatch.setattr(wardrobe.wardrobe_crud, "update", fake_update)
    monkeypatch.setattr(wardrobe.user_event_crud, "create", fake_create_event)
    monkeypatch.setattr(wardrobe.weaviate_service, "is_connected", lambda: False)
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[deps.get_current_active_user] = lambda: user

    response = await client.put(
        f"/api/v1/wardrobe/items/{item.id}", json={"texture": "knit"}
    )

    assert response.status_code == 200
    assert len(emitted) == 1
    event = emitted[0]
    assert event["event_type"] == "item_corrected"
    assert event["payload"]["field"] == "texture"
    assert event["payload"]["old_value"] == "smooth"
    assert event["payload"]["new_value"] == "knit"
    assert event["payload"]["was_confirmation"] is False

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_update_wardrobe_item_confirming_same_value_marks_was_confirmation(
    monkeypatch, client, dummy_db
):
    user = build_user()
    item = build_wardrobe_item(user_id=user.id, silhouette="regular", schema_version=2)
    emitted: list[dict] = []

    async def override_get_db():
        yield dummy_db

    async def fake_get_by_id(db, item_id, user_id=None):
        return item

    async def fake_update(db, item_id, update_data):
        for field, value in update_data.items():
            setattr(item, field, value)
        return item

    async def fake_create_event(db, *, user_id, event_type, payload=None):
        emitted.append(payload)

    monkeypatch.setattr(wardrobe.wardrobe_crud, "get_by_id", fake_get_by_id)
    monkeypatch.setattr(wardrobe.wardrobe_crud, "update", fake_update)
    monkeypatch.setattr(wardrobe.user_event_crud, "create", fake_create_event)
    monkeypatch.setattr(wardrobe.weaviate_service, "is_connected", lambda: False)
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[deps.get_current_active_user] = lambda: user

    response = await client.put(
        f"/api/v1/wardrobe/items/{item.id}", json={"silhouette": "regular"}
    )

    assert response.status_code == 200
    assert emitted[0]["was_confirmation"] is True

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_image_processor_bg_removal_failure_sets_llm_fallback_color(monkeypatch):
    """Worker-level: when background removal fails, `classification_path` is
    the ORIGINAL image (not background-removed) — pixel color extraction must
    be skipped entirely (`color_extraction_source="llm_fallback"`,
    `color_palette=None`), while classification still persists normally.
    """

    class FakeSessionCM:
        def __init__(self):
            self.db = DummyDB()

        async def __aenter__(self):
            return self.db

        async def __aexit__(self, *exc_info):
            return False

    captured_update: dict = {}

    async def fake_update_processing_status(db, item_id, status):
        return None

    async def fake_update(db, item_id, update_data):
        captured_update.update(update_data)

    async def fake_generate_processed_and_thumbnail(image_path, user_id, log_ref=None):
        # Background removal failed: processed_image_url is None.
        return image_path, None, None

    async def fake_detect_clothing(image_path):
        return {
            "category": "shirt",
            "color_primary": "blue",
            "color_secondary": None,
            "pattern": "solid",
            "season": ["all"],
            "occasion": ["casual"],
            "detection_confidence": 0.8,
            "classification_source": "ai",
            "processing_status": "completed",
        }

    monkeypatch.setattr(image_processor, "AsyncSessionLocal", FakeSessionCM)
    monkeypatch.setattr(image_processor.wardrobe_crud, "update_processing_status", fake_update_processing_status)
    monkeypatch.setattr(image_processor.wardrobe_crud, "update", fake_update)
    monkeypatch.setattr(
        image_processor, "generate_processed_and_thumbnail", fake_generate_processed_and_thumbnail
    )
    monkeypatch.setattr(image_processor.clothing_detection_service, "detect_clothing", fake_detect_clothing)
    monkeypatch.setattr(image_processor.weaviate_service, "is_connected", lambda: False)

    async def fake_invalidate_stats(user_id):
        return None

    monkeypatch.setattr(image_processor, "invalidate_wardrobe_stats_cache", fake_invalidate_stats)

    await image_processor.process_wardrobe_image(
        item_id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        original_image_ref="/tmp/original.jpg",
        original_image_url="/uploads/originals/original.jpg",
    )

    assert captured_update["color_extraction_source"] == "llm_fallback"
    assert captured_update["color_palette"] is None
    assert captured_update["category"] == "shirt"
    assert captured_update["processing_status"] == "completed"
