"""Composition engine (RI-4) — anchor selection + greedy slot-fill.

This module is the PURE core of outfit generation: every public function here
takes already-loaded in-memory objects (a list of `WardrobeItem`s, plain
dicts/dataclasses for weather/rotation state) and returns plain dataclasses.
No DB session, no `select()`, no network call. This is what makes
`scripts/eval_seven_day.py` and the unit tests in `tests/test_composition.py`
/ `tests/test_rotation.py` / `tests/test_explanations.py` runnable without a
live Postgres.

`algorithm.generate_daily_outfits` is the thin DB shell around
`compose_daily_outfits`: it loads the wardrobe/user/event rows, calls into
this module, and hands the result to the endpoint for persistence
(`recommendation_event_crud.bulk_create_shown`). Nothing in this module
imports `sqlalchemy` or touches `models.outfit.Outfit`.

Pair-scoring primitives (`calculate_color_harmony_detailed`,
`calculate_formality_score`, `_load_palette`, ...) stay defined in
`algorithm.py` — that module is still their canonical home (imported
elsewhere by `services/stats/wardrobe_stats.py` and `scripts/eval_outfits.py`)
— this module imports them rather than duplicating them. `algorithm.py`
imports `compose_daily_outfits` from here with a LAZY (in-function) import to
avoid a circular import, the same pattern `context_scoring.py` already uses
for the reverse direction.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import TYPE_CHECKING, Any

from attreq_api.services.recommendation.cold_start import (
    cold_start_prior,
    is_recently_added,
    warm_items_for,
)
from attreq_api.services.recommendation.color_harmony import harmony_against_set
from attreq_api.services.recommendation.color_utils import color_family
from attreq_api.services.recommendation.explanations import explain
from attreq_api.services.recommendation.rotation import (
    REDISCOVERY_LABEL_FLOOR,
    REDISCOVERY_MAX_BONUS,
    build_rotation_context,
    combo_in_recent,
    combo_penalty,
    item_decay_penalty,
    rediscovery_bonus_for_stale_item,
)

if TYPE_CHECKING:
    from datetime import datetime
    from uuid import UUID

    from attreq_api.models.wardrobe import WardrobeItem
    from attreq_api.services.recommendation.rotation import RotationContext

MIN_ANCHORS = 3
MAX_ANCHORS = 5

_FOOTWEAR_KEYS = ("shoe", "boot", "sneaker", "sandal", "footwear")
_OUTERWEAR_KEYS = ("jacket", "coat", "blazer", "outerwear")
_BOTTOM_KEYS = (
    "jeans",
    "pants",
    "trousers",
    "chinos",
    "shorts",
    "skirt",
    "dress pants",
    "sweatpants",
    "bottom",
)
_TOP_KEYS = (
    "shirt",
    "t-shirt",
    "tshirt",
    "blouse",
    "top",
    "sweater",
    "hoodie",
    "suit",
)
_ACCESSORY_KEYS = ("accessory", "bag", "hat", "scarf", "belt", "jewelry")

GREY_INVENTORY_STALE_DAYS = 60


# ============================================================================
# Dataclasses
# ============================================================================


@dataclass(frozen=True)
class WardrobePools:
    """Category-routed, already-14-day-worn-excluded item pools."""

    tops: list[WardrobeItem] = field(default_factory=list)
    bottoms: list[WardrobeItem] = field(default_factory=list)
    fullbody: list[WardrobeItem] = field(default_factory=list)
    footwear: list[WardrobeItem] = field(default_factory=list)
    outerwear: list[WardrobeItem] = field(default_factory=list)
    accessories: list[WardrobeItem] = field(default_factory=list)


@dataclass(frozen=True)
class SlotPlan:
    """Which slots today's outfit needs, decided from weather/occasion/pools."""

    need_footwear: bool
    need_outerwear: bool
    fullbody_eligible: bool


@dataclass
class OutfitCandidate:
    """One generated outfit + its full score breakdown."""

    top_item: WardrobeItem | None
    bottom_item: WardrobeItem | None
    fullbody_item: WardrobeItem | None
    footwear_item: WardrobeItem | None
    outerwear_item: WardrobeItem | None
    accessory_item: WardrobeItem | None
    color_harmony_branch: str
    score_components: dict[str, float]
    total_score: float
    weather: dict[str, Any]
    occasion: str
    explanation: str = ""
    confidence: str = "normal"
    rediscovery: bool = False
    rediscovery_item_id: str | None = None

    @property
    def combo_key(self) -> frozenset[UUID]:
        if self.fullbody_item is not None:
            return frozenset({self.fullbody_item.id})
        ids = {i.id for i in (self.top_item, self.bottom_item) if i is not None}
        return frozenset(ids)

    @property
    def core_items(self) -> list[WardrobeItem]:
        if self.fullbody_item is not None:
            return [self.fullbody_item]
        return [i for i in (self.top_item, self.bottom_item) if i is not None]


# ============================================================================
# Pool building + slot planning
# ============================================================================


