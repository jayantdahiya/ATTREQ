"""Pure-function tests for wardrobe stats / forgotten-items computation.

These test the pure compute functions directly (not the DB-backed wrappers)
because `tests/conftest.py`'s `DummyDB` is a no-op mock — correctness can
only be verified by hand-computing expected values against plain in-memory
ORM objects, never instantiated against a real session.
"""

from __future__ import annotations

import uuid
from datetime import date, timedelta

from attreq_api.models.wardrobe_photo import WardrobeItemPhoto
from attreq_api.services.recommendation.algorithm import score_pair
from attreq_api.services.stats.wardrobe_stats import (
    compute_forgotten_items,
    compute_wardrobe_stats,
    pick_best_partner,
)
from tests.conftest import build_outfit, build_wardrobe_item

TODAY = date(2026, 7, 22)


def _items_and_outfits(user_id: uuid.UUID):
    """Build a 6-item / 4-outfit fixture with hand-computable stats.

    Wear history (derived from worn outfits only):
      - shirt (Nike, $50):   worn in outfit1 (today-10) and outfit2 (today-5) -> wear_count=2, last_worn=today-5
      - jeans (Levis, $80):  worn in outfit1 (today-10)                       -> wear_count=1, last_worn=today-10
      - jacket (Unbranded, $120): worn as accessory in outfit2 (today-5)      -> wear_count=1, last_worn=today-5
      - dress (Nike, no price): worn in outfit3 (today-40)                    -> wear_count=1, last_worn=today-40
      - shoes (Unbranded, $40): never worn                                    -> wear_count=0
      - hat (Levis, no price): never worn                                     -> wear_count=0
    outfit4 has worn_date=None and must be ignored entirely.
    """
    shirt = build_wardrobe_item(
        user_id=user_id,
        category="shirt",
        color_primary="blue",
        brand="Nike",
        purchase_price=50.00,
    )
    jeans = build_wardrobe_item(
        user_id=user_id,
        category="jeans",
        color_primary="black",
        brand="Levis",
        purchase_price=80.00,
    )
    jacket = build_wardrobe_item(
        user_id=user_id,
        category="jacket",
        color_primary="red",
        brand=None,
        purchase_price=120.00,
    )
    dress = build_wardrobe_item(
        user_id=user_id,
        category="dress",
        color_primary="green",
        brand="Nike",
        purchase_price=None,
    )
    shoes = build_wardrobe_item(
        user_id=user_id,
        category="shoes",
        color_primary="white",
        brand=None,
        purchase_price=40.00,
    )
    hat = build_wardrobe_item(
        user_id=user_id,
        category="hat",
        color_primary="yellow",
        brand="Levis",
        purchase_price=None,
    )
    items = [shirt, jeans, jacket, dress, shoes, hat]

    outfit1 = build_outfit(
        user_id=user_id,
        top_item_id=shirt.id,
        bottom_item_id=jeans.id,
        worn_date=TODAY - timedelta(days=10),
    )
    outfit2 = build_outfit(
        user_id=user_id,
        top_item_id=shirt.id,
        bottom_item_id=None,
        accessory_ids=[jacket.id],
        worn_date=TODAY - timedelta(days=5),
    )
    outfit3 = build_outfit(
        user_id=user_id,
        top_item_id=dress.id,
        bottom_item_id=None,
        worn_date=TODAY - timedelta(days=40),
    )
    outfit4_unworn = build_outfit(
        user_id=user_id,
        top_item_id=shoes.id,
        bottom_item_id=None,
        worn_date=None,
    )
    outfits = [outfit1, outfit2, outfit3, outfit4_unworn]

    return items, outfits, {
        "shirt": shirt,
        "jeans": jeans,
        "jacket": jacket,
        "dress": dress,
        "shoes": shoes,
        "hat": hat,
    }


def test_compute_wardrobe_stats_hand_computed_values():
    user_id = uuid.uuid4()
    items, outfits, by_name = _items_and_outfits(user_id)

    result = compute_wardrobe_stats(items, outfits, today=TODAY)

    assert result["total_active_items"] == 6

    by_category = {row["category"]: row["count"] for row in result["by_category"]}
    assert by_category == {
        "shirt": 1,
        "jeans": 1,
        "jacket": 1,
        "dress": 1,
        "shoes": 1,
        "hat": 1,
    }

    by_color_family = {row["family"]: row["count"] for row in result["by_color_family"]}
    assert by_color_family == {"cool": 2, "neutral": 2, "warm": 2}

    by_brand = {row["brand"]: row["count"] for row in result["by_brand"]}
    assert by_brand == {"Nike": 2, "Levis": 2, "Unbranded": 2}

    # closet_value sums only items with a price set: 50 + 80 + 120 + 40
    assert result["closet_value"] == 290.0
    assert result["items_missing_price"] == 2  # dress, hat

    assert result["never_worn_count"] == 2  # shoes, hat
    assert result["never_worn_percent"] == round(2 / 6 * 100, 1)

    assert result["worn_last_30_days"] == 3  # shirt, jeans, jacket (not dress @ 40d)
    assert result["worn_last_90_days"] == 4  # shirt, jeans, jacket, dress

    most_worn_ids = [entry["item_id"] for entry in result["most_worn"]]
    assert most_worn_ids[0] == str(by_name["shirt"].id)  # wear_count=2, strictly most worn
    assert set(most_worn_ids) == {
        str(by_name["shirt"].id),
        str(by_name["jeans"].id),
        str(by_name["jacket"].id),
        str(by_name["dress"].id),
    }

    least_worn_ids = [entry["item_id"] for entry in result["least_worn"]]
    # least_worn is active items with wear_count >= 1, ascending — zero-wear
    # items (shoes, hat) must NOT appear here (they only live in never_worn_*).
    assert str(by_name["shoes"].id) not in least_worn_ids
    assert str(by_name["hat"].id) not in least_worn_ids
    assert least_worn_ids[-1] == str(by_name["shirt"].id)  # highest wear_count sorts last


