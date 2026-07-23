"""Tests for the RI-6 FashionCLIP centroid/propagation hooks threaded through
services/recommendation/composition.py.

Follows the style of test_composition.py: pure in-memory `WardrobeItem`
fixtures, `comp._build_fullbody_candidate`/`_fill_bottom_for_anchor` called
directly. `item_vectors`/`user_centroid`/`propagation_penalties` all default
to `None` in every existing call site — the key backward-compatibility
guarantee this file checks is that omitting them (or passing all-`None`)
reproduces the exact pre-RI-6 `total`/component values.
"""

from __future__ import annotations

import uuid
from datetime import date

from attreq_api.services.recommendation import composition as comp
from attreq_api.services.recommendation.rotation import RotationContext
from tests.conftest import build_wardrobe_item

USER_ID = uuid.uuid4()
TODAY = date(2026, 4, 20)


def _item(**overrides):
    return build_wardrobe_item(user_id=USER_ID, **overrides)


def _fullbody_candidate(
    dress, *, item_vectors=None, user_centroid=None, propagation_penalties=None, weights=None
):
    pools = comp.WardrobePools(fullbody=[dress])
    slot_plan = comp.SlotPlan(need_footwear=False, need_outerwear=False, fullbody_eligible=True)
    rotation_ctx = RotationContext(today=TODAY)

    return comp._build_fullbody_candidate(
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
        item_vectors=item_vectors,
        user_centroid=user_centroid,
        propagation_penalties=propagation_penalties,
        weights=weights,
    )


def test_centroid_and_propagation_default_to_none_and_inactive():
    """No RI-6 args passed at all -> exact pre-RI-6 code path: `centroid` is
    `None` (feature inactive, not merely neutral) and `propagation_adjustment`
    is `None` (never computed), matching the schema's optional fields."""
    dress = _item(category="dress", is_fullbody=True)
    candidate = _fullbody_candidate(dress)

    assert candidate.score_components["centroid"] is None
    assert candidate.score_components["propagation_adjustment"] is None


def test_centroid_active_when_item_vectors_supplied_even_if_item_has_no_vector():
    """Passing a real (possibly empty) `item_vectors` dict activates the
    centroid weight carve-out; an item with no stored vector still scores
    the neutral 0.5, per `similarity.centroid_score`'s contract."""
    dress = _item(category="dress", is_fullbody=True)
    candidate = _fullbody_candidate(dress, item_vectors={}, user_centroid=[1.0, 0.0])

    assert candidate.score_components["centroid"] == 0.5


def test_centroid_component_reflects_item_vector_similarity_to_centroid():
    dress = _item(category="dress", is_fullbody=True)
    vector = [1.0, 0.0]
    centroid = [1.0, 0.0]  # identical direction -> cosine 1.0 -> centroid_score 1.0

    candidate = _fullbody_candidate(
        dress, item_vectors={dress.id: vector}, user_centroid=centroid
    )

    assert candidate.score_components["centroid"] == 1.0