def build_pools(items: list[WardrobeItem], worn_item_ids: set[UUID]) -> WardrobePools:
    """Category-route `items`, hard-excluding the 14-day worn set.

    `is_fullbody` items are routed to `fullbody` regardless of their category
    string and never enter `tops`/`bottoms` — a fullbody garment is not
    top x bottom pairable (DeepFashion taxonomy). Items matching none of the
    known buckets simply don't participate (no 50/50 fallback — see module
    docstring / finalized plan section 5.1: with `is_fullbody` explicit, a
    blind fallback split can only mis-slot).
    """
    pools = WardrobePools(tops=[], bottoms=[], fullbody=[], footwear=[], outerwear=[], accessories=[])
    for item in items:
        if item.id in worn_item_ids:
            continue
        if item.is_fullbody:
            pools.fullbody.append(item)
            continue
        category = (item.category or "").lower()
        if any(k in category for k in _FOOTWEAR_KEYS):
            pools.footwear.append(item)
        elif any(k in category for k in _OUTERWEAR_KEYS):
            pools.outerwear.append(item)
        elif any(k in category for k in _BOTTOM_KEYS):
            pools.bottoms.append(item)
        elif any(k in category for k in _TOP_KEYS):
            pools.tops.append(item)
        elif any(k in category for k in _ACCESSORY_KEYS):
            pools.accessories.append(item)
    return pools


def plan_slots(weather: dict[str, Any], occasion: str, pools: WardrobePools) -> SlotPlan:
    """Decide today's slot list from context.

    Footwear is included whenever owned; outerwear iff temp < 15C or
    rain/snow (launch-M3 section 3.1 gate); fullbody is eligible whenever the
    pool is non-empty (the anchor-selection step decides whether it actually
    anchors any given candidate).
    """
    temp = weather.get("temp", 20.0)
    condition = (weather.get("condition") or "").lower()
    need_outerwear = temp < 15.0 or condition in {"rain", "rainy", "snow", "snowy", "storm", "thunderstorm"}
    return SlotPlan(
        need_footwear=bool(pools.footwear),
        need_outerwear=need_outerwear and bool(pools.outerwear),
        fullbody_eligible=bool(pools.fullbody),
    )


# ============================================================================
# Anchor selection
# ============================================================================


def _is_grey_inventory(item: WardrobeItem, today: date) -> bool:
    if (item.wear_count or 0) == 0:
        return True
    return bool(item.last_worn and (today - item.last_worn).days > GREY_INVENTORY_STALE_DAYS)


def _anchor_diversity_key(item: WardrobeItem) -> tuple[str, str]:
    return ((item.category or "").strip().lower(), color_family(item.color_primary))


def select_anchors(
    pools: WardrobePools,
    k: int,
    today: date | None = None,
    rotation_ctx: RotationContext | None = None,
) -> list[WardrobeItem]:
    """Pick 3-5 diverse anchor items from tops + fullbody.

    Diversity: no two anchors share (category, color-family). At least one
    grey-inventory anchor (wear_count == 0 or stale `last_worn`) and, when
    the wardrobe owns any, at least one fullbody anchor are force-included
    (up to `MAX_ANCHORS`) when the pool allows — this is what makes the
    "a wardrobe containing a dress can receive a dress-anchored outfit"
    exit criterion true on more than a single lucky day.

    Rotation-aware ordering: candidates are sorted least-recently-shown
    first (via `rotation_ctx.recent_item_last_shown`, the same 7-day signal
    `item_decay_penalty` uses), so which items become anchors ROTATES across
    consecutive days instead of freezing on the same fixed subset forever —
    necessary for `generate_outfits`'s hard combo-exclusion to actually reach
    enough of the top x bottom space over a multi-day window. Falls back to
    a deterministic id-sort when `rotation_ctx` is omitted (single-shot
    callers / tests that don't care about day-over-day rotation).
    """
    today = today or date.today()
    raw = list(pools.tops) + list(pools.fullbody)
    if not raw:
        return []

    def _sort_key(item: WardrobeItem) -> tuple[int, int, str]:
        last_shown = rotation_ctx.recent_item_last_shown.get(item.id) if rotation_ctx else None
        recency_rank = 0 if last_shown is None else 1
        last_shown_ordinal = last_shown.toordinal() if last_shown else 0
        return (recency_rank, last_shown_ordinal, str(item.id))

    candidates = sorted(raw, key=_sort_key)

    # Anchor pool size is independent of `k` (the number of outfits ultimately
    # returned) — always attempt up to MAX_ANCHORS so `generate_outfits` has
    # enough raw candidates to both rank well and satisfy hard exclusion.
    # Capped at `len(candidates)` first so a small pool (e.g. 2 items) never
    # gets a target above what actually exists — `min(len, MAX_ANCHORS)`
    # already lands at/above MIN_ANCHORS whenever the pool is that large.
    target = min(len(candidates), MAX_ANCHORS)

    # Strict diversity pass: a duplicate (category, color-family) key is never
    # added, even if that leaves fewer than `target` anchors — diversity is a
    # hard rule, not a soft preference backfilled with near-duplicates when
    # the pool is small (see finalized plan section 11: "diversity/pool
    # constraints shrink naturally").
    selected: list[WardrobeItem] = []
    seen_keys: set[tuple[str, str]] = set()
    for item in candidates:
        key = _anchor_diversity_key(item)
        if key in seen_keys:
            continue
        selected.append(item)
        seen_keys.add(key)
        if len(selected) >= target:
            break

    required: list[WardrobeItem] = []
    grey_pool = [c for c in candidates if _is_grey_inventory(c, today)]
    if grey_pool and not any(_is_grey_inventory(a, today) for a in selected):
        required.append(grey_pool[0])

    fullbody_pool = [c for c in candidates if c.is_fullbody]
    if fullbody_pool and not any(a.is_fullbody for a in selected):
        required.append(fullbody_pool[0])

    for extra in required:
        if extra in selected:
            continue
        if len(selected) < MAX_ANCHORS:
            selected.append(extra)
        else:
            # Replace the least-favored current slot (last, by rotation
            # order) that isn't itself one of `required`'s other entries.
            replace_at = len(selected) - 1
            while replace_at > 0 and selected[replace_at] in required:
                replace_at -= 1
            selected[replace_at] = extra

    return selected


