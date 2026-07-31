"""Recommendation algorithm for outfit generation."""

import asyncio
import json
import logging
from datetime import date, datetime, timedelta
from typing import Any
from uuid import UUID

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from attreq_api.config.settings import settings
from attreq_api.models.outfit import Outfit
from attreq_api.models.user import User
from attreq_api.models.wardrobe import WardrobeItem
from attreq_api.services.ai.embeddings import weaviate_service
from attreq_api.services.recommendation.color_harmony import (
    HarmonyResult,
    PaletteColor,
    harmony,
    is_functional_neutral,
)
from attreq_api.services.recommendation.legacy_color_lab import legacy_palette_for_item

logger = logging.getLogger(__name__)


# ============================================================================
# RI-6: FashionCLIP item-vector / centroid / propagation loading
# ============================================================================


async def _load_item_vectors(items: list[WardrobeItem]) -> dict[UUID, list[float]]:
    """Best-effort batch fetch of stored FashionCLIP vectors for scoring.

    One `get_vector` call per item via `asyncio.to_thread` (the weaviate-client
    v4 sync client is not awaitable) — soft-fails per item; only called when
    `settings.embeddings_enabled` is True (see caller in
    `generate_daily_outfits`), so this never runs on the default-off path.
    """
    if not items or not weaviate_service.is_connected():
        return {}

    async def _fetch(item: WardrobeItem) -> tuple[UUID, list[float] | None]:
        try:
            vector = await asyncio.to_thread(weaviate_service.get_vector, item.id)
            return item.id, vector
        except Exception as e:
            logger.warning(f"Failed to fetch vector for item {item.id}: {e}")
            return item.id, None

    results = await asyncio.gather(*(_fetch(item) for item in items))
    return {item_id: vector for item_id, vector in results if vector is not None}


async def _load_propagation_penalties(db: AsyncSession, user_id: UUID) -> dict[UUID, float]:
    """Best-effort thumbs-propagation penalties for this generation call —
    only called when `settings.embeddings_enabled` is True (see caller)."""
    try:
        from attreq_api.services.recommendation.similarity import compute_propagation_penalties

        return await compute_propagation_penalties(db, user_id)
    except Exception as e:
        logger.warning(f"Propagation penalty computation failed for user {user_id}: {e}")
        return {}


# ============================================================================
# 1. WEATHER FILTERING
# ============================================================================


async def filter_items_by_weather(
    items: list[WardrobeItem], weather: dict[str, Any]
) -> list[WardrobeItem]:
    """Filter wardrobe items suitable for current weather.

    Temperature-based filtering rules:
    - temp > 25°C: summer items (light fabrics, short sleeves)
    - temp < 15°C: winter items (warm fabrics, long sleeves, layers)
    - 15-25°C: spring/autumn items (moderate weight)

    Condition-based filtering:
    - rainy: avoid delicate fabrics (if we had fabric data)

    Args:
        items: List of wardrobe items
        weather: Weather data dict with 'temp' and 'condition' keys

    Returns:
        Filtered list of weather-appropriate items
    """
    temp = weather.get("temp", 20.0)
    condition = weather.get("condition", "Clear").lower()

    filtered_items = []

    for item in items:
        # Skip items without season data
        if not item.season:
            # Include items without season info by default
            filtered_items.append(item)
            continue

        # Temperature-based filtering
        if temp > 25:
            # Hot weather - prefer summer items
            if "summer" in item.season or "all" in item.season:
                filtered_items.append(item)
        elif temp < 15:
            # Cold weather - prefer winter items
            if "winter" in item.season or "all" in item.season:
                filtered_items.append(item)
        else:
            # Moderate weather - prefer spring/autumn or all-season
            if any(s in item.season for s in ["spring", "autumn", "all"]):
                filtered_items.append(item)

    logger.info(
        f"Weather filtering: {len(items)} items -> {len(filtered_items)} items "
        f"(temp: {temp}°C, condition: {condition})"
    )

    return filtered_items


