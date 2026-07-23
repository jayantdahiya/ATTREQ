"""Tests for RI-5 Task 5.2 — Bradley-Terry preference-pair weight fitting.

Pure-function tests over synthetic `PreferencePair`s for the math (mirror
symmetry, planted-preference recovery, grouped split, shrinkage), plus
real-DB integration tests for `extract_preference_pairs` (weather_wrong
exclusion) and `get_active_weights` (precedence + publish-guard behavior).
"""

from __future__ import annotations

import random
import uuid

import numpy as np
import pytest

from attreq_api.crud.recommendation_event import recommendation_event_crud
from attreq_api.crud.scoring_weights import scoring_weights_crud
from attreq_api.services.recommendation.weight_fitting import (
    COMPONENT_KEYS_FULL,
    FALLBACK_WEIGHTS,
    PreferencePair,
    build_feature_matrix,
    compute_holdout_user_auc,
    count_decision_batches,
    detect_component_keys,
    extract_preference_pairs,
    fit_weights,
    get_active_weights,
    grouped_train_holdout_split,
    shrink_to_global,
)

COMPONENT_KEYS = ["color_harmony", "formality", "style_dna", "behaviour"]


@pytest.fixture(autouse=True)
async def _clean_scoring_weights(db_session):
    """`scope="global"` is a real, hardcoded production scope name (not
    test-parameterizable — `get_active_weights` always queries it literally),
    so tests that publish under it must clean up rather than use a unique
    per-test scope, or a leftover row pollutes every other test/run."""
    from sqlalchemy import delete

    from attreq_api.models.scoring_weights import ScoringWeights

    await db_session.execute(delete(ScoringWeights))
    await db_session.commit()
    yield
    await db_session.execute(delete(ScoringWeights))
    await db_session.commit()


def _pair(pos: dict, neg: dict, user_id=None, recommendation_id=None) -> PreferencePair:
    return PreferencePair(
        components_pos=pos,
        components_neg=neg,
        user_id=user_id or uuid.uuid4(),
        recommendation_id=recommendation_id or uuid.uuid4(),
    )


# ---------------------------------------------------------------------------
# build_feature_matrix / mirror symmetry
# ---------------------------------------------------------------------------


def test_build_feature_matrix_mirrors_pairs():
    pairs = [_pair({"color_harmony": 0.9, "formality": 0.5}, {"color_harmony": 0.3, "formality": 0.5})]
    x, y = build_feature_matrix(pairs, ["color_harmony", "formality"])
    assert x.shape == (2, 2)
    assert list(y) == [1.0, 0.0]
    assert np.allclose(x[0], [0.6, 0.0])
    assert np.allclose(x[1], [-0.6, 0.0])


def test_fit_weights_mirror_symmetry_p_a_beats_b_equals_one_minus_reverse():
    """Bradley-Terry via mirrored pairs + fit_intercept=False: the fitted
    model must be exactly symmetric — P(A>B) == 1 - P(B>A)."""
    rng = random.Random(7)
    pairs = []
    for _ in range(200):
        color_pos = rng.uniform(0.5, 1.0)
        color_neg = rng.uniform(0.0, 0.5)
        pairs.append(_pair({"color_harmony": color_pos}, {"color_harmony": color_neg}))

    x, y = build_feature_matrix(pairs, ["color_harmony"])
    weights = fit_weights(x, y, ["color_harmony"])

    a = {"color_harmony": 0.9}
    b = {"color_harmony": 0.2}
    score_a_over_b = weights["color_harmony"] * (a["color_harmony"] - b["color_harmony"])
    score_b_over_a = weights["color_harmony"] * (b["color_harmony"] - a["color_harmony"])
    assert score_a_over_b == pytest.approx(-score_b_over_a)


def test_fit_weights_empty_input_returns_fallback():
    x, y = build_feature_matrix([], COMPONENT_KEYS)
    weights = fit_weights(x, y, COMPONENT_KEYS)
    assert set(weights) == set(COMPONENT_KEYS)
    assert sum(weights.values()) == pytest.approx(1.0)