def test_cost_per_wear_never_worn_is_null():
    user_id = uuid.uuid4()
    items, outfits, by_name = _items_and_outfits(user_id)
    result = compute_wardrobe_stats(items, outfits, today=TODAY)

    cpw_by_id = {row["item_id"]: row for row in result["cost_per_wear"]}

    # shoes: price set, never worn -> cost_per_wear is None (not omitted)
    shoes_entry = cpw_by_id[str(by_name["shoes"].id)]
    assert shoes_entry["purchase_price"] == 40.0
    assert shoes_entry["cost_per_wear"] is None


def test_cost_per_wear_missing_price_is_omitted_from_list():
    user_id = uuid.uuid4()
    items, outfits, by_name = _items_and_outfits(user_id)
    result = compute_wardrobe_stats(items, outfits, today=TODAY)

    cpw_item_ids = {row["item_id"] for row in result["cost_per_wear"]}
    # dress and hat have no purchase_price -> omitted from the CPW list,
    # counted only in items_missing_price
    assert str(by_name["dress"].id) not in cpw_item_ids
    assert str(by_name["hat"].id) not in cpw_item_ids
    assert result["items_missing_price"] == 2


def test_cost_per_wear_correct_division_when_both_set():
    user_id = uuid.uuid4()
    items, outfits, by_name = _items_and_outfits(user_id)
    result = compute_wardrobe_stats(items, outfits, today=TODAY)

    cpw_by_id = {row["item_id"]: row for row in result["cost_per_wear"]}

    shirt_entry = cpw_by_id[str(by_name["shirt"].id)]
    assert shirt_entry["wear_count"] == 2
    assert shirt_entry["cost_per_wear"] == round(50.00 / 2, 2)

    jeans_entry = cpw_by_id[str(by_name["jeans"].id)]
    assert jeans_entry["wear_count"] == 1
    assert jeans_entry["cost_per_wear"] == round(80.00 / 1, 2)


def test_multi_photo_item_counted_once():
    """An item with N photos must count once in by_category/total_active_items."""
    user_id = uuid.uuid4()
    item = build_wardrobe_item(user_id=user_id, category="shirt", color_primary="blue")
    item.photos = [
        WardrobeItemPhoto(id=uuid.uuid4(), item_id=item.id, original_image_url=f"/p{i}.jpg")
        for i in range(3)
    ]

    result = compute_wardrobe_stats([item], [], today=TODAY)

    assert result["total_active_items"] == 1
    assert result["by_category"] == [{"category": "shirt", "count": 1}]


def test_forgotten_items_60_day_inclusive_boundary():
    user_id = uuid.uuid4()
    item_60 = build_wardrobe_item(user_id=user_id, category="shirt")
    item_59 = build_wardrobe_item(user_id=user_id, category="jeans")

    outfit_60 = build_outfit(
        user_id=user_id,
        top_item_id=item_60.id,
        bottom_item_id=None,
        worn_date=TODAY - timedelta(days=60),
    )
    outfit_59 = build_outfit(
        user_id=user_id,
        top_item_id=item_59.id,
        bottom_item_id=None,
        worn_date=TODAY - timedelta(days=59),
    )

    forgotten = compute_forgotten_items(
        [item_60, item_59], [outfit_60, outfit_59], today=TODAY, days_threshold=60
    )
    forgotten_ids = {entry["item_id"] for entry in forgotten}

    assert str(item_60.id) in forgotten_ids  # exactly 60 days -> forgotten (inclusive)
    assert str(item_59.id) not in forgotten_ids  # 59 days -> not yet forgotten


def test_forgotten_items_never_worn_is_forgotten():
    user_id = uuid.uuid4()
    never_worn = build_wardrobe_item(user_id=user_id, category="hat")

    forgotten = compute_forgotten_items([never_worn], [], today=TODAY, days_threshold=60)

    assert len(forgotten) == 1
    assert forgotten[0]["item_id"] == str(never_worn.id)
    assert forgotten[0]["wear_count"] == 0
    assert forgotten[0]["last_worn"] is None
    assert forgotten[0]["days_since_worn"] is None


def test_pick_best_partner_prefers_opposite_category_role():
    user_id = uuid.uuid4()
    shirt = build_wardrobe_item(
        user_id=user_id, category="shirt", color_primary="blue", pattern="solid"
    )
    jeans = build_wardrobe_item(
        user_id=user_id, category="jeans", color_primary="black", pattern="solid"
    )
    hat = build_wardrobe_item(
        user_id=user_id, category="hat", color_primary="yellow", pattern="solid"
    )

    result = pick_best_partner(shirt, [jeans, hat])

    assert result is not None
    best_item, score = result
    assert best_item.id == jeans.id  # opposite role (bottom) preferred over "other" (hat)
    assert score == score_pair(shirt, jeans)


def test_pick_best_partner_empty_candidates_returns_none():
    user_id = uuid.uuid4()
    shirt = build_wardrobe_item(user_id=user_id, category="shirt")

    assert pick_best_partner(shirt, []) is None

    # Only same-category candidates -> also None (filtered out)
    another_shirt = build_wardrobe_item(user_id=user_id, category="shirt")
    assert pick_best_partner(shirt, [another_shirt]) is None