# ============================================================================
# Grey-inventory / cold-start dispatch (mutually exclusive, section 5.4)
# ============================================================================


def classify_item_bonus(
    item: WardrobeItem,
    *,
    warm_items: list[WardrobeItem],
    items_with_prior_events: set[UUID],
    today: date,
) -> tuple[str, float]:
    """Route one item to exactly one of {"cold_start", "rediscovery", "none"}.

    A `wear_count == 0` item is either genuinely new (cold-start: no prior
    `recommendation_events` AND recently added) or owned-but-neglected
    (rediscovery: everything else with `wear_count == 0`, or a stale
    `last_worn`) — never both, so the grey-inventory `<= +0.05` total cap
    (rediscovery) and the cold-start `<= +0.08` cap never stack on one item.
    """
    has_prior_events = item.id in items_with_prior_events
    recently_added = is_recently_added(item, today)

    if (item.wear_count or 0) == 0:
        if not has_prior_events and recently_added:
            bonus = cold_start_prior(
                item,
                warm_items,
                has_prior_events=has_prior_events,
                is_recently_added=recently_added,
            )
            return ("cold_start", bonus) if bonus > 0 else ("none", 0.0)
        return ("rediscovery", REDISCOVERY_MAX_BONUS)

    if item.last_worn and (today - item.last_worn).days >= 60:
        bonus = rediscovery_bonus_for_stale_item(item, today)
        return ("rediscovery", bonus) if bonus > 0 else ("none", 0.0)

    return ("none", 0.0)


# ============================================================================
# Pair / candidate scoring
# ============================================================================


def _apply_weights(weights: dict[str, float], centroid_active: bool) -> dict[str, float]:
    """Active-key renormalization (RI-5): when the RI-6 centroid signal isn't
    available this generation (`item_vectors`/`user_centroid` both `None`),
    drop its weight mass and renormalize the remaining keys to sum 1 rather
    than silently discarding it. Generic over both the Phase-A
    `weight_fitting.FALLBACK_WEIGHTS` constant and a Phase-B fitted `W` from
    `weight_fitting.get_active_weights` — same shape, same treatment.
    """
    if centroid_active:
        return weights
    active = {k: v for k, v in weights.items() if k != "centroid"}
    total = sum(active.values()) or 1.0
    return {k: v / total for k, v in active.items()}


