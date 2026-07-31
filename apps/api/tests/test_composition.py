"""Tests for services/recommendation/composition.py (RI-4).

All pure-function tests over in-memory `WardrobeItem` fixtures (via
`tests.conftest.build_wardrobe_item`) — no DB, matching the finalized plan's
pure-core refactor (composition/rotation/explanations need zero session).
"""

from __future__ import annotations

import uuid
from datetime import date, timedelta

from attreq_api.services.recommendation import composition as comp
from attreq_api.services.recommendation.rotation import RotationContext
from tests.conftest import build_wardrobe_item

USER_ID = uuid.uuid4()
TODAY = date(2026, 4, 20)


def _item(**overrides):
    return build_wardrobe_item(user_id=USER_ID, **overrides)


# ---------------------------------------------------------------------------
# plan_slots
# ---------------------------------------------------------------------------


def test_plan_slots_outerwear_gate_at_temp_boundary():
    pools = comp.WardrobePools(outerwear=[_item(category="jacket")])

    just_above = comp.plan_slots({"temp": 15.0, "condition": "Clear"}, "casual", pools)
    just_below = comp.plan_slots({"temp": 14.9, "condition": "Clear"}, "casual", pools)

    assert just_above.need_outerwear is False
    assert just_below.need_outerwear is True


def test_plan_slots_outerwear_gate_on_rain_regardless_of_temp():
    pools = comp.WardrobePools(outerwear=[_item(category="coat")])
    plan = comp.plan_slots({"temp": 24.0, "condition": "Rain"}, "casual", pools)
    assert plan.need_outerwear is True


def test_plan_slots_no_outerwear_need_when_none_owned():
    pools = comp.WardrobePools(outerwear=[])
    plan = comp.plan_slots({"temp": 5.0, "condition": "Snow"}, "casual", pools)
    assert plan.need_outerwear is False


def test_plan_slots_footwear_present_iff_owned():
    with_shoes = comp.plan_slots({"temp": 20, "condition": "Clear"}, "casual", comp.WardrobePools(footwear=[_item(category="sneaker")]))
    without_shoes = comp.plan_slots({"temp": 20, "condition": "Clear"}, "casual", comp.WardrobePools(footwear=[]))
    assert with_shoes.need_footwear is True
    assert without_shoes.need_footwear is False


# ---------------------------------------------------------------------------
# build_pools
# ---------------------------------------------------------------------------


def test_build_pools_routes_fullbody_regardless_of_category_string():
    """A dress-category item with `is_fullbody=True` must never leak into
    tops/bottoms, even though "dress" isn't in the top/bottom substring sets."""
    dress = _item(category="dress", is_fullbody=True)
    top = _item(category="shirt")

    pools = comp.build_pools([dress, top], worn_item_ids=set())

    assert pools.fullbody == [dress]
    assert dress not in pools.tops
    assert dress not in pools.bottoms
    assert pools.tops == [top]


def test_build_pools_excludes_14_day_worn_hard_set():
    worn = _item(category="shirt")
    fresh = _item(category="shirt")

    pools = comp.build_pools([worn, fresh], worn_item_ids={worn.id})

    assert worn not in pools.tops
    assert fresh in pools.tops


def test_build_pools_footwear_and_outerwear_substring_routing():
    sneaker = _item(category="sneaker")
    blazer = _item(category="blazer")
    jeans = _item(category="jeans")

    pools = comp.build_pools([sneaker, blazer, jeans], worn_item_ids=set())

    assert pools.footwear == [sneaker]
    assert pools.outerwear == [blazer]
    assert pools.bottoms == [jeans]


# ---------------------------------------------------------------------------
# Fullbody branch: never sets a phantom bottom
# ---------------------------------------------------------------------------


def test_fullbody_candidate_never_sets_bottom_or_top():
    dress = _item(category="dress", is_fullbody=True, wear_count=3, last_worn=TODAY - timedelta(days=10))
    pools = comp.WardrobePools(fullbody=[dress])
    slot_plan = comp.SlotPlan(need_footwear=False, need_outerwear=False, fullbody_eligible=True)
    rotation_ctx = RotationContext(today=TODAY)

    candidate = comp._build_fullbody_candidate(
        dress,
        pools,
        slot_plan=slot_plan,
        style_dna=None,
        rotation_ctx=rotation_ctx,
        weather={"temp": 20, "condition": "Clear"},
        occasion="casual",
        preferred_colors={},
        warm_items=[],
        items_with_prior_events=set(),
        today=TODAY,
        now=None,
        allow_repeat=False,
    )

    assert candidate is not None
    assert candidate.top_item is None
    assert candidate.bottom_item is None
    assert candidate.fullbody_item is dress
    assert candidate.combo_key == frozenset({dress.id})
    # Every score_components key is populated (0.0 where a term doesn't
    # apply) — never a missing key the schema layer would choke on.
    for key in ("color_harmony", "occasion_fit", "weather_score", "time_score", "style_dna", "behaviour", "base_compatibility", "preference_bonus", "cold_start_bonus", "rediscovery_bonus", "rotation_penalty", "total"):
        assert key in candidate.score_components


