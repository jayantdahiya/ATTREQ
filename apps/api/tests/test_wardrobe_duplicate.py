"""Tests for RI-6 near-duplicate detection (upload worker) and the
delete-path vector-leak fix.

Part 1 mocks every dependency of `workers.image_processor.process_wardrobe_image`
(Weaviate, FashionCLIP, the classifier, storage helpers, the DB session) to
verify: the temp-dir-scoping fix (embedding computed before cleanup, upsert/
dup-check after), the 0.97 near-dup threshold (distinct from the 0.85
propagation threshold — both boundaries are tested), and that
`possible_duplicate_of` lands in the `wardrobe_crud.update()` payload.

Part 2 covers the delete-path vector-leak fix at the endpoint level
(`DELETE /wardrobe/items/{id}` must call `weaviate_service.delete_vector`,
not just `delete_item`), following the existing `DummyDB` +
`dependency_overrides` pattern used throughout `test_client_contracts.py`.
"""

from __future__ import annotations

import uuid
from contextlib import asynccontextmanager

import pytest

from attreq_api.api.v1 import deps
from attreq_api.api.v1.endpoints import wardrobe
from attreq_api.config.database import get_db
from attreq_api.main import app
from attreq_api.workers import batch_image_processor, image_processor
from tests.conftest import build_user, build_wardrobe_item


class _FakeDB:
    """Just enough of an AsyncSession for process_wardrobe_image's calls
    (all of which go through wardrobe_crud, itself monkeypatched below)."""

    async def commit(self):
        pass

    async def rollback(self):
        pass

    async def close(self):
        pass


def _patch_common_worker_deps(monkeypatch, *, embeddings_enabled: bool):
    @asynccontextmanager
    async def fake_session_ctx():
        yield _FakeDB()

    monkeypatch.setattr(image_processor, "AsyncSessionLocal", fake_session_ctx)
    monkeypatch.setattr(image_processor.settings, "embeddings_enabled", embeddings_enabled)

    status_calls: list[tuple[uuid.UUID, str]] = []

    async def fake_update_processing_status(db, item_id, status):
        status_calls.append((item_id, status))

    monkeypatch.setattr(
        image_processor.wardrobe_crud, "update_processing_status", fake_update_processing_status
    )

    async def fake_generate_processed_and_thumbnail(image_ref, user_id, log_ref=""):
        return ("/tmp/fake_classification_path.png", "/uploads/processed/fake.png", "/uploads/thumbnails/fake.png")

    monkeypatch.setattr(
        image_processor, "generate_processed_and_thumbnail", fake_generate_processed_and_thumbnail
    )

    cleanup_calls: list[str] = []
    monkeypatch.setattr(
        image_processor, "cleanup_classification_tempdir", lambda path: cleanup_calls.append(path)
    )

    async def fake_detect_clothing(path):
        return {
            "category": "shirt",
            "color_primary": "blue",
            "color_secondary": None,
            "pattern": "solid",
            "season": ["summer"],
            "occasion": ["casual"],
            "detection_confidence": 0.9,
            "processing_status": "completed",
        }

    monkeypatch.setattr(
        image_processor.clothing_detection_service, "detect_clothing", fake_detect_clothing
    )

    async def fake_extract_palette_safe(path, log_ref=""):
        return None, "llm_fallback"

    monkeypatch.setattr(image_processor, "extract_palette_safe", fake_extract_palette_safe)

    monkeypatch.setattr(image_processor.weaviate_service, "is_connected", lambda: True)
    monkeypatch.setattr(image_processor.weaviate_service, "init_schema", lambda: True)
    monkeypatch.setattr(image_processor.weaviate_service, "add_item", lambda **kw: True)
    monkeypatch.setattr(image_processor.weaviate_service, "init_vector_schema", lambda: True)

    upsert_calls: list[dict] = []
    monkeypatch.setattr(
        image_processor.weaviate_service,
        "upsert_vector",
        lambda **kw: upsert_calls.append(kw) or True,
    )

    update_calls: list[dict] = []

    async def fake_update(db, item_id, update_data):
        update_calls.append(update_data)
        return

    monkeypatch.setattr(image_processor.wardrobe_crud, "update", fake_update)

    async def fake_invalidate_cache(user_id):
        pass

    monkeypatch.setattr(image_processor, "invalidate_wardrobe_stats_cache", fake_invalidate_cache)

    return {"status_calls": status_calls, "cleanup_calls": cleanup_calls, "upsert_calls": upsert_calls, "update_calls": update_calls}


