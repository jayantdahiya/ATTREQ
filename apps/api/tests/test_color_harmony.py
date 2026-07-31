"""Tests for services/recommendation/color_harmony.py (RI-3).

Two tiers, per the finalized RI-3 plan (F4 — never hard-code a branch
intuition the constants don't support):

- Synthetic-Lab tier: hand-set `PaletteColor` tuples exercise `tonal`
  directly (dormant on real named-color data — see F2/module docstring), plus
  the "reaches 1.0" and ceiling-ordering invariants.
- Real-vocab tier: goes through `legacy_color_lab.legacy_palette_for_item`
  against a transient `WardrobeItem`, using Lab values computed from the
  actual 16-name classifier vocabulary (`services/ai/color_extraction`), not
  intuited color-wheel expectations.
"""

from __future__ import annotations

import uuid

from attreq_api.services.recommendation import color_harmony as ch
from attreq_api.services.recommendation.algorithm import calculate_color_harmony_detailed
from attreq_api.services.recommendation.legacy_color_lab import LEGACY_COLOR_LAB, NEUTRAL_NAMES
from tests.conftest import build_wardrobe_item

# ---------------------------------------------------------------------------
# Synthetic-Lab tier
# ---------------------------------------------------------------------------


def test_tonal_reaches_1_0_at_ideal_synthetic_parameters():
    """dh=0, dc=0, dl=40 (band center) -> perfect tonal score."""
    a = ch.PaletteColor(lab=(70.0, -5.0, -20.0), is_neutral=False)
    b = ch.PaletteColor(lab=(30.0, -5.0, -20.0), is_neutral=False)

    result = ch.harmony(a, b)

    assert result.branch == "tonal"
    assert result.score == 1.0


def test_neutral_contrast_reaches_1_0_at_maximal_delta_l():
    """Black vs white — both neutral, dl=100 -> perfect neutral_contrast score."""
    black = ch.PaletteColor(lab=(0.0, 0.0, 0.0), is_neutral=True)
    white = ch.PaletteColor(lab=(100.0, 0.0, 0.0), is_neutral=True)

    result = ch.harmony(black, white)

    assert result.branch == "neutral_contrast"
    assert result.score == 1.0


def test_neutral_contrast_floor_at_zero_delta_l():
    """Two neutrals at the same lightness still score the floor, never below it."""
    a = ch.PaletteColor(lab=(50.0, 0.0, 0.0), is_neutral=True)
    b = ch.PaletteColor(lab=(50.0, 3.0, -3.0), is_neutral=True)

    result = ch.harmony(a, b)

    assert result.branch == "neutral_contrast"
    assert result.score == ch.NEUTRAL_CONTRAST_FLOOR


def test_tonal_wins_over_hue_rule_for_synthetic_light_dark_blue():
    """The plan's canonical dormant-on-legacy-data tonal case: same hue,
    different shade, small chroma delta. Both `tonal` and `hue_rule` are
    eligible (Δh=0 also satisfies the analogous hue_rule window) — `tonal`
    must win because ΔL*=45 lands inside its reward band."""
    light_blue = ch.PaletteColor(lab=(75.0, -5.0, -20.0), is_neutral=False)
    dark_blue = ch.PaletteColor(lab=(30.0, -6.0, -24.0), is_neutral=False)

    result = ch.harmony(light_blue, dark_blue)

    assert result.branch == "tonal"
    tonal_score = result.score
    hue_rule_result = ch._hue_rule_score(light_blue, dark_blue)
    assert hue_rule_result is not None
    assert tonal_score > hue_rule_result.score


def test_hue_rule_ceiling_strictly_below_tonal_and_neutral_contrast_maxima():
    """The qualitative invariant the plan requires: hue_rule's ceiling is
    strictly below the maximum achievable by tonal/neutral_contrast (1.0)."""
    assert ch.HUE_RULE_CEILING < 1.0

    # A best-case hue_rule pair (Δh=0, high average chroma) should still cap out
    # at HUE_RULE_CEILING, not reach 1.0.
    a = ch.PaletteColor(lab=(50.0, 60.0, 0.0), is_neutral=False)
    b = ch.PaletteColor(lab=(50.0, 60.0, 0.0), is_neutral=False)
    # Same Lab entirely -> dl=0, which is NOT in the tonal band [20,60], so
    # tonal is ineligible and hue_rule (Δh=0, analogous) wins outright.
    result = ch.harmony(a, b)
    assert result.branch == "hue_rule"
    assert result.score <= ch.HUE_RULE_CEILING
    assert result.score < 1.0


