"""Batch image processing worker for wardrobe items using Gemini API."""

import asyncio
import logging
from pathlib import Path
from typing import Any
from uuid import UUID

from attreq_api.config.database import AsyncSessionLocal
from attreq_api.config.settings import settings
from attreq_api.crud.wardrobe import wardrobe_crud
from attreq_api.services.ai.background_removal import background_removal_service
from attreq_api.services.ai.embeddings import weaviate_service
from attreq_api.services.ai.gemini_classifier import gemini_classifier_service
from attreq_api.services.storage.file_handler import file_storage
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


async def process_batch_wardrobe_images(
    item_ids: list[UUID], user_id: UUID, image_paths: list[str]
) -> None:
    """Process multiple wardrobe images in batches using Gemini API.

    Args:
        item_ids: List of wardrobe item IDs to process
        user_id: User ID who owns the items
        image_paths: List of image file paths
    """
    if len(item_ids) != len(image_paths):
        raise ValueError("Item IDs and image paths must have the same length")

    logger.info(f"Processing batch of {len(image_paths)} wardrobe images for user {user_id}")

    async with AsyncSessionLocal() as db:
        batch_size = settings.gemini_batch_size
        processed_count = 0

        for i in range(0, len(image_paths), batch_size):
            batch_item_ids = item_ids[i : i + batch_size]
            batch_image_paths = image_paths[i : i + batch_size]

            logger.info(f"Processing batch {i // batch_size + 1}: {len(batch_image_paths)} images")

            try:
                await _process_single_batch(
                    batch_item_ids=batch_item_ids,
                    batch_image_paths=batch_image_paths,
                    user_id=user_id,
                    db=db,
                )
                processed_count += len(batch_image_paths)

            except Exception as e:
                logger.error(f"Batch processing failed for batch {i // batch_size + 1}: {str(e)}")
                await _fallback_to_individual_processing(
                    batch_item_ids=batch_item_ids,
                    batch_image_paths=batch_image_paths,
                    user_id=user_id,
                    db=db,
                )
                processed_count += len(batch_image_paths)

        logger.info(
            f"Completed batch processing: {processed_count}/{len(image_paths)} images processed"
        )


async def _process_single_batch(
    batch_item_ids: list[UUID], batch_image_paths: list[str], user_id: UUID, db: AsyncSession
) -> None:
    """Process a single batch of images with Gemini API.

    Args:
        batch_item_ids: List of item IDs in this batch
        batch_image_paths: List of image paths in this batch
        user_id: User ID who owns the items
        db: Database session
    """
    try:
        # Classify images with Gemini
        classification_results = await gemini_classifier_service.classify_batch_images(
            batch_image_paths
        )

        # Ensure we have results for all images
        if len(classification_results) != len(batch_image_paths):
            logger.warning(
                f"Gemini returned {len(classification_results)} results for {len(batch_image_paths)} images"
            )
            # Pad with empty results if needed
            while len(classification_results) < len(batch_image_paths):
                classification_results.append(
                    {
                        "category": None,
                        "color_primary": None,
                        "color_secondary": None,
                        "pattern": None,
                        "season": [],
                        "occasion": [],
                        "detection_confidence": 0.0,
                        "processing_status": "failed",
                    }
                )

        # Process each item in the batch
        for item_id, image_path, classification_result in zip(
            batch_item_ids, batch_image_paths, classification_results, strict=False
        ):
            try:
                await _process_single_item(
                    item_id=item_id,
                    image_path=image_path,
                    classification_result=classification_result,
                    user_id=user_id,
                    db=db,
                )
                logger.info(f"Successfully processed item {item_id} in batch")

            except Exception as e:
                logger.error(f"Failed to process item {item_id} in batch: {str(e)}")
                # Mark item as failed
                await wardrobe_crud.update(
                    db=db, item_id=item_id, update_data={"processing_status": "failed"}
                )

    except Exception as e:
        logger.error(f"Single batch processing failed: {str(e)}")
        raise


