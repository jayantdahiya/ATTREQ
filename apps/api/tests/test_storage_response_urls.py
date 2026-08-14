"""Regression tests for client-usable image URLs in wardrobe responses."""

import uuid
from datetime import UTC, datetime

from attreq_api.schemas.wardrobe import WardrobeItemResponse
from attreq_api.services import storage


class _FakeS3Storage:
    def get_file_url(self, ref: str) -> str:
        return f"https://signed.example/{ref}"


def _wardrobe_response(**overrides: object) -> WardrobeItemResponse:
    now = datetime.now(UTC)
    values: dict[str, object] = {
        "id": uuid.uuid4(),
        "user_id": uuid.uuid4(),
        "original_image_url": "originals/item.png",
        "processed_image_url": "processed/item.png",
        "thumbnail_url": "thumbnails/item.jpg",
        "processing_status": "completed",
        "status": "active",
        "wear_count": 0,
        "created_at": now,
        "updated_at": now,
    }
    values.update(overrides)
    return WardrobeItemResponse(**values)


def test_single_item_response_presigns_all_r2_image_keys(monkeypatch):
    monkeypatch.setattr(storage.settings, "storage_backend", "s3")
    monkeypatch.setattr(storage, "get_storage", lambda: _FakeS3Storage())

    payload = _wardrobe_response().model_dump(mode="json")

    assert payload["original_image_url"] == "https://signed.example/originals/item.png"
    assert payload["processed_image_url"] == "https://signed.example/processed/item.png"
    assert payload["thumbnail_url"] == "https://signed.example/thumbnails/item.jpg"


def test_single_item_response_preserves_absolute_and_missing_urls(monkeypatch):
    monkeypatch.setattr(storage.settings, "storage_backend", "s3")
    monkeypatch.setattr(storage, "get_storage", lambda: _FakeS3Storage())

    payload = _wardrobe_response(
        original_image_url="https://cdn.example/original.png",
        processed_image_url=None,
        thumbnail_url=None,
    ).model_dump(mode="json")

    assert payload["original_image_url"] == "https://cdn.example/original.png"
    assert payload["processed_image_url"] is None
    assert payload["thumbnail_url"] is None