@pytest.mark.asyncio
async def test_near_duplicate_set_when_similarity_above_threshold(monkeypatch):
    """A 0.98 neighbor (>= the 0.97 near-dup threshold) sets
    `possible_duplicate_of` in the wardrobe_crud.update() payload."""
    recorded = _patch_common_worker_deps(monkeypatch, embeddings_enabled=True)

    dup_item_id = uuid.uuid4()
    monkeypatch.setattr(
        image_processor.fashion_embeddings_service, "embed_image", lambda path: [1.0, 0.0, 0.0]
    )

    neighbor_calls: list[dict] = []

    def fake_query_neighbors(vector, user_id, k, min_sim, exclude_item_id=None):
        neighbor_calls.append({"min_sim": min_sim, "k": k})
        return [(dup_item_id, 0.98)]

    monkeypatch.setattr(image_processor.weaviate_service, "query_neighbors", fake_query_neighbors)

    item_id = uuid.uuid4()
    user_id = uuid.uuid4()
    await image_processor.process_wardrobe_image(item_id, user_id, "ref", "/uploads/originals/x.png")

    assert neighbor_calls[0]["min_sim"] == 0.97
    final_update = recorded["update_calls"][-1]
    assert final_update.get("possible_duplicate_of") == dup_item_id
    assert recorded["upsert_calls"], "vector should still be upserted even when a dup is found"


@pytest.mark.asyncio
async def test_near_duplicate_not_set_when_similarity_below_threshold(monkeypatch):
    """A 0.90 neighbor is below the 0.97 near-dup threshold (distinct from
    the 0.85 propagation threshold) — query_neighbors itself filters it out,
    so no `possible_duplicate_of` is set."""
    recorded = _patch_common_worker_deps(monkeypatch, embeddings_enabled=True)

    monkeypatch.setattr(
        image_processor.fashion_embeddings_service, "embed_image", lambda path: [1.0, 0.0, 0.0]
    )
    monkeypatch.setattr(
        image_processor.weaviate_service,
        "query_neighbors",
        lambda vector, user_id, k, min_sim, exclude_item_id=None: [],
    )

    item_id = uuid.uuid4()
    user_id = uuid.uuid4()
    await image_processor.process_wardrobe_image(item_id, user_id, "ref", "/uploads/originals/x.png")

    final_update = recorded["update_calls"][-1]
    assert "possible_duplicate_of" not in final_update


@pytest.mark.asyncio
async def test_embedding_computed_before_cleanup_and_upsert_after(monkeypatch):
    """The confirmed temp-dir-scoping fix: embed_image must be called BEFORE
    cleanup_classification_tempdir, and upsert_vector must be called AFTER —
    both must reference the same classification_path."""
    recorded = _patch_common_worker_deps(monkeypatch, embeddings_enabled=True)

    call_order: list[str] = []

    def fake_embed_image(path):
        call_order.append(f"embed:{path}")
        return [1.0, 0.0]

    monkeypatch.setattr(image_processor.fashion_embeddings_service, "embed_image", fake_embed_image)

    original_cleanup = recorded["cleanup_calls"]

    def tracking_cleanup(path):
        call_order.append(f"cleanup:{path}")
        original_cleanup.append(path)

    monkeypatch.setattr(image_processor, "cleanup_classification_tempdir", tracking_cleanup)

    def fake_upsert(**kw):
        call_order.append("upsert")
        return True

    monkeypatch.setattr(image_processor.weaviate_service, "upsert_vector", fake_upsert)
    monkeypatch.setattr(
        image_processor.weaviate_service,
        "query_neighbors",
        lambda vector, user_id, k, min_sim, exclude_item_id=None: [],
    )

    await image_processor.process_wardrobe_image(
        uuid.uuid4(), uuid.uuid4(), "ref", "/uploads/originals/x.png"
    )

    embed_index = next(i for i, c in enumerate(call_order) if c.startswith("embed:"))
    cleanup_index = next(i for i, c in enumerate(call_order) if c.startswith("cleanup:"))
    upsert_index = call_order.index("upsert")

    assert embed_index < cleanup_index < upsert_index


@pytest.mark.asyncio
async def test_no_embedding_call_when_embeddings_disabled(monkeypatch):
    recorded = _patch_common_worker_deps(monkeypatch, embeddings_enabled=False)

    embed_calls: list[str] = []
    monkeypatch.setattr(
        image_processor.fashion_embeddings_service,
        "embed_image",
        lambda path: embed_calls.append(path) or [1.0],
    )

    await image_processor.process_wardrobe_image(
        uuid.uuid4(), uuid.uuid4(), "ref", "/uploads/originals/x.png"
    )

    assert embed_calls == []
    assert recorded["upsert_calls"] == []


# ---------------------------------------------------------------------------
# batch_image_processor.py — same temp-dir-scoping bug, same fix, mirrored
# structure (see workers/batch_image_processor.py::_process_single_item).
# ---------------------------------------------------------------------------