# ============================================================================
# 2. OCCASION FILTERING
# ============================================================================


async def filter_items_by_occasion(items: list[WardrobeItem], occasion: str) -> list[WardrobeItem]:
    """Filter items by occasion type.

    Supported occasions: casual, formal, party, business, athletic, etc.

    Args:
        items: List of wardrobe items
        occasion: Occasion type (e.g., "casual", "formal")

    Returns:
        Filtered list of occasion-appropriate items
    """
    occasion_lower = occasion.lower()

    filtered_items = []

    for item in items:
        # Skip items without occasion data
        if not item.occasion:
            # Include items without occasion info by default
            filtered_items.append(item)
            continue

        # Check if item is suitable for the occasion
        if occasion_lower in [occ.lower() for occ in item.occasion]:
            filtered_items.append(item)
        elif "all" in [occ.lower() for occ in item.occasion]:
            # Items marked as "all" occasions
            filtered_items.append(item)

    logger.info(
        f"Occasion filtering: {len(items)} items -> {len(filtered_items)} items "
        f"(occasion: {occasion})"
    )

    return filtered_items


# ============================================================================
# 3. RECENT OUTFIT HISTORY
# ============================================================================


async def get_recently_worn_items(db: AsyncSession, user_id: UUID, days: int = 14) -> set[UUID]:
    """Get item IDs worn in the last N days to avoid repetition.

    Args:
        db: Database session
        user_id: User ID
        days: Number of days to look back (default: 14)

    Returns:
        Set of item IDs that were recently worn
    """
    cutoff_date = date.today() - timedelta(days=days)

    # Query outfits worn in the last N days
    query = select(Outfit).where(
        and_(
            Outfit.user_id == user_id,
            Outfit.worn_date >= cutoff_date,
            Outfit.worn_date.isnot(None),
        )
    )

    result = await db.execute(query)
    recent_outfits = result.scalars().all()

    # Collect all item IDs from recent outfits
    worn_item_ids = set()
    for outfit in recent_outfits:
        if outfit.top_item_id:
            worn_item_ids.add(outfit.top_item_id)
        if outfit.bottom_item_id:
            worn_item_ids.add(outfit.bottom_item_id)
        if outfit.fullbody_item_id:
            worn_item_ids.add(outfit.fullbody_item_id)
        if outfit.footwear_item_id:
            worn_item_ids.add(outfit.footwear_item_id)
        if outfit.outerwear_item_id:
            worn_item_ids.add(outfit.outerwear_item_id)
        if outfit.accessory_ids:
            worn_item_ids.update(outfit.accessory_ids)

    logger.info(f"Found {len(worn_item_ids)} items worn in last {days} days")

    return worn_item_ids


# ============================================================================
# 4. COLOR HARMONY SCORING
# ============================================================================


def _load_palette(item: WardrobeItem) -> list[PaletteColor]:
    """RI-3: real RI-2 pixel palette when present, else the legacy named-color
    bridge. `getattr(..., None) or 1` guards transient (never-flushed)
    instances — e.g. `scripts/eval_outfits.py`'s synthetic `WardrobeItem`s —
    where the column's client-side `default=1` hasn't been applied yet, so
    plain attribute access reads `None`, not `1`.
    """
    schema_version = getattr(item, "schema_version", None) or 1
    color_palette = getattr(item, "color_palette", None)

    if schema_version == 2 and color_palette:
        colors: list[PaletteColor] = []
        for entry in color_palette:
            lab = tuple(float(v) for v in entry["lab"])
            raw_is_neutral = bool(entry.get("is_neutral", False))
            colors.append(
                PaletteColor(
                    lab=lab,
                    is_neutral=raw_is_neutral or is_functional_neutral(lab),
                    share=float(entry.get("share", 1.0)),
                )
            )
        return colors

    return legacy_palette_for_item(item)


