"""Cold-start content-similarity prior (RI-4).

Items with no wear/feedback history get scored with a small content-
similarity prior toward the user's most-worn items (same coarse category +
color) instead of a neutral default. Deliberately mutually exclusive with
the grey-inventory rediscovery bonus (`rotation.py`) — see
`composition.classify_grey_inventory_bonus`, the single dispatcher that
decides which of {cold_start, rediscovery, neither} applies to a given item,
so the two paths can never both fire for the same item.
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from datetime import date

    from attreq_api.models.wardrobe import WardrobeItem

COLD_START_MAX_BONUS = 0.08
COLD_START_RECENTLY_ADDED_DAYS = 14
WARM_ITEMS_TOP_N = 10


def _coarse_category(category: str | None) -> str:
    """Very coarse bucket so "t-shirt" and "tshirt" etc. still match — content
    similarity only needs a rough category match, not an exact string."""
    c = (category or "").strip().lower()
    return c


def is_recently_added(item: WardrobeItem, today: date, window_days: int = COLD_START_RECENTLY_ADDED_DAYS) -> bool:
    created = getattr(item, "created_at", None)
    if created is None:
        return False
    created_date = created.date() if isinstance(created, datetime) else created
    return (today - created_date).days <= window_days


def warm_items_for(items: list[WardrobeItem], top_n: int = WARM_ITEMS_TOP_N) -> list[WardrobeItem]:
    """Top-N items by `wear_count`, computed once per generation call."""
    return sorted(items, key=lambda i: (i.wear_count or 0), reverse=True)[:top_n]


def cold_start_prior(
    item: WardrobeItem,
    warm_items: list[WardrobeItem],
    *,
    has_prior_events: bool,
    is_recently_added: bool,
    max_bonus: float = COLD_START_MAX_BONUS,
) -> float:
    """Fires ONLY for genuinely-new items: `wear_count == 0` AND no prior
    `recommendation_events` AND recently added. Such items must NOT also
    receive the rediscovery bonus (enforced by the caller's dispatch, not
    here — this function has no knowledge of rediscovery at all).
    """
    if item.wear_count != 0 or has_prior_events or not is_recently_added:
        return 0.0

    same_cat_warm = [
        w for w in warm_items if _coarse_category(w.category) == _coarse_category(item.category)
    ]
    if not same_cat_warm:
        return 0.0

    matches = sum(
        1
        for w in same_cat_warm
        if (w.color_primary or "").lower() == (item.color_primary or "").lower()
    )
    return round(min(max_bonus, max_bonus * matches / len(same_cat_warm)), 4)
