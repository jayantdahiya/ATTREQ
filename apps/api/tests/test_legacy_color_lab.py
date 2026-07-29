"""Tests for services/recommendation/legacy_color_lab.py (RI-3, F1/F3)."""

from __future__ import annotations

import uuid

import numpy as np
import pytest

from attreq_api.services.ai.color_extraction import _NAMED_COLOR_RGB, srgb_to_lab
from attreq_api.services.recommendation.legacy_color_lab import (
    DEFAULT_UNKNOWN_LAB,
    LEGACY_COLOR_LAB,
    NEUTRAL_NAMES,
    legacy_palette_for_item,
)
from tests.conftest import build_wardrobe_item


def test_legacy_color_lab_covers_the_real_16_name_vocab_plus_grey():
    expected_names = set(_NAMED_COLOR_RGB.keys()) | {"grey"}
    assert expected_names <= set(LEGACY_COLOR_LAB.keys())
    # F1: the plan's stale camel/burgundy/forest/coral/teal/turquoise/"light
    # blue"/"dark blue" names must NOT be present — the classifiers never emit them.
    for stale_name in (
        "camel",
        "burgundy",
        "forest",
        "coral",
        "teal",
        "turquoise",
        "light blue",
        "dark blue",
    ):
        assert stale_name not in LEGACY_COLOR_LAB


@pytest.mark.parametrize("name", list(_NAMED_COLOR_RGB.keys()))
def test_legacy_color_lab_matches_independently_computed_srgb_to_lab(name):
    """Spot-check every entry against a fresh `srgb_to_lab` conversion of the
    same reference RGB swatch (independent of import-time caching)."""
    rgb = np.array(_NAMED_COLOR_RGB[name], dtype=float)
    expected = tuple(float(v) for v in srgb_to_lab(rgb))
    actual = LEGACY_COLOR_LAB[name]
    for e, a in zip(expected, actual, strict=True):
        assert a == pytest.approx(e, abs=1e-6)


def test_grey_is_an_alias_for_gray():
    assert LEGACY_COLOR_LAB["grey"] == LEGACY_COLOR_LAB["gray"]


def test_neutral_names_fires_for_navy_tan_maroon_beige():
    for name in ("navy", "tan", "maroon", "beige"):
        assert name in NEUTRAL_NAMES


def test_neutral_names_does_not_fire_for_chromatic_colors():
    for name in ("red", "blue", "green", "purple", "pink", "yellow", "orange"):
        assert name not in NEUTRAL_NAMES


def test_unmapped_name_falls_back_to_default_unknown_lab_never_raises():
    item = build_wardrobe_item(user_id=uuid.uuid4(), color_primary="turquoise", color_secondary=None)
    palette = legacy_palette_for_item(item)

    assert len(palette) == 1
    assert palette[0].lab == DEFAULT_UNKNOWN_LAB
    assert palette[0].is_neutral is False  # "turquoise" isn't in NEUTRAL_NAMES


def test_legacy_palette_for_item_shares_sum_to_one_with_both_colors():
    item = build_wardrobe_item(user_id=uuid.uuid4(), color_primary="navy", color_secondary="tan")
    palette = legacy_palette_for_item(item)

    assert len(palette) == 2
    assert palette[0].share == pytest.approx(0.7)
    assert palette[1].share == pytest.approx(0.3)
    assert palette[0].is_neutral is True  # navy
    assert palette[1].is_neutral is True  # tan


def test_legacy_palette_for_item_single_color_gets_full_share():
    item = build_wardrobe_item(user_id=uuid.uuid4(), color_primary="red", color_secondary=None)
    palette = legacy_palette_for_item(item)

    assert len(palette) == 1
    assert palette[0].share == 1.0
    assert palette[0].is_neutral is False


def test_legacy_palette_for_item_no_colors_is_empty():
    item = build_wardrobe_item(user_id=uuid.uuid4(), color_primary=None, color_secondary=None)
    assert legacy_palette_for_item(item) == []
