"""Vector-similarity primitives for RI-6: FashionCLIP centroid scoring +
thumbs-propagation.

All heavy lifting (torch/model inference) lives in `services/ai/
fashion_embeddings.py`; this module only does numpy-level cosine math plus
Weaviate reads via `asyncio.to_thread` (the weaviate-client v4 sync client is
not awaitable). Every function here is soft-fail: a missing vector, a
disconnected Weaviate, or any other error degrades to a neutral default
rather than raising — recommendation generation must never break because of
this milestone.
"""

import asyncio
import logging
from uuid import UUID

import numpy as np
from sqlalchemy.ext.asyncio import AsyncSession

from attreq_api.services.ai.embeddings import weaviate_service

logger = logging.getLogger(__name__)

DEFAULT_NEIGHBOR_K = 5
DEFAULT_MIN_SIM = 0.85

# Half-strength like bonus vs. dislike penalty per neighbor (finalized plan §4).
DISLIKE_ADJUSTMENT_PER_NEIGHBOR = -0.05
LIKE_ADJUSTMENT_PER_NEIGHBOR = 0.025
MAX_PROPAGATION_ADJUSTMENT = 0.05


async def neighbors(
    item_id: UUID,
    user_id: UUID,
    k: int = DEFAULT_NEIGHBOR_K,
    min_sim: float = DEFAULT_MIN_SIM,
) -> list[tuple[UUID, float]]:
    """Nearest-neighbor items (FashionCLIP cosine similarity) for `item_id`.

    Wraps `get_vector` -> `query_neighbors` for the common case where only an
    item id is known. Soft-fails to `[]` on any miss (item never embedded,
    Weaviate down, etc.) — callers must treat an empty list as "no signal".
    """

    def _lookup() -> list[tuple[UUID, float]]:
        vector = weaviate_service.get_vector(item_id)
        if vector is None:
            return []
        return weaviate_service.query_neighbors(
            vector=vector, user_id=user_id, k=k, min_sim=min_sim, exclude_item_id=item_id
        )

    try:
        return await asyncio.to_thread(_lookup)
    except Exception as e:
        logger.warning(f"neighbors() lookup failed for item {item_id}: {e}")
        return []


def centroid_score(
    item_vector: list[float] | None, user_centroid: list[float] | None
) -> float:
    """Cosine similarity between an item vector and the user's style centroid,
    mapped from [-1, 1] to [0, 1]. Neutral `0.5` when either input is
    missing — matches the neutral-default convention in
    `services/style_dna/scoring.py`.

    The centroid is stored UNNORMALIZED (a running mean — see
    `services/style_dna/scoring.py::update_style_dna_centroid`); both inputs
    are L2-normalized here, at scoring time, not at write time.
    """
    if not item_vector or not user_centroid:
        return 0.5

    v = np.asarray(item_vector, dtype=float)
    c = np.asarray(user_centroid, dtype=float)
    v_norm = np.linalg.norm(v)
    c_norm = np.linalg.norm(c)
    if v_norm == 0 or c_norm == 0:
        return 0.5

    cos = float(np.dot(v, c) / (v_norm * c_norm))
    cos = max(-1.0, min(1.0, cos))
    return round((cos + 1.0) / 2.0, 4)


async def compute_propagation_penalties(
    db: AsyncSession, user_id: UUID, days: int = 30
) -> dict[UUID, float]:
    """Thumbs-propagation: items visually near recent dislikes get a small
    score penalty; items near recent likes get a smaller bonus (half
    strength). Computed ONCE per `generate_daily_outfits()` call — not per
    candidate pair, not Redis-cached this milestone (finalized plan §4).

    Per-neighbor adjustment is `ADJUSTMENT_PER_NEIGHBOR * similarity`;
    adjustments to the same neighbor from multiple disliked/liked items
    accumulate, then the FINAL per-item total is clamped to
    `[-MAX_PROPAGATION_ADJUSTMENT, +MAX_PROPAGATION_ADJUSTMENT]`.
    """
    # Deferred import: avoids a cycle with feedback_source (which does not
    # import this module, but keeps the dependency direction explicit here).
    from attreq_api.services.recommendation.feedback_source import (
        get_recent_dislikes,
        get_recent_likes,
    )

    adjustments: dict[UUID, float] = {}

    try:
        disliked_items = await get_recent_dislikes(db, user_id, days=days)
    except Exception as e:
        logger.warning(f"compute_propagation_penalties: get_recent_dislikes failed: {e}")
        disliked_items = []

    for item_id in disliked_items:
        for neighbor_id, sim in await neighbors(item_id, user_id):
            adjustments[neighbor_id] = (
                adjustments.get(neighbor_id, 0.0) + DISLIKE_ADJUSTMENT_PER_NEIGHBOR * sim
            )

    try:
        liked_items = await get_recent_likes(db, user_id, days=days)
    except Exception as e:
        logger.warning(f"compute_propagation_penalties: get_recent_likes failed: {e}")
        liked_items = []

    for item_id in liked_items:
        for neighbor_id, sim in await neighbors(item_id, user_id):
            adjustments[neighbor_id] = (
                adjustments.get(neighbor_id, 0.0) + LIKE_ADJUSTMENT_PER_NEIGHBOR * sim
            )

    return {
        item_id: round(
            max(-MAX_PROPAGATION_ADJUSTMENT, min(MAX_PROPAGATION_ADJUSTMENT, adj)), 4
        )
        for item_id, adj in adjustments.items()
    }
