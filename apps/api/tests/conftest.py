from __future__ import annotations

import os
import uuid
from collections.abc import AsyncGenerator
from datetime import date, datetime, timezone

import pytest
from httpx import ASGITransport, AsyncClient

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://attreq_user:attreq_password@localhost:5432/attreq_db")
os.environ.setdefault("POSTGRES_DB", "attreq_db")
os.environ.setdefault("POSTGRES_USER", "attreq_user")
os.environ.setdefault("POSTGRES_PASSWORD", "attreq_password")
os.environ.setdefault("SECRET_KEY", "test-secret-key-that-is-long-enough-for-jwt")
os.environ["UPLOAD_DIR"] = "/tmp/attreq-test-uploads"

from attreq_api.main import app
from attreq_api.models.outfit import Outfit
from attreq_api.models.user import User
from attreq_api.models.wardrobe import WardrobeItem


class DummyDB:
    async def execute(self, *args, **kwargs):  # pragma: no cover - placeholder for dependency override
        return None

    async def commit(self):  # pragma: no cover - placeholder for dependency override
        return None

    async def rollback(self):  # pragma: no cover - placeholder for dependency override
        return None

    async def refresh(self, *args, **kwargs):  # pragma: no cover - placeholder for dependency override
        return None

    async def close(self):  # pragma: no cover - placeholder for dependency override
        return None


def build_user(**overrides) -> User:
    timestamp = datetime.now(timezone.utc)
    defaults = {
        "id": uuid.uuid4(),
        "email": "test@example.com",
        "password_hash": "hashed-password",
        "full_name": "Test User",
        "location": "Mumbai",
        "saved_latitude": 19.076,
        "saved_longitude": 72.8777,
        "saved_city": "Mumbai",
        "is_active": True,
        "is_verified": True,
        "created_at": timestamp,
        "updated_at": timestamp,
        "last_login": timestamp,
        "oauth_provider": None,
        "oauth_id": None,
        "style_preferences": None,
    }
    defaults.update(overrides)
    return User(**defaults)


def build_wardrobe_item(*, user_id: uuid.UUID, **overrides) -> WardrobeItem:
    timestamp = datetime.now(timezone.utc)
    defaults = {
        "id": uuid.uuid4(),
        "user_id": user_id,
        "original_image_url": "/uploads/originals/item.jpg",
        "processed_image_url": "/uploads/processed/item.png",
        "thumbnail_url": "/uploads/thumbnails/item.png",
        "category": "shirt",
        "color_primary": "blue",
        "color_secondary": None,
        "pattern": "solid",
        "season": ["summer"],
        "occasion": ["casual"],
        "detection_confidence": 0.92,
        "processing_status": "completed",
        "wear_count": 2,
        "last_worn": date(2026, 4, 17),
        "created_at": timestamp,
        "updated_at": timestamp,
    }
    defaults.update(overrides)
    return WardrobeItem(**defaults)


def build_outfit(*, user_id: uuid.UUID, top_item_id: uuid.UUID | None = None, bottom_item_id: uuid.UUID | None = None, **overrides) -> Outfit:
    timestamp = datetime.now(timezone.utc)
    defaults = {
        "id": uuid.uuid4(),
        "user_id": user_id,
        "top_item_id": top_item_id,
        "bottom_item_id": bottom_item_id,
        "accessory_ids": [],
        "occasion_context": "casual",
        "weather_context": {"temp": 28, "condition": "Sunny"},
        "feedback_score": None,
        "worn_date": None,
        "created_at": timestamp,
        "updated_at": timestamp,
    }
    defaults.update(overrides)
    return Outfit(**defaults)


@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://localhost") as async_client:
        yield async_client


@pytest.fixture
def dummy_db() -> DummyDB:
    return DummyDB()
