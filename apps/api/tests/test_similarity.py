"""Tests for services/recommendation/similarity.py (RI-6).

`centroid_score` is pure numpy math — no mocking needed. `neighbors`/
`compute_propagation_penalties` go through `weaviate_service`
(services/ai/embeddings.py) and `feedback_source` (real-DB), so those are
mocked/monkeypatched rather than hitting a live Weaviate instance.
"""

from __future__ import annotations

import uuid

import numpy as np
import pytest

from attreq_api.services.recommendation import similarity


def _unit(vec: list[float]) -> list[float]:
    arr = np.asarray(vec, dtype=float)
    return (arr / np.linalg.norm(arr)).tolist()


# ---------------------------------------------------------------------------
# centroid_score
# ---------------------------------------------------------------------------


def test_centroid_score_neutral_when_item_vector_missing():
    assert similarity.centroid_score(None, _unit([1.0, 0.0])) == 0.5


def test_centroid_score_neutral_when_centroid_missing():
    assert similarity.centroid_score(_unit([1.0, 0.0]), None) == 0.5


def test_centroid_score_neutral_when_both_missing():
    assert similarity.centroid_score(None, None) == 0.5


def test_centroid_score_identical_vectors_scores_near_one():
    vec = _unit([1.0, 2.0, 3.0])
    assert similarity.centroid_score(vec, vec) == pytest.approx(1.0, abs=1e-6)


def test_centroid_score_opposite_vectors_scores_near_zero():
    vec = _unit([1.0, 0.0])
    opposite = _unit([-1.0, 0.0])
    assert similarity.centroid_score(vec, opposite) == pytest.approx(0.0, abs=1e-6)


def test_centroid_score_orthogonal_vectors_scores_near_half():
    a = _unit([1.0, 0.0])
    b = _unit([0.0, 1.0])
    assert similarity.centroid_score(a, b) == pytest.approx(0.5, abs=1e-6)


def test_centroid_score_hand_computed_cosine():
    a = [1.0, 0.0]
    b = [1.0, 1.0]
    cos = 1.0 / (1.0 * (2**0.5))  # dot=1, |a|=1, |b|=sqrt(2)
    expected = round((cos + 1.0) / 2.0, 4)
    assert similarity.centroid_score(a, b) == expected


def test_centroid_score_accepts_unnormalized_input():
    """Centroid is stored UNNORMALIZED (running mean) — centroid_score must
    normalize both inputs itself, not assume pre-normalized vectors."""
    a = [3.0, 4.0]  # norm 5
    b = [6.0, 8.0]  # same direction, norm 10
    assert similarity.centroid_score(a, b) == pytest.approx(1.0, abs=1e-6)


# ---------------------------------------------------------------------------
# compute_propagation_penalties
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_compute_propagation_penalties_applies_dislike_and_like_adjustments(monkeypatch):
    user_id = uuid.uuid4()
    disliked_item = uuid.uuid4()
    liked_item = uuid.uuid4()
    neighbor_sim_1 = uuid.uuid4()
    neighbor_sim_09 = uuid.uuid4()
    neighbor_sim_07 = uuid.uuid4()  # excluded by min_sim in the real neighbors() call

    async def fake_get_recent_dislikes(db, uid, days=30):
        return [disliked_item]

    async def fake_get_recent_likes(db, uid, days=30):
        return [liked_item]

    async def fake_neighbors(item_id, uid, k=5, min_sim=0.85):
        if item_id == disliked_item:
            return [(neighbor_sim_1, 1.0), (neighbor_sim_09, 0.9)]
        if item_id == liked_item:
            return [(neighbor_sim_1, 1.0)]
        return []

    monkeypatch.setattr(
        "attreq_api.services.recommendation.feedback_source.get_recent_dislikes",
        fake_get_recent_dislikes,
    )
    monkeypatch.setattr(
        "attreq_api.services.recommendation.feedback_source.get_recent_likes",
        fake_get_recent_likes,
    )
    monkeypatch.setattr(similarity, "neighbors", fake_neighbors)

    penalties = await similarity.compute_propagation_penalties(db=None, user_id=user_id)

    # neighbor_sim_1 got both a dislike (-0.05*1.0) and a like (+0.025*1.0)
    # adjustment -> net -0.025.
    assert penalties[neighbor_sim_1] == pytest.approx(-0.025, abs=1e-6)
    # neighbor_sim_09 only got the dislike adjustment: -0.05 * 0.9 = -0.045.
    assert penalties[neighbor_sim_09] == pytest.approx(-0.045, abs=1e-6)
    assert neighbor_sim_07 not in penalties