def test_fit_weights_single_class_returns_fallback():
    """All-identical diffs (zero variance) still degrade gracefully."""
    pairs = [_pair({"color_harmony": 0.5}, {"color_harmony": 0.5}) for _ in range(5)]
    x, y = build_feature_matrix(pairs, ["color_harmony"])
    weights = fit_weights(x, y, ["color_harmony"])
    assert weights["color_harmony"] >= 0.0


# ---------------------------------------------------------------------------
# Planted-preference recovery
# ---------------------------------------------------------------------------


def test_fit_weights_recovers_planted_color_preference():
    """500 synthetic pairs where `color_harmony` is ALWAYS higher on the
    winner and the other components are noise -> the fit must rank
    `color_harmony` as the top weight."""
    rng = random.Random(42)
    keys = ["color_harmony", "formality", "style_dna", "behaviour"]
    pairs = []
    for _ in range(500):
        pos = {
            "color_harmony": rng.uniform(0.6, 1.0),
            "formality": rng.uniform(0.0, 1.0),
            "style_dna": rng.uniform(0.0, 1.0),
            "behaviour": rng.uniform(0.0, 1.0),
        }
        neg = {
            "color_harmony": rng.uniform(0.0, 0.4),
            "formality": rng.uniform(0.0, 1.0),
            "style_dna": rng.uniform(0.0, 1.0),
            "behaviour": rng.uniform(0.0, 1.0),
        }
        pairs.append(_pair(pos, neg))

    x, y = build_feature_matrix(pairs, keys)
    weights = fit_weights(x, y, keys)

    assert weights["color_harmony"] == max(weights.values())
    assert weights["color_harmony"] > 0.5


# ---------------------------------------------------------------------------
# Grouped train/holdout split (Correction 8 — no batch straddles both sides)
# ---------------------------------------------------------------------------


def test_grouped_split_no_recommendation_id_in_both_sides():
    rng = random.Random(1)
    pairs = []
    for _ in range(20):
        rec_id = uuid.uuid4()
        # Two pairs sharing the same recommendation_id (one batch, 3 shown items).
        pairs.append(_pair({"color_harmony": rng.random()}, {"color_harmony": rng.random()}, recommendation_id=rec_id))
        pairs.append(_pair({"color_harmony": rng.random()}, {"color_harmony": rng.random()}, recommendation_id=rec_id))

    train, holdout = grouped_train_holdout_split(pairs, holdout_frac=0.3, seed=1)
    train_ids = {p.recommendation_id for p in train}
    holdout_ids = {p.recommendation_id for p in holdout}
    assert train_ids.isdisjoint(holdout_ids)
    assert len(train) + len(holdout) == len(pairs)


def test_grouped_split_empty_input():
    train, holdout = grouped_train_holdout_split([], holdout_frac=0.2, seed=1)
    assert train == []
    assert holdout == []


# ---------------------------------------------------------------------------
# compute_holdout_user_auc
# ---------------------------------------------------------------------------


def test_compute_holdout_user_auc_perfect_weights_scores_one():
    pairs = [_pair({"color_harmony": 0.9}, {"color_harmony": 0.1}) for _ in range(10)]
    auc = compute_holdout_user_auc(pairs, {"color_harmony": 1.0}, ["color_harmony"])
    assert auc == 1.0


def test_compute_holdout_user_auc_no_pairs_is_uninformative():
    assert compute_holdout_user_auc([], {"color_harmony": 1.0}, ["color_harmony"]) == 0.5


def test_compute_holdout_user_auc_macro_averages_per_user():
    """One prolific user (many pairs, all wrong) must not dominate a second
    user (few pairs, all correct) — macro average, not micro/pooled."""
    user_a = uuid.uuid4()
    user_b = uuid.uuid4()
    pairs = [_pair({"color_harmony": 0.1}, {"color_harmony": 0.9}, user_id=user_a) for _ in range(100)]
    pairs += [_pair({"color_harmony": 0.9}, {"color_harmony": 0.1}, user_id=user_b) for _ in range(1)]

    auc = compute_holdout_user_auc(pairs, {"color_harmony": 1.0}, ["color_harmony"])
    # Macro average of (0.0, 1.0) = 0.5, NOT ~0.0099 (what a pooled/micro
    # average over 101 mostly-wrong pairs would give).
    assert auc == pytest.approx(0.5)


