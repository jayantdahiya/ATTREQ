"""Tests for scripts/eval_outfits.py — the RI-3/4/5 scorer regression gate."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import eval_outfits  # noqa: E402

FIXTURE_LABELS_CSV = Path(__file__).resolve().parent / "fixtures" / "eval" / "outfit_labels.csv"


def test_generate_synthetic_wardrobe_covers_tops_and_bottoms():
    wardrobe = eval_outfits.generate_synthetic_wardrobe(seed=42)

    tops = [item for item in wardrobe if item["id"].startswith("top-")]
    bottoms = [item for item in wardrobe if item["id"].startswith("bottom-")]

    assert len(tops) >= 5
    assert len(bottoms) >= 5


def test_generate_pairs_returns_requested_count():
    wardrobe = eval_outfits.generate_synthetic_wardrobe(seed=42)
    pairs = eval_outfits.generate_pairs(wardrobe, n=20, seed=1)

    assert len(pairs) == 20
    for pair in pairs:
        assert "pair_id" in pair
        assert "top_item_json" in pair
        assert "bottom_item_json" in pair


def test_score_pair_returns_value_in_unit_interval():
    score = eval_outfits.score_pair(
        {"category": "t-shirt", "color_primary": "white", "occasion": ["casual"]},
        {"category": "jeans", "color_primary": "blue", "occasion": ["casual"]},
    )
    assert 0.0 <= score <= 1.0


def test_score_against_scorer_returns_valid_auc():
    """Exit criterion: eval_outfits.py reports scorer AUC against >=100 labeled pairs.

    We assert the AUC is a valid probability, not a specific value — the baseline
    number is documented (in the eval run output), not pinned as a regression target
    here (that's what re-running this script after each scorer change is for).
    """
    if not FIXTURE_LABELS_CSV.exists():
        pytest.skip("outfit_labels.csv fixture not present")

    labeled_df = eval_outfits.ingest_labels(FIXTURE_LABELS_CSV)
    assert len(labeled_df) >= 100

    auc = eval_outfits.score_against_scorer(labeled_df)

    assert 0.0 <= auc <= 1.0


def test_score_against_scorer_raises_on_single_class():
    import pandas as pd

    single_class_df = pd.DataFrame(
        [
            {
                "pair_id": "p1",
                "top_item_json": '{"category": "t-shirt", "color_primary": "white", "occasion": ["casual"]}',
                "bottom_item_json": '{"category": "jeans", "color_primary": "blue", "occasion": ["casual"]}',
                "label": 1,
            },
            {
                "pair_id": "p2",
                "top_item_json": '{"category": "blazer", "color_primary": "blue", "occasion": ["formal"]}',
                "bottom_item_json": '{"category": "dress pants", "color_primary": "black", "occasion": ["formal"]}',
                "label": 1,
            },
        ]
    )

    with pytest.raises(ValueError, match="both classes"):
        eval_outfits.score_against_scorer(single_class_df)
