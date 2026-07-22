"""Image processing worker for wardrobe items."""

import asyncio
import logging
from uuid import UUID

from attreq_api.config.database import AsyncSessionLocal
from attreq_api.crud.wardrobe import wardrobe_crud
from attreq_api.crud.wardrobe_photo import wardrobe_photo_crud
from attreq_api.services.ai.background_removal import (
    cleanup_classification_tempdir,
    generate_processed_and_thumbnail,
)
from attreq_api.services.ai.clothing_detection import clothing_detection_service
from attreq_api.services.ai.color_extraction import extract_palette_safe
from attreq_api.services.ai.embeddings import weaviate_service
from attreq_api.services.ai.schema_mapper import build_wardrobe_update_payload
from attreq_api.services.stats.wardrobe_stats import invalidate_wardrobe_stats_cache

logger = logging.getLogger(__name__)


async def process_wardrobe_image(
    item_id: UUID, user_id: UUID, original_image_ref: str, original_image_url: str
) -> None:
    """Process a wardrobe image through the AI pipeline.

    This function orchestrates the complete AI processing pipeline:
    1. Update status to "processing"
    2. Remove background + generate thumbnail (shared, storage-agnostic helper)
    3. Detect clothing attributes with the configured LLM classifier
    4. Add to Weaviate for vector search
    5. Update database with results
    6. Invalidate the wardrobe-stats cache
    7. Set status to "completed" or "failed"

    Args:
        item_id: UUID of the wardrobe item
        user_id: UUID of the user
        original_image_ref: Storage reference of the original upload
            (local path or S3 object key)
        original_image_url: Stored URL/key of the original upload, used as
            the processed-image fallback when background removal fails
    """
    logger.info(f"Starting image processing for item {item_id}")

    async with AsyncSessionLocal() as db:
        try:
            # Step 1: Update status to "processing"
            await wardrobe_crud.update_processing_status(db, item_id, "processing")
            logger.info(f"Item {item_id} status updated to processing")

            # Step 2: Remove background + generate thumbnail (shared helper).
            # `classification_path` lives in a temp dir we own and must clean
            # up ourselves once classification is done.
            classification_path, bg_removed_url, thumbnail_url = (
                await generate_processed_and_thumbnail(
                    original_image_ref, user_id, log_ref=f"item {item_id}"
                )
            )
            # `bg_removed_url` is None iff background removal failed, in which
            # case `classification_path` is `original_tmp`, not a
            # background-removed image — pixel color extraction must not run
            # against it (see color_extraction.py docstring).
            bg_removal_succeeded = bg_removed_url is not None
            # Background removal failed -> fall back to the already-stored
            # original URL/key, never a freshly (and, for S3, presigned) one.
            processed_image_url = bg_removed_url or original_image_url

            try:
                # Step 3: Detect clothing attributes and extract the pixel
                # color palette concurrently — a failure in one must not
                # affect the other.
                detect_coro = clothing_detection_service.detect_clothing(classification_path)
                palette_coro = extract_palette_safe(
                    classification_path if bg_removal_succeeded else None,
                    log_ref=f"item {item_id}",
                )
                detection_outcome, palette_outcome = await asyncio.gather(
                    detect_coro, palette_coro, return_exceptions=True
                )

                if isinstance(detection_outcome, BaseException):
                    logger.error(f"Clothing detection failed for item {item_id}: {str(detection_outcome)}")
                    detection_result = {
                        "category": None,
                        "color_primary": None,
                        "color_secondary": None,
                        "pattern": None,
                        "season": [],
                        "occasion": [],
                        "detection_confidence": 0.0,
                        "processing_status": "failed",
                    }
                else:
                    detection_result = detection_outcome
                    logger.info(
                        f"Clothing detection completed for item {item_id}: {detection_result}"
                    )

                # `extract_palette_safe` never raises — it degrades internally
                # to (None, "llm_fallback"). `isinstance` check here is a
                # defensive backstop only.
                if isinstance(palette_outcome, BaseException):
                    logger.error(f"Color extraction task errored for item {item_id}: {str(palette_outcome)}")
                    palette, color_extraction_source = None, "llm_fallback"
                else:
                    palette, color_extraction_source = palette_outcome
            finally:
                cleanup_classification_tempdir(classification_path)

            # Step 4: Add to Weaviate
            try:
                if weaviate_service.is_connected():
                    weaviate_service.init_schema()
                    weaviate_service.add_item(
                        item_id=item_id,
                        user_id=user_id,
                        category=detection_result.get("category"),
                        color_primary=detection_result.get("color_primary"),
                        color_secondary=detection_result.get("color_secondary"),
                        pattern=detection_result.get("pattern"),
                        season=detection_result.get("season", []),
                        occasion=detection_result.get("occasion", []),
                    )
                    logger.info(f"Item {item_id} added to Weaviate")
                else:
                    logger.warning("Weaviate not connected, skipping vector indexing")
            except Exception as e:
                logger.error(f"Failed to add item {item_id} to Weaviate: {str(e)}")

            update_data = build_wardrobe_update_payload(
                detection_result=detection_result,
                palette=palette,
                color_extraction_source=color_extraction_source,
                processed_image_url=processed_image_url,
                thumbnail_url=thumbnail_url,
            )

            await wardrobe_crud.update(db, item_id, update_data)
            logger.info(f"Item {item_id} processing completed successfully")

            try:
                await invalidate_wardrobe_stats_cache(user_id)
            except Exception as e:
                logger.warning(f"Failed to invalidate stats cache for user {user_id}: {str(e)}")

        except Exception as e:
            logger.error(f"Image processing failed for item {item_id}: {str(e)}")
            try:
                await wardrobe_crud.update_processing_status(db, item_id, "failed")
            except Exception as update_error:
                logger.error(
                    f"Failed to update status to 'failed' for item {item_id}: {str(update_error)}"
                )


async def process_wardrobe_item_photo(
    photo_id: UUID, user_id: UUID, original_image_path: str
) -> None:
    """Process an additional photo attached to an existing wardrobe item.

    Reuses the shared bg-removal + thumbnail pipeline only — no
    re-classification and no Weaviate indexing, since the item's
    classification is already established. The item still counts once in
    stats regardless of how many photos it has, so no stats-cache
    invalidation happens here.

    Args:
        photo_id: UUID of the wardrobe_item_photos row
        user_id: UUID of the user who owns the item
        original_image_path: Storage reference of the original uploaded
            photo (local path or S3 object key)
    """
    logger.info(f"Starting photo processing for photo {photo_id}")

    async with AsyncSessionLocal() as db:
        try:
            classification_path, processed_image_url, thumbnail_url = (
                await generate_processed_and_thumbnail(
                    original_image_path, user_id, log_ref=f"photo {photo_id}"
                )
            )
            cleanup_classification_tempdir(classification_path)

            if processed_image_url is None:
                # Background removal failed — fall back to the photo's
                # already-persisted original URL rather than minting a new
                # one (would be a presigned URL under the S3 backend).
                existing_photo = await wardrobe_photo_crud.get_by_id(db, photo_id)
                processed_image_url = (
                    existing_photo.original_image_url if existing_photo else None
                )

            await wardrobe_photo_crud.update(
                db,
                photo_id,
                {
                    "processed_image_url": processed_image_url,
                    "thumbnail_url": thumbnail_url,
                },
            )
            logger.info(f"Photo {photo_id} processing completed successfully")
        except Exception as e:
            logger.error(f"Photo processing failed for photo {photo_id}: {str(e)}")
