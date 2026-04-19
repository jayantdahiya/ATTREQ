from __future__ import annotations

import uuid
from datetime import date

import pytest
from fastapi import HTTPException

from attreq_api.api.v1 import deps
from attreq_api.api.v1.endpoints import auth, outfits, recommendations, users
from attreq_api.config import security
from attreq_api.config.database import get_db
from attreq_api.main import app
from tests.conftest import build_outfit, build_user, build_wardrobe_item


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
        return None

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
