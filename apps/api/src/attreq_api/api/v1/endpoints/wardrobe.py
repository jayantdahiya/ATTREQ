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

from attreq_api.api.v1.deps import get_current_active_user
from attreq_api.config.database import get_db
from attreq_api.config.settings import settings
from attreq_api.crud.wardrobe import wardrobe_crud
from attreq_api.crud.wardrobe_photo import wardrobe_photo_crud
from attreq_api.models.user import User
from attreq_api.schemas.wardrobe import (
    WardrobeItemList,
    WardrobeItemListEntry,
    WardrobeItemPhotoResponse,
    WardrobeItemPhotoUploadResponse,
    WardrobeItemResponse,
    WardrobeItemStatusUpdate,
    WardrobeItemUpdate,
    WardrobeItemUploadResponse,
)
from attreq_api.services.ai.embeddings import weaviate_service
from attreq_api.services.cache.invalidation import invalidate_daily_suggestions
from attreq_api.services.stats.wardrobe_stats import invalidate_wardrobe_stats_cache
from attreq_api.services.storage.file_handler import file_storage
from attreq_api.workers.batch_image_processor import process_batch_wardrobe_images
from attreq_api.workers.image_processor import process_wardrobe_image, process_wardrobe_item_photo

router = APIRouter()
logger = logging.getLogger(__name__)


def _validate_image_upload(file: UploadFile, *, label: str = "File") -> None:
    """Validate an uploaded file is a supported image (content-type + extension).

    Shared by the single-upload, batch-upload, and add-photo endpoints
    (previously duplicated three ways).

    Raises:
        HTTPException: 400 if the file isn't a supported image.
    """
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{label} must be an image (JPEG or PNG)",
        )

    if file.filename:
        extension = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
        if extension not in ["jpg", "jpeg", "png"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"{label}: Only JPG and PNG images are supported",
            )


@router.post(
    "/upload", response_model=WardrobeItemUploadResponse, status_code=status.HTTP_201_CREATED
)
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
    _validate_image_upload(file)

    try:
        # Save uploaded file
        file_path, file_url = await file_storage.save_upload_file(
            file, current_user.id, "originals"
        )

        # Create database record with pending status
        item = await wardrobe_crud.create(
            db=db, user_id=current_user.id, original_image_url=file_url
        )

        # Queue background processing
        background_tasks.add_task(
            process_wardrobe_image,
            item_id=item.id,
            user_id=current_user.id,
            original_image_path=file_path,
        )

        logger.info(f"Wardrobe item {item.id} uploaded by user {current_user.id}")

        return WardrobeItemUploadResponse(
            id=item.id,
            status="processing",
            message="Image uploaded successfully. AI processing started.",
            original_image_url=file_url,
        )

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    except Exception as e:
        logger.error(f"Upload failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to upload image"
        ) from e