# ---------------------------------------------------------------------------
# Anchor diversity
# ---------------------------------------------------------------------------


def test_select_anchors_rejects_same_category_same_color_family_duplicates():
    """Two shirts, both "blue" (same category + color family) must not both
    become anchors — diversity key is (category, color_family)."""
    shirt_blue_1 = _item(category="shirt", color_primary="blue")
    shirt_blue_dup = _item(category="shirt", color_primary="blue")

    pools = comp.WardrobePools(tops=[shirt_blue_1, shirt_blue_dup])
    anchors = comp.select_anchors(pools, k=3, today=TODAY)

    # Only one of the two identical (category, color) shirts can be an anchor.
    assert len(anchors) == 1


def test_select_anchors_diverse_categories_all_included_up_to_max():
    items = [
        _item(category="shirt", color_primary="blue"),
        _item(category="t-shirt", color_primary="red"),
        _item(category="blouse", color_primary="green"),
        _item(category="sweater", color_primary="black"),
        _item(category="hoodie", color_primary="white"),
    ]
    pools = comp.WardrobePools(tops=items)
    anchors = comp.select_anchors(pools, k=3, today=TODAY)

    assert len(anchors) == comp.MAX_ANCHORS


def test_select_anchors_forces_at_least_one_grey_inventory_anchor():
    warm_items = [
        _item(category="shirt", color_primary="blue", wear_count=5, last_worn=TODAY - timedelta(days=2))
        for _ in range(5)
    ]
    grey_item = _item(category="t-shirt", color_primary="red", wear_count=0, last_worn=None)
    pools = comp.WardrobePools(tops=[*warm_items, grey_item])

    anchors = comp.select_anchors(pools, k=3, today=TODAY)

    assert any(comp._is_grey_inventory(a, TODAY) for a in anchors)


def test_select_anchors_forces_a_fullbody_anchor_when_owned():
    tops = [_item(category="shirt", color_primary=c) for c in ["blue", "red", "green", "black", "white"]]
    dress = _item(category="dress", is_fullbody=True, color_primary="pink", wear_count=4, last_worn=TODAY - timedelta(days=3))
    pools = comp.WardrobePools(tops=tops, fullbody=[dress])

    anchors = comp.select_anchors(pools, k=3, today=TODAY)

    assert dress in anchors


# ---------------------------------------------------------------------------
# Hard combo-exclusion
# ---------------------------------------------------------------------------


def test_generate_outfits_hard_excludes_recent_combo_while_unseen_combo_exists():
    top_a = _item(category="shirt", color_primary="blue")
    top_b = _item(category="t-shirt", color_primary="red")
    bottom_a = _item(category="jeans", color_primary="black")
    bottom_b = _item(category="chinos", color_primary="tan")

    pools = comp.WardrobePools(tops=[top_a, top_b], bottoms=[bottom_a, bottom_b])
    slot_plan = comp.SlotPlan(need_footwear=False, need_outerwear=False, fullbody_eligible=False)

    # top_a + bottom_a was already shown yesterday — the only combo seen so far.
    rotation_ctx = RotationContext(
        recent_combos={frozenset({top_a.id, bottom_a.id})},
        today=TODAY,
    )

    candidates = comp.generate_outfits(
        slot_plan,
        pools,
        style_dna=None,
        rotation_ctx=rotation_ctx,
        weather={"temp": 20, "condition": "Clear"},
        occasion="casual",
        today=TODAY,
        k=4,
    )

    combos = [c.combo_key for c in candidates]
    assert frozenset({top_a.id, bottom_a.id}) not in combos


def test_generate_outfits_allows_repeat_only_when_no_unseen_combo_exists():
    """Tiny wardrobe (1 top, 1 bottom) — the only combo has already been
    shown. With no unseen alternative, the feasibility fallback must still
    return that combo (better a repeat than nothing) rather than an empty list."""
    top = _item(category="shirt", color_primary="blue")
    bottom = _item(category="jeans", color_primary="black")
    pools = comp.WardrobePools(tops=[top], bottoms=[bottom])
    slot_plan = comp.SlotPlan(need_footwear=False, need_outerwear=False, fullbody_eligible=False)
    rotation_ctx = RotationContext(recent_combos={frozenset({top.id, bottom.id})}, today=TODAY)

    candidates = comp.generate_outfits(
        slot_plan,
        pools,
        style_dna=None,
        rotation_ctx=rotation_ctx,
        weather={"temp": 20, "condition": "Clear"},
        occasion="casual",
        today=TODAY,
        k=3,
    )

    assert len(candidates) == 1
    assert candidates[0].combo_key == frozenset({top.id, bottom.id})
    # The residual soft penalty was applied.
    assert candidates[0].score_components["rotation_penalty"] < 0
