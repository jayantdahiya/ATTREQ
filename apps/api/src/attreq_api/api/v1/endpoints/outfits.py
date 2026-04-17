"""Outfit management endpoints for ATTREQ API."""

import logging
import math
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from attreq_api.api.v1.deps import get_current_active_user
from attreq_api.config.database import get_db
from attreq_api.crud.outfit import outfit_crud
from attreq_api.crud.wardrobe import wardrobe_crud
from attreq_api.models.user import User
from attreq_api.schemas.outfit import (
    OutfitCreate,
    OutfitFeedback,
    OutfitList,
    OutfitResponse,
    OutfitWear,
)

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("", response_model=OutfitResponse, status_code=status.HTTP_201_CREATED)
async def create_outfit(
    outfit_data: OutfitCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Create a new outfit manually.

    Args:
        outfit_data: Outfit creation data
        db: Database session
        current_user: Currently authenticated user

    Returns:
        Created outfit

    Raises:
        HTTPException: If referenced items don't exist or don't belong to user
    """
    # Verify that referenced items belong to the user
    if outfit_data.top_item_id:
        top_item = await wardrobe_crud.get_by_id(db, outfit_data.top_item_id, current_user.id)
        if not top_item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Top item {outfit_data.top_item_id} not found",
            )

    if outfit_data.bottom_item_id:
        bottom_item = await wardrobe_crud.get_by_id(db, outfit_data.bottom_item_id, current_user.id)
        if not bottom_item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Bottom item {outfit_data.bottom_item_id} not found",
            )

    # Verify accessory items
    if outfit_data.accessory_ids:
        for acc_id in outfit_data.accessory_ids:
            accessory = await wardrobe_crud.get_by_id(db, acc_id, current_user.id)
            if not accessory:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Accessory item {acc_id} not found",
                )

    # Create outfit
    outfit = await outfit_crud.create(
        db=db,
        user_id=current_user.id,
        top_item_id=outfit_data.top_item_id,
        bottom_item_id=outfit_data.bottom_item_id,
        accessory_ids=outfit_data.accessory_ids,
        occasion_context=outfit_data.occasion_context,
    )

    logger.info(f"Outfit {outfit.id} created by user {current_user.id}")

    return OutfitResponse.model_validate(outfit)


@router.get("", response_model=OutfitList)
async def list_outfits(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """List all outfits for the current user.

    Args:
        page: Page number (starting from 1)
        page_size: Number of items per page
        db: Database session
        current_user: Currently authenticated user

    Returns:
        Paginated list of outfits
    """
    skip = (page - 1) * page_size

    outfits, total = await outfit_crud.get_by_user(
        db=db,
        user_id=current_user.id,
        skip=skip,
        limit=page_size,
        load_items=False,  # Don't load items for list view
    )

    total_pages = math.ceil(total / page_size) if total > 0 else 0

    return OutfitList(
        items=[OutfitResponse.model_validate(outfit) for outfit in outfits],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get("/{outfit_id}", response_model=OutfitResponse)
async def get_outfit(
    outfit_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get a specific outfit by ID.

    Args:
        outfit_id: UUID of the outfit
        db: Database session
        current_user: Currently authenticated user

    Returns:
        Outfit details

    Raises:
        HTTPException: If outfit not found or user doesn't have access
    """
    outfit = await outfit_crud.get_by_id(db, outfit_id, current_user.id, load_items=True)

    if not outfit:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Outfit not found")

    return OutfitResponse.model_validate(outfit)


@router.post("/{outfit_id}/wear", response_model=OutfitResponse)
async def mark_outfit_worn(
    outfit_id: UUID,
    wear_data: OutfitWear,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Mark an outfit as worn on a specific date.

    This will:
    - Set the worn_date for the outfit
    - Increment wear_count for all items in the outfit
    - Update last_worn date for all items

    Args:
        outfit_id: UUID of the outfit
        wear_data: Wear data with date
        db: Database session
        current_user: Currently authenticated user

    Returns:
        Updated outfit

    Raises:
        HTTPException: If outfit not found or user doesn't have access
    """
    # Verify ownership
    outfit = await outfit_crud.get_by_id(db, outfit_id, current_user.id)

    if not outfit:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Outfit not found")

    # Mark outfit as worn
    updated_outfit = await outfit_crud.mark_as_worn(db, outfit_id, wear_data.worn_date)

    # Increment wear count for items
    if outfit.top_item_id:
        item = await wardrobe_crud.get_by_id(db, outfit.top_item_id)
        if item:
            await wardrobe_crud.update(
                db,
                outfit.top_item_id,
                {"wear_count": item.wear_count + 1, "last_worn": wear_data.worn_date},
            )

    if outfit.bottom_item_id:
        item = await wardrobe_crud.get_by_id(db, outfit.bottom_item_id)
        if item:
            await wardrobe_crud.update(
                db,
                outfit.bottom_item_id,
                {"wear_count": item.wear_count + 1, "last_worn": wear_data.worn_date},
            )

    # Update accessories
    if outfit.accessory_ids:
        for acc_id in outfit.accessory_ids:
            item = await wardrobe_crud.get_by_id(db, acc_id)
            if item:
                await wardrobe_crud.update(
                    db,
                    acc_id,
                    {"wear_count": item.wear_count + 1, "last_worn": wear_data.worn_date},
                )

    logger.info(f"Outfit {outfit_id} marked as worn by user {current_user.id}")

    return OutfitResponse.model_validate(updated_outfit)


@router.post("/{outfit_id}/feedback", response_model=OutfitResponse)
async def submit_outfit_feedback(
    outfit_id: UUID,
    feedback: OutfitFeedback,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Submit feedback (like/dislike) for an outfit.

    Feedback scores:
    - -1: Dislike
    - 0: Neutral
    - 1: Like

    Args:
        outfit_id: UUID of the outfit
        feedback: Feedback data
        db: Database session
        current_user: Currently authenticated user

    Returns:
        Updated outfit

    Raises:
        HTTPException: If outfit not found or user doesn't have access
    """
    # Verify ownership
    outfit = await outfit_crud.get_by_id(db, outfit_id, current_user.id)

    if not outfit:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Outfit not found")

    # Update feedback
    updated_outfit = await outfit_crud.update_feedback(db, outfit_id, feedback.feedback_score)

    logger.info(
        f"Feedback {feedback.feedback_score} submitted for outfit {outfit_id} by user {current_user.id}"
    )

    return OutfitResponse.model_validate(updated_outfit)


@router.delete("/{outfit_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_outfit(
    outfit_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Delete an outfit.

    Args:
        outfit_id: UUID of the outfit
        db: Database session
        current_user: Currently authenticated user

    Raises:
        HTTPException: If outfit not found or user doesn't have access
    """
    deleted = await outfit_crud.delete(db, outfit_id, current_user.id)

    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Outfit not found")

    logger.info(f"Outfit {outfit_id} deleted by user {current_user.id}")

    return