def calculate_color_harmony_detailed(item1: WardrobeItem, item2: WardrobeItem) -> HarmonyResult:
    """RI-3 color harmony: `max(tonal, neutral_contrast, hue_rule)` over every
    `(c1, c2)` palette-color pair, keeping the single highest-scoring pair
    (not a weighted mean, so a strong secondary-color match on a patterned
    item isn't diluted by an unrelated dominant-color pairing).

    Empty palette on either side (schema_version==1 item with neither
    `color_primary` nor `color_secondary` set) returns the old "unknown color"
    0.5 fallback, branch `"neutral_contrast"` (matches the pre-RI-3 default).
    """
    palette1 = _load_palette(item1)
    palette2 = _load_palette(item2)

    if not palette1 or not palette2:
        return HarmonyResult(0.5, "neutral_contrast", {"reason": "empty_palette"})

    best: HarmonyResult | None = None
    for c1 in palette1:
        for c2 in palette2:
            result = harmony(c1, c2)
            if best is None or result.score > best.score:
                best = result

    assert best is not None  # both palettes non-empty => at least one pair scored
    return best


def calculate_color_harmony_score(item1: WardrobeItem, item2: WardrobeItem) -> float:
    """Calculate color compatibility score between two items (0-1).

    RI-3: delegates to `calculate_color_harmony_detailed().score` — real
    CIELAB palettes (RI-2, `schema_version == 2`) or the legacy named-color
    Lab bridge otherwise. Name+signature preserved for existing importers
    (`services/stats/wardrobe_stats.py::score_pair`,
    `scripts/eval_outfits.py`, `services/recommendation/__init__.py`).
    """
    return calculate_color_harmony_detailed(item1, item2).score


# ============================================================================
# 5. FORMALITY MATCHING
# ============================================================================


# RI-4 (launch-M3 section 3.2, satisfied here): extended with footwear/
# outerwear substring keys so `_lookup_formality_level` (and, through it,
# `composition._pick_best_slot_item`'s formality_fit term) can judge shoe/coat
# formality the same way top/bottom formality is judged.
FORMALITY_MAP = {
    "suit": 3,
    "blazer": 3,
    "dress shirt": 3,
    "dress pants": 3,
    "dress shoe": 3,
    "dress": 3,
    "skirt": 2,
    "blouse": 2,
    "chinos": 2,
    "coat": 2,
    "boot": 2,
    "jeans": 1,
    "t-shirt": 1,
    "shorts": 1,
    "hoodie": 1,
    "jacket": 1,
    "sneaker": 1,
    "sandal": 1,
    "sweatpants": 0,
    "athletic wear": 0,
}


def _lookup_formality_level(category: str | None, occasion: list[str] | None = None) -> int:
    """Best-effort formality level (0-3) for one item's category + occasion
    tags. Extracted out of `calculate_formality_score` so
    `composition._pick_best_slot_item` (footwear/outerwear picks) can reuse
    the exact same lookup rather than a second, drifting copy."""
    category_lower = (category or "").lower()
    level = 1  # Default to casual
    for key, mapped_level in FORMALITY_MAP.items():
        if key in category_lower:
            level = mapped_level
            break

    if occasion:
        occasion_lower = [occ.lower() for occ in occasion]
        if "formal" in occasion_lower:
            level = max(level, 3)
        elif "business" in occasion_lower:
            level = max(level, 2)

    return level


def calculate_formality_score(items: list[WardrobeItem]) -> float:
    """Ensure outfit items have similar formality level.

    Formality levels:
    - Formal: 3
    - Business/Smart Casual: 2
    - Casual: 1
    - Athletic: 0

    Args:
        items: List of wardrobe items in the outfit

    Returns:
        Formality consistency score between 0 and 1
    """
    # Get formality levels for each item
    formality_levels = [_lookup_formality_level(item.category, item.occasion) for item in items]

    # Calculate variance in formality levels
    if not formality_levels:
        return 0.5

    if len(formality_levels) == 1:
        return 1.0

    # Calculate standard deviation
    mean_formality = sum(formality_levels) / len(formality_levels)
    variance = sum((x - mean_formality) ** 2 for x in formality_levels) / len(formality_levels)
    std_dev = variance**0.5

    # Convert to score (lower variance = higher score)
    # Max std_dev is ~1.5 for very mismatched items
    score = max(0.0, 1.0 - (std_dev / 1.5))

    logger.debug(f"Formality score: {score:.2f} (levels: {formality_levels})")

    return score


