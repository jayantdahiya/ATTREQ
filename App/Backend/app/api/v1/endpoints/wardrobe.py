"""Wardrobe management endpoints for ATTREQ API."""

import logging
import math
from uuid import UUID

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    HTTPException,
    Query,
    UploadFile,
    status,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_current_active_user
from app.core.database import get_db
from app.crud.wardrobe import wardrobe_crud
from app.models.user import User
from app.schemas.wardrobe import (
    WardrobeItemList,
    WardrobeItemResponse,
    WardrobeItemUpdate,
    WardrobeItemUploadResponse,
)
from app.services.ai.embeddings import weaviate_service
from app.services.storage.file_handler import file_storage
from app.workers.image_processor import process_wardrobe_image

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/upload", response_model=WardrobeItemUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_wardrobe_item(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(..., description="Clothing image to upload (JPG or PNG)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Upload a new clothing item to wardrobe.

    This endpoint accepts an image upload and triggers background processing to:
    - Remove background
    - Detect clothing attributes (category, color, pattern)
    - Generate thumbnail
    - Add to vector database for similarity search

    Args:
        background_tasks: FastAPI background tasks
        file: Uploaded image file
        db: Database session
        current_user: Currently authenticated user

    Returns:
        Upload response with item ID and status

    Raises:
        HTTPException: If file validation fails
    """
    # Validate file type
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be an image (JPEG or PNG)"
        )

    # Validate file extension
    if file.filename:
        extension = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
        if extension not in ["jpg", "jpeg", "png"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only JPG and PNG images are supported"
            )

    try:
        # Save uploaded file
        file_path, file_url = await file_storage.save_upload_file(
            file,
            current_user.id,
            "originals"
        )

        # Create database record with pending status
        item = await wardrobe_crud.create(
            db=db,
            user_id=current_user.id,
            original_image_url=file_url
        )

        # Queue background processing
        background_tasks.add_task(
            process_wardrobe_image,
            item_id=item.id,
            user_id=current_user.id,
            original_image_path=file_path,
            db=db
        )

        logger.info(f"Wardrobe item {item.id} uploaded by user {current_user.id}")

        return WardrobeItemUploadResponse(
            id=item.id,
            status="processing",
            message="Image uploaded successfully. AI processing started.",
            original_image_url=file_url
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        ) from e
    except Exception as e:
        logger.error(f"Upload failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload image"
        ) from e


@router.get("/items", response_model=WardrobeItemList)
async def list_wardrobe_items(
    category: str | None = Query(None, description="Filter by category"),
    color: str | None = Query(None, description="Filter by color (primary or secondary)"),
    season: str | None = Query(None, description="Filter by season"),
    occasion: str | None = Query(None, description="Filter by occasion"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """List all wardrobe items for the current user with optional filters.

    Args:
        category: Optional category filter
        color: Optional color filter
        season: Optional season filter
        occasion: Optional occasion filter
        page: Page number (starting from 1)
        page_size: Number of items per page
        db: Database session
        current_user: Currently authenticated user

    Returns:
        Paginated list of wardrobe items
    """
    skip = (page - 1) * page_size

    items, total = await wardrobe_crud.get_by_user(
        db=db,
        user_id=current_user.id,
        category=category,
        color=color,
        season=season,
        occasion=occasion,
        skip=skip,
        limit=page_size
    )

    total_pages = math.ceil(total / page_size) if total > 0 else 0

    return WardrobeItemList(
        items=[WardrobeItemResponse.model_validate(item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.get("/items/{item_id}", response_model=WardrobeItemResponse)
async def get_wardrobe_item(
    item_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get a specific wardrobe item by ID.

    Args:
        item_id: UUID of the wardrobe item
        db: Database session
        current_user: Currently authenticated user

    Returns:
        Wardrobe item details

    Raises:
        HTTPException: If item not found or user doesn't have access
    """
    item = await wardrobe_crud.get_by_id(db, item_id, current_user.id)

    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Wardrobe item not found"
        )

    return WardrobeItemResponse.model_validate(item)


@router.put("/items/{item_id}", response_model=WardrobeItemResponse)
async def update_wardrobe_item(
    item_id: UUID,
    item_update: WardrobeItemUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Update tags for a wardrobe item.

    Allows manual correction or addition of item attributes.

    Args:
        item_id: UUID of the wardrobe item
        item_update: Updated item data
        db: Database session
        current_user: Currently authenticated user

    Returns:
        Updated wardrobe item

    Raises:
        HTTPException: If item not found or user doesn't have access
    """
    # Verify ownership
    item = await wardrobe_crud.get_by_id(db, item_id, current_user.id)

    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Wardrobe item not found"
        )

    # Prepare update data (exclude None values)
    update_data = item_update.model_dump(exclude_unset=True)

    # Update in database
    updated_item = await wardrobe_crud.update(db, item_id, update_data)

    # Update in Weaviate if connected
    try:
        if weaviate_service.is_connected():
            # Delete old entry
            weaviate_service.delete_item(item_id)

            # Add updated entry
            weaviate_service.add_item(
                item_id=updated_item.id,
                user_id=updated_item.user_id,
                category=updated_item.category,
                color_primary=updated_item.color_primary,
                color_secondary=updated_item.color_secondary,
                pattern=updated_item.pattern,
                season=updated_item.season,
                occasion=updated_item.occasion,
            )
    except Exception as e:
        logger.warning(f"Failed to update item in Weaviate: {str(e)}")

    logger.info(f"Wardrobe item {item_id} updated by user {current_user.id}")

    return WardrobeItemResponse.model_validate(updated_item)


@router.delete("/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_wardrobe_item(
    item_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Delete a wardrobe item.

    This will remove the item from:
    - Database
    - Weaviate vector database
    - File storage (images)

    Args:
        item_id: UUID of the wardrobe item
        db: Database session
        current_user: Currently authenticated user

    Raises:
        HTTPException: If item not found or user doesn't have access
    """
    # Get item to retrieve file paths
    item = await wardrobe_crud.get_by_id(db, item_id, current_user.id)

    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Wardrobe item not found"
        )

    # Delete from database
    deleted = await wardrobe_crud.delete(db, item_id, current_user.id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete item"
        )

    # Delete from Weaviate
    try:
        if weaviate_service.is_connected():
            weaviate_service.delete_item(item_id)
    except Exception as e:
        logger.warning(f"Failed to delete item from Weaviate: {str(e)}")

    # Delete files (best effort, don't fail if files don't exist)
    # Note: File paths would need to be reconstructed from URLs or stored separately
    # For now, log the operation
    logger.info(f"Wardrobe item {item_id} deleted by user {current_user.id}")

    return

