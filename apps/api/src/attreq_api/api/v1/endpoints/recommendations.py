"""Recommendation endpoints for ATTREQ API."""

import logging
import uuid
from datetime import date, datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from attreq_api.api.v1.deps import get_current_active_user
from attreq_api.config.database import get_db
from attreq_api.config.settings import settings
from attreq_api.crud.recommendation_event import recommendation_event_crud
from attreq_api.crud.user_event import user_event_crud
from attreq_api.integrations.external.weather_api import weather_service
from attreq_api.models.user import User
from attreq_api.schemas.recommendation import DailySuggestionsResponse, SwipeDeckStatusResponse
from attreq_api.schemas.telemetry import (
    RecommendationFeedbackAction,
    RecommendationFeedbackRequest,
    RecommendationFeedbackResponse,
)
from attreq_api.services.cache.invalidation import invalidate_daily_suggestions
from attreq_api.services.cache.redis_client import redis_cache
from attreq_api.services.rate_limit import enforce_user_rate_limit
from attreq_api.services.recommendation.algorithm import generate_daily_outfits
from attreq_api.services.recommendation.reranker import rerank
from attreq_api.services.recommendation.vibe import VALID_OCCASION_HINTS
from attreq_api.services.recommendation.weight_fitting import get_active_weights

# RI-6: reranker pool — how many diverse candidates to generate/rerank before
# slicing down to the display count, when RERANKER_ENABLED. See finalized
# plan §9: "the reranker needs a top-5" (generate_daily_outfits's diversity
# dedup otherwise never produces more than the display count on its own).
RERANKER_POOL_SIZE = 5


async def _resolve_weather(
    current_user: User, lat: float | None, lon: float | None
) -> dict:
    """Resolve current weather for a request, preferring explicit query coords,
    then the user's saved coordinates, then their saved city name (typed-city
    registration never geocodes to lat/lon — see `saved_city` on `User` —
    so this is the only path that makes weather-aware recommendations work
    for users who didn't grant device location).
    """
    weather_lat = lat
    weather_lon = lon
    if weather_lat is None or weather_lon is None:
        if current_user.saved_latitude is not None and current_user.saved_longitude is not None:
            weather_lat = current_user.saved_latitude
            weather_lon = current_user.saved_longitude
        elif current_user.saved_city:
            return await weather_service.get_weather_by_city(current_user.saved_city)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No location available. Please provide coordinates or set your location in profile.",
            )
    return await weather_service.get_current_weather(weather_lat, weather_lon)


async def _enforce_force_refresh_rate_limit(force_refresh: bool, user_id: UUID) -> None:
    """Charge only explicit regenerations; cached recommendation reads stay free."""
    if not force_refresh:
        return
    await enforce_user_rate_limit(
        bucket="recommendation-refreshes",
        user_id=user_id,
        limit=settings.rate_limit_recommendation_refreshes,
        window_seconds=settings.rate_limit_recommendation_window_seconds,
    )

