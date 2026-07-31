"""Tests for RI-5 Task 5.1 — the Bayesian quiz->behaviour blend.

Pure-function tests over `services/style_dna/blend.py`, plus one real-DB
integration test proving `update_behaviour_weights` maintains the per-key
observation counts the blend depends on.
"""

from __future__ import annotations

import json

import pytest

from attreq_api.services.style_dna.blend import (
    DEFAULT_K,
    blend_key,
    blend_weight,
    compute_effective_pref,
    quiz_prior_from_style_dna,
)
from tests.conftest import build_outfit, build_wardrobe_item

# ---------------------------------------------------------------------------
# blend_key limits
# ---------------------------------------------------------------------------


def test_blend_key_zero_observations_returns_quiz_value():
    assert blend_key(quiz_value=0.9, behaviour_value=0.1, n_key=0) == 0.9


def test_blend_key_zero_observations_no_quiz_returns_neutral():
    assert blend_key(quiz_value=None, behaviour_value=0.1, n_key=0) == 0.5


def test_blend_key_large_n_converges_to_behaviour():
    result = blend_key(quiz_value=0.9, behaviour_value=0.1, n_key=1_000_000)
    assert result == pytest.approx(0.1, abs=1e-3)


def test_blend_key_k15_crossover_at_n_equals_k():
    """quiz=0.9, behaviour=0.1, n_key=k=15 -> exact midpoint 0.5, regardless
    of the two input values (Correction: crossover at n==k)."""
    result = blend_key(quiz_value=0.9, behaviour_value=0.1, n_key=15, k=15)
    assert result == pytest.approx(0.5)


def test_blend_key_missing_behaviour_defaults_neutral_no_exception():
    result = blend_key(quiz_value=0.7, behaviour_value=None, n_key=5)
    # n_key=5 pulls slightly toward the neutral 0.5 behaviour default.
    assert 0.5 < result < 0.7


def test_blend_key_negative_n_key_clamped_to_zero():
    assert blend_key(quiz_value=0.8, behaviour_value=0.2, n_key=-5) == 0.8


# ---------------------------------------------------------------------------
# blend_weight — the quantity that demonstrates "behaviour dominates" ratio
# (Correction 7: behaviour VALUES barely move, but this WEIGHT does)
# ---------------------------------------------------------------------------


def test_blend_weight_at_n50_k15_is_077():
    assert blend_weight(50, k=15) == pytest.approx(50 / 65, abs=1e-4)
    assert blend_weight(50, k=15) == pytest.approx(0.7692, abs=1e-3)


def test_blend_weight_zero_at_n_zero():
    assert blend_weight(0) == 0.0


def test_blend_weight_approaches_one_at_large_n():
    assert blend_weight(100_000, k=DEFAULT_K) > 0.999


# ---------------------------------------------------------------------------
# quiz_prior_from_style_dna
# ---------------------------------------------------------------------------


def test_quiz_prior_maps_dominant_accent_avoids():
    style_dna = {
        "color_palette": {"dominant": ["Navy"], "accent": ["White"], "avoids": ["Orange"]},
        "patterns": {"preferred": ["Solid"]},
        "formality_bias": {"level": 2.0},
    }
    prior = quiz_prior_from_style_dna(style_dna)
    assert prior["category_likes"] == {}
    assert prior["color_likes"]["navy"] == 0.9
    assert prior["color_likes"]["white"] == 0.7
    assert prior["color_likes"]["orange"] == 0.1
    assert prior["pattern_likes"]["solid"] == 0.8
    assert prior["formality_level"] == 2.0


def test_quiz_prior_none_style_dna_is_all_neutral():
    prior = quiz_prior_from_style_dna(None)
    assert prior == {
        "category_likes": {},
        "color_likes": {},
        "pattern_likes": {},
        "formality_level": 1.5,
    }


def test_quiz_prior_avoids_overrides_dominant_if_both_listed():
    style_dna = {"color_palette": {"dominant": ["red"], "avoids": ["red"]}}
    prior = quiz_prior_from_style_dna(style_dna)
    assert prior["color_likes"]["red"] == 0.1


# ---------------------------------------------------------------------------
# compute_effective_pref — the per-key isolation guard (Correction 6)
# ---------------------------------------------------------------------------


def test_compute_effective_pref_none_style_dna_end_to_end_neutral_no_crash():
    result = compute_effective_pref(None, None)
    assert result == {"category_likes": {}, "color_likes": {}, "pattern_likes": {}}


