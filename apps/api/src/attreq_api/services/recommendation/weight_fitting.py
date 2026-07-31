"""RI-5 Phase B — Bradley-Terry preference-pair weight fitting.

Fits the aggregation weights (`color_harmony`, `formality`, `style_dna`,
`behaviour`, `centroid` — the exact keys `composition._base_compatibility`'s
weighted sum reads) on real accept/reject preference pairs from
`recommendation_events`, via Bradley-Terry logistic regression over
score-component differences.

Adaptation note: the additive bonus terms (`preference_bonus`,
`cold_start_bonus`, `rediscovery_bonus`, `rotation_penalty`,
`propagation_adjustment`) are NOT part of this fit. In the current
architecture (`composition._build_candidate`) they are applied ADDITIVELY
after the weighted aggregation (`total = base_compatibility + bonuses...`),
a structurally different role than `W` (which only governs
`base_compatibility`'s weighted sum, always summing to 1.0 over its keys).
Re-weighting the additive bonuses would require restructuring that
additive-bonus architecture, which is out of scope for this milestone.

No fitting ever runs in a request path — `LogisticRegression.fit()` is only
ever called from `scripts/fit_scoring_weights.py`. The request path only
calls `get_active_weights()`, an O(1) indexed read with the hardcoded
constants as ultimate fallback.
"""

from __future__ import annotations

import contextlib
import logging
import random
from dataclasses import dataclass
from typing import TYPE_CHECKING

import numpy as np
from sqlalchemy import select

from attreq_api.crud.recommendation_event import recommendation_event_crud
from attreq_api.crud.scoring_weights import scoring_weights_crud
from attreq_api.models.recommendation_event import RecommendationEvent

if TYPE_CHECKING:
    from uuid import UUID

    from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

# The exact keys composition._base_compatibility's weighted sum reads.
# `detect_component_keys` runtime-detects which are actually present in a
# given data sample rather than hard-assuming all five — a pre-RI-6 (no
# centroid data) scores dict still fits cleanly over the remaining four.
COMPONENT_KEYS_FULL = ["color_harmony", "formality", "style_dna", "behaviour", "centroid"]

FALLBACK_WEIGHTS: dict[str, float] = {
    "color_harmony": 0.20,
    "formality": 0.20,
    "style_dna": 0.40,
    "behaviour": 0.20,
    "centroid": 0.0,
}

# Rejections with this reason are a context failure (weather changed, wrong
# call), not a taste signal — excluded from pair derivation (RI-1 pinned
# contract, finalized RI-5 plan section 1).
CONTEXT_FAILURE_REASON = "weather_wrong"


@dataclass(frozen=True)
class PreferencePair:
    """One (chosen, skipped) preference observation from a single generation batch."""

    components_pos: dict[str, float]
    components_neg: dict[str, float]
    user_id: UUID
    recommendation_id: UUID


async def extract_preference_pairs(
    db: AsyncSession, user_id: UUID | None = None
) -> list[PreferencePair]:
    """Derive preference pairs from `recommendation_events`.

    Per `recommendation_id`: positive = the row with `event_type in
    {accepted, worn}`; negatives = every other `shown` row in the same batch,
    EXCEPT one whose `outfit_index` also has a `rejected` row with
    `rejection_reason == "weather_wrong"` (dropped). Batches with no
    positive, or no remaining `shown` rows after the drop rule, yield no
    pairs. `user_id` is carried on the pair for macro-averaging (holdout
    AUC) and per-user refit grouping — never used as a model FEATURE (pooled
    fits are anonymized).
    """
    raw_pairs = await recommendation_event_crud.get_preference_pairs(db, user_id=user_id)

    reject_query = select(RecommendationEvent).where(
        RecommendationEvent.event_type == "rejected",
        RecommendationEvent.rejection_reason == CONTEXT_FAILURE_REASON,
    )
    if user_id is not None:
        reject_query = reject_query.where(RecommendationEvent.user_id == user_id)
    reject_result = await db.execute(reject_query)
    weather_wrong_keys = {
        (row.recommendation_id, row.outfit_index) for row in reject_result.scalars().all()
    }

    pairs: list[PreferencePair] = []
    for positive, shown in raw_pairs:
        key = (shown.recommendation_id, shown.outfit_index)
        if key in weather_wrong_keys:
            continue
        pos_scores = (positive.outfit_payload or {}).get("scores", {}) or {}
        neg_scores = (shown.outfit_payload or {}).get("scores", {}) or {}
        pairs.append(
            PreferencePair(
                components_pos=pos_scores,
                components_neg=neg_scores,
                user_id=positive.user_id,
                recommendation_id=positive.recommendation_id,
            )
        )
    return pairs


