"""Wardrobe stats & forgotten-items retention surface endpoints."""

import logging

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from attreq_api.api.v1.deps import get_current_active_user
from attreq_api.config.database import get_db
from attreq_api.models.user import User
from attreq_api.schemas.stats import (
    ForgottenItemsResponse,
    WardrobeStatsResponse,
    build_forgotten_items_response,
    build_wardrobe_stats_response,
)
from attreq_api.services.stats.wardrobe_stats import get_forgotten_items, get_wardrobe_stats

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/wardrobe", response_model=WardrobeStatsResponse)
async def get_wardrobe_stats_endpoint(
    force_refresh: bool = Query(False, description="Force recomputation, bypass cache"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Return the wardrobe stats dashboard payload for the current user.

    Composition, closet value, cost-per-wear, most/least worn, and
    never-worn percentage — computed over *active* items only (archived
    items keep their outfit history but aren't in these dashboard numbers).
    Cached in Redis for 1 hour; pass `force_refresh=true` to bypass.
    """
    result = await get_wardrobe_stats(db, current_user.id, force_refresh=force_refresh)
    return build_wardrobe_stats_response(result)


@router.get("/forgotten", response_model=ForgottenItemsResponse)
async def get_forgotten_items_endpoint(
    force_refresh: bool = Query(False, description="Force recomputation, bypass cache"),
    days_threshold: int = Query(
        60, ge=1, description="Days since last worn before an item counts as forgotten"
    ),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Return never-worn / long-unworn active items, each with a suggested pairing.

    Cached in Redis for 1 hour; pass `force_refresh=true` to bypass.
    """
    result = await get_forgotten_items(
        db, current_user.id, days_threshold=days_threshold, force_refresh=force_refresh
    )
    return build_forgotten_items_response(result)
