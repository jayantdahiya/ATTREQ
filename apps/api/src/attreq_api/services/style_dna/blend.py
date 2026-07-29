"""Bayesian quiz -> behaviour blend (RI-5, Task 5.1).

The Style DNA quiz seeds a one-time prior; behaviour observed from feedback
(worn/liked/disliked, `style_dna_service.update_behaviour_weights`) should
fade the quiz's influence in *per key*, not per profile — a user with many
shirt-category feedback events but zero signal on a particular color must not
have that color's quiz opinion diluted by an unrelated key's observation
count (finalized RI-5 plan, Correction 6 — the "per-key n bug").

Formula per key: `effective = (k*quiz + n_key*behaviour) / (k + n_key)`,
k=15 pseudo-observations (mid of the research base's 10-20 range). `n_key=0`
-> pure quiz (or neutral 0.5 if there is no quiz opinion on that key either).
`n_key` large -> behaviour dominates regardless of the quiz value. Crossover
at `n_key == k` regardless of the two values (they weight equally).

Note (finalized plan Correction 7): behaviour values are a clamped +/-0.05
walk, not a running mean, so the blended *value* barely leaves 0.5 even at
large n. The exit criterion "behaviour dominates after ~50 events" refers to
the blend *weight* `n/(n+k)` (0.77 at n=50), not the magnitude of the
resulting value — see `blend_weight()` below and the test suite.
"""

from __future__ import annotations

from typing import Any

DEFAULT_K = 15
NEUTRAL = 0.5


def quiz_prior_from_style_dna(style_dna: dict[str, Any] | None) -> dict[str, Any]:
    """Derive a quiz-only preference prior shaped like `behaviour_weights`.

    `category_likes` is always `{}` — the quiz never asks about garment
    category preference, only color/pattern/formality. `color_likes`: dominant
    colors -> 0.9, accent -> 0.7 (only if not already set from dominant),
    avoids -> 0.1 (overrides). `pattern_likes`: preferred patterns -> 0.8.
    `formality_level` comes from `formality_bias.level` (0-3 scale), default
    1.5 (neutral midpoint) when absent.

    Safe to call with `style_dna=None` — returns an all-empty/neutral prior.
    """
    style_dna = style_dna or {}

    color_likes: dict[str, float] = {}
    palette = style_dna.get("color_palette", {}) or {}
    for color in palette.get("dominant", []) or []:
        color_likes[str(color).lower()] = 0.9
    for color in palette.get("accent", []) or []:
        color_likes.setdefault(str(color).lower(), 0.7)
    for color in palette.get("avoids", []) or []:
        color_likes[str(color).lower()] = 0.1

    pattern_likes: dict[str, float] = {}
    for pattern in (style_dna.get("patterns", {}) or {}).get("preferred", []) or []:
        pattern_likes[str(pattern).lower()] = 0.8

    formality_level = float((style_dna.get("formality_bias", {}) or {}).get("level", 1.5) or 1.5)

    return {
        "category_likes": {},
        "color_likes": color_likes,
        "pattern_likes": pattern_likes,
        "formality_level": formality_level,
    }


def blend_key(
    quiz_value: float | None, behaviour_value: float | None, n_key: int, k: int = DEFAULT_K
) -> float:
    """Bayesian blend of one key's quiz prior and behaviour-observed value.

    Missing quiz/behaviour values default to the neutral 0.5 midpoint —
    never raises. `n_key` is clamped to >= 0 defensively.
    """
    quiz = NEUTRAL if quiz_value is None else quiz_value
    behaviour = NEUTRAL if behaviour_value is None else behaviour_value
    n_key = max(0, int(n_key or 0))
    return (k * quiz + n_key * behaviour) / (k + n_key)


def blend_weight(n_key: int, k: int = DEFAULT_K) -> float:
    """The behaviour side's share of the blend, `n_key / (n_key + k)`.

    Exposed standalone because the blended *value* barely moves even at high
    n (behaviour is a clamped +/-0.05 walk around 0.5) — this weight is the
    quantity that actually demonstrates "behaviour dominates after ~50
    events" (Correction 7).
    """
    n_key = max(0, int(n_key or 0))
    denom = n_key + k
    return n_key / denom if denom else 0.0


def compute_effective_pref(
    style_dna: dict[str, Any] | None,
    behaviour_counts: dict[str, Any] | None,
    k: int = DEFAULT_K,
) -> dict[str, Any]:
    """Blend the quiz prior with observed behaviour, per key, using each
    key's own observation count from `behaviour_counts`
    (`{category_counts, color_counts, pattern_counts}`, maintained by
    `style_dna_service.update_behaviour_weights`).

    Returns a dict shaped exactly like `behaviour_weights`
    (`{category_likes, color_likes, pattern_likes}`) — directly usable as the
    `behaviour_weights` argument to `scoring.calculate_behaviour_score`.

    Safe end-to-end with `style_dna=None` and/or `behaviour_counts=None` —
    returns an all-empty dict (no keys observed anywhere), which
    `calculate_behaviour_score` already treats as "no signal -> neutral 0.5".
    """
    quiz = quiz_prior_from_style_dna(style_dna)
    behaviour_counts = behaviour_counts or {}
    style_dna = style_dna or {}
    behaviour_weights = style_dna.get("behaviour_weights", {}) or {}

    def _blend_group(quiz_group: dict, behaviour_group: dict, count_group: dict) -> dict[str, float]:
        keys = set(quiz_group) | set(behaviour_group)
        return {
            key: round(
                blend_key(
                    quiz_group.get(key), behaviour_group.get(key), int(count_group.get(key, 0) or 0), k
                ),
                4,
            )
            for key in keys
        }

    return {
        "category_likes": _blend_group(
            quiz.get("category_likes", {}),
            behaviour_weights.get("category_likes", {}),
            behaviour_counts.get("category_counts", {}) or {},
        ),
        "color_likes": _blend_group(
            quiz.get("color_likes", {}),
            behaviour_weights.get("color_likes", {}),
            behaviour_counts.get("color_counts", {}) or {},
        ),
        "pattern_likes": _blend_group(
            quiz.get("pattern_likes", {}),
            behaviour_weights.get("pattern_likes", {}),
            behaviour_counts.get("pattern_counts", {}) or {},
        ),
    }