# RI-5 (Task 5.3): swipe deck. Adaptation note: `composition.select_anchors`
# hard-caps anchor selection at `MAX_ANCHORS == 5` regardless of the
# requested `k` (a pre-existing RI-4 constant, not an RI-5 choice) — so
# "sample 5 from a top-15 pool" isn't literally achievable without deeper
# restructuring of the anchor-selection architecture. The deck instead takes
# every anchor-diverse candidate the pipeline produces (already maximally
# diverse by construction, since `select_anchors` never picks two anchors of
# the same (category, color-family)) — `SWIPE_DECK_SIZE` names the display
# count. The relaxed anti-repetition window (a rating exercise, not "wear
# this today") is the real diversity lever here.
SWIPE_DECK_SIZE = 5
SWIPE_DECK_RECENTLY_WORN_DAYS = 3
SWIPE_DECK_DAILY_CAP = 5

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/daily", response_model=DailySuggestionsResponse)
async def get_daily_suggestions(
    lat: float | None = Query(None, description="Latitude for weather lookup", ge=-90, le=90),
    lon: float | None = Query(None, description="Longitude for weather lookup", ge=-180, le=180),
    occasion: str = Query("casual", description="Occasion type (casual, formal, party, etc.)"),
    occasion_hint: str | None = Query(
        None,
        description=(
            "RI-5: optional one-tap morning vibe hint (sharp|relaxed|bold) — a soft "
            "formality nudge, not a hard filter. Unknown values are ignored (no-op), "
            "never 4xx, since the vibe prompt is always skippable."
        ),
    ),
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
    # RI-5 (finalized plan Correction 10): normalize the hint up front so an
    # unknown/garbage value behaves exactly like "no hint" everywhere below
    # (cache key, generation, vibe_answered recording) rather than silently
    # fragmenting the cache namespace with junk hint strings.
    normalized_hint = occasion_hint.lower().strip() if occasion_hint else None
    if normalized_hint not in VALID_OCCASION_HINTS:
        normalized_hint = None

    await _enforce_force_refresh_rate_limit(force_refresh, current_user.id)

    # v2 (RI-4): the cached payload shape changed (fullbody/footwear/outerwear
    # slots, explanation/confidence/rediscovery) — bumping the key namespace
    # retires every pre-deploy cache entry instead of 500ing on
    # `DailySuggestionsResponse(**cached)` for up to 24h per user. Must match
    # `services/cache/invalidation.py::invalidate_daily_suggestions`.
    # RI-5 (Correction 10): `occasion_hint` is now part of the cache key too —
    # without this, a hinted request could serve a stale un-hinted cached
    # result (or vice versa) for up to 24h.
    cache_key = (
        f"daily_suggestions:v2:{current_user.id}:{today}:{occasion}:{normalized_hint or 'none'}"
    )

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

    # Step 2 & 3: Resolve location (explicit coords > saved coords > saved
    # city) and fetch weather data (with its own cache)
    try:
        weather_data = await _resolve_weather(current_user, lat, lon)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch weather: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Weather service temporarily unavailable",
        ) from e

    # Step 3b (RI-5): read the active scoring weights ONCE per generation —
    # an O(1) indexed read, never a fit (see weight_fitting.get_active_weights
    # docstring). `source_label` is logged into the shown-batch context below
    # for observability (which weight set served this recommendation).
    active_weights, weight_source = await get_active_weights(db, current_user.id)

    # Step 4: Generate outfit suggestions. RI-6: when the LLM reranker is on,
    # generate a larger diverse pool (RERANKER_POOL_SIZE) so there is
    # something to rerank, then slice back down to the display count below —
    # `generate_daily_outfits`'s own diversity dedup never returns more than
    # `num_suggestions` on its own.
    display_count = 3
    try:
        suggestions = await generate_daily_outfits(
            db=db,
            user_id=current_user.id,
            weather=weather_data,
            occasion=occasion,
            num_suggestions=display_count,
            pool_size=RERANKER_POOL_SIZE if settings.reranker_enabled else None,
            weights=active_weights,
            occasion_hint=normalized_hint,
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

    # Step 4a (RI-6): rerank the pool for DISPLAY ORDER + rationale only —
    # never re-derives scores (see services/recommendation/reranker.py). Runs
    # BEFORE caching (the 24h cache would otherwise make the reranker
    # invisible on every cache hit) and before the pool is sliced down to the
    # display count, so the reranker actually has >1 outfit's worth of
    # choice. Zero LLM calls when RERANKER_ENABLED=false (the shipped default).
    reranker_rationales: dict[str, str] | None = None
    if settings.reranker_enabled:
        day_of_week = datetime.utcnow().strftime("%A")
        rerank_context = {"occasion": occasion, "weather": weather_data, "day_of_week": day_of_week}
        suggestions, reranker_rationales = await rerank(suggestions, rerank_context)

    suggestions = suggestions[:display_count]

    reranker_served = bool(reranker_rationales)
    if reranker_rationales:
        for suggestion in suggestions:
            key = f"{suggestion.get('top_item_id')}:{suggestion.get('bottom_item_id')}"
            suggestion["rationale"] = reranker_rationales.get(key)

    # Step 4b: Stamp recommendation_id + outfit_index (single source of truth = list
    # order at write time, AFTER any reranker reordering/slicing above).
    # generate_daily_outfits stays a pure scoring function.
    recommendation_id = uuid.uuid4()
    for index, suggestion in enumerate(suggestions):
        suggestion["outfit_index"] = index

    logger.info(f"reranker_served={reranker_served} user={current_user.id}")

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
        context={
            "weather": weather_data,
            "occasion": occasion,
            "date": today,
            # RI-5: which weight set served this batch ("user:<id>" |
            # "global" | "fallback") and the morning-vibe hint, if any —
            # observability for the fit script / eval gate.
            "weight_source": weight_source,
            "occasion_hint": normalized_hint,
        },
    )

    # RI-5 (Task 5.4b): record the day's vibe answer as a `user_events` row —
    # a labeled preference event, "remembered per day" by checking for an
    # existing `vibe_answered` event today first. Best-effort, never blocks
    # the response; only recorded on a genuine fresh generation (a cache hit
    # returns before this point).
    if normalized_hint is not None:
        try:
            todays_vibe_events = await user_event_crud.list_for_user(
                db,
                user_id=current_user.id,
                since=datetime.combine(date.today(), datetime.min.time()),
                event_types=["vibe_answered"],
                limit=1,
            )
            if not todays_vibe_events:
                await user_event_crud.create(
                    db,
                    user_id=current_user.id,
                    event_type="vibe_answered",
                    payload={"vibe": normalized_hint, "date": today},
                )
        except Exception as e:
            logger.warning(f"Failed to record vibe_answered event: {e}")

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