@router.post(
    "/batch-upload",
    response_model=list[WardrobeItemUploadResponse],
    status_code=status.HTTP_201_CREATED,
)
async def batch_upload_wardrobe_items(
    background_tasks: BackgroundTasks,
    files: list[UploadFile] = File(
        ..., description="Multiple clothing images to upload (JPG or PNG)"
    ),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Upload multiple clothing items to wardrobe in a single batch.

    This endpoint accepts multiple image uploads and triggers batch processing to:
    - Process images with bounded concurrency (one isolated DB session per
      item — see `workers/batch_image_processor.py`)
    - Remove backgrounds for all images
    - Detect clothing attributes for all items
    - Generate thumbnails for all images
    - Add all items to vector database for similarity search

    One bad image never fails the rest of the batch.

    Args:
        background_tasks: FastAPI background tasks
        files: List of uploaded image files (up to `wardrobe_batch_upload_max_files`)
        db: Database session
        current_user: Currently authenticated user

    Returns:
        List of upload responses with item IDs and status

    Raises:
        HTTPException: If file validation fails or too many files
    """
    # Validate number of files
    max_files = settings.wardrobe_batch_upload_max_files
    if len(files) > max_files:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Too many files. Maximum {max_files} files allowed per batch.",
        )

    if len(files) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one file is required for batch upload.",
        )

    # Validate all files
    validated_files = []
    for i, file in enumerate(files):
        _validate_image_upload(file, label=f"File {i + 1}")
        validated_files.append(file)

    try:
        # Save all uploaded files and create database records
        saved_items = []
        image_paths = []

        for file in validated_files:
            # Save uploaded file
            file_path, file_url = await file_storage.save_upload_file(
                file, current_user.id, "originals"
            )

            # Create database record with pending status
            item = await wardrobe_crud.create(
                db=db, user_id=current_user.id, original_image_url=file_url
            )

            saved_items.append(item)
            image_paths.append(file_path)

        # Queue batch background processing
        background_tasks.add_task(
            process_batch_wardrobe_images,
            item_ids=[item.id for item in saved_items],
            user_id=current_user.id,
            image_paths=image_paths,
        )

        logger.info(
            f"Batch upload: {len(saved_items)} wardrobe items uploaded by user {current_user.id}"
        )

        # Return responses for all items
        return [
            WardrobeItemUploadResponse(
                id=item.id,
                status="processing",
                message=f"Image {i + 1} uploaded successfully. Batch AI processing started.",
                original_image_url=item.original_image_url,
            )
            for i, item in enumerate(saved_items)
        ]

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    except Exception as e:
        logger.error(f"Batch upload failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to upload images"
        ) from e


@router.get("/items", response_model=WardrobeItemList)
async def list_wardrobe_items(
    category: str | None = Query(None, description="Filter by category"),
    color: str | None = Query(None, description="Filter by color (primary or secondary)"),
    season: str | None = Query(None, description="Filter by season"),
    occasion: str | None = Query(None, description="Filter by occasion"),
    item_status: str = Query(
        "active", alias="status", pattern="^(active|archived)$", description="Item status filter"
    ),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """List all wardrobe items for the current user with optional filters.

    Note: the list response omits `photos` (see `WardrobeItemListEntry`) — the
    list query deliberately does not eager-load photos to avoid N+1 queries
    and async lazy-load crashes. Use `GET /items/{id}` or the dedicated
    photos endpoint for the gallery.

    Args:
        category: Optional category filter
        color: Optional color filter
        season: Optional season filter
        occasion: Optional occasion filter
        item_status: "active" (default) or "archived" — powers the default
            wardrobe view and the Archived view
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
        status=item_status,
        skip=skip,
        limit=page_size,
    )

    total_pages = math.ceil(total / page_size) if total > 0 else 0

    return WardrobeItemList(
        items=[WardrobeItemListEntry.model_validate(item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
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
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Wardrobe item not found")

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
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Wardrobe item not found")

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

    if "purchase_price" in update_data or "brand" in update_data:
        try:
            await invalidate_wardrobe_stats_cache(current_user.id)
        except Exception as e:
            logger.warning(f"Failed to invalidate stats cache: {str(e)}")

    logger.info(f"Wardrobe item {item_id} updated by user {current_user.id}")

    refreshed_item = await wardrobe_crud.get_by_id(db, item_id, current_user.id)
    return WardrobeItemResponse.model_validate(refreshed_item or updated_item)


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
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Wardrobe item not found")

    # Delete from database
    deleted = await wardrobe_crud.delete(db, item_id, current_user.id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to delete item"
        )

    # Delete from Weaviate
    try:
        if weaviate_service.is_connected():
            weaviate_service.delete_item(item_id)
    except Exception as e:
        logger.warning(f"Failed to delete item from Weaviate: {str(e)}")

    # Invalidate caches — a deleted item must disappear from stats and from
    # "Today" immediately, not after the 24h daily-suggestions TTL.
    try:
        await invalidate_wardrobe_stats_cache(current_user.id)
    except Exception as e:
        logger.warning(f"Failed to invalidate stats cache: {str(e)}")
    try:
        await invalidate_daily_suggestions(current_user.id)
    except Exception as e:
        logger.warning(f"Failed to invalidate daily-suggestions cache: {str(e)}")

    # Delete files (best effort, don't fail if files don't exist)
    # Note: File paths would need to be reconstructed from URLs or stored separately
    # For now, log the operation
    logger.info(f"Wardrobe item {item_id} deleted by user {current_user.id}")

    return


@router.post(
    "/items/bulk",
    response_model=list[WardrobeItemListEntry],
    status_code=status.HTTP_201_CREATED,
)
async def bulk_add_wardrobe_items(
    items_data: list[dict],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Bulk-insert wardrobe items detected from Style DNA photos or camera roll.

    Accepts a list of detected item dicts (from StyleDnaUploadResponse).
    Items are created with classification_source matching the caller's context.

    Returns `WardrobeItemListEntry` (no `photos`) — bulk-added items have no
    photos yet, and `db.refresh()` would expire the (never-loaded) `photos`
    relationship, which would otherwise trigger an async lazy-load crash if
    validated against the photos-carrying response type.
    """
    from attreq_api.models.wardrobe import WardrobeItem

    if not items_data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No items provided")

    if len(items_data) > 50:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Maximum 50 items per bulk request")

    created = []
    for data in items_data:
        category = data.get("subcategory") or data.get("category", "top")
        item = WardrobeItem(
            user_id=current_user.id,
            original_image_url=data.get("original_image_url", "/uploads/style-dna/placeholder.jpg"),
            category=category,
            color_primary=data.get("color_primary"),
            color_secondary=data.get("color_secondary"),
            pattern=data.get("pattern"),
            season=data.get("season", ["all"]),
            occasion=data.get("occasion", ["casual"]),
            detection_confidence=data.get("confidence", 0.7),
            classification_source=data.get("classification_source", "style_dna_seed"),
            processing_status="completed",
        )
        db.add(item)
        created.append(item)

    await db.commit()
    for item in created:
        await db.refresh(item)

    try:
        await invalidate_wardrobe_stats_cache(current_user.id)
    except Exception as e:
        logger.warning(f"Failed to invalidate stats cache: {str(e)}")

    logger.info(f"Bulk added {len(created)} wardrobe items for user {current_user.id}")
    return [WardrobeItemListEntry.model_validate(item) for item in created]


@router.patch("/items/{item_id}/status", response_model=WardrobeItemResponse)
async def update_wardrobe_item_status(
    item_id: UUID,
    status_update: WardrobeItemStatusUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Archive or unarchive a wardrobe item.

    Archiving removes the item from recommendation pools and from the
    default wardrobe list immediately (Weaviate entry removed, daily-
    suggestions cache invalidated for every occasion so it drops out of
    "Today" without waiting for the 24h TTL) while preserving its outfit
    history. Unarchiving reverses both.

    Args:
        item_id: UUID of the wardrobe item
        status_update: New status ("active" or "archived")
        db: Database session
        current_user: Currently authenticated user

    Returns:
        Updated wardrobe item (with photos)

    Raises:
        HTTPException: If item not found or user doesn't have access
    """
    item = await wardrobe_crud.get_by_id(db, item_id, current_user.id)

    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Wardrobe item not found")

    updated_item = await wardrobe_crud.update(db, item_id, {"status": status_update.status})

    try:
        if weaviate_service.is_connected():
            if status_update.status == "archived":
                weaviate_service.delete_item(item_id)
            else:
                weaviate_service.init_schema()
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

    try:
        await invalidate_wardrobe_stats_cache(current_user.id)
    except Exception as e:
        logger.warning(f"Failed to invalidate stats cache: {str(e)}")
    try:
        await invalidate_daily_suggestions(current_user.id)
    except Exception as e:
        logger.warning(f"Failed to invalidate daily-suggestions cache: {str(e)}")

    logger.info(
        f"Wardrobe item {item_id} status set to '{status_update.status}' by user {current_user.id}"
    )

    refreshed_item = await wardrobe_crud.get_by_id(db, item_id, current_user.id)
    return WardrobeItemResponse.model_validate(refreshed_item)


@router.post(
    "/items/{item_id}/photos",
    response_model=WardrobeItemPhotoUploadResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_wardrobe_item_photo(
    item_id: UUID,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(..., description="Additional photo for this item (JPG or PNG)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Add an additional photo to an existing wardrobe item's gallery.

    Only runs the shared bg-removal + thumbnail pipeline in the background —
    no re-classification, and no stats-cache invalidation (an item still
    counts once in stats regardless of how many photos it has).

    Args:
        item_id: UUID of the wardrobe item
        background_tasks: FastAPI background tasks
        file: Uploaded image file
        db: Database session
        current_user: Currently authenticated user

    Returns:
        Upload response with photo ID and status

    Raises:
        HTTPException: If item not found, not owned, or file validation fails
    """
    item = await wardrobe_crud.get_by_id(db, item_id, current_user.id)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Wardrobe item not found")

    _validate_image_upload(file)

    try:
        file_path, file_url = await file_storage.save_upload_file(
            file, current_user.id, "originals"
        )

        photo = await wardrobe_photo_crud.create(
            db=db, item_id=item_id, original_image_url=file_url
        )

        background_tasks.add_task(
            process_wardrobe_item_photo,
            photo_id=photo.id,
            user_id=current_user.id,
            original_image_path=file_path,
        )

        logger.info(f"Photo {photo.id} added to wardrobe item {item_id} by user {current_user.id}")

        return WardrobeItemPhotoUploadResponse(
            id=photo.id,
            status="processing",
            message="Photo uploaded successfully. Processing started.",
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    except Exception as e:
        logger.error(f"Add photo failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to upload photo"
        ) from e


@router.get("/items/{item_id}/photos", response_model=list[WardrobeItemPhotoResponse])
async def list_wardrobe_item_photos(
    item_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """List all additional photos for a wardrobe item (the gallery source).

    Also used by the client to poll photo processing status (checking for
    `processed_image_url`/`thumbnail_url` becoming non-null).

    Args:
        item_id: UUID of the wardrobe item
        db: Database session
        current_user: Currently authenticated user

    Returns:
        List of photos for the item

    Raises:
        HTTPException: If item not found or not owned
    """
    item = await wardrobe_crud.get_by_id(db, item_id, current_user.id)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Wardrobe item not found")

    photos = await wardrobe_photo_crud.get_by_item(db, item_id)
    return [WardrobeItemPhotoResponse.model_validate(photo) for photo in photos]


@router.delete("/items/{item_id}/photos/{photo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_wardrobe_item_photo(
    item_id: UUID,
    photo_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Delete an additional photo from a wardrobe item's gallery.

    Args:
        item_id: UUID of the wardrobe item
        photo_id: UUID of the photo to delete
        db: Database session
        current_user: Currently authenticated user

    Raises:
        HTTPException: 404 if item/photo not found or not owned/scoped;
            400 if attempting to delete the primary photo
    """
    item = await wardrobe_crud.get_by_id(db, item_id, current_user.id)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Wardrobe item not found")

    photo = await wardrobe_photo_crud.get_by_id(db, photo_id, item_id=item_id)
    if not photo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Photo not found")

    if photo.is_primary:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot delete the primary photo"
        )

    # Best-effort file cleanup — don't fail the request if files are already gone.
    for ref in (photo.original_image_url, photo.processed_image_url, photo.thumbnail_url):
        if ref:
            try:
                file_storage.delete_file(ref)
            except Exception as e:
                logger.warning(f"Failed to delete photo file {ref}: {str(e)}")

    await wardrobe_photo_crud.delete(db, photo_id)

    logger.info(f"Photo {photo_id} deleted from wardrobe item {item_id} by user {current_user.id}")

    return
