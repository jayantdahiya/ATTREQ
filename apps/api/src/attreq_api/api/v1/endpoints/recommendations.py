"""Recommendation endpoints for ATTREQ API."""

import logging
import uuid
from datetime import date, datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from attreq_api.api.v1.deps import get_current_active_user
from attreq_api.config.database import get_db
from attreq_api.crud.recommendation_event import recommendation_event_crud
from attreq_api.crud.user_event import user_event_crud
from attreq_api.integrations.external.weather_api import weather_service
from attreq_api.models.user import User
from attreq_api.schemas.recommendation import DailySuggestionsResponse
from attreq_api.schemas.telemetry import (
    RecommendationFeedbackAction,
    RecommendationFeedbackRequest,
    RecommendationFeedbackResponse,
)
from attreq_api.services.cache.invalidation import invalidate_daily_suggestions
from attreq_api.services.cache.redis_client import redis_cache
from attreq_api.services.recommendation.algorithm import generate_daily_outfits

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/daily", response_model=DailySuggestionsResponse)
async def get_daily_suggestions(
    lat: float | None = Query(None, description="Latitude for weather lookup", ge=-90, le=90),
    lon: float | None = Query(None, description="Longitude for weather lookup", ge=-180, le=180),
    occasion: str = Query("casual", description="Occasion type (casual, formal, party, etc.)"),
    force_refresh: bool = Query(False, description="Force regeneration, bypass cache"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Generate daily outfit suggestions based on weather and occasion.

    This endpoint orchestrates the complete recommendation flow:
    1. Check Redis cache for today's suggestions (unless force_refresh=True)
    2. If cached, return cached suggestions
    3. If not cached:
       a. Determine location (provided coords or user's saved location)
       b. Fetch weather from OpenWeatherMap (with Redis cache)
       c. Generate outfits using recommendation algorithm
       d. Store suggestions in Redis (24h TTL)
       e. Return suggestions

    Args:
        lat: Latitude for weather lookup (optional, uses saved location if not provided)
        lon: Longitude for weather lookup (optional, uses saved location if not provided)
        occasion: Occasion type (default: "casual")
        force_refresh: Force regeneration, bypass cache (default: False)
        db: Database session
        current_user: Currently authenticated user

    Returns:
        Daily outfit suggestions with weather context

    Raises:
        HTTPException: If user has insufficient wardrobe items or no location available
    """
    today = date.today().isoformat()
    cache_key = f"daily_suggestions:{current_user.id}:{today}:{occasion}"

    # Step 1: Check cache (unless force refresh)
    if not force_refresh:
        cached_suggestions = await redis_cache.get(cache_key)
        # Stale-cache guard: pre-deploy cache entries were written before
        # `recommendation_id` became a required response field. Treat their absence
        # as a cache miss and fall through to regenerate, instead of a ValidationError
        # -> 500 for every user with a warm cache until the 24h TTL expires.
        if cached_suggestions and "recommendation_id" in cached_suggestions:
            logger.info(f"Returning cached suggestions for user {current_user.id}")
            # Add cached flag
            cached_suggestions["cached"] = True
            return DailySuggestionsResponse(**cached_suggestions)

    # Step 2: Determine location coordinates
    weather_lat = lat
    weather_lon = lon

    # If no coordinates provided, use user's saved location
    if weather_lat is None or weather_lon is None:
        if current_user.saved_latitude is None or current_user.saved_longitude is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No location available. Please provide coordinates or set your location in profile.",
            )
        weather_lat = current_user.saved_latitude
        weather_lon = current_user.saved_longitude
        logger.info(
            f"Using saved location for user {current_user.id}: {weather_lat}, {weather_lon}"
        )

    # Step 3: Fetch weather data (with its own cache)
    try:
        weather_data = await weather_service.get_current_weather(weather_lat, weather_lon)
    except Exception as e:
        logger.error(f"Failed to fetch weather: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Weather service temporarily unavailable",
        ) from e

    # Step 4: Generate outfit suggestions
    try:
        suggestions = await generate_daily_outfits(
            db=db,
            user_id=current_user.id,
            weather=weather_data,
            occasion=occasion,
            num_suggestions=3,
        )
    except Exception as e:
        logger.error(f"Failed to generate outfit suggestions: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate outfit suggestions",
        ) from e

    # Check if we got any suggestions
    if not suggestions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Insufficient wardrobe items to generate outfit suggestions. Please add more items to your wardrobe.",
        )

    # Step 4b: Stamp recommendation_id + outfit_index (single source of truth = list
    # order at write time). generate_daily_outfits stays a pure scoring function.
    recommendation_id = uuid.uuid4()
    for index, suggestion in enumerate(suggestions):
        suggestion["outfit_index"] = index

    # Step 4c: Write one `shown` telemetry row per candidate, from the raw candidate
    # dicts (which still carry all 6 component scores, including style_dna/behaviour —
    # the response schema historically dropped these). A failure here surfaces via the
    # existing 500 handling further up the stack; telemetry loss on generation must be
    # loud, not swallowed silently.
    await recommendation_event_crud.bulk_create_shown(
        db,
        user_id=current_user.id,
        recommendation_id=recommendation_id,
        candidates=suggestions,
        context={"weather": weather_data, "occasion": occasion, "date": today},
    )

    # Step 5: Build response. recommendation_id must be `str`, never a raw UUID:
    # redis_cache.set does json.dumps, which raises on a UUID and silently returns
    # False, so the entry would never be cached.
    response_data = {
        "recommendation_id": str(recommendation_id),
        "suggestions": suggestions,
        "total_suggestions": len(suggestions),
        "generated_at": datetime.utcnow().isoformat(),
        "weather": weather_data,
        "occasion": occasion,
        "cached": False,
    }

    # Step 6: Cache the response (24 hours TTL)
    # Known behavior (documented, not guarded): if Redis is down, `get` always misses,
    # so every call regenerates and writes a fresh `shown` batch — acceptable, each
    # generation is a genuine distinct impression.
    cache_ttl = 24 * 60 * 60  # 24 hours in seconds
    await redis_cache.set(cache_key, response_data, ttl=cache_ttl)

    logger.info(
        f"Generated {len(suggestions)} outfit suggestions for user {current_user.id} "
        f"(occasion: {occasion}, temp: {weather_data['temp']}°C)"
    )

    return DailySuggestionsResponse(**response_data)


@router.delete("/cache", status_code=status.HTTP_204_NO_CONTENT)
async def clear_suggestion_cache(
    current_user: User = Depends(get_current_active_user),
):
    """Clear cached outfit suggestions for the current user.

    This allows users to manually refresh their suggestions without waiting
    for the cache to expire.

    Args:
        current_user: Currently authenticated user
    """
    cleared_count = await invalidate_daily_suggestions(current_user.id)

    logger.info(f"Cleared {cleared_count} cached suggestions for user {current_user.id}")

    return


@router.post("/{recommendation_id}/feedback", response_model=RecommendationFeedbackResponse)
async def submit_recommendation_feedback(
    recommendation_id: UUID,
    feedback: RecommendationFeedbackRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Record feedback (accepted/rejected/swapped) for one outfit in a shown batch.

    This writes a new `recommendation_events` row referencing the same
    (recommendation_id, outfit_index) as the original `shown` row — it never updates
    that row. It also writes a `user_events` row for the same signal.

    Does NOT materialize an outfit — the client still calls `POST /outfits/`
    independently to do that (unchanged contract). The two paths stay decoupled.

    Args:
        recommendation_id: UUID of the generation batch (from DailySuggestionsResponse)
        feedback: Feedback body (outfit_index, action, optional rejection reason/note)
        db: Database session
        current_user: Currently authenticated user

    Returns:
        Confirmation of the recorded feedback event

    Raises:
        HTTPException: 404 if no `shown` row exists for this user at
            (recommendation_id, outfit_index) — covers both an unknown
            recommendation_id and a user trying to address someone else's batch.
    """
    shown_event = await recommendation_event_crud.get_shown(
        db,
        recommendation_id=recommendation_id,
        outfit_index=feedback.outfit_index,
        user_id=current_user.id,
    )
    if not shown_event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No matching shown recommendation found for this user",
        )

    # rejection_reason/rejection_note are only meaningful for REJECTED; the request
    # schema is forgiving (doesn't 4xx) if they're sent otherwise, but we don't
    # persist them unless the action is actually a rejection.
    is_rejection = feedback.action == RecommendationFeedbackAction.REJECTED
    rejection_reason = feedback.rejection_reason.value if (is_rejection and feedback.rejection_reason) else None
    rejection_note = feedback.rejection_note if is_rejection else None

    event = await recommendation_event_crud.create_feedback_event(
        db,
        user_id=current_user.id,
        recommendation_id=recommendation_id,
        outfit_index=feedback.outfit_index,
        event_type=feedback.action.value,
        outfit_payload=shown_event.outfit_payload,
        context=shown_event.context,
        rejection_reason=rejection_reason,
        rejection_note=rejection_note,
    )

    # Best-effort user_events mirror — never blocks the feedback response.
    try:
        user_event_type_map = {
            RecommendationFeedbackAction.ACCEPTED: "outfit_accepted",
            RecommendationFeedbackAction.REJECTED: "outfit_rejected",
            RecommendationFeedbackAction.SWAPPED: "outfit_swapped",
        }
        user_event_payload: dict = {
            "recommendation_id": str(recommendation_id),
            "outfit_index": feedback.outfit_index,
        }
        if feedback.swapped_item_ids:
            user_event_payload["swapped_item_ids"] = feedback.swapped_item_ids
        await user_event_crud.create(
            db,
            user_id=current_user.id,
            event_type=user_event_type_map[feedback.action],
            payload=user_event_payload,
        )
    except Exception as e:
        logger.warning(f"Failed to write user_event for recommendation feedback: {e}")

    logger.info(
        f"Recommendation feedback recorded: user={current_user.id} "
        f"recommendation_id={recommendation_id} outfit_index={feedback.outfit_index} "
        f"action={feedback.action.value}"
    )

    return RecommendationFeedbackResponse(
        recommendation_id=str(recommendation_id),
        outfit_index=event.outfit_index,
        event_type=event.event_type,
        created_at=event.created_at,
    )
