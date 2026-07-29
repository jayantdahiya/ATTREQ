"""Wardrobe stats & forgotten-items computation.

Split into pure-compute functions (hand-testable against plain in-memory
objects) and thin async DB/cache wrappers, because `tests/conftest.py`'s
`DummyDB` is a no-op mock — exit-criteria correctness can only be verified
against pure functions, not against a mocked session.

Semantic note (RI-7 plan finding B): `wear_count`/`last_worn` computed here
come from scanning `Outfit.worn_date`, i.e. "number of distinct worn outfits
containing the item". This differs from the denormalized
`WardrobeItem.wear_count` column (which increments on every `mark_as_worn`,
including re-wearing the *same* outfit). The outfit-scan is the drift-free
source of truth for these stats; flag the definition to product before
shipping "cost per wear" copy broadly.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date, timedelta
from typing import TYPE_CHECKING, Any

from attreq_api.crud.outfit import outfit_crud
from attreq_api.crud.wardrobe import wardrobe_crud
from attreq_api.services.cache.redis_client import redis_cache
from attreq_api.services.recommendation.algorithm import category_role, score_pair
from attreq_api.services.recommendation.color_utils import color_family

if TYPE_CHECKING:
    from uuid import UUID

    from attreq_api.models.outfit import Outfit
    from attreq_api.models.wardrobe import WardrobeItem

logger = logging.getLogger(__name__)

# Practical cap for "fetch everything for stats" queries — no user realistically
# has more items/outfits than this, and it avoids adding a dedicated
# unpaginated CRUD method.
_STATS_FETCH_LIMIT = 10_000

WARDROBE_STATS_CACHE_TTL = 3600  # 1 hour
FORGOTTEN_ITEMS_CACHE_TTL = 3600  # 1 hour

DEFAULT_FORGOTTEN_DAYS_THRESHOLD = 60
_TOP_N = 5


@dataclass
class WearHistory:
    """Aggregated wear signal for a single item, derived from worn outfits."""

    wear_count: int = 0
    last_worn: date | None = None


def _build_wear_history(outfits: list[Outfit]) -> dict[UUID, WearHistory]:
    """Scan worn outfits and count each item once per worn outfit it appears in.

    This is "distinct worn outfits containing the item" — see module docstring
    for the semantic caveat vs. the denormalized `wear_count` column.
    """
    history: dict[UUID, WearHistory] = {}

    for outfit in outfits:
        if outfit.worn_date is None:
            continue

        item_ids: set[UUID] = set()
        if outfit.top_item_id:
            item_ids.add(outfit.top_item_id)
        if outfit.bottom_item_id:
            item_ids.add(outfit.bottom_item_id)
        if outfit.accessory_ids:
            item_ids.update(outfit.accessory_ids)

        for item_id in item_ids:
            wh = history.setdefault(item_id, WearHistory())
            wh.wear_count += 1
            if wh.last_worn is None or outfit.worn_date > wh.last_worn:
                wh.last_worn = outfit.worn_date

    return history


def _entry(item: WardrobeItem, wh: WearHistory | None) -> dict[str, Any]:
    return {
        "item_id": str(item.id),
        "category": item.category,
        "color_primary": item.color_primary,
        "thumbnail_url": item.thumbnail_url,
        "wear_count": wh.wear_count if wh else 0,
        "last_worn": (wh.last_worn if wh else None),
    }


def compute_wardrobe_stats(
    items: list[WardrobeItem], outfits: list[Outfit], today: date | None = None
) -> dict[str, Any]:
    """Pure computation of wardrobe stats from active items + all user outfits.

    `items` MUST already be filtered to active items — composition/value/CPW
    are "your current closet" numbers (archived items keep their outfit
    history but aren't in dashboard numbers). Never iterates `item.photos`,
    so an item with N photos counts once regardless of N.
    """
    today = today or date.today()
    wear_history = _build_wear_history(outfits)

    by_category: dict[str, int] = {}
    by_color_family: dict[str, int] = {}
    by_brand: dict[str, int] = {}

    closet_value = 0.0
    items_missing_price = 0
    never_worn_count = 0
    worn_last_30_days = 0
    worn_last_90_days = 0

    worn_candidates: list[tuple[WardrobeItem, WearHistory]] = []
    cost_per_wear_entries: list[dict[str, Any]] = []

    for item in items:
        category = item.category or "Unknown"
        by_category[category] = by_category.get(category, 0) + 1

        family = color_family(item.color_primary)
        by_color_family[family] = by_color_family.get(family, 0) + 1

        brand = item.brand or "Unbranded"
        by_brand[brand] = by_brand.get(brand, 0) + 1

        wh = wear_history.get(item.id)
        wear_count = wh.wear_count if wh else 0
        last_worn = wh.last_worn if wh else None

        if item.purchase_price is not None:
            closet_value += float(item.purchase_price)
        else:
            items_missing_price += 1

        if wear_count == 0:
            never_worn_count += 1
        else:
            worn_candidates.append((item, wh))  # type: ignore[arg-type]

        if last_worn is not None:
            days_since = (today - last_worn).days
            if days_since <= 30:
                worn_last_30_days += 1
            if days_since <= 90:
                worn_last_90_days += 1

        if item.purchase_price is not None:
            cost_per_wear = (
                round(float(item.purchase_price) / wear_count, 2) if wear_count >= 1 else None
            )
            cost_per_wear_entries.append(
                {
                    "item_id": str(item.id),
                    "category": item.category,
                    "color_primary": item.color_primary,
                    "thumbnail_url": item.thumbnail_url,
                    "purchase_price": float(item.purchase_price),
                    "wear_count": wear_count,
                    "cost_per_wear": cost_per_wear,
                }
            )

    total_active_items = len(items)
    never_worn_percent = (
        round(never_worn_count / total_active_items * 100, 1) if total_active_items > 0 else 0.0
    )

    most_worn_sorted = sorted(worn_candidates, key=lambda pair: pair[1].wear_count, reverse=True)
    least_worn_sorted = sorted(worn_candidates, key=lambda pair: pair[1].wear_count)

    most_worn = [_entry(item, wh) for item, wh in most_worn_sorted[:_TOP_N]]
    least_worn = [_entry(item, wh) for item, wh in least_worn_sorted[:_TOP_N]]

    return {
        "total_active_items": total_active_items,
        "by_category": [
            {"category": k, "count": v} for k, v in sorted(by_category.items(), key=lambda kv: -kv[1])
        ],
        "by_color_family": [
            {"family": k, "count": v}
            for k, v in sorted(by_color_family.items(), key=lambda kv: -kv[1])
        ],
        "by_brand": [
            {"brand": k, "count": v} for k, v in sorted(by_brand.items(), key=lambda kv: -kv[1])
        ],
        "closet_value": round(closet_value, 2),
        "items_missing_price": items_missing_price,
        "never_worn_count": never_worn_count,
        "never_worn_percent": never_worn_percent,
        "most_worn": most_worn,
        "least_worn": least_worn,
        "cost_per_wear": cost_per_wear_entries,
        "worn_last_30_days": worn_last_30_days,
        "worn_last_90_days": worn_last_90_days,
    }


def pick_best_partner(
    forgotten_item: WardrobeItem, candidates: list[WardrobeItem]
) -> tuple[WardrobeItem, float] | None:
    """Pick the best-scoring pairing candidate for a forgotten item.

    Categories are garment names, never "top"/"bottom" (RI-7 plan finding C),
    so this never relies on literal role strings as the primary signal:
    filters out same-category candidates, then prefers an opposite
    `category_role` (top<->bottom) as a soft tiebreak, falling back to any
    remaining candidate. Returns None (never raises) when there is nothing
    to pair with.
    """
    eligible = [c for c in candidates if c.category != forgotten_item.category]
    if not eligible:
        return None

    target_role = category_role(forgotten_item.category)
    opposite_role = {"top": "bottom", "bottom": "top"}.get(target_role)

    pool = eligible
    if opposite_role:
        opposite_candidates = [c for c in eligible if category_role(c.category) == opposite_role]
        if opposite_candidates:
            pool = opposite_candidates

    best = max(pool, key=lambda c: score_pair(forgotten_item, c))
    return best, score_pair(forgotten_item, best)


def compute_forgotten_items(
    items: list[WardrobeItem],
    outfits: list[Outfit],
    today: date | None = None,
    days_threshold: int = DEFAULT_FORGOTTEN_DAYS_THRESHOLD,
) -> list[dict[str, Any]]:
    """Pure computation of forgotten items: never worn, or not worn in N days.

    Boundary is inclusive: an item last worn exactly `days_threshold` days ago
    IS forgotten (`last_worn <= today - days_threshold`).
    """
    today = today or date.today()
    wear_history = _build_wear_history(outfits)
    cutoff = today - timedelta(days=days_threshold)

    forgotten: list[dict[str, Any]] = []

    for item in items:
        wh = wear_history.get(item.id)
        wear_count = wh.wear_count if wh else 0
        last_worn = wh.last_worn if wh else None

        is_forgotten = wear_count == 0 or (last_worn is not None and last_worn <= cutoff)
        if not is_forgotten:
            continue

        candidates = [c for c in items if c.id != item.id]
        partner_result = pick_best_partner(item, candidates)
        best_partner = None
        if partner_result is not None:
            partner_item, score = partner_result
            best_partner = {
                "item_id": str(partner_item.id),
                "category": partner_item.category,
                "color_primary": partner_item.color_primary,
                "thumbnail_url": partner_item.thumbnail_url,
                "score": score,
            }

        days_since_worn = (today - last_worn).days if last_worn is not None else None

        forgotten.append(
            {
                "item_id": str(item.id),
                "category": item.category,
                "color_primary": item.color_primary,
                "thumbnail_url": item.thumbnail_url,
                "wear_count": wear_count,
                "last_worn": last_worn,
                "days_since_worn": days_since_worn,
                "best_partner": best_partner,
            }
        )

    return forgotten


# ============================================================================
# Thin async DB + cache wrappers
# ============================================================================

WARDROBE_STATS_CACHE_KEY = "wardrobe_stats:{user_id}"
FORGOTTEN_ITEMS_CACHE_KEY = "forgotten_items:{user_id}"


async def get_wardrobe_stats(db: Any, user_id: UUID, force_refresh: bool = False) -> dict[str, Any]:
    """Fetch active items + all outfits, compute stats, cache the result."""
    cache_key = WARDROBE_STATS_CACHE_KEY.format(user_id=user_id)

    if not force_refresh:
        cached = await redis_cache.get(cache_key)
        if cached:
            cached["cached"] = True
            return cached

    items, _ = await wardrobe_crud.get_by_user(
        db=db, user_id=user_id, status="active", skip=0, limit=_STATS_FETCH_LIMIT
    )
    outfits, _ = await outfit_crud.get_by_user(
        db=db, user_id=user_id, skip=0, limit=_STATS_FETCH_LIMIT, load_items=False
    )

    result = compute_wardrobe_stats(items, outfits)
    result["generated_at"] = date.today().isoformat()
    result["cached"] = False

    await redis_cache.set(cache_key, result, ttl=WARDROBE_STATS_CACHE_TTL)

    return result


async def get_forgotten_items(
    db: Any,
    user_id: UUID,
    days_threshold: int = DEFAULT_FORGOTTEN_DAYS_THRESHOLD,
    force_refresh: bool = False,
) -> dict[str, Any]:
    """Fetch active items + all outfits, compute forgotten items, cache result."""
    cache_key = FORGOTTEN_ITEMS_CACHE_KEY.format(user_id=user_id)

    if not force_refresh:
        cached = await redis_cache.get(cache_key)
        if cached:
            cached["cached"] = True
            return cached

    items, _ = await wardrobe_crud.get_by_user(
        db=db, user_id=user_id, status="active", skip=0, limit=_STATS_FETCH_LIMIT
    )
    outfits, _ = await outfit_crud.get_by_user(
        db=db, user_id=user_id, skip=0, limit=_STATS_FETCH_LIMIT, load_items=False
    )

    forgotten_items = compute_forgotten_items(items, outfits, days_threshold=days_threshold)
    result = {
        "items": forgotten_items,
        "count": len(forgotten_items),
        "generated_at": date.today().isoformat(),
        "cached": False,
    }

    await redis_cache.set(cache_key, result, ttl=FORGOTTEN_ITEMS_CACHE_TTL)

    return result


async def invalidate_wardrobe_stats_cache(user_id: UUID) -> None:
    """Delete both stat caches for a user (call on any event that changes them)."""
    await redis_cache.delete(WARDROBE_STATS_CACHE_KEY.format(user_id=user_id))
    await redis_cache.delete(FORGOTTEN_ITEMS_CACHE_KEY.format(user_id=user_id))
