"""Batch image processing worker for wardrobe items using Groq API."""

import asyncio
import logging
import tempfile
from pathlib import Path
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from attreq_api.config.database import AsyncSessionLocal
from attreq_api.crud.wardrobe import wardrobe_crud
from attreq_api.services.ai.background_removal import background_removal_service
from attreq_api.services.ai.clothing_detection import clothing_detection_service
from attreq_api.services.ai.embeddings import weaviate_service
from attreq_api.services.storage import get_storage
from attreq_api.services.storage.base import get_file_extension

logger = logging.getLogger(__name__)

BATCH_SIZE = 5


async def process_batch_wardrobe_images(
    item_ids: list[UUID],
    user_id: UUID,
    image_refs: list[str],
    image_urls: list[str],
) -> None:
    """Process multiple wardrobe images sequentially using Groq API.

    Args:
        item_ids: List of wardrobe item IDs to process
        user_id: User ID who owns the items
        image_refs: Storage references of the original uploads
            (local paths or S3 object keys)
        image_urls: Stored URLs/keys of the original uploads, used as
            processed-image fallbacks when background removal fails
    """
    if not (len(item_ids) == len(image_refs) == len(image_urls)):
        raise ValueError("Item IDs, image refs, and image URLs must have the same length")

    logger.info(f"Processing batch of {len(image_refs)} wardrobe images for user {user_id}")

    async with AsyncSessionLocal() as db:
        processed_count = 0

        for i in range(0, len(image_refs), BATCH_SIZE):
            batch_item_ids = item_ids[i : i + BATCH_SIZE]
            batch_image_refs = image_refs[i : i + BATCH_SIZE]
            batch_image_urls = image_urls[i : i + BATCH_SIZE]

            logger.info(f"Processing batch {i // BATCH_SIZE + 1}: {len(batch_image_refs)} images")

            for item_id, image_ref, image_url in zip(
                batch_item_ids, batch_image_refs, batch_image_urls, strict=False
            ):
                try:
                    await _process_single_item(
                        item_id=item_id,
                        image_ref=image_ref,
                        image_url=image_url,
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
            f"Completed batch processing: {processed_count}/{len(image_refs)} images processed"
        )


async def _process_single_item(
    item_id: UUID,
    image_ref: str,
    image_url: str,
    user_id: UUID,
    db: AsyncSession,
) -> None:
    """Process a single wardrobe item through the full AI pipeline.

    Args:
        item_id: Wardrobe item ID
        image_ref: Storage reference of the original image
        image_url: Stored URL/key of the original image
        user_id: User ID who owns the item
        db: Database session
    """
    try:
        storage = get_storage()
        original_bytes = await storage.get_file_bytes(image_ref)
        extension = get_file_extension(image_ref)

        with tempfile.TemporaryDirectory() as tmpdir:
            original_tmp = str(Path(tmpdir) / f"original.{extension}")
            await asyncio.to_thread(Path(original_tmp).write_bytes, original_bytes)

            # Background removal (rembg outputs PNG with alpha)
            try:
                processed_tmp = str(Path(tmpdir) / "processed.png")
                await asyncio.to_thread(
                    background_removal_service.remove_background,
                    original_tmp,
                    processed_tmp,
                )
                processed_bytes = await asyncio.to_thread(Path(processed_tmp).read_bytes)
                _, processed_image_url = await storage.save_image_from_bytes(
                    processed_bytes, user_id, "processed", "png"
                )
                classification_path = processed_tmp
                thumbnail_source, thumbnail_ext = processed_bytes, "png"
                logger.info(f"Background removal completed for item {item_id}")
            except Exception as e:
                logger.warning(f"Background removal failed for item {item_id}: {str(e)}")
                processed_image_url = image_url
                classification_path = original_tmp
                thumbnail_source, thumbnail_ext = original_bytes, extension

            # Thumbnail generation
            thumbnail_url = None
            try:
                _, thumbnail_url = await storage.generate_thumbnail(
                    thumbnail_source, user_id, 300, thumbnail_ext
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
                    classification_path
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