def score_pair(item_a: WardrobeItem, item_b: WardrobeItem) -> float:
    """Score compatibility of a pair of items (color + formality blend).

    This is the swappable RI-3 seam: the not-yet-built pair scorer will
    replace this implementation with a learned model. Everything that
    consumes pairwise compatibility (forgotten-items partner picking, stats)
    should call this function rather than duplicating scoring logic.
    """
    color = calculate_color_harmony_score(item_a, item_b)
    formality = calculate_formality_score([item_a, item_b])
    return round(color * 0.5 + formality * 0.5, 4)


def category_role(category: str | None) -> str:
    """Best-effort garment category -> role classification ("top"/"bottom"/"other").

    Backend categories are garment names (shirt, jeans, dress, ...), never
    literal "top"/"bottom" roles. This helper is a soft heuristic used only as
    a tiebreak (e.g. preferring an opposite-role partner when scores are close)
    — it must never be relied upon as the sole basis for pairing or gating.
    """
    c = (category or "").lower()
    tops = {
        "shirt",
        "t-shirt",
        "tshirt",
        "blouse",
        "top",
        "sweater",
        "hoodie",
        "jacket",
        "blazer",
        "suit",
    }
    bottoms = {"jeans", "pants", "trousers", "chinos", "shorts", "skirt", "dress pants", "sweatpants"}
    if any(k in c for k in bottoms):
        return "bottom"
    if "dress" in c:
        return "other"  # one-piece; not a pairing top/bottom
    if any(k in c for k in tops):
        return "top"
    return "other"


# ============================================================================
# 6. USER PREFERENCE LEARNING
# ============================================================================


async def get_user_preference_weights(db: AsyncSession, user_id: UUID) -> dict[str, Any]:
    """Analyze past feedback to learn user preferences.

    Analyzes outfits with positive feedback (score = 1) to identify:
    - Preferred colors
    - Preferred categories
    - Preferred patterns
    - Formality preference

    Args:
        db: Database session
        user_id: User ID

    Returns:
        Dictionary with preference weights
    """
    # Query outfits with positive feedback
    query = select(Outfit).where(and_(Outfit.user_id == user_id, Outfit.feedback_score == 1))

    result = await db.execute(query)
    liked_outfits = result.scalars().all()

    # Initialize preference counters
    color_counts: dict[str, int] = {}
    category_counts: dict[str, int] = {}
    pattern_counts: dict[str, int] = {}
    formality_sum = 0
    formality_count = 0

    # Analyze liked outfits
    for outfit in liked_outfits:
        # Load related items
        items = []
        if outfit.top_item:
            items.append(outfit.top_item)
        if outfit.bottom_item:
            items.append(outfit.bottom_item)

        for item in items:
            # Count colors
            if item.color_primary:
                color_counts[item.color_primary.lower()] = (
                    color_counts.get(item.color_primary.lower(), 0) + 1
                )

            # Count categories
            if item.category:
                category_counts[item.category.lower()] = (
                    category_counts.get(item.category.lower(), 0) + 1
                )

            # Count patterns
            if item.pattern:
                pattern_counts[item.pattern.lower()] = (
                    pattern_counts.get(item.pattern.lower(), 0) + 1
                )

        # Calculate formality
        if items:
            formality = calculate_formality_score(items)
            formality_sum += formality
            formality_count += 1

    # Calculate average formality preference
    avg_formality = formality_sum / formality_count if formality_count > 0 else 0.5

    preferences = {
        "preferred_colors": color_counts,
        "preferred_categories": category_counts,
        "preferred_patterns": pattern_counts,
        "formality_preference": avg_formality,
        "total_liked_outfits": len(liked_outfits),
    }

    logger.info(
        f"User preferences learned from {len(liked_outfits)} liked outfits: "
        f"formality={avg_formality:.2f}"
    )

    return preferences