@router.get("/swipe-deck", response_model=DailySuggestionsResponse)
async def get_swipe_deck(
    lat: float | None = Query(None, description="Latitude for weather lookup", ge=-90, le=90),
    lon: float | None = Query(None, description="Longitude for weather lookup", ge=-180, le=180),
    occasion: str = Query("casual", description="Occasion type (casual, formal, party, etc.)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """RI-5 (Task 5.3): a daily, optional deck of outfits to rate 👍/👎.

    Never cached (each call is a fresh browsing impression) and never itself
    rate-limited (browsing is free) — only the ratings, submitted through the
    existing `POST /{recommendation_id}/feedback` endpoint, are capped at
    `SWIPE_DECK_DAILY_CAP`/day (enforced there). Relaxes the 14-day
    recently-worn exclusion to `SWIPE_DECK_RECENTLY_WORN_DAYS` — a rating
    exercise, not "wear this today".
    """
    try:
        weather_data = await _resolve_weather(current_user, lat, lon)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch weather for swipe deck: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Weather service temporarily unavailable",
        ) from e

    active_weights, weight_source = await get_active_weights(db, current_user.id)

    try:
        suggestions = await generate_daily_outfits(
            db=db,
            user_id=current_user.id,
            weather=weather_data,
            occasion=occasion,
            num_suggestions=SWIPE_DECK_SIZE,
            weights=active_weights,
            recently_worn_days=SWIPE_DECK_RECENTLY_WORN_DAYS,
        )
    except Exception as e:
        logger.error(f"Failed to generate swipe deck: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate swipe deck",
        ) from e

    if not suggestions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Insufficient wardrobe items to generate a swipe deck.",
        )

    recommendation_id = uuid.uuid4()
    for index, suggestion in enumerate(suggestions):
        suggestion["outfit_index"] = index

    today = date.today().isoformat()
    await recommendation_event_crud.bulk_create_shown(
        db,
        user_id=current_user.id,
        recommendation_id=recommendation_id,
        candidates=suggestions,
        context={
            "weather": weather_data,
            "occasion": occasion,
            "date": today,
            "weight_source": weight_source,
            "source": "swipe_deck",
        },
    )

    response_data = {
        "recommendation_id": str(recommendation_id),
        "suggestions": suggestions,
        "total_suggestions": len(suggestions),
        "generated_at": datetime.utcnow().isoformat(),
        "weather": weather_data,
        "occasion": occasion,
        "cached": False,
    }

    logger.info(f"Generated swipe deck of {len(suggestions)} outfits for user {current_user.id}")

    return DailySuggestionsResponse(**response_data)


async def _count_swipe_ratings_today(db: AsyncSession, user_id: UUID) -> int:
    """Count today's `swipe_rated` user_events — the source of truth for both
    the display-only status endpoint and the feedback endpoint's 429 gate."""
    events = await user_event_crud.list_for_user(
        db,
        user_id=user_id,
        since=datetime.combine(date.today(), datetime.min.time()),
        event_types=["swipe_rated"],
        limit=100,
    )
    return len(events)


@router.get("/swipe-deck/status", response_model=SwipeDeckStatusResponse)
async def get_swipe_deck_status(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """How many swipe-deck ratings the user has submitted today, and the daily
    cap — lets the client show/hide the entry point without inferring state
    from a 429 on the feedback endpoint."""
    ratings_today = await _count_swipe_ratings_today(db, current_user.id)
    return SwipeDeckStatusResponse(ratings_today=ratings_today, cap=SWIPE_DECK_DAILY_CAP)


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

    # RI-5 (Task 5.3): a rating on a swipe-deck-sourced `shown` row counts
    # against the daily cap. Only accepted/rejected are "ratings" (swapped
    # doesn't apply to a rating deck, but is not itself blocked here — the
    # client simply never offers it on deck candidates).
    is_swipe_deck_rating = bool(
        shown_event.context
        and shown_event.context.get("source") == "swipe_deck"
        and feedback.action
        in (RecommendationFeedbackAction.ACCEPTED, RecommendationFeedbackAction.REJECTED)
    )
    if is_swipe_deck_rating:
        ratings_today = await _count_swipe_ratings_today(db, current_user.id)
        if ratings_today >= SWIPE_DECK_DAILY_CAP:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Daily swipe-deck rating cap ({SWIPE_DECK_DAILY_CAP}) reached",
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

    # RI-5 (Task 5.3): a swipe-deck rating is ALSO its own labeled event —
    # `extract_preference_pairs` reads the underlying accepted/rejected rows
    # (unchanged shape, source distinguished via `context.source`), this is
    # purely the daily-cap counter's source of truth. Equal weight for
    # negative signal: no upweighting path exists for accepted vs rejected —
    # both simply increment the same counter.
    if is_swipe_deck_rating:
        try:
            await user_event_crud.create(
                db,
                user_id=current_user.id,
                event_type="swipe_rated",
                payload={
                    "recommendation_id": str(recommendation_id),
                    "outfit_index": feedback.outfit_index,
                    "action": feedback.action.value,
                },
            )
        except Exception as e:
            logger.warning(f"Failed to write swipe_rated event: {e}")

    # RI-6 (finalized plan §4, exit-criterion enabler): a "dislike_item"
    # rejection is the primary signal `feedback_source.get_recent_dislikes`
    # reads, which feeds thumbs-propagation — but propagation is only
    # recomputed on a fresh `generate_daily_outfits()` call. Without
    # invalidating today's cache here, "rejecting an item measurably lowers
    # near-duplicate candidates' scores next generation" would be
    # unobservable for up to 24h. Best-effort, never blocks the response.
    if is_rejection and rejection_reason == "dislike_item":
        try:
            await invalidate_daily_suggestions(current_user.id)
        except Exception as e:
            logger.warning(f"Failed to invalidate daily-suggestions cache for feedback: {e}")

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