def test_dead_zone_chromatic_pair_falls_back_to_none_branch():
    """Two chromatic (non-neutral) colors whose hue delta lands in neither the
    analogous nor complementary window, and whose ΔL* is too small for tonal,
    must fall back to the flat "none" branch — never mislabelled `hue_rule`."""
    a = ch.PaletteColor(lab=(50.0, 40.0, 0.0), is_neutral=False)  # hue 0
    b = ch.PaletteColor(lab=(50.0, 0.0, 40.0), is_neutral=False)  # hue 90 -> Δh=90, dead zone

    result = ch.harmony(a, b)

    assert result.branch == "none"
    assert result.score == ch.FALLBACK_SCORE


def test_tonal_score_returns_none_when_either_side_neutral():
    neutral = ch.PaletteColor(lab=(20.0, 5.0, -5.0), is_neutral=True)
    chromatic = ch.PaletteColor(lab=(60.0, 10.0, -10.0), is_neutral=False)

    assert ch._tonal_score(neutral, chromatic) is None
    assert ch._tonal_score(chromatic, neutral) is None


def test_hue_rule_score_returns_none_when_either_side_neutral():
    neutral = ch.PaletteColor(lab=(20.0, 5.0, -5.0), is_neutral=True)
    chromatic = ch.PaletteColor(lab=(60.0, 10.0, -10.0), is_neutral=False)

    assert ch._hue_rule_score(neutral, chromatic) is None
    assert ch._hue_rule_score(chromatic, neutral) is None


def test_is_functional_neutral_catches_dark_low_chroma_but_not_saturated_navy():
    # Dark, modest chroma (e.g. a near-black-brown) -> functional neutral.
    assert ch.is_functional_neutral((20.0, 8.0, 8.0)) is True
    # Pure achromatic at any lightness -> functional neutral.
    assert ch.is_functional_neutral((60.0, 0.0, 0.0)) is True
    # Real pixel-extracted navy-like chroma (~80) exceeds even the darker
    # threshold — documented limitation, not a bug (see module docstring).
    assert ch.is_functional_neutral((13.0, 47.5, -64.7)) is False


def test_harmony_against_set_returns_neutral_when_no_others():
    color = ch.PaletteColor(lab=(50.0, 0.0, 0.0), is_neutral=True)
    assert ch.harmony_against_set(color, []) == 0.5


def test_harmony_against_set_is_mean_of_pairwise_harmony():
    base = ch.PaletteColor(lab=(0.0, 0.0, 0.0), is_neutral=True)  # black
    white = ch.PaletteColor(lab=(100.0, 0.0, 0.0), is_neutral=True)
    same = ch.PaletteColor(lab=(0.0, 0.0, 0.0), is_neutral=True)

    result = ch.harmony_against_set(base, [white, same])

    expected = (ch.harmony(base, white).score + ch.harmony(base, same).score) / 2
    assert result == round(expected, 4)


# ---------------------------------------------------------------------------
# Real-vocab tier — via the legacy bridge, expected branches derived from
# computed Lab (never intuited). See docstring at top of file.
# ---------------------------------------------------------------------------


def _item(color_primary: str, color_secondary: str | None = None):
    return build_wardrobe_item(
        user_id=uuid.uuid4(),
        color_primary=color_primary,
        color_secondary=color_secondary,
        schema_version=1,
        color_palette=None,
    )