def _base_compatibility(
    core_items: list[WardrobeItem],
    weather: dict[str, Any],
    occasion: str,
    style_dna: dict[str, Any] | None,
    now: datetime | None,
    item_vectors: dict[UUID, list[float]] | None = None,
    user_centroid: list[float] | None = None,
    weights: dict[str, float] | None = None,
    formality_bias: float = 0.0,
) -> tuple[float, dict[str, float], str]:
    """Weighted color/context/style_dna/behaviour(/centroid) blend.

    RI-5 (Task 5.1): the old hard scheme-switch keyed on "does this user have
    a Style DNA profile" is gone. Unconditionally: `style_dna_score` (quiz
    content, defaults 0.5 with no quiz) and `behaviour_score` (now computed
    from the Bayesian quiz->behaviour blend, `blend.compute_effective_pref` —
    a no-quiz, no-feedback user gets a neutral 0.5 for both, same net effect
    as the old "no style_dna" branch, but with no cliff as behaviour
    accumulates). `weights` is the aggregation weight set — a Phase-A
    hand-tuned constant or a Phase-B fitted `W`
    (`weight_fitting.get_active_weights`), read ONCE per generation by the
    caller and threaded down here; never fitted in this call path. Absent
    centroid data, its weight mass is redistributed (`_apply_weights`) rather
    than wasted on a fixed neutral 0.5 term.

    Returns `(base_compatibility, components, branch)`. `components` never
    includes `preference_bonus` — that stays a separate additive term
    (section 5.5) so `base_compatibility` is purely the positive
    compatibility signal the confidence hedge keys off of.
    """
    # Deferred import: algorithm.py is the canonical home of these pair-scoring
    # primitives (also imported by services/stats + scripts/eval_outfits.py);
    # importing them at module load time here would be fine in this direction
    # (composition -> algorithm), but algorithm.py needs compose_daily_outfits
    # from THIS module, so algorithm.py defers ITS import instead. Both sides
    # import lazily is unnecessary; importing here at module scope is safe.
    from attreq_api.services.recommendation.algorithm import (
        _load_palette,
        calculate_color_harmony_detailed,
    )
    from attreq_api.services.recommendation.context_scoring import calculate_context_score
    from attreq_api.services.recommendation.weight_fitting import FALLBACK_WEIGHTS
    from attreq_api.services.style_dna.blend import compute_effective_pref
    from attreq_api.services.style_dna.color_families import color_family_for_name
    from attreq_api.services.style_dna.personal_color import apply_personal_color_adjustment
    from attreq_api.services.style_dna.scoring import (
        calculate_behaviour_score,
        calculate_style_dna_score,
    )

    if len(core_items) == 2:
        top, bottom = core_items
        harmony_result = calculate_color_harmony_detailed(top, bottom)
        color_score = harmony_result.score
        branch = harmony_result.branch

        top_palette = _load_palette(top)
        top_dominant_lab = top_palette[0].lab if top_palette else None
        top_color_family = color_family_for_name(top.color_primary)
        color_score = apply_personal_color_adjustment(
            color_score, top_dominant_lab, top_color_family, style_dna
        )
    else:
        # Fullbody: a single garment has no partner to judge color harmony
        # against by construction. A one-piece was designed as a single
        # look (no mix-and-match mismatch risk the way separates have), so
        # the flat default sits above the *average* pair score rather than
        # the middle of the range — mild flat default, branch "none" (never
        # mislabelled as a real winning branch).
        color_score = 0.85
        branch = "none"

    context_score, context_detail = calculate_context_score(
        core_items, occasion, weather, now=now, formality_bias=formality_bias
    )

    # RI-6: centroid is "active" only when the caller (algorithm.py, gated by
    # settings.embeddings_enabled) actually threaded non-None data through —
    # so EMBEDDINGS_ENABLED=false takes the exact pre-RI-6 branches below,
    # unchanged. `centroid_score` itself defaults to a neutral 0.5 when a
    # given item has no stored vector yet, even while active.
    from attreq_api.services.recommendation.similarity import centroid_score as _centroid_score

    centroid_active = item_vectors is not None or user_centroid is not None
    centroid_component = 0.5
    if centroid_active:
        item_vectors = item_vectors or {}
        per_item = [
            _centroid_score(item_vectors.get(item.id), user_centroid) for item in core_items
        ]
        if per_item:
            centroid_component = sum(per_item) / len(per_item)

    # RI-5 (Task 5.1): unconditional Bayesian blend — no hard switch on
    # "profile exists". `style_dna or {}` -> calculate_style_dna_score
    # defaults 0.5 with no quiz; compute_effective_pref -> neutral 0.5 per
    # key with no quiz AND no observed behaviour, fading toward observed
    # behaviour per-key as `behaviour_counts` accumulate (see blend.py).
    style_dna_dict = style_dna or {}
    effective_pref = compute_effective_pref(
        style_dna_dict, style_dna_dict.get("behaviour_counts", {}), k=15
    )
    style_dna_score = calculate_style_dna_score(core_items, style_dna_dict)
    behaviour_score = calculate_behaviour_score(core_items, effective_pref)

    active_weights = _apply_weights(weights or FALLBACK_WEIGHTS, centroid_active)
    base = (
        active_weights.get("color_harmony", 0.0) * color_score
        + active_weights.get("formality", 0.0) * context_score
        + active_weights.get("style_dna", 0.0) * style_dna_score
        + active_weights.get("behaviour", 0.0) * behaviour_score
    )
    if centroid_active:
        base += active_weights.get("centroid", 0.0) * centroid_component

    components = {
        "color_harmony": round(color_score, 4),
        "formality": round(context_score, 4),
        "occasion_fit": round(context_detail["occasion_fit"], 4),
        "weather_score": round(context_detail["weather_score"], 4),
        "time_score": round(context_detail["time_score"], 4),
        "style_dna": round(style_dna_score, 4),
        "behaviour": round(behaviour_score, 4),
        "centroid": round(centroid_component, 4) if centroid_active else None,
        "base_compatibility": round(base, 4),
    }
    return base, components, branch


def _preference_bonus(core_items: list[WardrobeItem], preferred_colors: dict[str, int]) -> float:
    if not preferred_colors:
        return 0.0
    bonus = 0.0
    for item in core_items:
        if item.color_primary and item.color_primary.lower() in preferred_colors:
            bonus += 0.1
    return round(bonus, 4)


