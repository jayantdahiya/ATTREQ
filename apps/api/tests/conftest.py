from __future__ import annotations

import os
import uuid
from datetime import UTC, date, datetime
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

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
    def add(self, *args, **kwargs):  # pragma: no cover - placeholder for dependency override
        return None

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
    timestamp = datetime.now(UTC)
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
        "onboarding_completed": False,
        "onboarding_step": "pending",
    }
    defaults.update(overrides)
    return User(**defaults)


def build_wardrobe_item(*, user_id: uuid.UUID, **overrides) -> WardrobeItem:
    timestamp = datetime.now(UTC)
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
        "status": "active",
        "wear_count": 2,
        "last_worn": date(2026, 4, 17),
        "created_at": timestamp,
        "updated_at": timestamp,
        # Classifier schema v2 (RI-2) — default to a v1-shaped row (all
        # `None`/`False`/`schema_version=1`) so existing callers building a
        # fixture without these kwargs still get a realistic pre-RI-2 item.
        "texture": overrides.get("texture"),
        "silhouette": overrides.get("silhouette"),
        "neckline": overrides.get("neckline"),
        "sleeve_length": overrides.get("sleeve_length"),
        "statement_level": overrides.get("statement_level"),
        "llm_formality": overrides.get("llm_formality"),
        "is_fullbody": overrides.get("is_fullbody", False),
        "color_palette": overrides.get("color_palette"),
        "color_extraction_source": overrides.get("color_extraction_source"),
        "attribute_confidence": overrides.get("attribute_confidence"),
        "schema_version": overrides.get("schema_version", 1),
    }
    defaults.update(overrides)
    return WardrobeItem(**defaults)


def build_outfit(*, user_id: uuid.UUID, top_item_id: uuid.UUID | None = None, bottom_item_id: uuid.UUID | None = None, **overrides) -> Outfit:
    timestamp = datetime.now(UTC)
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


@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Real (Postgres) async session — genuinely new test infra for RI-1.

    Every other fixture in this file mocks `DummyDB`; the new
    RecommendationEventCRUD/UserEventCRUD methods commit internally (get_db never
    commits on its own — see config/database.py), so a plain `session.rollback()`
    would not undo their inserts. Tests that need real persistence must clean up
    explicitly (see the `real_user` fixture below, which deletes its own throwaway
    user row and relies on ON DELETE CASCADE for dependents).
    """
    from attreq_api.config.database import AsyncSessionLocal

    async with AsyncSessionLocal() as session:
        yield session
        await session.close()


@pytest.fixture
async def real_user(db_session: AsyncSession) -> AsyncGenerator[User, None]:
    """A real, persisted throwaway user for real-DB tests.

    Cleanup deletes only this user's row by id; ON DELETE CASCADE on
    recommendation_events.user_id / user_events.user_id takes care of dependents,
    so we never need `rollback()` to undo the CRUD-internal commits.
    """
    user = build_user(email=f"ri1-test-{uuid.uuid4()}@example.com")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    yield user

    await db_session.execute(delete(User).where(User.id == user.id))
    await db_session.commit()