def test_compute_effective_pref_new_user_is_quiz_driven():
    """A user who did the quiz but has zero behaviour events: effective_pref
    should reflect the quiz palette directly (n_key=0 everywhere -> pure quiz)."""
    style_dna = {"color_palette": {"dominant": ["navy"]}}
    result = compute_effective_pref(style_dna, {})
    assert result["color_likes"]["navy"] == 0.9


def test_compute_effective_pref_per_key_isolation_guards_the_bug():
    """Correction 6's core guard: behaviour has 50 shirt-category events but
    ZERO navy-color events. Navy must stay at the quiz value; shirt fades
    toward its (very different) behaviour value."""
    style_dna = {
        "color_palette": {"dominant": ["navy"]},  # navy quiz value 0.9
        "behaviour_weights": {
            "category_likes": {"shirt": 0.1},  # behaviour disagrees strongly
            "color_likes": {},  # navy never touched by behaviour
        },
        "behaviour_counts": {
            "category_counts": {"shirt": 50},
            "color_counts": {},  # navy: n_key = 0
        },
    }
    result = compute_effective_pref(style_dna, style_dna["behaviour_counts"])

    # navy: n_key=0 -> untouched by the shirt category's 50 observations.
    assert result["color_likes"]["navy"] == 0.9
    # shirt: n_key=50 >> k=15 -> mostly behaviour's 0.1, far from quiz-neutral 0.5.
    assert result["category_likes"]["shirt"] < 0.3


def test_compute_effective_pref_missing_quiz_key_present_behaviour_defaults_neutral():
    style_dna = {
        "behaviour_weights": {"color_likes": {"red": 0.9}},
        "behaviour_counts": {"color_counts": {"red": 3}},
    }
    result = compute_effective_pref(style_dna, style_dna["behaviour_counts"])
    # quiz has no opinion on "red" (not in color_palette at all) -> blended
    # against the neutral 0.5 quiz default, not an exception.
    assert 0.5 < result["color_likes"]["red"] < 0.9


# ---------------------------------------------------------------------------
# update_behaviour_weights — real-DB integration: per-key counts persist
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_update_behaviour_weights_tracks_per_key_counts(db_session, real_user):
    from sqlalchemy import select, update

    from attreq_api.models.user import User
    from attreq_api.services.style_dna.style_dna_service import update_behaviour_weights

    top = build_wardrobe_item(user_id=real_user.id, category="shirt", color_primary="navy", pattern="solid")
    bottom = build_wardrobe_item(user_id=real_user.id, category="jeans", color_primary="black", pattern="solid")
    db_session.add(top)
    db_session.add(bottom)
    await db_session.commit()

    outfit = build_outfit(user_id=real_user.id, top_item_id=top.id, bottom_item_id=bottom.id)
    db_session.add(outfit)
    await db_session.commit()
    await db_session.refresh(outfit)

    await db_session.execute(
        update(User)
        .where(User.id == real_user.id)
        .values(style_preferences=json.dumps({"color_palette": {"dominant": ["navy"]}}))
    )
    await db_session.commit()

    mutated_1 = await update_behaviour_weights(db_session, real_user.id, outfit.id, signal="liked")
    assert mutated_1 is True

    mutated_2 = await update_behaviour_weights(db_session, real_user.id, outfit.id, signal="liked")
    assert mutated_2 is True

    result = await db_session.execute(select(User).where(User.id == real_user.id))
    refreshed = result.scalar_one()
    style_dna = json.loads(refreshed.style_preferences)

    counts = style_dna["behaviour_counts"]
    assert counts["category_counts"]["shirt"] == 2
    assert counts["category_counts"]["jeans"] == 2
    assert counts["color_counts"]["navy"] == 2
    assert counts["color_counts"]["black"] == 2
    assert counts["pattern_counts"]["solid"] == 4  # both items, both calls
    assert style_dna["n_feedback_events"] == 2

    # And the blend actually uses these counts (n_key=2 is small, so shirt
    # stays close to quiz/neutral, not yet dominated by behaviour).
    from attreq_api.services.style_dna.blend import compute_effective_pref

    effective = compute_effective_pref(style_dna, style_dna["behaviour_counts"])
    assert "shirt" in effective["category_likes"]
    assert "navy" in effective["color_likes"]