def test_centroid_weight_carve_out_changes_base_compatibility_without_style_dna():
    """RI-5 (Task 5.1) superseded the old hard style_dna/no-style_dna scheme
    switch: with no quiz AND no observed behaviour, `style_dna_score` and
    `behaviour_score` are both the neutral 0.5 default (see
    `services/style_dna/blend.py`), but the FALLBACK_WEIGHTS terms for them
    (0.40/0.20) still apply unconditionally — no cliff.

    RI-5 also deliberately sets `FALLBACK_WEIGHTS["centroid"] = 0.0`
    (`weight_fitting.py` docstring: "provisional pending RI-5's fitted
    weights" — until a real fit assigns it a data-driven coefficient, the
    conservative Phase-A default is to not weight it at all). So activating
    centroid data with the DEFAULT weights changes `components['centroid']`
    but NOT `base_compatibility` — verified below. Passing an explicit
    weights dict WITH a nonzero centroid share (simulating a published fit)
    DOES change it, proving the carve-out mechanism (`_apply_weights`) itself
    still works end to end.
    """
    dress = _item(category="dress", is_fullbody=True)

    inactive = _fullbody_candidate(dress)
    active_default_weights = _fullbody_candidate(
        dress, item_vectors={dress.id: [1.0, 0.0]}, user_centroid=[1.0, 0.0]
    )
    fitted_weights = {
        "color_harmony": 0.20,
        "formality": 0.20,
        "style_dna": 0.30,
        "behaviour": 0.20,
        "centroid": 0.10,
    }
    active_fitted_weights = _fullbody_candidate(
        dress,
        item_vectors={dress.id: [1.0, 0.0]},
        user_centroid=[1.0, 0.0],
        weights=fitted_weights,
    )

    color = inactive.score_components["color_harmony"]
    context = inactive.score_components["formality"]
    style_dna_score = inactive.score_components["style_dna"]
    behaviour_score = inactive.score_components["behaviour"]
    assert style_dna_score == 0.5
    assert behaviour_score == 0.5

    expected_inactive_base = round(
        color * 0.20 + context * 0.20 + style_dna_score * 0.40 + behaviour_score * 0.20, 4
    )
    expected_active_fitted_base = round(
        color * 0.20 + context * 0.20 + style_dna_score * 0.30 + behaviour_score * 0.20 + 1.0 * 0.10, 4
    )

    assert active_default_weights.score_components["centroid"] == 1.0
    assert inactive.score_components["base_compatibility"] == expected_inactive_base
    # Default (unfitted) weights: centroid data is computed but not weighted.
    assert (
        active_default_weights.score_components["base_compatibility"]
        == expected_inactive_base
    )
    # An explicit weights dict with a nonzero centroid share DOES change it.
    assert active_fitted_weights.score_components["base_compatibility"] == expected_active_fitted_base


def test_propagation_adjustment_folds_into_total_and_is_recorded():
    dress = _item(category="dress", is_fullbody=True)

    inactive = _fullbody_candidate(dress)
    penalized = _fullbody_candidate(dress, propagation_penalties={dress.id: -0.05})
    bonused = _fullbody_candidate(dress, propagation_penalties={dress.id: 0.03})

    assert penalized.score_components["propagation_adjustment"] == -0.05
    assert bonused.score_components["propagation_adjustment"] == 0.03

    assert penalized.total_score == max(0.0, min(1.0, inactive.total_score - 0.05))
    assert bonused.total_score == max(0.0, min(1.0, inactive.total_score + 0.03))


def test_propagation_adjustment_missing_item_defaults_to_zero():
    dress = _item(category="dress", is_fullbody=True)
    other_item_id = uuid.uuid4()

    candidate = _fullbody_candidate(dress, propagation_penalties={other_item_id: -0.05})

    assert candidate.score_components["propagation_adjustment"] == 0.0


def test_two_core_item_propagation_sums_both_items_clamped_per_item_upstream():
    """A top+bottom outfit sums each core item's already-clamped adjustment
    (composition.py does not re-clamp the outfit-level sum — the +/-0.05
    clamp is per item, applied upstream in similarity.compute_propagation_penalties)."""
    top = _item(category="shirt")
    bottom = _item(category="jeans", color_primary="black")
    pools = comp.WardrobePools(tops=[top], bottoms=[bottom])
    slot_plan = comp.SlotPlan(need_footwear=False, need_outerwear=False, fullbody_eligible=False)
    rotation_ctx = RotationContext(today=TODAY)

    candidate = comp._fill_bottom_for_anchor(
        top,
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
        allow_repeat=True,
        used_bottom_ids=set(),
        propagation_penalties={top.id: -0.05, bottom.id: -0.03},
    )

    assert candidate is not None
    assert candidate.score_components["propagation_adjustment"] == -0.08