# ============================================================================
# 7. WEAVIATE SEMANTIC SEARCH
# ============================================================================


async def find_compatible_items(
    base_item: WardrobeItem, user_id: UUID, category: str, limit: int = 10
) -> list[dict[str, Any]]:
    """Use Weaviate hybrid search to find items that go well with base item.

    Args:
        base_item: The base item to match with
        user_id: User ID
        category: Category of items to search for (e.g., "top", "bottom")
        limit: Maximum number of results

    Returns:
        List of compatible items from Weaviate
    """
    if not weaviate_service.is_connected():
        logger.warning("Weaviate not connected, cannot search for compatible items")
        return []

    # Build search query based on base item attributes
    query_parts = []

    if base_item.color_primary:
        query_parts.append(f"{base_item.color_primary}")

    if base_item.pattern:
        query_parts.append(f"{base_item.pattern}")

    if base_item.occasion:
        query_parts.extend(base_item.occasion)

    query_parts.append(category)

    query = " ".join(query_parts)

    # Search Weaviate
    results = weaviate_service.search_similar_items(
        query=query, user_id=user_id, limit=limit, category_filter=category
    )

    logger.info(f"Found {len(results)} compatible {category} items for base item {base_item.id}")

    return results


# ============================================================================
# 8. MAIN GENERATION FUNCTION
# ============================================================================


