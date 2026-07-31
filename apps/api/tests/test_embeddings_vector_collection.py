"""Tests for the RI-6 `ClothingItemVector` collection methods added to
`services/ai/embeddings.py::WeaviateEmbeddingsService`.

Uses a lightweight in-memory `FakeWeaviateClient` (never a real Weaviate
connection) that implements just enough of the weaviate-client v4 surface
(`collections.exists/create/get`, `data.insert/delete_many`,
`query.fetch_objects`, `query.near_vector` with cosine `distance` metadata)
for these methods to round-trip against. The real `weaviate` package (a
lightweight client library, no torch) IS installed in this environment, so
`Filter.by_property(...).equal(...)` objects are real — only the network-
talking `client` is faked.
"""

from __future__ import annotations

import types
import uuid

import numpy as np
import pytest

from attreq_api.services.ai.embeddings import VECTOR_COLLECTION_NAME, WeaviateEmbeddingsService


def _cosine_distance(a, b) -> float:
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    cos = float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))
    return 1.0 - cos


class _FakeObj:
    def __init__(self, properties, vector=None, metadata=None):
        self.properties = properties
        self.vector = vector
        self.metadata = metadata


class _FakeData:
    def __init__(self, store: list[dict]):
        self._store = store

    def insert(self, properties, vector=None):
        row = dict(properties)
        row["_vector"] = list(vector) if vector is not None else None
        self._store.append(row)

    def delete_many(self, where):
        target, value = where.target, where.value
        self._store[:] = [r for r in self._store if r.get(target) != value]


class _FakeQuery:
    def __init__(self, store: list[dict]):
        self._store = store

    def fetch_objects(self, filters=None, limit=1, include_vector=False):
        target, value = (filters.target, filters.value) if filters is not None else (None, None)
        matches = [r for r in self._store if target is None or r.get(target) == value][:limit]
        objects = [
            _FakeObj(properties={k: v for k, v in r.items() if k != "_vector"}, vector=r.get("_vector"))
            for r in matches
        ]
        return types.SimpleNamespace(objects=objects)

    def near_vector(self, near_vector, limit=10, filters=None, return_metadata=None):
        target, value = (filters.target, filters.value) if filters is not None else (None, None)
        candidates = [r for r in self._store if target is None or r.get(target) == value]
        scored = sorted(candidates, key=lambda r: _cosine_distance(near_vector, r["_vector"]))
        scored = scored[:limit]
        objects = [
            _FakeObj(
                properties={k: v for k, v in r.items() if k != "_vector"},
                metadata=types.SimpleNamespace(distance=_cosine_distance(near_vector, r["_vector"])),
            )
            for r in scored
        ]
        return types.SimpleNamespace(objects=objects)


class _FakeCollection:
    def __init__(self, store: list[dict]):
        self.data = _FakeData(store)
        self.query = _FakeQuery(store)


class _FakeCollectionsManager:
    def __init__(self):
        self._existing: set[str] = set()
        self._stores: dict[str, list[dict]] = {}

    def exists(self, name: str) -> bool:
        return name in self._existing

    def create(self, name: str, **kwargs):
        self._existing.add(name)
        self._stores.setdefault(name, [])

    def get(self, name: str) -> _FakeCollection:
        self._stores.setdefault(name, [])
        return _FakeCollection(self._stores[name])


class FakeWeaviateClient:
    """Just enough of the weaviate-client v4 surface to round-trip the
    `ClothingItemVector` methods — no network, no real Weaviate instance."""

    def __init__(self):
        self.collections = _FakeCollectionsManager()

    def is_ready(self) -> bool:
        return True

    def close(self) -> None:
        pass


@pytest.fixture
def service() -> WeaviateEmbeddingsService:
    svc = WeaviateEmbeddingsService.__new__(WeaviateEmbeddingsService)
    svc.client = FakeWeaviateClient()
    svc.collection_name = "ClothingItem"
    return svc


def _unit(vec: list[float]) -> list[float]:
    arr = np.asarray(vec, dtype=float)
    return (arr / np.linalg.norm(arr)).tolist()


def test_init_vector_schema_creates_collection(service):
    assert service.client.collections.exists(VECTOR_COLLECTION_NAME) is False
    assert service.init_vector_schema() is True
    assert service.client.collections.exists(VECTOR_COLLECTION_NAME) is True


def test_init_vector_schema_is_idempotent(service):
    assert service.init_vector_schema() is True
    assert service.init_vector_schema() is True  # second call is a no-op, still True