def detect_component_keys(pairs: list[PreferencePair]) -> list[str]:
    """Runtime-detect which of `COMPONENT_KEYS_FULL` are actually present
    (numeric, non-None) across a sample of pairs' component dicts — a
    pre-centroid batch (no RI-6 data) still fits cleanly over the keys that
    ARE present, instead of crashing or zero-filling a signal that was never
    computed for that batch.
    """
    present: set[str] = set()
    sample = pairs[:50] if len(pairs) > 50 else pairs
    for pair in sample:
        for key in COMPONENT_KEYS_FULL:
            for components in (pair.components_pos, pair.components_neg):
                value = components.get(key)
                if isinstance(value, int | float) and not isinstance(value, bool):
                    present.add(key)
    return [k for k in COMPONENT_KEYS_FULL if k in present]


def _component_vector(components: dict[str, float], keys: list[str]) -> list[float]:
    return [float(components.get(k) or 0.0) for k in keys]


def build_feature_matrix(
    pairs: list[PreferencePair], component_keys: list[str]
) -> tuple[np.ndarray, np.ndarray]:
    """Bradley-Terry mirrored-pairs trick: for each pair, `diff = pos - neg`;
    `X = [diff, -diff]`, `y = [1, 0]`. With `fit_intercept=False` (see
    `fit_weights`), this yields a symmetric classifier through the origin (an
    all-zero diff scores exactly 50/50) — the correct Bradley-Terry
    assumption, and `P(A>B) == 1 - P(B>A)` by construction. Deliberately NOT
    `StandardScaler`d (finalized plan Correction 11) — the fitted
    coefficients must live in the original 0-1 component space to be usable
    directly as aggregation weights.
    """
    diffs = []
    for pair in pairs:
        pos = _component_vector(pair.components_pos, component_keys)
        neg = _component_vector(pair.components_neg, component_keys)
        diffs.append([p - n for p, n in zip(pos, neg, strict=True)])

    if not diffs:
        return np.zeros((0, len(component_keys))), np.zeros(0)

    diff_arr = np.array(diffs, dtype=float)
    x = np.vstack([diff_arr, -diff_arr])
    y = np.concatenate([np.ones(len(diff_arr)), np.zeros(len(diff_arr))])
    return x, y


def _restricted_fallback(component_keys: list[str]) -> dict[str, float]:
    restricted = {k: FALLBACK_WEIGHTS.get(k, 0.0) for k in component_keys}
    total = sum(restricted.values()) or 1.0
    return {k: v / total for k, v in restricted.items()}


def fit_weights(x: np.ndarray, y: np.ndarray, component_keys: list[str]) -> dict[str, float]:
    """Fit Bradley-Terry logistic regression (`fit_intercept=False`), clip
    negative coefficients to zero, renormalize to sum 1. Degenerate inputs
    (no data, single class, or every coefficient clipped to zero) fall back
    to `FALLBACK_WEIGHTS` restricted to `component_keys` and renormalized —
    never raises.
    """
    from sklearn.linear_model import LogisticRegression

    fallback = _restricted_fallback(component_keys)

    if x.shape[0] == 0 or len(set(y.tolist())) < 2:
        logger.warning("fit_weights: insufficient data (%d rows) — returning fallback", x.shape[0])
        return fallback

    model = LogisticRegression(fit_intercept=False, C=1.0)
    model.fit(x, y)
    coefs = model.coef_[0]

    clipped = np.clip(coefs, 0.0, None)
    total = clipped.sum()
    if total <= 1e-9:
        logger.warning("fit_weights: all coefficients clipped to zero — returning fallback")
        return fallback

    normalized = clipped / total
    return dict(zip(component_keys, (float(v) for v in normalized), strict=True))