async def generate_daily_outfits(
    db: AsyncSession,
    user_id: UUID,
    weather: dict[str, Any],
    occasion: str = "casual",
    num_suggestions: int = 3,
    now: datetime | None = None,
    pool_size: int | None = None,
    weights: dict[str, float] | None = None,
    occasion_hint: str | None = None,
    recently_worn_days: int = 14,
) -> list[dict[str, Any]]:
    """Generate daily outfit suggestions using all recommendation functions.

    Main orchestration flow:
    1. Get user's wardrobe items
    2. Filter by weather
    3. Filter by occasion
    4. Get recently worn items
    5. Get user preferences
    6. For each suggestion:
       a. Select base item (bottom)
       b. Find compatible tops using Weaviate
       c. Score combinations (color harmony + context + preferences)
       d. Select accessories if available
    7. Return top 3 unique combinations

    Args:
        db: Database session
        user_id: User ID
        weather: Weather data dict
        occasion: Occasion type (default: "casual")
        num_suggestions: Number of suggestions to generate (default: 3)
        now: RI-3 testability hook for `context_scoring.calculate_time_score`
            (defaults to `datetime.now()` inside `calculate_context_score`
            when omitted). Not threaded to the endpoint — production calls
            always use the real current time.
        pool_size: RI-6 re-ranker hook — when set, generates this many
            diverse candidates instead of `num_suggestions` (the endpoint
            reranks the larger pool, then slices to the display count).
            Defaults to `num_suggestions` when omitted, so existing callers
            are unaffected.
        weights: RI-5 (Task 5.2) — the aggregation weight set to apply. When
            omitted, this function self-fetches the currently active weights
            via `weight_fitting.get_active_weights` (still a pure O(1) read,
            never a fit) — real request-path callers (the `/daily` endpoint)
            fetch once themselves so they can also log the `source_label`
            into the `shown` events' `context`, and pass the result here to
            avoid a redundant second read.
        occasion_hint: RI-5 (Task 5.4a) — optional morning-vibe hint
            (`sharp`/`relaxed`/`bold`/`None`), mapped to a soft formality bias
            via `services.recommendation.vibe.formality_bias_for_hint`.
            Absent (`None`, the default) reproduces byte-identical pre-RI-5
            behavior.
        recently_worn_days: RI-5 (Task 5.3) — the swipe deck relaxes the
            14-day anti-repetition window (it's a rating exercise, not
            "wear this today"); defaults to the pre-RI-5 14-day window for
            every other caller.

    Returns:
        List of outfit suggestions with scores and metadata
    """
    effective_k = pool_size if pool_size is not None else num_suggestions
    logger.info(f"Generating {effective_k} outfit suggestions for user {user_id}")

    if weights is None:
        from attreq_api.services.recommendation.weight_fitting import get_active_weights

        weights, _source_label = await get_active_weights(db, user_id)

    from attreq_api.services.recommendation.vibe import formality_bias_for_hint

    formality_bias = formality_bias_for_hint(occasion_hint)

    # Step 1: Get user's wardrobe items (active only — archived items must
    # never surface in recommendations)
    query = select(WardrobeItem).where(
        and_(
            WardrobeItem.user_id == user_id,
            WardrobeItem.processing_status == "completed",
            WardrobeItem.status == "active",
        )
    )
    result = await db.execute(query)
    all_items = list(result.scalars().all())

    if len(all_items) < 2:
        logger.warning(
            f"User {user_id} has insufficient items ({len(all_items)}) for outfit generation"
        )
        return []

    # Step 2: Filter by weather
    weather_filtered = await filter_items_by_weather(all_items, weather)

    # Step 3: Filter by occasion
    occasion_filtered = await filter_items_by_occasion(weather_filtered, occasion)

    if len(occasion_filtered) < 2:
        logger.warning(f"Insufficient items after filtering: {len(occasion_filtered)}")
        # Fall back to weather-filtered items if occasion filtering is too restrictive
        occasion_filtered = weather_filtered

    # Step 4: Get recently worn items (14-day hard exclusion by default; the
    # RI-5 swipe deck relaxes this via `recently_worn_days` — it's a rating
    # exercise, not "wear this today").
    recently_worn = await get_recently_worn_items(db, user_id, days=recently_worn_days)

    # Step 5: Get user preferences
    user_preferences = await get_user_preference_weights(db, user_id)

    # Load Style DNA if available
    user_result = await db.execute(select(User).where(User.id == user_id))
    user_obj = user_result.scalar_one_or_none()
    style_dna = None
    if user_obj and user_obj.style_preferences:
        try:
            style_dna = json.loads(user_obj.style_preferences)
        except (json.JSONDecodeError, TypeError):
            style_dna = None

    # Step 6: Load recent `shown` events (RI-4 rotation + cold-start signal).
    # 90-day lookback: generous enough to cover "has this item ever been
    # shown before" for cold-start eligibility; `build_rotation_context`
    # internally restricts to the real 7-day item / 14-day combo windows, so
    # a wider raw window here does not loosen anti-repetition.
    shown_events = await _load_recent_shown_events(db, user_id, days=90)

    # Step 6b (RI-6): FashionCLIP item vectors / style centroid / thumbs-
    # propagation penalties — ONLY loaded when the feature is enabled, and
    # left as `None` otherwise so `composition.py` takes its exact pre-RI-6
    # code path (no weight reallocation, no propagation adjustment) when
    # `EMBEDDINGS_ENABLED=false`, the shipped default.
    item_vectors: dict[UUID, list[float]] | None = None
    user_centroid: list[float] | None = None
    propagation_penalties: dict[UUID, float] | None = None
    if settings.embeddings_enabled:
        item_vectors = await _load_item_vectors(occasion_filtered)
        if user_obj and user_obj.style_dna_centroid:
            raw_vector = user_obj.style_dna_centroid.get("vector")
            if raw_vector:
                user_centroid = raw_vector
        propagation_penalties = await _load_propagation_penalties(db, user_id)

    # Step 7: Delegate to the PURE composition core (no DB access below this
    # line) — see services/recommendation/composition.py.
    from attreq_api.services.recommendation.composition import compose_daily_outfits

    candidates = compose_daily_outfits(
        occasion_filtered,
        weather,
        occasion,
        recently_worn,
        shown_events,
        style_dna,
        k=effective_k,
        now=now,
        preferred_colors=user_preferences.get("preferred_colors"),
        item_vectors=item_vectors,
        user_centroid=user_centroid,
        propagation_penalties=propagation_penalties,
        weights=weights,
        formality_bias=formality_bias,
    )

    suggestions = [_candidate_to_payload(c) for c in candidates]

    logger.info(f"Generated {len(suggestions)} outfit suggestions")

    return suggestions