def test_upsert_and_get_vector_round_trip(service):
    service.init_vector_schema()
    item_id = uuid.uuid4()
    user_id = uuid.uuid4()
    vector = _unit([1.0, 2.0, 3.0])

    assert service.upsert_vector(item_id, user_id, "shirt", vector) is True

    fetched = service.get_vector(item_id)
    assert fetched is not None
    assert np.allclose(fetched, vector)


def test_upsert_vector_is_idempotent_delete_then_insert(service):
    service.init_vector_schema()
    item_id = uuid.uuid4()
    user_id = uuid.uuid4()

    service.upsert_vector(item_id, user_id, "shirt", _unit([1.0, 0.0, 0.0]))
    service.upsert_vector(item_id, user_id, "jeans", _unit([0.0, 1.0, 0.0]))

    # Only one row should remain for this item_id (delete-then-insert, not append).
    store = service.client.collections._stores[VECTOR_COLLECTION_NAME]
    matching = [r for r in store if r["itemId"] == str(item_id)]
    assert len(matching) == 1
    assert matching[0]["category"] == "jeans"


def test_get_vector_returns_none_when_absent(service):
    service.init_vector_schema()
    assert service.get_vector(uuid.uuid4()) is None


def test_delete_vector_removes_row(service):
    service.init_vector_schema()
    item_id = uuid.uuid4()
    user_id = uuid.uuid4()
    service.upsert_vector(item_id, user_id, "shirt", _unit([1.0, 0.0, 0.0]))

    assert service.delete_vector(item_id) is True
    assert service.get_vector(item_id) is None


def test_query_neighbors_self_query_similarity_is_approximately_one(service):
    """Distance -> similarity: `sim = 1 - distance` for COSINE; a self-query
    (same vector, item not excluded) must return similarity ~= 1.0."""
    service.init_vector_schema()
    item_id = uuid.uuid4()
    user_id = uuid.uuid4()
    vector = _unit([1.0, 2.0, 3.0])
    service.upsert_vector(item_id, user_id, "shirt", vector)

    results = service.query_neighbors(vector=vector, user_id=user_id, k=5, min_sim=0.0)

    assert len(results) == 1
    neighbor_id, similarity = results[0]
    assert neighbor_id == item_id
    assert similarity == pytest.approx(1.0, abs=1e-6)


def test_query_neighbors_excludes_self_and_respects_min_sim(service):
    service.init_vector_schema()
    user_id = uuid.uuid4()
    anchor_id = uuid.uuid4()
    close_id = uuid.uuid4()
    far_id = uuid.uuid4()

    anchor_vector = _unit([1.0, 0.0])
    close_vector = _unit([0.99, 0.01])  # very similar, sim close to 1
    far_vector = _unit([0.0, 1.0])  # orthogonal, sim ~= 0

    service.upsert_vector(anchor_id, user_id, "shirt", anchor_vector)
    service.upsert_vector(close_id, user_id, "shirt", close_vector)
    service.upsert_vector(far_id, user_id, "shirt", far_vector)

    results = service.query_neighbors(
        vector=anchor_vector, user_id=user_id, k=5, min_sim=0.85, exclude_item_id=anchor_id
    )

    result_ids = {r[0] for r in results}
    assert anchor_id not in result_ids
    assert close_id in result_ids
    assert far_id not in result_ids


def test_query_neighbors_scopes_to_user(service):
    service.init_vector_schema()
    user_a = uuid.uuid4()
    user_b = uuid.uuid4()
    item_a = uuid.uuid4()
    item_b = uuid.uuid4()
    vector = _unit([1.0, 1.0])

    service.upsert_vector(item_a, user_a, "shirt", vector)
    service.upsert_vector(item_b, user_b, "shirt", vector)

    results = service.query_neighbors(vector=vector, user_id=user_a, k=5, min_sim=0.0)
    result_ids = {r[0] for r in results}
    assert item_a in result_ids
    assert item_b not in result_ids


def test_all_vector_methods_soft_fail_when_not_connected():
    svc = WeaviateEmbeddingsService.__new__(WeaviateEmbeddingsService)
    svc.client = None
    svc.collection_name = "ClothingItem"

    assert svc.init_vector_schema() is False
    assert svc.upsert_vector(uuid.uuid4(), uuid.uuid4(), "shirt", [1.0]) is False
    assert svc.get_vector(uuid.uuid4()) is None
    assert svc.query_neighbors([1.0], uuid.uuid4()) == []
    assert svc.delete_vector(uuid.uuid4()) is False