# ---------------------------------------------------------------------------
# Shrinkage
# ---------------------------------------------------------------------------


def test_shrink_to_global_bounds_monotonic_across_m():
    w_user = {"color_harmony": 1.0, "formality": 0.0}
    w_global = {"color_harmony": 0.2, "formality": 0.8}

    small_m = shrink_to_global(w_user, w_global, m=1, lam=20)
    mid_m = shrink_to_global(w_user, w_global, m=50, lam=20)
    large_m = shrink_to_global(w_user, w_global, m=500, lam=20)

    # Small m -> close to global; large m -> close to user's own fit.
    assert abs(small_m["color_harmony"] - w_global["color_harmony"]) < abs(
        large_m["color_harmony"] - w_global["color_harmony"]
    )
    assert small_m["color_harmony"] < mid_m["color_harmony"] < large_m["color_harmony"]
    assert large_m["color_harmony"] > 0.9


def test_shrink_to_global_stays_sum_one():
    w_user = {"color_harmony": 0.7, "formality": 0.3}
    w_global = {"color_harmony": 0.2, "formality": 0.8}
    shrunk = shrink_to_global(w_user, w_global, m=10, lam=20)
    assert sum(shrunk.values()) == pytest.approx(1.0)


def test_count_decision_batches_counts_distinct_recommendation_ids():
    rec_a, rec_b = uuid.uuid4(), uuid.uuid4()
    pairs = [
        _pair({"color_harmony": 0.5}, {"color_harmony": 0.4}, recommendation_id=rec_a),
        _pair({"color_harmony": 0.5}, {"color_harmony": 0.3}, recommendation_id=rec_a),
        _pair({"color_harmony": 0.5}, {"color_harmony": 0.2}, recommendation_id=rec_b),
    ]
    assert count_decision_batches(pairs) == 2


# ---------------------------------------------------------------------------
# detect_component_keys
# ---------------------------------------------------------------------------


def test_detect_component_keys_absent_centroid_not_included():
    pairs = [_pair({"color_harmony": 0.5, "formality": 0.5}, {"color_harmony": 0.4, "formality": 0.4})]
    keys = detect_component_keys(pairs)
    assert "centroid" not in keys
    assert set(keys) == {"color_harmony", "formality"}


def test_detect_component_keys_full_set_when_present():
    pairs = [
        _pair(
            dict.fromkeys(COMPONENT_KEYS_FULL, 0.5),
            dict.fromkeys(COMPONENT_KEYS_FULL, 0.4),
        )
    ]
    assert detect_component_keys(pairs) == COMPONENT_KEYS_FULL


def test_detect_component_keys_ignores_none_centroid():
    pairs = [_pair({"color_harmony": 0.5, "centroid": None}, {"color_harmony": 0.4, "centroid": None})]
    keys = detect_component_keys(pairs)
    assert "centroid" not in keys


# ---------------------------------------------------------------------------
# extract_preference_pairs — real DB, weather_wrong exclusion
# ---------------------------------------------------------------------------


def _candidate(scores: dict) -> dict:
    return {
        "top_item_id": "top-1",
        "bottom_item_id": "bottom-1",
        "scores": scores,
    }