def _item_bonuses(
    core_items: list[WardrobeItem],
    *,
    warm_items: list[WardrobeItem],
    items_with_prior_events: set[UUID],
    today: date,
) -> tuple[float, float, str | None, float]:
    """Sum cold-start / rediscovery bonuses across `core_items`. Returns
    `(cold_start_bonus, rediscovery_bonus, best_rediscovery_item_id, best_rediscovery_bonus)`
    — the sum of rediscovery bonuses is capped at `REDISCOVERY_MAX_BONUS`
    (not per-item, section 5.2); the "best" item/bonus feed the one-per-batch
    labeling post-pass in `generate_outfits`.
    """
    cold_start_total = 0.0
    rediscovery_total = 0.0
    best_item_id: str | None = None
    best_bonus = 0.0
    for item in core_items:
        kind, bonus = classify_item_bonus(
            item, warm_items=warm_items, items_with_prior_events=items_with_prior_events, today=today
        )
        if kind == "cold_start":
            cold_start_total += bonus
        elif kind == "rediscovery":
            rediscovery_total += bonus
            if bonus > best_bonus:
                best_bonus = bonus
                best_item_id = str(item.id)
    rediscovery_total = min(REDISCOVERY_MAX_BONUS, rediscovery_total)
    return round(cold_start_total, 4), round(rediscovery_total, 4), best_item_id, best_bonus


def _rotation_penalty(core_items: list[WardrobeItem], rotation_ctx: RotationContext) -> float:
    return round(sum(item_decay_penalty(i.id, rotation_ctx) for i in core_items), 4)


def _pick_best_slot_item(
    pool: list[WardrobeItem],
    reference_items: list[WardrobeItem],
    rotation_ctx: RotationContext,
) -> WardrobeItem | None:
    """Argmax-fill one accessory-ish slot (footwear/outerwear) against an
    already-chosen reference set, per launch-M3 section 3.2:
    `0.5*avg_harmony_against_reference + 0.5*formality_fit`, minus the same
    soft item-decay penalty core items get.
    """
    from attreq_api.services.recommendation.algorithm import _load_palette, _lookup_formality_level

    if not pool:
        return None

    reference_palettes = []
    for ref in reference_items:
        palette = _load_palette(ref)
        if palette:
            reference_palettes.append(palette[0])

    reference_levels = [_lookup_formality_level(ref.category, ref.occasion) for ref in reference_items]
    avg_reference_level = sum(reference_levels) / len(reference_levels) if reference_levels else 1.0

    best: tuple[WardrobeItem, float] | None = None
    for candidate in pool:
        candidate_palette = _load_palette(candidate)
        dominant = candidate_palette[0] if candidate_palette else None
        harmony_score = harmony_against_set(dominant, reference_palettes) if dominant else 0.5

        level = _lookup_formality_level(candidate.category, candidate.occasion)
        formality_fit = max(0.0, 1.0 - abs(level - avg_reference_level) / 3.0)

        score = 0.5 * harmony_score + 0.5 * formality_fit
        score += item_decay_penalty(candidate.id, rotation_ctx)

        if best is None or score > best[1]:
            best = (candidate, score)

    return best[0] if best else None


def _accessory_pick(pool: list[WardrobeItem], rotation_ctx: RotationContext) -> WardrobeItem | None:
    """Best-not-recently-shown accessory (deterministic replacement for the
    pre-RI-4 `random.choice` — reproducible for tests/eval): the one with the
    least (least-negative/most-zero) item-decay penalty, ties broken by id.
    """
    if not pool:
        return None
    return min(pool, key=lambda a: (-item_decay_penalty(a.id, rotation_ctx), str(a.id)))


def _propagation_adjustment(
    core_items: list[WardrobeItem], propagation_penalties: dict[UUID, float] | None
) -> float:
    """Sum of each core item's already-clamped (+/-0.05) thumbs-propagation
    adjustment (finalized plan §4) — e.g. a top+bottom outfit can see up to
    +/-0.10 total, since the clamp is per-item, not per-outfit."""
    if not propagation_penalties:
        return 0.0
    return round(sum(propagation_penalties.get(item.id, 0.0) for item in core_items), 4)