def compute_holdout_user_auc(
    pairs: list[PreferencePair], weights: dict[str, float], component_keys: list[str]
) -> float:
    """User-conditioned AUC: per pair, correct if `sum(w*pos) > sum(w*neg)`
    (0.5 credit on an exact tie); macro-averaged per user, then averaged
    across users — a model that only learns pooled popularity must not look
    good just because one prolific user has many pairs (Stitch Fix's
    per-user evaluation discipline). Users with zero pairs here are simply
    absent from the average. Returns `0.5` (uninformative) if there are no
    pairs at all.
    """
    per_user_scores: dict[UUID, list[float]] = {}
    for pair in pairs:
        pos = _component_vector(pair.components_pos, component_keys)
        neg = _component_vector(pair.components_neg, component_keys)
        w = [weights.get(k, 0.0) for k in component_keys]
        pos_score = sum(a * b for a, b in zip(w, pos, strict=True))
        neg_score = sum(a * b for a, b in zip(w, neg, strict=True))
        if pos_score > neg_score:
            correct = 1.0
        elif pos_score < neg_score:
            correct = 0.0
        else:
            correct = 0.5
        per_user_scores.setdefault(pair.user_id, []).append(correct)

    if not per_user_scores:
        return 0.5

    per_user_means = [sum(scores) / len(scores) for scores in per_user_scores.values()]
    return sum(per_user_means) / len(per_user_means)


def grouped_train_holdout_split(
    pairs: list[PreferencePair], holdout_frac: float = 0.2, seed: int = 42
) -> tuple[list[PreferencePair], list[PreferencePair]]:
    """Split by `recommendation_id` (grouped), not by individual pair — every
    pair from the same batch shares the positive item's component vector, so
    a per-pair split would leak that vector across train/holdout (finalized
    plan Correction 8: "holdout leakage"). Fixed seed for reproducibility.
    """
    batch_ids = sorted({pair.recommendation_id for pair in pairs}, key=str)
    if not batch_ids:
        return [], []

    rng = random.Random(seed)
    rng.shuffle(batch_ids)

    n_holdout = max(1, round(len(batch_ids) * holdout_frac))
    holdout_ids = set(batch_ids[:n_holdout])

    train = [p for p in pairs if p.recommendation_id not in holdout_ids]
    holdout = [p for p in pairs if p.recommendation_id in holdout_ids]
    return train, holdout


def count_decision_batches(pairs: list[PreferencePair]) -> int:
    """Distinct `recommendation_id`s represented — the milestone's "30
    decisions" threshold is expressed in decision BATCHES, not raw pairs
    (finalized plan Correction 9: one batch with N shown items yields up to
    N-1 pairs from a single decision, so counting pairs overstates data volume).
    """
    return len({pair.recommendation_id for pair in pairs})


def shrink_to_global(
    w_user: dict[str, float], w_global: dict[str, float], m: int, lam: int = 20
) -> dict[str, float]:
    """Convex shrinkage toward the global weights:
    `(m*w_user + lam*w_global) / (m + lam)`. Both inputs are sum-1 vectors
    over the same keys, so the result stays sum-1 (a convex combination of
    two sum-1 vectors is sum-1). `m` = the user's distinct decision-batch
    count (`count_decision_batches`) — small `m` -> mostly global; large `m`
    -> mostly the user's own fit.
    """
    keys = set(w_user) | set(w_global)
    denom = m + lam
    if denom <= 0:
        return dict(w_global)
    return {key: (m * w_user.get(key, 0.0) + lam * w_global.get(key, 0.0)) / denom for key in keys}


async def get_active_weights(db: AsyncSession, user_id: UUID | None) -> tuple[dict[str, float], str]:
    """O(1) indexed read of the currently-active scoring weights — NEVER
    fits/trains anything in this call path. Precedence: per-user active row
    -> global active row -> `FALLBACK_WEIGHTS`. Any failure (table not yet
    migrated, disconnected/mocked session, malformed row, etc.) falls back
    silently — the request path's "ultimate fallback" guarantee, so a
    scoring_weights outage can never break a recommendation request.

    Returns `(weights, source_label)` where `source_label` is one of
    `"user:<id>"`, `"global"`, `"fallback"` — the caller logs this into the
    generation batch's `shown`-event `context` for observability.
    """
    try:
        if user_id is not None:
            user_row = await scoring_weights_crud.get_active(db, scope=str(user_id))
            if user_row is not None:
                return dict(user_row.weights), f"user:{user_id}"

        global_row = await scoring_weights_crud.get_active(db, scope="global")
        if global_row is not None:
            return dict(global_row.weights), "global"
    except Exception as e:  # noqa: BLE001 - ultimate fallback must never raise
        logger.warning("get_active_weights: falling back to constants after error: %s", e)
        # A failed query (e.g. table not yet migrated) can leave the session's
        # underlying transaction aborted — roll back so subsequent queries on
        # this same session (the rest of the generation request) don't also
        # fail with "current transaction is aborted". Safe no-op otherwise.
        with contextlib.suppress(Exception):
            await db.rollback()

    return dict(FALLBACK_WEIGHTS), "fallback"