@pytest.mark.asyncio
async def test_compute_propagation_penalties_clamps_stacked_dislikes(monkeypatch):
    user_id = uuid.uuid4()
    disliked_a = uuid.uuid4()
    disliked_b = uuid.uuid4()
    shared_neighbor = uuid.uuid4()

    async def fake_get_recent_dislikes(db, uid, days=30):
        return [disliked_a, disliked_b]

    async def fake_get_recent_likes(db, uid, days=30):
        return []

    async def fake_neighbors(item_id, uid, k=5, min_sim=0.85):
        # Both disliked items are near the same neighbor at sim=1.0 each,
        # which alone would total -0.10 without the clamp.
        return [(shared_neighbor, 1.0)]

    monkeypatch.setattr(
        "attreq_api.services.recommendation.feedback_source.get_recent_dislikes",
        fake_get_recent_dislikes,
    )
    monkeypatch.setattr(
        "attreq_api.services.recommendation.feedback_source.get_recent_likes",
        fake_get_recent_likes,
    )
    monkeypatch.setattr(similarity, "neighbors", fake_neighbors)

    penalties = await similarity.compute_propagation_penalties(db=None, user_id=user_id)

    assert penalties[shared_neighbor] == pytest.approx(-similarity.MAX_PROPAGATION_ADJUSTMENT, abs=1e-6)


@pytest.mark.asyncio
async def test_compute_propagation_penalties_clamps_stacked_likes(monkeypatch):
    user_id = uuid.uuid4()
    liked_a = uuid.uuid4()
    liked_b = uuid.uuid4()
    liked_c = uuid.uuid4()
    shared_neighbor = uuid.uuid4()

    async def fake_get_recent_dislikes(db, uid, days=30):
        return []

    async def fake_get_recent_likes(db, uid, days=30):
        return [liked_a, liked_b, liked_c]

    async def fake_neighbors(item_id, uid, k=5, min_sim=0.85):
        # 3 likes at sim=1.0 -> 3 * 0.025 = 0.075 without the clamp.
        return [(shared_neighbor, 1.0)]

    monkeypatch.setattr(
        "attreq_api.services.recommendation.feedback_source.get_recent_dislikes",
        fake_get_recent_dislikes,
    )
    monkeypatch.setattr(
        "attreq_api.services.recommendation.feedback_source.get_recent_likes",
        fake_get_recent_likes,
    )
    monkeypatch.setattr(similarity, "neighbors", fake_neighbors)

    penalties = await similarity.compute_propagation_penalties(db=None, user_id=user_id)

    assert penalties[shared_neighbor] == pytest.approx(similarity.MAX_PROPAGATION_ADJUSTMENT, abs=1e-6)


@pytest.mark.asyncio
async def test_compute_propagation_penalties_empty_when_no_signal(monkeypatch):
    async def fake_empty(db, uid, days=30):
        return []

    monkeypatch.setattr(
        "attreq_api.services.recommendation.feedback_source.get_recent_dislikes", fake_empty
    )
    monkeypatch.setattr(
        "attreq_api.services.recommendation.feedback_source.get_recent_likes", fake_empty
    )

    penalties = await similarity.compute_propagation_penalties(db=None, user_id=uuid.uuid4())

    assert penalties == {}


@pytest.mark.asyncio
async def test_neighbors_returns_empty_when_item_never_embedded(monkeypatch):
    monkeypatch.setattr(
        "attreq_api.services.ai.embeddings.weaviate_service.get_vector", lambda item_id: None
    )
    result = await similarity.neighbors(uuid.uuid4(), uuid.uuid4())
    assert result == []


@pytest.mark.asyncio
async def test_neighbors_soft_fails_on_exception(monkeypatch):
    def _raise(item_id):
        raise RuntimeError("weaviate down")

    monkeypatch.setattr("attreq_api.services.ai.embeddings.weaviate_service.get_vector", _raise)
    result = await similarity.neighbors(uuid.uuid4(), uuid.uuid4())
    assert result == []