def _build_candidate(
    *,
    top_item: WardrobeItem | None,
    bottom_item: WardrobeItem | None,
    fullbody_item: WardrobeItem | None,
    pools: WardrobePools,
    slot_plan: SlotPlan,
    style_dna: dict[str, Any] | None,
    rotation_ctx: RotationContext,
    weather: dict[str, Any],
    occasion: str,
    preferred_colors: dict[str, int],
    warm_items: list[WardrobeItem],
    items_with_prior_events: set[UUID],
    today: date,
    now: datetime | None,
    item_vectors: dict[UUID, list[float]] | None = None,
    user_centroid: list[float] | None = None,
    propagation_penalties: dict[UUID, float] | None = None,
    weights: dict[str, float] | None = None,
    formality_bias: float = 0.0,
) -> OutfitCandidate:
    core_items = [i for i in (top_item, bottom_item, fullbody_item) if i is not None]

    base, components, branch = _base_compatibility(
        core_items,
        weather,
        occasion,
        style_dna,
        now,
        item_vectors,
        user_centroid,
        weights=weights,
        formality_bias=formality_bias,
    )
    preference_bonus = _preference_bonus(core_items, preferred_colors)
    cold_start_bonus, rediscovery_bonus, best_redisc_id, best_redisc_bonus = _item_bonuses(
        core_items, warm_items=warm_items, items_with_prior_events=items_with_prior_events, today=today
    )
    rotation_penalty = _rotation_penalty(core_items, rotation_ctx)
    propagation_adjustment = _propagation_adjustment(core_items, propagation_penalties)

    reference_so_far = list(core_items)
    footwear_item = None
    if slot_plan.need_footwear:
        footwear_item = _pick_best_slot_item(pools.footwear, reference_so_far, rotation_ctx)
        if footwear_item is not None:
            reference_so_far = [*reference_so_far, footwear_item]

    outerwear_item = None
    if slot_plan.need_outerwear:
        outerwear_item = _pick_best_slot_item(pools.outerwear, reference_so_far, rotation_ctx)

    accessory_item = _accessory_pick(pools.accessories, rotation_ctx)

    total = (
        base
        + preference_bonus * 0.2
        + cold_start_bonus
        + rediscovery_bonus
        + rotation_penalty
        + propagation_adjustment
    )
    total = max(0.0, min(1.0, total))

    components["preference_bonus"] = round(preference_bonus, 4)
    components["cold_start_bonus"] = round(cold_start_bonus, 4)
    components["rediscovery_bonus"] = round(rediscovery_bonus, 4)
    components["rotation_penalty"] = round(rotation_penalty, 4)
    components["propagation_adjustment"] = propagation_adjustment if propagation_penalties is not None else None
    components["total"] = round(total, 4)

    return OutfitCandidate(
        top_item=top_item,
        bottom_item=bottom_item,
        fullbody_item=fullbody_item,
        footwear_item=footwear_item,
        outerwear_item=outerwear_item,
        accessory_item=accessory_item,
        color_harmony_branch=branch,
        score_components=components,
        total_score=total,
        weather=weather,
        occasion=occasion,
        rediscovery_item_id=best_redisc_id if best_redisc_bonus > REDISCOVERY_LABEL_FLOOR else None,
    )


# ============================================================================
# Generation
# ============================================================================


def _any_unseen_combo_exists(
    anchors: list[WardrobeItem], pools: WardrobePools, rotation_ctx: RotationContext
) -> bool:
    for anchor in anchors:
        if anchor.is_fullbody:
            if not combo_in_recent(frozenset({anchor.id}), rotation_ctx):
                return True
            continue
        for bottom in pools.bottoms:
            if bottom.id == anchor.id:
                continue
            if not combo_in_recent(frozenset({anchor.id, bottom.id}), rotation_ctx):
                return True
    return False


def _fill_bottom_for_anchor(
    anchor: WardrobeItem,
    pools: WardrobePools,
    *,
    slot_plan: SlotPlan,
    style_dna: dict[str, Any] | None,
    rotation_ctx: RotationContext,
    weather: dict[str, Any],
    occasion: str,
    preferred_colors: dict[str, int],
    warm_items: list[WardrobeItem],
    items_with_prior_events: set[UUID],
    today: date,
    now: datetime | None,
    allow_repeat: bool,
    used_bottom_ids: set[UUID],
    item_vectors: dict[UUID, list[float]] | None = None,
    user_centroid: list[float] | None = None,
    propagation_penalties: dict[UUID, float] | None = None,
    weights: dict[str, float] | None = None,
    formality_bias: float = 0.0,
) -> OutfitCandidate | None:
    """Argmax-fill the bottom slot for a top anchor, HARD-excluding any
    bottom whose combo with this anchor is already in `rotation_ctx
    .recent_combos` unless `allow_repeat` (the feasibility fallback — every
    remaining combo in this batch has already been shown)."""

    def _candidates_from(bottoms: list[WardrobeItem]) -> OutfitCandidate | None:
        best: OutfitCandidate | None = None
        for bottom in bottoms:
            if bottom.id == anchor.id:
                continue
            combo = frozenset({anchor.id, bottom.id})
            is_repeat = combo_in_recent(combo, rotation_ctx)
            if is_repeat and not allow_repeat:
                continue

            candidate = _build_candidate(
                top_item=anchor,
                bottom_item=bottom,
                fullbody_item=None,
                pools=pools,
                slot_plan=slot_plan,
                style_dna=style_dna,
                rotation_ctx=rotation_ctx,
                weather=weather,
                occasion=occasion,
                preferred_colors=preferred_colors,
                warm_items=warm_items,
                items_with_prior_events=items_with_prior_events,
                today=today,
                now=now,
                item_vectors=item_vectors,
                user_centroid=user_centroid,
                propagation_penalties=propagation_penalties,
                weights=weights,
                formality_bias=formality_bias,
            )
            if is_repeat:
                penalty = combo_penalty(combo, rotation_ctx)
                candidate.total_score = max(0.0, min(1.0, candidate.total_score + penalty))
                candidate.score_components["rotation_penalty"] = round(
                    candidate.score_components["rotation_penalty"] + penalty, 4
                )
                candidate.score_components["total"] = round(candidate.total_score, 4)

            if best is None or candidate.total_score > best.total_score:
                best = candidate
        return best

    # Prefer bottoms not already used by another candidate in this batch;
    # fall back to the full pool if that leaves nothing (small wardrobes).
    unused = [b for b in pools.bottoms if b.id not in used_bottom_ids]
    result = _candidates_from(unused)
    if result is None:
        result = _candidates_from(pools.bottoms)
    return result


