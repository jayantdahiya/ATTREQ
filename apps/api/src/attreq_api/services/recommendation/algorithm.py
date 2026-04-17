"""Recommendation algorithm for outfit generation."""

import logging
import random
from datetime import date, timedelta
from typing import Any
from uuid import UUID

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from attreq_api.models.outfit import Outfit
from attreq_api.models.wardrobe import WardrobeItem
from attreq_api.services.ai.embeddings import weaviate_service

logger = logging.getLogger(__name__)


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
        if outfit.accessory_ids:
            worn_item_ids.update(outfit.accessory_ids)

    logger.info(f"Found {len(worn_item_ids)} items worn in last {days} days")

    return worn_item_ids


# ============================================================================
# 4. COLOR HARMONY SCORING
# ============================================================================


def calculate_color_harmony_score(item1: WardrobeItem, item2: WardrobeItem) -> float:
    """Calculate color compatibility score between two items.

    Scoring rules:
    - Complementary colors: 0.9
    - Analogous colors: 0.8
    - Neutral + any: 0.7
    - Same color family: 0.6
    - Clashing: 0.3

    Args:
        item1: First wardrobe item
        item2: Second wardrobe item

    Returns:
        Compatibility score between 0 and 1
    """
    # Define color relationships
    neutrals = {"white", "black", "gray", "grey", "beige", "cream", "brown"}
    warm_colors = {"red", "orange", "yellow", "pink", "coral"}
    cool_colors = {"blue", "green", "purple", "teal", "turquoise"}

    # Complementary pairs
    complementary = {
        ("red", "green"),
        ("blue", "orange"),
        ("yellow", "purple"),
        ("pink", "green"),
    }

    color1 = (item1.color_primary or "").lower()
    color2 = (item2.color_primary or "").lower()

    # Handle missing colors
    if not color1 or not color2:
        return 0.5  # Neutral score for unknown colors

    # Same color
    if color1 == color2:
        return 0.6

    # Neutral + any color
    if color1 in neutrals or color2 in neutrals:
        return 0.7

    # Complementary colors
    if (color1, color2) in complementary or (color2, color1) in complementary:
        return 0.9

    # Same color family (warm or cool)
    if (color1 in warm_colors and color2 in warm_colors) or (
        color1 in cool_colors and color2 in cool_colors
    ):
        return 0.8

    # Different color families (potential clash)
    return 0.3


