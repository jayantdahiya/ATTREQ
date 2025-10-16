"""Recommendation endpoints for ATTREQ API."""

import logging
from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_current_active_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.recommendation import DailySuggestionsResponse, OutfitSuggestion, WeatherData
from app.services.cache.redis_client import redis_cache
from app.services.external.weather_api import weather_service
from app.services.recommendation.algorithm import generate_daily_outfits

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
        if cached_suggestions:
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
                detail="No location available. Please provide coordinates or set your location in profile."
            )
        weather_lat = current_user.saved_latitude
        weather_lon = current_user.saved_longitude
        logger.info(f"Using saved location for user {current_user.id}: {weather_lat}, {weather_lon}")

    # Step 3: Fetch weather data (with its own cache)
    try:
        weather_data = await weather_service.get_current_weather(weather_lat, weather_lon)
    except Exception as e:
        logger.error(f"Failed to fetch weather: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Weather service temporarily unavailable"
        )

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
            detail="Failed to generate outfit suggestions"
        )

    # Check if we got any suggestions
    if not suggestions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Insufficient wardrobe items to generate outfit suggestions. Please add more items to your wardrobe."
        )

    # Step 5: Build response
    response_data = {
        "suggestions": suggestions,
        "total_suggestions": len(suggestions),
        "generated_at": datetime.utcnow().isoformat(),
        "weather": weather_data,
        "occasion": occasion,
        "cached": False,
    }

    # Step 6: Cache the response (24 hours TTL)
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
    today = date.today().isoformat()

    # Clear cache for all occasions
    occasions = ["casual", "formal", "party", "business", "athletic"]
    cleared_count = 0

    for occasion in occasions:
        cache_key = f"daily_suggestions:{current_user.id}:{today}:{occasion}"
        if await redis_cache.delete(cache_key):
            cleared_count += 1

    logger.info(f"Cleared {cleared_count} cached suggestions for user {current_user.id}")

    return