def _build_fullbody_candidate(
    anchor: WardrobeItem,
    pools: WardrobePools,
    *,
    slot_plan: SlotPlan,
    style_dna: dict[str, Any] | None,
    rotation_ctx: RotationContext,
    weather: dict[str, Any],
    occasion: str,
    preferred_colors: dict[str, int],
    warm_items: list[WardrobeItem],
    items_with_prior_events: set[UUID],
    today: date,
    now: datetime | None,
    allow_repeat: bool,
    item_vectors: dict[UUID, list[float]] | None = None,
    user_centroid: list[float] | None = None,
    propagation_penalties: dict[UUID, float] | None = None,
    weights: dict[str, float] | None = None,
    formality_bias: float = 0.0,
) -> OutfitCandidate | None:
    combo = frozenset({anchor.id})
    is_repeat = combo_in_recent(combo, rotation_ctx)
    if is_repeat and not allow_repeat:
        return None

    candidate = _build_candidate(
        top_item=None,
        bottom_item=None,
        fullbody_item=anchor,
        pools=pools,
        slot_plan=slot_plan,
        style_dna=style_dna,
        rotation_ctx=rotation_ctx,
        weather=weather,
        occasion=occasion,
        preferred_colors=preferred_colors,
        warm_items=warm_items,
        items_with_prior_events=items_with_prior_events,
        today=today,
        now=now,
        item_vectors=item_vectors,
        user_centroid=user_centroid,
        propagation_penalties=propagation_penalties,
        weights=weights,
        formality_bias=formality_bias,
    )
    if is_repeat:
        penalty = combo_penalty(combo, rotation_ctx)
        candidate.total_score = max(0.0, min(1.0, candidate.total_score + penalty))
        candidate.score_components["rotation_penalty"] = round(
            candidate.score_components["rotation_penalty"] + penalty, 4
        )
        candidate.score_components["total"] = round(candidate.total_score, 4)
    return candidate


def _mark_rediscovery(candidates: list[OutfitCandidate]) -> None:
    """At most one candidate per batch is labeled `rediscovery=True` — the one
    whose best rediscovery item has the highest bonus (must exceed the label
    floor). Every candidate's `total_score` already includes its own
    rediscovery bonus regardless of labeling (see `_item_bonuses`)."""
    best_candidate: OutfitCandidate | None = None
    best_bonus = REDISCOVERY_LABEL_FLOOR
    for candidate in candidates:
        if candidate.rediscovery_item_id is None:
            continue
        bonus = candidate.score_components.get("rediscovery_bonus", 0.0)
        if bonus > best_bonus:
            best_bonus = bonus
            best_candidate = candidate

    for candidate in candidates:
        candidate.rediscovery = candidate is best_candidate
        if not candidate.rediscovery:
            candidate.rediscovery_item_id = None


