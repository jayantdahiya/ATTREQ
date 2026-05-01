"""Batch image processing worker for wardrobe items using Groq API."""

import asyncio
import logging
from pathlib import Path
from typing import Any
from uuid import UUID

from attreq_api.config.database import AsyncSessionLocal
from attreq_api.crud.wardrobe import wardrobe_crud
from attreq_api.services.ai.background_removal import background_removal_service
from attreq_api.services.ai.clothing_detection import clothing_detection_service
from attreq_api.services.ai.embeddings import weaviate_service
from attreq_api.services.storage.file_handler import file_storage
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

BATCH_SIZE = 5


async def process_batch_wardrobe_images(
    item_ids: list[UUID], user_id: UUID, image_paths: list[str]
) -> None:
    """Process multiple wardrobe images sequentially using Groq API.

    Args:
        item_ids: List of wardrobe item IDs to process
        user_id: User ID who owns the items
        image_paths: List of image file paths
    """
    if len(item_ids) != len(image_paths):
        raise ValueError("Item IDs and image paths must have the same length")

    logger.info(f"Processing batch of {len(image_paths)} wardrobe images for user {user_id}")

    async with AsyncSessionLocal() as db:
        processed_count = 0

        for i in range(0, len(image_paths), BATCH_SIZE):
            batch_item_ids = item_ids[i : i + BATCH_SIZE]
            batch_image_paths = image_paths[i : i + BATCH_SIZE]

            logger.info(f"Processing batch {i // BATCH_SIZE + 1}: {len(batch_image_paths)} images")

            for item_id, image_path in zip(batch_item_ids, batch_image_paths, strict=False):
                try:
                    await _process_single_item(
                        item_id=item_id,
                        image_path=image_path,
                        user_id=user_id,
                        db=db,
                    )
                    logger.info(f"Successfully processed item {item_id}")
                    processed_count += 1
                except Exception as e:
                    logger.error(f"Failed to process item {item_id}: {str(e)}")
                    await wardrobe_crud.update(
                        db=db, item_id=item_id, update_data={"processing_status": "failed"}
                    )

        logger.info(
            f"Completed batch processing: {processed_count}/{len(image_paths)} images processed"
        )


async def _process_single_item(
    item_id: UUID,
    image_path: str,
    user_id: UUID,
    db: AsyncSession,
) -> None:
    """Process a single wardrobe item through the full AI pipeline.

    Args:
        item_id: Wardrobe item ID
        image_path: Path to the original image
        user_id: User ID who owns the item
        db: Database session
    """
    try:
        # Background removal
        processed_image_path = image_path
        processed_image_url = file_storage.get_file_url(image_path)
        try:
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
            processed_image_url = file_storage.get_file_url(processed_image_path)
            logger.info(f"Background removal completed for item {item_id}")
        except Exception as e:
            logger.warning(f"Background removal failed for item {item_id}: {str(e)}")
            processed_image_path = image_path

        # Thumbnail generation
        thumbnail_url = None
        try:
            _, thumbnail_url = await asyncio.to_thread(
                file_storage.generate_thumbnail,
                processed_image_path,
                str(user_id),
                300,
            )
            logger.info(f"Thumbnail generation completed for item {item_id}")
        except Exception as e:
            logger.warning(f"Thumbnail generation failed for item {item_id}: {str(e)}")

        # Classify via Groq (or fallback)
        classification_result: dict[str, Any] = {
            "category": None,
            "color_primary": None,
            "color_secondary": None,
            "pattern": None,
            "season": [],
            "occasion": [],
            "detection_confidence": 0.0,
            "classification_source": "fallback",
            "processing_status": "failed",
        }
        try:
            classification_result = await clothing_detection_service.detect_clothing(
                processed_image_path
            )
        except Exception as e:
            logger.error(f"Clothing detection failed for item {item_id}: {str(e)}")

        # Weaviate indexing
        try:
            if weaviate_service.is_connected():
                weaviate_service.init_schema()
                weaviate_service.add_item(
                    item_id=item_id,
                    user_id=user_id,
                    category=classification_result.get("category"),
                    color_primary=classification_result.get("color_primary"),
                    color_secondary=classification_result.get("color_secondary"),
                    pattern=classification_result.get("pattern"),
                    season=classification_result.get("season", []),
                    occasion=classification_result.get("occasion", []),
                )
        except Exception as e:
            logger.warning(f"Weaviate indexing failed for item {item_id}: {str(e)}")

        await wardrobe_crud.update(
            db=db,
            item_id=item_id,
            update_data={
                "processed_image_url": processed_image_url,
                "thumbnail_url": thumbnail_url,
                "category": classification_result.get("category"),
                "color_primary": classification_result.get("color_primary"),
                "color_secondary": classification_result.get("color_secondary"),
                "pattern": classification_result.get("pattern"),
                "season": classification_result.get("season", []),
                "occasion": classification_result.get("occasion", []),
                "detection_confidence": classification_result.get("detection_confidence", 0.0),
                "classification_source": classification_result.get("classification_source"),
                "processing_status": "completed",
            },
        )
        logger.info(f"Item {item_id} processing completed successfully")

    except Exception as e:
        logger.error(f"Failed to process item {item_id}: {str(e)}")
        await wardrobe_crud.update(
            db=db, item_id=item_id, update_data={"processing_status": "failed"}
        )
        raise