# ============================================================================
# 5. FORMALITY MATCHING
# ============================================================================


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
    # Define formality levels for categories
    formality_map = {
        "suit": 3,
        "blazer": 3,
        "dress shirt": 3,
        "dress pants": 3,
        "dress": 3,
        "skirt": 2,
        "blouse": 2,
        "chinos": 2,
        "jeans": 1,
        "t-shirt": 1,
        "shorts": 1,
        "hoodie": 1,
        "sweatpants": 0,
        "athletic wear": 0,
    }

    # Get formality levels for each item
    formality_levels = []
    for item in items:
        category = (item.category or "").lower()

        # Check if category matches any formality key
        formality = 1  # Default to casual
        for key, level in formality_map.items():
            if key in category:
                formality = level
                break

        # Also check occasion tags
        if item.occasion:
            if "formal" in [occ.lower() for occ in item.occasion]:
                formality = max(formality, 3)
            elif "business" in [occ.lower() for occ in item.occasion]:
                formality = max(formality, 2)

        formality_levels.append(formality)

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
       c. Score combinations (color + formality + preferences)
       d. Select accessories if available
    7. Return top 3 unique combinations

    Args:
        db: Database session
        user_id: User ID
        weather: Weather data dict
        occasion: Occasion type (default: "casual")
        num_suggestions: Number of suggestions to generate (default: 3)

    Returns:
        List of outfit suggestions with scores and metadata
    """
    logger.info(f"Generating {num_suggestions} outfit suggestions for user {user_id}")

    # Step 1: Get user's wardrobe items
    query = select(WardrobeItem).where(
        and_(
            WardrobeItem.user_id == user_id,
            WardrobeItem.processing_status == "completed",
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

    # Step 4: Get recently worn items
    recently_worn = await get_recently_worn_items(db, user_id, days=14)

    # Step 5: Get user preferences
    user_preferences = await get_user_preference_weights(db, user_id)

    # Separate items by category
    tops = [item for item in occasion_filtered if item.category and "top" in item.category.lower()]
    bottoms = [
        item for item in occasion_filtered if item.category and "bottom" in item.category.lower()
    ]
    accessories = [
        item
        for item in occasion_filtered
        if item.category
        and any(acc in item.category.lower() for acc in ["accessory", "shoe", "bag"])
    ]

    # If no clear categories, try to infer
    if not tops and not bottoms:
        # Use all items as potential tops or bottoms
        tops = occasion_filtered[: len(occasion_filtered) // 2]
        bottoms = occasion_filtered[len(occasion_filtered) // 2 :]

    logger.info(
        f"Available items: {len(tops)} tops, {len(bottoms)} bottoms, {len(accessories)} accessories"
    )

    # Step 6: Generate outfit combinations
    outfit_candidates = []

    for bottom in bottoms:
        # Skip recently worn items
        if bottom.id in recently_worn:
            continue

        for top in tops:
            # Skip recently worn items
            if top.id in recently_worn:
                continue

            # Skip same item
            if top.id == bottom.id:
                continue

            # Calculate scores
            color_score = calculate_color_harmony_score(top, bottom)
            formality_score = calculate_formality_score([top, bottom])

            # Preference bonus
            preference_bonus = 0.0
            if user_preferences["preferred_colors"]:
                if (
                    top.color_primary
                    and top.color_primary.lower() in user_preferences["preferred_colors"]
                ):
                    preference_bonus += 0.1
                if (
                    bottom.color_primary
                    and bottom.color_primary.lower() in user_preferences["preferred_colors"]
                ):
                    preference_bonus += 0.1

            # Combined score
            total_score = (color_score * 0.4) + (formality_score * 0.4) + (preference_bonus * 0.2)

            # Select an accessory if available
            accessory = None
            if accessories:
                # Pick a random accessory that wasn't recently worn
                available_accessories = [acc for acc in accessories if acc.id not in recently_worn]
                if available_accessories:
                    accessory = random.choice(available_accessories)

            outfit_candidates.append(
                {
                    "top_item_id": str(top.id),
                    "top_item": {
                        "id": str(top.id),
                        "category": top.category,
                        "color_primary": top.color_primary,
                        "pattern": top.pattern,
                        "image_url": top.processed_image_url or top.original_image_url,
                        "thumbnail_url": top.thumbnail_url,
                    },
                    "bottom_item_id": str(bottom.id),
                    "bottom_item": {
                        "id": str(bottom.id),
                        "category": bottom.category,
                        "color_primary": bottom.color_primary,
                        "pattern": bottom.pattern,
                        "image_url": bottom.processed_image_url or bottom.original_image_url,
                        "thumbnail_url": bottom.thumbnail_url,
                    },
                    "accessory_item": (
                        {
                            "id": str(accessory.id),
                            "category": accessory.category,
                            "color_primary": accessory.color_primary,
                            "image_url": accessory.processed_image_url
                            or accessory.original_image_url,
                            "thumbnail_url": accessory.thumbnail_url,
                        }
                        if accessory
                        else None
                    ),
                    "scores": {
                        "color_harmony": round(color_score, 2),
                        "formality": round(formality_score, 2),
                        "preference_bonus": round(preference_bonus, 2),
                        "total": round(total_score, 2),
                    },
                    "weather_context": weather,
                    "occasion_context": occasion,
                }
            )

    # Step 7: Sort by score and return top N unique combinations
    outfit_candidates.sort(key=lambda x: x["scores"]["total"], reverse=True)

    # Select diverse suggestions (avoid same items in multiple outfits)
    selected_outfits = []
    used_items = set()

    for outfit in outfit_candidates:
        top_id = outfit["top_item_id"]
        bottom_id = outfit["bottom_item_id"]

        # Check if items already used
        if top_id not in used_items and bottom_id not in used_items:
            selected_outfits.append(outfit)
            used_items.add(top_id)
            used_items.add(bottom_id)

            if len(selected_outfits) >= num_suggestions:
                break

    logger.info(f"Generated {len(selected_outfits)} outfit suggestions")

    return selected_outfits
