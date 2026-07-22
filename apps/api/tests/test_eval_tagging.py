"""Tests for scripts/eval_tagging.py — unit tests only (no classifier calls, no images)."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import eval_tagging  # noqa: E402


def test_score_computes_per_field_accuracy():
    predictions = [
        {"category": "shirt", "pattern": "solid"},
        {"category": "jeans", "pattern": "striped"},  # category wrong (gt: pants)
        {"category": "dress", "pattern": "floral"},
        {"category": "skirt", "pattern": "plaid"},  # both wrong
    ]
    ground_truth = [
        {"category": "shirt", "pattern": "solid"},
        {"category": "pants", "pattern": "striped"},
        {"category": "dress", "pattern": "floral"},
        {"category": "jacket", "pattern": "abstract"},
    ]

    results = eval_tagging.score(predictions, ground_truth)

    assert results["category"]["n"] == 4
    assert results["category"]["accuracy"] == pytest.approx(2 / 4)
    assert results["pattern"]["n"] == 4
    assert results["pattern"]["accuracy"] == pytest.approx(3 / 4)

    # 2 rows match on both fields (row 0 and row 2)
    assert results["exact_match"]["n"] == 4
    assert results["exact_match"]["rate"] == pytest.approx(2 / 4)

    assert results["fields_scored"] == ["category", "pattern"]
    assert "color_primary" in results["fields_excluded_no_ground_truth"]
    assert "season" in results["fields_excluded_no_ground_truth"]
    assert "occasion" in results["fields_excluded_no_ground_truth"]


def test_score_skips_na_ground_truth_rows():
    predictions = [{"category": "shirt", "pattern": "solid"}]
    ground_truth = [{"category": "NA", "pattern": "solid"}]

    results = eval_tagging.score(predictions, ground_truth)

    assert results["category"]["n"] == 0
    assert results["category"]["accuracy"] is None
    assert results["pattern"]["n"] == 1
    assert results["pattern"]["accuracy"] == 1.0


def test_score_returns_top_confusions_for_mismatches():
    predictions = [{"category": "jeans", "pattern": "solid"}] * 3
    ground_truth = [{"category": "pants", "pattern": "solid"}] * 3

    results = eval_tagging.score(predictions, ground_truth)

    assert results["category"]["accuracy"] == 0.0
    confusions = results["category"]["top_confusions"]
    assert confusions[0]["ground_truth"] == "pants"
    assert confusions[0]["predicted"] == "jeans"
    assert confusions[0]["count"] == 3
