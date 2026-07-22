"""Tests for services/style_dna/personal_color.py (RI-3).

Covers the exit criteria verbatim: low/absent confidence => unchanged
bit-for-bit; the C6 combined-clamp regression (pc + affinity adjustments
jointly bounded to a single ±10% envelope, never the ~21% two independent
±10% multiplicative adjustments would compound to).
"""

from __future__ import annotations

import pytest

from attreq_api.services.style_dna.personal_color import (
    MAX_INFLUENCE,
    MIN_CONFIDENCE,
    PERSONAL_COLOR_ELIGIBLE_CATEGORIES,
    apply_personal_color_adjustment,
    is_eligible_slot,
    personal_color_adjustment,
)

WARM_LAB = (40.0, 10.0, 40.0)  # low L*, high +b* -> "deep" + "warm" leaning


def test_confidence_below_threshold_returns_zero_adjustment():
    personal_color = {"undertone_warm_cool": 1.0, "depth_light_deep": 1.0, "confidence": 0.49}
    assert personal_color_adjustment(WARM_LAB, personal_color) == 0.0


def test_confidence_at_or_above_threshold_can_be_nonzero():
    personal_color = {"undertone_warm_cool": 1.0, "depth_light_deep": 1.0, "confidence": 0.9}
    adj = personal_color_adjustment(WARM_LAB, personal_color)
    assert adj != 0.0


def test_absent_personal_color_profile_returns_zero_adjustment():
    assert personal_color_adjustment(WARM_LAB, None) == 0.0
    assert personal_color_adjustment(WARM_LAB, {}) == 0.0


def test_absent_dominant_lab_returns_zero_adjustment():
    personal_color = {"undertone_warm_cool": 1.0, "depth_light_deep": 1.0, "confidence": 1.0}
    assert personal_color_adjustment(None, personal_color) == 0.0


def test_personal_color_adjustment_is_bounded_to_max_influence():
    personal_color = {"undertone_warm_cool": 1.0, "depth_light_deep": 1.0, "confidence": 1.0}
    adj = personal_color_adjustment(WARM_LAB, personal_color)
    assert -MAX_INFLUENCE <= adj <= MAX_INFLUENCE


def test_apply_personal_color_adjustment_unchanged_bit_for_bit_at_low_confidence():
    base_score = 0.6734
    style_dna = {
        "personal_color": {"undertone_warm_cool": 1.0, "depth_light_deep": 1.0, "confidence": 0.1},
        "color_affinity": {},  # no affinity signal either
    }

    result = apply_personal_color_adjustment(base_score, WARM_LAB, "red", style_dna)

    assert result == base_score


def test_apply_personal_color_adjustment_unchanged_for_none_style_dna():
    base_score = 0.5
    assert apply_personal_color_adjustment(base_score, WARM_LAB, "red", None) == base_score


def test_apply_personal_color_adjustment_unchanged_for_empty_style_dna():
    base_score = 0.5
    assert apply_personal_color_adjustment(base_score, WARM_LAB, "red", {}) == base_score


def test_c6_combined_adjustment_never_exceeds_max_influence_even_at_both_maxima():
    """The C6 regression test: pc_adj and aff_adj both at their individual
    maxima (+0.10 each) must jointly clamp to +0.10, not compound toward the
    ~21% two independent multiplicative ±10% adjustments would give
    (1.10 * 1.10 = 1.21)."""
    base_score = 0.6
    style_dna = {
        "personal_color": {
            "undertone_warm_cool": 1.0,
            "depth_light_deep": 1.0,
            "confidence": 1.0,
        },
        "color_affinity": {"red": 1.3},  # affinity clamp max
    }

    result = apply_personal_color_adjustment(base_score, WARM_LAB, "red", style_dna)

    # Single ±10% envelope: worst case is exactly base_score * 1.10.
    max_possible = round(base_score * (1.0 + MAX_INFLUENCE), 10)
    assert result <= max_possible + 1e-9
    # And strictly less than the ~21% compounding two independent
    # multiplicative ±10% adjustments would have produced.
    compounded_wrong_value = base_score * (1.0 + MAX_INFLUENCE) * (1.0 + MAX_INFLUENCE)
    assert result < compounded_wrong_value


def test_c6_combined_adjustment_never_exceeds_max_influence_at_both_negative_maxima():
    """Item axes disagree with the user's cool/light preference (WARM_LAB is
    warm+moderately-deep) -> negative pc_adj, combined with affinity at its
    clamp minimum -> both terms negative, jointly clamped to exactly -10%."""
    base_score = 0.6
    style_dna = {
        "personal_color": {
            "undertone_warm_cool": -1.0,
            "depth_light_deep": -1.0,
            "confidence": 1.0,
        },
        "color_affinity": {"red": 0.7},  # affinity clamp min
    }

    result = apply_personal_color_adjustment(base_score, WARM_LAB, "red", style_dna)

    min_possible = round(base_score * (1.0 - MAX_INFLUENCE), 10)
    assert result == pytest.approx(min_possible)


def test_result_always_clamped_to_unit_interval():
    style_dna = {
        "personal_color": {"undertone_warm_cool": 1.0, "depth_light_deep": 1.0, "confidence": 1.0},
        "color_affinity": {"red": 1.3},
    }
    result = apply_personal_color_adjustment(0.99, WARM_LAB, "red", style_dna)
    assert 0.0 <= result <= 1.0


def test_min_confidence_constant_is_0_5():
    assert MIN_CONFIDENCE == 0.5


def test_max_influence_constant_is_0_10():
    assert pytest.approx(0.10) == MAX_INFLUENCE


def test_eligible_slots_include_top_outerwear_fullbody_only():
    assert {"top", "outerwear", "fullbody"} == PERSONAL_COLOR_ELIGIBLE_CATEGORIES
    assert is_eligible_slot("top") is True
    assert is_eligible_slot("outerwear") is True
    assert is_eligible_slot("fullbody") is True
    assert is_eligible_slot("bottom") is False
    assert is_eligible_slot("footwear") is False
    assert is_eligible_slot("accessory") is False