def test_navy_and_tan_is_neutral_contrast_high():
    """navy is a NEUTRAL_NAME (F3) -> always routes to neutral_contrast,
    regardless of tan's own chromaticity. ΔL* (navy ~13, tan ~75) is large, so
    the score should land in the "high" range, not the floor."""
    navy = _item("navy")
    tan = _item("tan")

    result = calculate_color_harmony_detailed(navy, tan)

    assert result.branch == "neutral_contrast"

    delta_l = abs(LEGACY_COLOR_LAB["navy"][0] - LEGACY_COLOR_LAB["tan"][0])
    expected = round(min(1.0, ch.NEUTRAL_CONTRAST_FLOOR + 0.4 * (min(delta_l, 100.0) / 100.0)), 4)
    assert result.score == expected
    assert result.score > 0.8  # "high" per the plan's canonical fixture


def test_black_and_red_is_neutral_contrast():
    black = _item("black")
    red = _item("red")

    result = calculate_color_harmony_detailed(black, red)

    assert result.branch == "neutral_contrast"
    delta_l = abs(LEGACY_COLOR_LAB["black"][0] - LEGACY_COLOR_LAB["red"][0])
    expected = round(min(1.0, ch.NEUTRAL_CONTRAST_FLOOR + 0.4 * (min(delta_l, 100.0) / 100.0)), 4)
    assert result.score == expected


def test_red_and_green_chromatic_dead_zone_falls_back_to_none():
    """Both red and green are chromatic (not in NEUTRAL_NAMES). Their hue
    delta (~96°) lands outside both the analogous and complementary windows,
    and their ΔL* (~7) is below the tonal band -> "none" fallback, not
    hue_rule (computed offline, not intuited — see F4)."""
    red = _item("red")
    green = _item("green")

    result = calculate_color_harmony_detailed(red, green)

    assert result.branch == "none"
    assert result.score == ch.FALLBACK_SCORE


def test_blue_and_green_is_complementary_hue_rule():
    """Δh ~= 170° (within the 150-210 complementary window); ΔL* ~= 14 is
    below the tonal band, so hue_rule (not tonal) wins."""
    blue = _item("blue")
    green = _item("green")

    result = calculate_color_harmony_detailed(blue, green)

    assert result.branch == "hue_rule"
    assert result.score <= ch.HUE_RULE_CEILING


def test_yellow_and_orange_analogous_hue_rule_beats_tonal():
    """Both tonal- and hue_rule-eligible on real Lab (Δh~30, ΔC~14, ΔL~22 all
    inside tolerance) — hue_rule's higher chroma-scaled base wins the max()."""
    yellow = _item("yellow")
    orange = _item("orange")

    result = calculate_color_harmony_detailed(yellow, orange)

    assert result.branch == "hue_rule"
    assert result.score <= ch.HUE_RULE_CEILING


def test_maroon_is_a_neutral_name_per_f3():
    assert "maroon" in NEUTRAL_NAMES
    maroon = _item("maroon")
    green = _item("green")

    result = calculate_color_harmony_detailed(maroon, green)

    assert result.branch == "neutral_contrast"


def test_empty_palette_falls_back_to_0_5_neutral_contrast():
    item_a = _item(None)
    item_b = _item("blue")

    result = calculate_color_harmony_detailed(item_a, item_b)

    assert result.score == 0.5
    assert result.branch == "neutral_contrast"


def test_secondary_color_can_win_over_dominant_pairing():
    """Multi-color scoring keeps the single highest-scoring (c1, c2) pair, not
    a weighted mean — a strong secondary-color match must not be diluted."""
    # navy (primary, neutral) paired against an item whose secondary (tan) is
    # a much better match than its primary (also navy, dl=0 -> floor score).
    top = _item("navy")
    bottom = _item("navy", color_secondary="tan")

    result = calculate_color_harmony_detailed(top, bottom)

    # Best pair is navy(top) vs tan(secondary), not navy vs navy(dl=0, floor).
    delta_l_best = abs(LEGACY_COLOR_LAB["navy"][0] - LEGACY_COLOR_LAB["tan"][0])
    expected_best = round(
        min(1.0, ch.NEUTRAL_CONTRAST_FLOOR + 0.4 * (min(delta_l_best, 100.0) / 100.0)), 4
    )
    assert result.score == expected_best
