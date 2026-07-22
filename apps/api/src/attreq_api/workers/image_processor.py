"""Image processing worker for wardrobe items."""

import asyncio
import logging
import tempfile
from pathlib import Path
from uuid import UUID

from attreq_api.config.database import AsyncSessionLocal
from attreq_api.crud.wardrobe import wardrobe_crud
from attreq_api.services.ai.background_removal import background_removal_service
from attreq_api.services.ai.clothing_detection import clothing_detection_service
from attreq_api.services.ai.embeddings import weaviate_service
from attreq_api.services.storage import get_storage
from attreq_api.services.storage.base import get_file_extension

logger = logging.getLogger(__name__)


async def process_wardrobe_image(
    item_id: UUID, user_id: UUID, original_image_ref: str, original_image_url: str
) -> None:
    """Process a wardrobe image through the AI pipeline.

    This function orchestrates the complete AI processing pipeline:
    1. Update status to "processing"
    2. Fetch original image bytes from storage into a temp workspace
    3. Remove background from image
    4. Generate thumbnail
    5. Detect clothing attributes with the configured LLM classifier
    6. Add to Weaviate for vector search
    7. Update database with results
    8. Set status to "completed" or "failed"

    Args:
        item_id: UUID of the wardrobe item
        user_id: UUID of the user
        original_image_ref: Storage reference of the original upload
            (local path or S3 object key)
        original_image_url: Stored URL/key of the original upload, used as
            the processed-image fallback when background removal fails
    """
    logger.info(f"Starting image processing for item {item_id}")

    storage = get_storage()

    async with AsyncSessionLocal() as db:
        try:
            # Step 1: Update status to "processing"
            await wardrobe_crud.update_processing_status(db, item_id, "processing")
            logger.info(f"Item {item_id} status updated to processing")

            # Step 2: Fetch original bytes into a temp workspace
            # (rembg and the classifier are path-based)
            original_bytes = await storage.get_file_bytes(original_image_ref)
            extension = get_file_extension(original_image_ref)

            with tempfile.TemporaryDirectory() as tmpdir:
                original_tmp = str(Path(tmpdir) / f"original.{extension}")
                await asyncio.to_thread(Path(original_tmp).write_bytes, original_bytes)

                # Step 3: Remove background (rembg outputs PNG with alpha)
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
                    logger.info(f"Background removed for item {item_id}")
                    classification_path = processed_tmp
                    thumbnail_source, thumbnail_ext = processed_bytes, "png"

                except Exception as e:
                    logger.warning(f"Background removal failed for item {item_id}: {str(e)}")
                    processed_image_url = original_image_url
                    classification_path = original_tmp
                    thumbnail_source, thumbnail_ext = original_bytes, extension

                # Step 4: Generate thumbnail
                try:
                    _, thumbnail_url = await storage.generate_thumbnail(
                        thumbnail_source, user_id, 300, thumbnail_ext
                    )
                    logger.info(f"Thumbnail generated for item {item_id}")
                except Exception as e:
                    logger.warning(f"Thumbnail generation failed for item {item_id}: {str(e)}")
                    thumbnail_url = None

                # Step 5: Detect clothing attributes
                try:
                    detection_result = await clothing_detection_service.detect_clothing(
                        classification_path
                    )
                    logger.info(
                        f"Clothing detection completed for item {item_id}: {detection_result}"
                    )
                except Exception as e:
                    logger.error(f"Clothing detection failed for item {item_id}: {str(e)}")
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

            # Step 6: Add to Weaviate
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

            update_data = {
                "processed_image_url": processed_image_url,
                "thumbnail_url": thumbnail_url,
                "category": detection_result.get("category"),
                "color_primary": detection_result.get("color_primary"),
                "color_secondary": detection_result.get("color_secondary"),
                "pattern": detection_result.get("pattern"),
                "season": detection_result.get("season", []),
                "occasion": detection_result.get("occasion", []),
                "detection_confidence": detection_result.get("detection_confidence", 0.0),
                "classification_source": detection_result.get("classification_source"),
                "processing_status": "completed",
            }

            await wardrobe_crud.update(db, item_id, update_data)
            logger.info(f"Item {item_id} processing completed successfully")

        except Exception as e:
            logger.error(f"Image processing failed for item {item_id}: {str(e)}")
            try:
                await wardrobe_crud.update_processing_status(db, item_id, "failed")
            except Exception as update_error:
                logger.error(
                    f"Failed to update status to 'failed' for item {item_id}: {str(update_error)}"
                )
