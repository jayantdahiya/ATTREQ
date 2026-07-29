"""Context weighting (RI-3) — occasion / weather / time split.

Occupies the formality slot in the existing top-level weight structure
(`algorithm.generate_daily_outfits`'s `0.4/0.4/0.2` no-DNA branch and
`0.2/0.2/0.4/0.2` DNA branch) rather than adding a new top-level weight —
`context_score` *is* what `formality_score` used to mean in that slot, just
computed more richly. Formality-consistency between the two items is folded
inside `calculate_occasion_fit` (via `algorithm.calculate_formality_score`,
imported lazily to avoid a module-load cycle with `algorithm.py`, which
imports `calculate_context_score` from here) rather than blended 50/50
alongside it — blending a second formality term would double-count
formality, since occasion/formality-tier fit already grades it once.

Weights: occasion 0.55 / weather 0.35 / time-of-day 0.10 (SMARTWEAR:
event 50 / weather 30 / age 15 / time 5 over 600 scenarios, 92.4% precision;
age dropped here — Style DNA personalizes instead). `filter_items_by_weather`
remains a hard filter upstream (no shorts at 5°C) — `calculate_weather_score`
only grades items that already passed it.
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from attreq_api.models.wardrobe import WardrobeItem

OCCASION_WEIGHT = 0.55
WEATHER_WEIGHT = 0.35
TIME_WEIGHT = 0.10

_EVENING_OCCASIONS = frozenset({"party", "formal", "date"})
_DAYTIME_OCCASIONS = frozenset({"business", "work"})


def calculate_occasion_fit(items: list[WardrobeItem], occasion: str) -> float:
    """Occasion-tag fit blended with formality consistency (absorbs the old
    `calculate_formality_score`-as-top-level-term role).

    Robust to items lacking occasion tags entirely (`filter_items_by_occasion`
    may have fallen back to weather-filtered items,
    `algorithm.py` ~L560-563): returns a flat neutral 0.5 when *no* item in
    the set carries an occasion tag — there is nothing to assess fit against.
    """
    if not items:
        return 0.5

    tagged_items = [item for item in items if item.occasion]
    if not tagged_items:
        return 0.5

    occasion_lower = (occasion or "").lower()
    tag_scores = []
    for item in items:
        tags = [t.lower() for t in (item.occasion or [])]
        if not tags:
            tag_scores.append(0.5)
        elif occasion_lower in tags:
            tag_scores.append(1.0)
        elif "all" in tags:
            tag_scores.append(0.8)
        else:
            tag_scores.append(0.2)

    tag_fit = sum(tag_scores) / len(tag_scores)

    # Lazy import — `algorithm.py` imports `calculate_context_score` from this
    # module at module scope, so importing `algorithm` here at module scope
    # would be circular. Deferred import breaks the cycle safely.
    from attreq_api.services.recommendation.algorithm import calculate_formality_score

    consistency = calculate_formality_score(items)

    return round(0.7 * tag_fit + 0.3 * consistency, 4)


def calculate_weather_score(items: list[WardrobeItem], weather: dict[str, Any]) -> float:
    """Graded season-tag fit for items that already passed the hard filter
    (`filter_items_by_weather`, which stays as-is — this never re-excludes
    anything, only grades)."""
    if not items:
        return 0.5

    temp = weather.get("temp", 20.0)
    if temp > 25:
        target: str | None = "summer"
    elif temp < 15:
        target = "winter"
    else:
        target = None  # spring/autumn band — multiple tags are equally valid

    scores = []
    for item in items:
        seasons = [s.lower() for s in (item.season or [])]
        if not seasons:
            scores.append(0.7)  # no data — already passed the hard filter, mild credit
        elif "all" in seasons:
            scores.append(0.7)
        elif target and target in seasons or not target and any(s in seasons for s in ("spring", "autumn", "fall")):
            scores.append(1.0)
        else:
            scores.append(0.5)

    return round(sum(scores) / len(scores), 4)


def calculate_time_score(occasion: str, now: datetime | None = None) -> float:
    """Coarse day/evening nudge. Weakest-evidence, low-stakes term (10% mass) —
    a rough heuristic, not a learned signal."""
    now = now or datetime.now()
    is_evening = now.hour >= 17 or now.hour < 5
    occasion_lower = (occasion or "").lower()

    if occasion_lower in _EVENING_OCCASIONS:
        return 0.8 if is_evening else 0.5
    if occasion_lower in _DAYTIME_OCCASIONS:
        return 0.8 if not is_evening else 0.5
    return 0.6


def _formality_hint_alignment(items: list[WardrobeItem], formality_bias: float) -> float:
    """RI-5 (Task 5.4a) — soft morning-vibe nudge, not a hard filter.

    Maps `formality_bias` (from `services.recommendation.vibe
    .VIBE_FORMALITY_BIAS`, roughly [-1, 1]) onto a shifted target formality
    level (0-3 scale, neutral midpoint 1.5) and scores how well the items'
    average formality level aligns with that shifted target — the same
    "consistency" primitive `calculate_occasion_fit` already uses, just
    re-centered. `formality_bias == 0.0` (no hint given) must be a no-op at
    the call site (never invoked with a truthy bias), so this function is
    only ever reached when a hint is actually present.
    """
    from attreq_api.services.recommendation.algorithm import _lookup_formality_level

    if not items:
        return 0.5

    levels = [_lookup_formality_level(item.category, item.occasion) for item in items]
    avg_level = sum(levels) / len(levels)
    target = 1.5 + formality_bias * 1.5
    return round(max(0.0, 1.0 - abs(avg_level - target) / 3.0), 4)


def calculate_context_score(
    items: list[WardrobeItem],
    occasion: str,
    weather: dict[str, Any],
    now: datetime | None = None,
    formality_bias: float = 0.0,
) -> tuple[float, dict[str, float]]:
    """`0.55*occasion_fit + 0.35*weather_score + 0.10*time_score`.

    `formality_bias` (RI-5, Task 5.4a): when nonzero (a morning-vibe hint was
    given — `sharp`/`relaxed`/`bold`), `occasion_fit` is re-blended 70/30
    with a hint-shifted formality-alignment term (`_formality_hint_alignment`)
    — a soft nudge toward higher/lower-formality picks, never a hard filter.
    `formality_bias == 0.0` (the default; no hint) is byte-identical to
    pre-RI-5 behavior — the blend is skipped entirely, not blended with a
    zero-shift (which would still perturb rounding).

    Returns `(total, detail)` — `detail` is added to the outfit's `scores`
    dict for observability (RI-4/eval), not part of the `OutfitScores`
    Pydantic contract.
    """
    occasion_fit = calculate_occasion_fit(items, occasion)
    weather_score = calculate_weather_score(items, weather)
    time_score = calculate_time_score(occasion, now)

    if formality_bias:
        alignment = _formality_hint_alignment(items, formality_bias)
        occasion_fit = round(0.7 * occasion_fit + 0.3 * alignment, 4)

    total = round(
        OCCASION_WEIGHT * occasion_fit + WEATHER_WEIGHT * weather_score + TIME_WEIGHT * time_score,
        4,
    )
    return total, {
        "occasion_fit": occasion_fit,
        "weather_score": weather_score,
        "time_score": time_score,
    }