async def _fallback_to_individual_processing(
    batch_item_ids: list[UUID], batch_image_paths: list[str], user_id: UUID, db: AsyncSession
) -> None:
    """Fallback to individual image processing if batch processing fails.

    Args:
        batch_item_ids: List of item IDs in this batch
        batch_image_paths: List of image paths in this batch
        user_id: User ID who owns the items
        db: Database session
    """
    logger.info(f"Falling back to individual processing for {len(batch_image_paths)} images")

    for item_id, image_path in zip(batch_item_ids, batch_image_paths, strict=False):
        try:
            # Use single image classification
            classification_result = await gemini_classifier_service.classify_single_image(
                image_path
            )

            await _process_single_item(
                item_id=item_id,
                image_path=image_path,
                classification_result=classification_result,
                user_id=user_id,
                db=db,
            )
            logger.info(f"Successfully processed item {item_id} individually")

        except Exception as e:
            logger.error(f"Individual processing failed for item {item_id}: {str(e)}")
            # Mark item as failed
            await wardrobe_crud.update(
                db=db, item_id=item_id, update_data={"processing_status": "failed"}
            )


async def _process_single_item(
    item_id: UUID,
    image_path: str,
    classification_result: dict[str, Any],
    user_id: UUID,
    db: AsyncSession,
) -> None:
    """Process a single wardrobe item with classification results.

    Args:
        item_id: Wardrobe item ID
        image_path: Path to the image file
        classification_result: Classification results from Gemini
        user_id: User ID who owns the item
        db: Database session
    """
    try:
        # Update item with classification results
        update_data = {
            "category": classification_result.get("category"),
            "color_primary": classification_result.get("color_primary"),
            "color_secondary": classification_result.get("color_secondary"),
            "pattern": classification_result.get("pattern"),
            "season": classification_result.get("season", []),
            "occasion": classification_result.get("occasion", []),
            "detection_confidence": classification_result.get("detection_confidence", 0.0),
            "processing_status": "processing",  # Will be updated to completed at the end
        }

        await wardrobe_crud.update(db=db, item_id=item_id, update_data=update_data)

        # Process background removal
        try:
            # Determine processed image path
            original_path = Path(image_path)
            processed_filename = original_path.name.replace(
                original_path.suffix, f"_processed{original_path.suffix}"
            )
            processed_image_path = str(file_storage.processed_dir / processed_filename)

            await asyncio.to_thread(
                background_removal_service.remove_background,
                image_path,
                processed_image_path,
            )

            # Get URL for processed image
            processed_image_url = file_storage.get_file_url(processed_image_path)

            # Update with processed image URL
            await wardrobe_crud.update(
                db=db, item_id=item_id, update_data={"processed_image_url": processed_image_url}
            )
            logger.info(f"Background removal completed for item {item_id}")

        except Exception as e:
            logger.warning(f"Background removal failed for item {item_id}: {str(e)}")
            # Continue without processed image
            processed_image_path = image_path

        # Generate thumbnail
        try:
            thumbnail_path, thumbnail_url = await asyncio.to_thread(
                file_storage.generate_thumbnail,
                processed_image_path,
                str(user_id),
                300,
            )

            # Update with thumbnail URL
            await wardrobe_crud.update(
                db=db, item_id=item_id, update_data={"thumbnail_url": thumbnail_url}
            )
            logger.info(f"Thumbnail generation completed for item {item_id}")

        except Exception as e:
            logger.warning(f"Thumbnail generation failed for item {item_id}: {str(e)}")
            # Continue without thumbnail

        # Add to Weaviate vector database
        try:
            if weaviate_service.is_connected():
                # Get updated item data
                updated_item = await wardrobe_crud.get_by_id(db, item_id, user_id)
                if updated_item:
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
                logger.info(f"Weaviate indexing completed for item {item_id}")

        except Exception as e:
            logger.warning(f"Weaviate indexing failed for item {item_id}: {str(e)}")
            # Continue without Weaviate indexing

        # Mark as completed
        await wardrobe_crud.update(
            db=db, item_id=item_id, update_data={"processing_status": "completed"}
        )

        logger.info(f"Item {item_id} processing completed successfully")

    except Exception as e:
        logger.error(f"Failed to process item {item_id}: {str(e)}")
        # Mark as failed
        await wardrobe_crud.update(
            db=db, item_id=item_id, update_data={"processing_status": "failed"}
        )
        raise
