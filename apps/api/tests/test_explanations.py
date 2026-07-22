"""Tests for services/recommendation/explanations.py (RI-4)."""

from __future__ import annotations

import uuid

from attreq_api.services.recommendation.composition import OutfitCandidate
from attreq_api.services.recommendation.explanations import CONFIDENCE_THRESHOLD, explain


def _candidate(score_components: dict, **overrides) -> OutfitCandidate:
    defaults = {
        "top_item": None,
        "bottom_item": None,
        "fullbody_item": None,
        "footwear_item": None,
        "outerwear_item": None,
        "accessory_item": None,
        "color_harmony_branch": "neutral_contrast",
        "score_components": score_components,
        "total_score": score_components.get("total", 0.5),
        "weather": {"temp": 20, "condition": "Clear"},
        "occasion": "casual",
    }
    defaults.update(overrides)
    return OutfitCandidate(**defaults)


def _full_components(**overrides) -> dict:
    base = {
        "color_harmony": 0.5,
        "formality": 0.5,
        "occasion_fit": 0.5,
        "weather_score": 0.5,
        "time_score": 0.5,
        "style_dna": 0.5,
        "behaviour": 0.5,
        "base_compatibility": 0.7,
        "preference_bonus": 0.0,
        "cold_start_bonus": 0.0,
        "rediscovery_bonus": 0.0,
        "rotation_penalty": 0.0,
        "total": 0.7,
    }
    base.update(overrides)
    return base


# ---------------------------------------------------------------------------
# Template selection matches the top-ranked component
# ---------------------------------------------------------------------------


def test_explain_top_component_drives_the_first_clause():
    components = _full_components(color_harmony=0.95, occasion_fit=0.1, weather_score=0.1, style_dna=0.1, behaviour=0.1, preference_bonus=0.0)
    candidate = _candidate(components, color_harmony_branch="tonal")

    result = explain(candidate, {"occasion": "casual", "weather": {"temp": 20, "condition": "Clear"}}, None)

    assert result.confidence == "normal"
    assert "tonal" in result.text


def test_explain_ranks_occasion_fit_when_it_dominates():
    components = _full_components(color_harmony=0.1, occasion_fit=0.95, weather_score=0.1, style_dna=0.1, behaviour=0.1)
    candidate = _candidate(components)

    result = explain(candidate, {"occasion": "business", "weather": {"temp": 20, "condition": "Clear"}}, None)

    assert "business" in result.text


# ---------------------------------------------------------------------------
# Confidence hedge keys off base_compatibility, not the penalized total
# ---------------------------------------------------------------------------


def test_confidence_hedge_fires_below_threshold_on_base_compatibility():
    components = _full_components(base_compatibility=CONFIDENCE_THRESHOLD - 0.05, total=CONFIDENCE_THRESHOLD - 0.05)
    candidate = _candidate(components)

    result = explain(candidate, {}, None)

    assert result.confidence == "low"
    assert "Experimental" in result.text


def test_confidence_hedge_does_not_fire_for_high_base_despite_large_rotation_penalty():
    """A candidate with a strong base_compatibility but a large negative
    rotation penalty (because it merely repeats a recently-shown combo) must
    NOT be mislabeled 'Experimental' — the hedge is calibrated off the
    positive compatibility base, not the penalized total."""
    components = _full_components(
        base_compatibility=0.9,
        rotation_penalty=-0.4,
        total=0.5,  # well above threshold numerically but irrelevant here
    )
    candidate = _candidate(components)

    result = explain(candidate, {}, None)

    assert result.confidence == "normal"
    assert "Experimental" not in result.text


# ---------------------------------------------------------------------------
# Rediscovery clause
# ---------------------------------------------------------------------------


def test_rediscovery_clause_appended_only_when_marked():
    components = _full_components(base_compatibility=0.8, total=0.8)
    item_id = str(uuid.uuid4())

    marked = _candidate(components, rediscovery=True, rediscovery_item_id=item_id)
    unmarked = _candidate(components, rediscovery=False, rediscovery_item_id=None)

    marked_result = explain(marked, {}, None)
    unmarked_result = explain(unmarked, {}, None)

    assert "not worn in a while" in marked_result.text
    assert "not worn in a while" not in unmarked_result.text