async def _load_recent_shown_events(
    db: AsyncSession, user_id: UUID, days: int = 90
) -> list[dict[str, Any]]:
    """Load `shown`-event rows into the plain-dict shape
    `composition.build_rotation_context` / `compose_daily_outfits` expect:
    `{"date": date, "item_ids": [UUID, ...]}` — core garment ids only
    (top/bottom/fullbody; footwear/outerwear/accessory are not part of the
    anti-repetition combo signal).
    """
    from attreq_api.models.recommendation_event import RecommendationEvent

    cutoff = datetime.utcnow() - timedelta(days=days)
    query = select(RecommendationEvent).where(
        and_(
            RecommendationEvent.user_id == user_id,
            RecommendationEvent.event_type == "shown",
            RecommendationEvent.created_at >= cutoff,
        )
    )
    result = await db.execute(query)
    rows = result.scalars().all()

    events: list[dict[str, Any]] = []
    for row in rows:
        payload = row.outfit_payload or {}
        raw_ids = [
            payload.get("top_item_id"),
            payload.get("bottom_item_id"),
            payload.get("fullbody_item_id"),
        ]
        item_ids = [UUID(raw_id) for raw_id in raw_ids if raw_id]
        if not item_ids:
            continue
        event_date = row.created_at.date() if row.created_at else date.today()
        events.append({"date": event_date, "item_ids": item_ids})

    return events


def _item_detail(item: WardrobeItem | None) -> dict[str, Any] | None:
    if item is None:
        return None
    return {
        "id": str(item.id),
        "category": item.category,
        "color_primary": item.color_primary,
        "pattern": item.pattern,
        "image_url": item.processed_image_url or item.original_image_url,
        "thumbnail_url": item.thumbnail_url,
    }


def _candidate_to_payload(candidate: Any) -> dict[str, Any]:
    """Convert a `composition.OutfitCandidate` into the raw candidate dict
    shape the endpoint/telemetry/schema layer expects. Keeps the pre-RI-4
    dict-shape contract (RI-1's `bulk_create_shown` reads this directly) while
    adding the new fullbody/footwear/outerwear/explanation/confidence/
    rediscovery fields.
    """
    scores = dict(candidate.score_components)
    scores["color_harmony_branch"] = candidate.color_harmony_branch

    return {
        "top_item_id": str(candidate.top_item.id) if candidate.top_item else None,
        "top_item": _item_detail(candidate.top_item),
        "bottom_item_id": str(candidate.bottom_item.id) if candidate.bottom_item else None,
        "bottom_item": _item_detail(candidate.bottom_item),
        "fullbody_item_id": str(candidate.fullbody_item.id) if candidate.fullbody_item else None,
        "fullbody_item": _item_detail(candidate.fullbody_item),
        "footwear_item_id": str(candidate.footwear_item.id) if candidate.footwear_item else None,
        "footwear_item": _item_detail(candidate.footwear_item),
        "outerwear_item_id": str(candidate.outerwear_item.id) if candidate.outerwear_item else None,
        "outerwear_item": _item_detail(candidate.outerwear_item),
        "accessory_item": _item_detail(candidate.accessory_item),
        "scores": scores,
        "weather_context": candidate.weather,
        "occasion_context": candidate.occasion,
        "explanation": candidate.explanation,
        "confidence": candidate.confidence,
        "rediscovery": candidate.rediscovery,
        "rediscovery_item_id": candidate.rediscovery_item_id,
    }