def generate_outfits(
    slot_plan: SlotPlan,
    pools: WardrobePools,
    *,
    style_dna: dict[str, Any] | None,
    rotation_ctx: RotationContext,
    weather: dict[str, Any],
    occasion: str,
    preferred_colors: dict[str, int] | None = None,
    warm_items: list[WardrobeItem] | None = None,
    items_with_prior_events: set[UUID] | None = None,
    today: date | None = None,
    now: datetime | None = None,
    k: int = 3,
    item_vectors: dict[UUID, list[float]] | None = None,
    user_centroid: list[float] | None = None,
    propagation_penalties: dict[UUID, float] | None = None,
    weights: dict[str, float] | None = None,
    formality_bias: float = 0.0,
) -> list[OutfitCandidate]:
    """Anchor selection + greedy slot-fill, over already-built pools.

    `item_vectors`/`user_centroid`/`propagation_penalties` are RI-6 hooks —
    all default `None`, which is the exact pre-RI-6 code path in
    `_base_compatibility`/`_build_candidate` (no weight reallocation, no
    propagation adjustment). Callers that want the FashionCLIP centroid/
    thumbs-propagation to participate in scoring must pass non-`None` values
    (see `algorithm.py::generate_daily_outfits`, gated behind
    `settings.embeddings_enabled`).

    `weights` (RI-5): the aggregation weight set applied in
    `_base_compatibility` — `None` falls back to
    `weight_fitting.FALLBACK_WEIGHTS` (Phase-A hand-tuned constants); real
    callers pass the result of `weight_fitting.get_active_weights`, read ONCE
    per generation. `formality_bias` (RI-5, Task 5.4a): soft occasion-hint
    bias (`services.recommendation.vibe.VIBE_FORMALITY_BIAS`) folded into the
    context score — `0.0` (the default) reproduces byte-identical pre-RI-5
    behavior.
    """
    today = today or date.today()
    preferred_colors = preferred_colors or {}
    warm_items = warm_items if warm_items is not None else []
    items_with_prior_events = items_with_prior_events or set()

    anchors = select_anchors(pools, k, today=today, rotation_ctx=rotation_ctx)
    if not anchors:
        return []

    allow_repeat = not _any_unseen_combo_exists(anchors, pools, rotation_ctx)

    candidates: list[OutfitCandidate] = []
    used_bottom_ids: set[UUID] = set()
    for anchor in anchors:
        if anchor.is_fullbody:
            candidate = _build_fullbody_candidate(
                anchor,
                pools,
                slot_plan=slot_plan,
                style_dna=style_dna,
                rotation_ctx=rotation_ctx,
                weather=weather,
                occasion=occasion,
                preferred_colors=preferred_colors,
                warm_items=warm_items,
                items_with_prior_events=items_with_prior_events,
                today=today,
                now=now,
                allow_repeat=allow_repeat,
                item_vectors=item_vectors,
                user_centroid=user_centroid,
                propagation_penalties=propagation_penalties,
                weights=weights,
                formality_bias=formality_bias,
            )
        else:
            candidate = _fill_bottom_for_anchor(
                anchor,
                pools,
                slot_plan=slot_plan,
                style_dna=style_dna,
                rotation_ctx=rotation_ctx,
                weather=weather,
                occasion=occasion,
                preferred_colors=preferred_colors,
                warm_items=warm_items,
                items_with_prior_events=items_with_prior_events,
                today=today,
                now=now,
                allow_repeat=allow_repeat,
                used_bottom_ids=used_bottom_ids,
                item_vectors=item_vectors,
                user_centroid=user_centroid,
                propagation_penalties=propagation_penalties,
                weights=weights,
                formality_bias=formality_bias,
            )
        if candidate is not None:
            candidates.append(candidate)
            if candidate.bottom_item is not None:
                used_bottom_ids.add(candidate.bottom_item.id)

    candidates.sort(key=lambda c: c.total_score, reverse=True)
    selected = candidates[:k]

    _mark_rediscovery(selected)

    for candidate in selected:
        result = explain(candidate, {"occasion": occasion, "weather": weather}, style_dna)
        candidate.explanation = result.text
        candidate.confidence = result.confidence

    return selected


def compose_daily_outfits(
    items: list[WardrobeItem],
    weather: dict[str, Any],
    occasion: str,
    worn_item_ids: set[UUID],
    shown_events: list[dict],
    style_dna: dict[str, Any] | None,
    k: int = 3,
    today: date | None = None,
    now: datetime | None = None,
    preferred_colors: dict[str, int] | None = None,
    item_vectors: dict[UUID, list[float]] | None = None,
    user_centroid: list[float] | None = None,
    propagation_penalties: dict[UUID, float] | None = None,
    weights: dict[str, float] | None = None,
    formality_bias: float = 0.0,
) -> list[OutfitCandidate]:
    """PURE core: no DB access, no session. Drives the eval harness and the
    unit test suite; `algorithm.generate_daily_outfits` is the thin DB shell
    that loads `items`/`shown_events` and calls this.

    `shown_events` (list of `{"date": date, "item_ids": Iterable[UUID]}`
    dicts) doubles as both the rotation window source (`build_rotation_context`
    internally restricts to the 7-day item / 14-day combo windows) and the
    cold-start "has prior events" signal (here, unfiltered — any historical
    appearance counts), matching section 5.4 of the finalized plan.

    `item_vectors`/`user_centroid`/`propagation_penalties`: RI-6 hooks, see
    `generate_outfits` docstring — all default `None` (no-op, pre-RI-6
    behavior).
    """
    today = today or date.today()
    pools = build_pools(items, worn_item_ids)
    slot_plan = plan_slots(weather, occasion, pools)
    rotation_ctx = build_rotation_context(shown_events, today=today)
    warm_items = warm_items_for(items)
    items_with_prior_events = {
        item_id for event in shown_events for item_id in event.get("item_ids", ())
    }

    return generate_outfits(
        slot_plan,
        pools,
        style_dna=style_dna,
        rotation_ctx=rotation_ctx,
        weather=weather,
        occasion=occasion,
        preferred_colors=preferred_colors or {},
        warm_items=warm_items,
        items_with_prior_events=items_with_prior_events,
        today=today,
        now=now,
        k=k,
        item_vectors=item_vectors,
        user_centroid=user_centroid,
        propagation_penalties=propagation_penalties,
        weights=weights,
        formality_bias=formality_bias,
    )
