"""Tests for services/style_dna/color_families.py (RI-3)."""

from __future__ import annotations

import pytest

from attreq_api.services.style_dna.color_families import (
    AFFINITY_CLAMP_MAX,
    AFFINITY_CLAMP_MIN,
    AFFINITY_SEED_ACCENT,
    AFFINITY_SEED_AVOID,
    AFFINITY_SEED_DOMINANT,
    COLOR_FAMILIES,
    MAX_AFFINITY_INFLUENCE,
    NAMED_COLOR_TO_FAMILY,
    affinity_adjustment,
    bump_affinity,
    color_family_for_name,
    seed_color_affinity,
)


def test_color_families_has_twelve_families():
    assert len(COLOR_FAMILIES) == 12


@pytest.mark.parametrize(
    ("name", "family"),
    [
        ("black", "black"),
        ("white", "white"),
        ("gray", "gray"),
        ("grey", "gray"),
        ("navy", "navy"),
        ("beige", "beige_tan"),
        ("tan", "beige_tan"),
        ("cream", "beige_tan"),
        ("brown", "brown"),
        ("red", "red"),
        ("maroon", "red"),
        ("pink", "pink_purple"),
        ("purple", "pink_purple"),
        ("blue", "blue"),
        ("green", "green"),
        ("yellow", "yellow_orange"),
        ("orange", "yellow_orange"),
    ],
)
def test_named_color_to_family_covers_the_real_16_name_vocab(name, family):
    assert color_family_for_name(name) == family


def test_color_family_for_name_handles_case_and_whitespace():
    assert color_family_for_name("  NAVY ") == "navy"


def test_color_family_for_name_none_or_unmapped_returns_none():
    assert color_family_for_name(None) is None
    assert color_family_for_name("") is None
    assert color_family_for_name("turquoise") is None


def test_seed_color_affinity_dominant_gets_1_2():
    style_dna = {"color_palette": {"dominant": ["navy", "black"], "accent": [], "avoids": []}}
    affinity = seed_color_affinity(style_dna)

    assert affinity["navy"] == AFFINITY_SEED_DOMINANT
    assert affinity["black"] == AFFINITY_SEED_DOMINANT
    assert pytest.approx(1.2) == AFFINITY_SEED_DOMINANT


def test_seed_color_affinity_accent_gets_1_05():
    style_dna = {"color_palette": {"dominant": [], "accent": ["yellow"], "avoids": []}}
    affinity = seed_color_affinity(style_dna)

    assert affinity["yellow_orange"] == AFFINITY_SEED_ACCENT
    assert pytest.approx(1.05) == AFFINITY_SEED_ACCENT


def test_seed_color_affinity_avoids_gets_0_8():
    style_dna = {"color_palette": {"dominant": [], "accent": [], "avoids": ["pink"]}}
    affinity = seed_color_affinity(style_dna)

    assert affinity["pink_purple"] == AFFINITY_SEED_AVOID
    assert pytest.approx(0.8) == AFFINITY_SEED_AVOID


def test_seed_color_affinity_dominant_hit_is_not_downgraded_by_later_accent():
    """A family already seeded at 1.2 (dominant) via one color must not be
    lowered to 1.05 just because a different accent color maps to the same
    family."""
    style_dna = {
        "color_palette": {"dominant": ["red"], "accent": ["maroon"], "avoids": []}
    }
    affinity = seed_color_affinity(style_dna)

    assert affinity["red"] == AFFINITY_SEED_DOMINANT


def test_seed_color_affinity_empty_palette_is_empty_dict():
    assert seed_color_affinity({}) == {}
    assert seed_color_affinity({"color_palette": {}}) == {}


def test_bump_affinity_worn_and_liked_increase():
    affinity = {"blue": 1.0}
    assert bump_affinity(affinity, "blue", "worn")["blue"] > 1.0
    assert bump_affinity(affinity, "blue", "liked")["blue"] > 1.0


def test_bump_affinity_disliked_decreases():
    affinity = {"blue": 1.0}
    assert bump_affinity(affinity, "blue", "disliked")["blue"] < 1.0


def test_bump_affinity_does_not_mutate_input():
    affinity = {"blue": 1.0}
    bump_affinity(affinity, "blue", "worn")
    assert affinity["blue"] == 1.0


def test_bump_affinity_clamps_to_0_7_1_3():
    affinity = {"blue": AFFINITY_CLAMP_MAX}
    for _ in range(20):
        affinity = bump_affinity(affinity, "blue", "worn")
    assert affinity["blue"] == AFFINITY_CLAMP_MAX

    affinity = {"blue": AFFINITY_CLAMP_MIN}
    for _ in range(20):
        affinity = bump_affinity(affinity, "blue", "disliked")
    assert affinity["blue"] == AFFINITY_CLAMP_MIN


def test_affinity_clamp_bounds_are_0_7_and_1_3():
    assert pytest.approx(0.7) == AFFINITY_CLAMP_MIN
    assert pytest.approx(1.3) == AFFINITY_CLAMP_MAX


def test_affinity_adjustment_neutral_family_is_zero():
    assert affinity_adjustment("blue", {}) == 0.0
    assert affinity_adjustment("blue", {"blue": 1.0}) == 0.0


def test_affinity_adjustment_bounded_to_max_influence():
    adj_high = affinity_adjustment("blue", {"blue": AFFINITY_CLAMP_MAX})
    adj_low = affinity_adjustment("blue", {"blue": AFFINITY_CLAMP_MIN})

    assert adj_high == pytest.approx(MAX_AFFINITY_INFLUENCE)
    assert adj_low == pytest.approx(-MAX_AFFINITY_INFLUENCE)


def test_affinity_adjustment_none_family_is_zero():
    assert affinity_adjustment(None, {"blue": 1.3}) == 0.0


def test_named_color_to_family_has_no_stray_entries_outside_vocab():
    expected_keys = {
        "black", "white", "gray", "grey", "navy", "beige", "tan", "cream",
        "brown", "red", "maroon", "pink", "purple", "blue", "green",
        "yellow", "orange",
    }
    assert set(NAMED_COLOR_TO_FAMILY.keys()) == expected_keys