@pytest.mark.asyncio
async def test_extract_preference_pairs_excludes_weather_wrong_rejection(db_session, real_user):
    recommendation_id = uuid.uuid4()
    candidates = [
        _candidate({"color_harmony": 0.9, "formality": 0.5}),
        _candidate({"color_harmony": 0.3, "formality": 0.5}),
        _candidate({"color_harmony": 0.2, "formality": 0.5}),
    ]
    await recommendation_event_crud.bulk_create_shown(
        db_session,
        user_id=real_user.id,
        recommendation_id=recommendation_id,
        candidates=candidates,
        context={"occasion": "casual"},
    )
    shown = await recommendation_event_crud.get_shown(
        db_session, recommendation_id=recommendation_id, outfit_index=0, user_id=real_user.id
    )
    await recommendation_event_crud.create_feedback_event(
        db_session,
        user_id=real_user.id,
        recommendation_id=recommendation_id,
        outfit_index=0,
        event_type="accepted",
        outfit_payload=shown.outfit_payload,
    )
    # outfit_index 2 was rejected for a context reason (weather_wrong) -> its
    # `shown` row must be dropped from pair derivation entirely.
    rejected_shown = await recommendation_event_crud.get_shown(
        db_session, recommendation_id=recommendation_id, outfit_index=2, user_id=real_user.id
    )
    await recommendation_event_crud.create_feedback_event(
        db_session,
        user_id=real_user.id,
        recommendation_id=recommendation_id,
        outfit_index=2,
        event_type="rejected",
        outfit_payload=rejected_shown.outfit_payload,
        rejection_reason="weather_wrong",
    )

    pairs = await extract_preference_pairs(db_session, user_id=real_user.id)
    batch_pairs = [p for p in pairs if p.recommendation_id == recommendation_id]

    assert len(batch_pairs) == 1
    assert batch_pairs[0].components_neg["color_harmony"] == 0.3


# ---------------------------------------------------------------------------
# get_active_weights — precedence + graceful fallback
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_active_weights_no_rows_falls_back_to_constants(db_session, real_user):
    weights, source = await get_active_weights(db_session, real_user.id)
    assert weights == FALLBACK_WEIGHTS
    assert source == "fallback"


@pytest.mark.asyncio
async def test_get_active_weights_prefers_user_over_global(db_session, real_user):
    global_weights = {"color_harmony": 0.5, "formality": 0.5}
    user_weights = {"color_harmony": 0.9, "formality": 0.1}

    await scoring_weights_crud.publish(
        db_session, scope="global", weights=global_weights, fitted_on_n_pairs=300, holdout_user_auc=0.6
    )
    await scoring_weights_crud.publish(
        db_session,
        scope=str(real_user.id),
        weights=user_weights,
        fitted_on_n_pairs=40,
        holdout_user_auc=0.7,
    )

    weights, source = await get_active_weights(db_session, real_user.id)
    assert weights == user_weights
    assert source == f"user:{real_user.id}"

    # A different user (no personal row) falls through to global.
    other_user_id = uuid.uuid4()
    other_weights, other_source = await get_active_weights(db_session, other_user_id)
    assert other_weights == global_weights
    assert other_source == "global"


@pytest.mark.asyncio
async def test_publish_deactivates_prior_active_row_for_scope(db_session, real_user):
    first = await scoring_weights_crud.publish(
        db_session, scope="global", weights={"color_harmony": 1.0}, fitted_on_n_pairs=300, holdout_user_auc=0.6
    )
    second = await scoring_weights_crud.publish(
        db_session, scope="global", weights={"formality": 1.0}, fitted_on_n_pairs=400, holdout_user_auc=0.65
    )

    await db_session.refresh(first)
    assert first.is_active is False
    assert second.is_active is True

    weights, source = await get_active_weights(db_session, None)
    assert weights == {"formality": 1.0}
    assert source == "global"


@pytest.mark.asyncio
async def test_record_refused_never_flips_active_row(db_session):
    scope = f"test-refuse-{uuid.uuid4()}"
    published = await scoring_weights_crud.publish(
        db_session, scope=scope, weights={"color_harmony": 1.0}, fitted_on_n_pairs=300, holdout_user_auc=0.6
    )
    await scoring_weights_crud.record_refused(
        db_session, scope=scope, weights={"formality": 1.0}, fitted_on_n_pairs=50, holdout_user_auc=0.4
    )

    active = await scoring_weights_crud.get_active(db_session, scope=scope)
    assert active is not None
    assert active.id == published.id
    assert active.weights == {"color_harmony": 1.0}
