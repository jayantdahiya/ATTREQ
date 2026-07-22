"""Scoring functions for Style DNA integration into recommendation algorithm."""

import uuid
from datetime import datetime
from typing import Any

import numpy as np
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from attreq_api.models.user import User


def calculate_style_dna_score(outfit_items: list, style_dna: dict[str, Any]) -> float:
    """Score an outfit against the user's Style DNA profile.

    Subcomponents:
    - Aesthetic alignment (30%)
    - Color palette match (30%)
    - Silhouette match (20%)
    - Pattern match (20%)

    Returns float 0.0–1.0.
    """
    if not style_dna or not outfit_items:
        return 0.5

    scores = []

    # Color palette match
    palette = style_dna.get("color_palette", {})
    dominant = [c.lower() for c in palette.get("dominant", [])]
    accent = [c.lower() for c in palette.get("accent", [])]
    avoids = [c.lower() for c in palette.get("avoids", [])]

    color_hits = 0
    color_total = 0
    for item in outfit_items:
        primary = (getattr(item, "color_primary", None) or "").lower()
        secondary = (getattr(item, "color_secondary", None) or "").lower()
        for color in [primary, secondary]:
            if not color:
                continue
            color_total += 1
            if color in avoids:
                color_hits -= 0.5
            elif color in dominant:
                color_hits += 1.0
            elif color in accent:
                color_hits += 0.6
            else:
                color_hits += 0.3

    color_score = max(0.0, min(1.0, color_hits / color_total)) if color_total else 0.5
    scores.append((color_score, 0.30))

    # Silhouette match
    silhouette_confidence = style_dna.get("silhouette", {}).get("confidence", 0.5)
    # Silhouette is hard to check from wardrobe item attributes alone — use confidence as proxy
    silhouette_score = 0.5 + (silhouette_confidence - 0.5) * 0.4
    scores.append((silhouette_score, 0.20))

    # Pattern match
    preferred_patterns = [p.lower() for p in style_dna.get("patterns", {}).get("preferred", [])]
    pattern_confidence = style_dna.get("patterns", {}).get("confidence", 0.5)
    if preferred_patterns:
        pattern_hits = 0
        pattern_total = len(outfit_items)
        for item in outfit_items:
            item_pattern = (getattr(item, "pattern", None) or "").lower()
            if item_pattern in preferred_patterns:
                pattern_hits += 1
            elif item_pattern == "solid":
                pattern_hits += 0.5  # solid is neutral
        pattern_score = pattern_hits / pattern_total if pattern_total else 0.5
    else:
        pattern_score = 0.5 * pattern_confidence + 0.5
    scores.append((pattern_score, 0.20))

    # Aesthetic alignment — use formality bias as a proxy for overall alignment
    formality_bias = style_dna.get("formality_bias", {})
    target_formality = formality_bias.get("level", 1.5)
    formality_confidence = formality_bias.get("confidence", 0.5)

    item_formalities = []
    for item in outfit_items:
        item_occasions = getattr(item, "occasion", None) or []
        if "formal" in item_occasions:
            item_formalities.append(3)
        elif "business" in item_occasions or "work" in item_occasions:
            item_formalities.append(2)
        elif "athletic" in item_occasions:
            item_formalities.append(0)
        else:
            item_formalities.append(1)

    if item_formalities:
        avg_formality = sum(item_formalities) / len(item_formalities)
        formality_diff = abs(avg_formality - target_formality) / 3.0  # normalise to 0–1
        aesthetic_score = max(0.0, 1.0 - formality_diff) * (0.5 + formality_confidence * 0.5)
    else:
        aesthetic_score = 0.5
    scores.append((aesthetic_score, 0.30))

    total = sum(score * weight for score, weight in scores)
    return round(max(0.0, min(1.0, total)), 4)


def calculate_behaviour_score(outfit_items: list, behaviour_weights: dict[str, Any]) -> float:
    """Score an outfit against learned behaviour weights from feedback history.

    behaviour_weights schema (built up over time):
    {
      "category_likes": {"shirt": 0.8, "jeans": 0.9},
      "color_likes": {"navy": 0.9, "white": 0.7},
      "pattern_likes": {"solid": 0.8}
    }

    Returns float 0.0–1.0.
    """
    if not behaviour_weights or not outfit_items:
        return 0.5

    category_likes = behaviour_weights.get("category_likes", {})
    color_likes = behaviour_weights.get("color_likes", {})
    pattern_likes = behaviour_weights.get("pattern_likes", {})

    if not (category_likes or color_likes or pattern_likes):
        return 0.5

    total_score = 0.0
    total_weight = 0

    for item in outfit_items:
        category = (getattr(item, "category", None) or "").lower()
        color = (getattr(item, "color_primary", None) or "").lower()
        pattern = (getattr(item, "pattern", None) or "").lower()

        if category and category in category_likes:
            total_score += category_likes[category]
            total_weight += 1

        if color and color in color_likes:
            total_score += color_likes[color]
            total_weight += 1

        if pattern and pattern in pattern_likes:
            total_score += pattern_likes[pattern]
            total_weight += 1

    return round(total_score / total_weight, 4) if total_weight else 0.5


async def update_style_dna_centroid(
    db: AsyncSession,
    user_id: uuid.UUID,
    item_vector: list[float] | None,
    signal: str,
) -> bool:
    """Online update of the user's FashionCLIP style centroid (RI-6).

    `signal` must be `"liked"` or `"worn"` — POSITIVE ONLY. Dislikes are
    handled entirely by thumbs-propagation
    (`services/recommendation/similarity.py::compute_propagation_penalties`),
    never by pulling the centroid away from a disliked item.

    Storage: `users.style_dna_centroid` JSONB, shape
    `{"vector": [512 floats, UNNORMALIZED running mean], "n_items": int,
    "updated_at": iso str}`. Math: `new_mean = (old_mean * n + item_vector) /
    (n + 1)`. The vector is stored UNNORMALIZED and normalized only at
    scoring time (`services/recommendation/similarity.py::centroid_score`) —
    normalizing and re-storing after every update would corrupt the
    incremental mean (each subsequent update would be averaging a
    unit-length vector against a fresh raw item vector, which is not the
    same recurrence as a true running mean).

    Returns True only when the centroid was actually mutated and committed;
    False on every early-return (bad signal, missing vector, missing user).
    """
    if item_vector is None or signal not in ("liked", "worn"):
        return False

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        return False

    existing = user.style_dna_centroid or {}
    old_vector = existing.get("vector")
    n_items = existing.get("n_items", 0) or 0

    item_arr = np.asarray(item_vector, dtype=float)
    if old_vector and n_items > 0:
        old_arr = np.asarray(old_vector, dtype=float)
        new_arr = (old_arr * n_items + item_arr) / (n_items + 1)
    else:
        new_arr = item_arr

    new_centroid = {
        "vector": new_arr.tolist(),
        "n_items": n_items + 1,
        "updated_at": datetime.utcnow().isoformat(),
    }

    await db.execute(
        update(User).where(User.id == user_id).values(style_dna_centroid=new_centroid)
    )
    await db.commit()

    return True