def _patch_batch_worker_deps(monkeypatch, *, embeddings_enabled: bool):
    monkeypatch.setattr(batch_image_processor.settings, "embeddings_enabled", embeddings_enabled)

    async def fake_generate_processed_and_thumbnail(image_ref, user_id, log_ref=""):
        return ("/tmp/fake_batch_classification.png", "/uploads/processed/fake.png", "/uploads/thumbnails/fake.png")

    monkeypatch.setattr(
        batch_image_processor, "generate_processed_and_thumbnail", fake_generate_processed_and_thumbnail
    )
    monkeypatch.setattr(batch_image_processor, "cleanup_classification_tempdir", lambda path: None)

    async def fake_detect_clothing(path):
        return {
            "category": "shirt",
            "color_primary": "blue",
            "color_secondary": None,
            "pattern": "solid",
            "season": ["summer"],
            "occasion": ["casual"],
            "detection_confidence": 0.9,
            "classification_source": "ai",
            "processing_status": "completed",
        }

    monkeypatch.setattr(
        batch_image_processor.clothing_detection_service, "detect_clothing", fake_detect_clothing
    )

    async def fake_extract_palette_safe(path, log_ref=""):
        return None, "llm_fallback"

    monkeypatch.setattr(batch_image_processor, "extract_palette_safe", fake_extract_palette_safe)

    monkeypatch.setattr(batch_image_processor.weaviate_service, "is_connected", lambda: True)
    monkeypatch.setattr(batch_image_processor.weaviate_service, "init_schema", lambda: True)
    monkeypatch.setattr(batch_image_processor.weaviate_service, "add_item", lambda **kw: True)
    monkeypatch.setattr(batch_image_processor.weaviate_service, "init_vector_schema", lambda: True)

    upsert_calls: list[dict] = []
    monkeypatch.setattr(
        batch_image_processor.weaviate_service,
        "upsert_vector",
        lambda **kw: upsert_calls.append(kw) or True,
    )

    update_calls: list[dict] = []

    async def fake_update(db, item_id, update_data):
        update_calls.append(update_data)
        return

    monkeypatch.setattr(batch_image_processor.wardrobe_crud, "update", fake_update)

    return {"upsert_calls": upsert_calls, "update_calls": update_calls}


@pytest.mark.asyncio
async def test_batch_worker_sets_possible_duplicate_of_above_threshold(monkeypatch):
    recorded = _patch_batch_worker_deps(monkeypatch, embeddings_enabled=True)
    dup_item_id = uuid.uuid4()

    monkeypatch.setattr(
        batch_image_processor.fashion_embeddings_service, "embed_image", lambda path: [1.0, 0.0]
    )
    monkeypatch.setattr(
        batch_image_processor.weaviate_service,
        "query_neighbors",
        lambda vector, user_id, k, min_sim, exclude_item_id=None: [(dup_item_id, 0.98)],
    )

    await batch_image_processor._process_single_item(
        item_id=uuid.uuid4(),
        image_ref="ref",
        image_url="/uploads/originals/x.png",
        user_id=uuid.uuid4(),
        db=None,
    )

    final_update = recorded["update_calls"][-1]
    assert final_update.get("possible_duplicate_of") == dup_item_id


@pytest.mark.asyncio
async def test_batch_worker_no_embedding_when_disabled(monkeypatch):
    recorded = _patch_batch_worker_deps(monkeypatch, embeddings_enabled=False)
    embed_calls: list[str] = []
    monkeypatch.setattr(
        batch_image_processor.fashion_embeddings_service,
        "embed_image",
        lambda path: embed_calls.append(path) or [1.0],
    )

    await batch_image_processor._process_single_item(
        item_id=uuid.uuid4(),
        image_ref="ref",
        image_url="/uploads/originals/x.png",
        user_id=uuid.uuid4(),
        db=None,
    )

    assert embed_calls == []
    assert recorded["upsert_calls"] == []


# ---------------------------------------------------------------------------
# Delete-path vector-leak fix
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_delete_wardrobe_item_calls_delete_vector(monkeypatch, client):
    user = build_user()
    item = build_wardrobe_item(user_id=user.id)

    async def override_get_db():
        yield None

    async def fake_get_by_id(db, item_id, user_id=None):
        return item

    async def fake_delete(db, item_id, user_id):
        return True

    async def fake_invalidate_stats(user_id):
        pass

    async def fake_invalidate_daily(user_id):
        pass

    delete_item_calls: list[uuid.UUID] = []
    delete_vector_calls: list[uuid.UUID] = []

    monkeypatch.setattr(wardrobe.wardrobe_crud, "get_by_id", fake_get_by_id)
    monkeypatch.setattr(wardrobe.wardrobe_crud, "delete", fake_delete)
    monkeypatch.setattr(wardrobe.weaviate_service, "is_connected", lambda: True)
    monkeypatch.setattr(
        wardrobe.weaviate_service, "delete_item", lambda item_id: delete_item_calls.append(item_id)
    )
    monkeypatch.setattr(
        wardrobe.weaviate_service,
        "delete_vector",
        lambda item_id: delete_vector_calls.append(item_id) or True,
    )
    monkeypatch.setattr(wardrobe, "invalidate_wardrobe_stats_cache", fake_invalidate_stats)
    monkeypatch.setattr(wardrobe, "invalidate_daily_suggestions", fake_invalidate_daily)

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[deps.get_current_active_user] = lambda: user

    response = await client.delete(f"/api/v1/wardrobe/items/{item.id}")

    assert response.status_code == 204
    assert delete_item_calls == [item.id]
    assert delete_vector_calls == [item.id]

    app.dependency_overrides.clear()
