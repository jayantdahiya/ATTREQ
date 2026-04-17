"""Image processing worker for wardrobe items."""

import logging
from pathlib import Path
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from attreq_api.crud.wardrobe import wardrobe_crud
from attreq_api.services.ai.background_removal import background_removal_service
from attreq_api.services.ai.clothing_detection import clothing_detection_service
from attreq_api.services.ai.embeddings import weaviate_service
from attreq_api.services.storage.file_handler import file_storage

logger = logging.getLogger(__name__)


async def process_wardrobe_image(
    item_id: UUID, user_id: UUID, original_image_path: str, db: AsyncSession
) -> None:
    """Process a wardrobe image through the AI pipeline.

    This function orchestrates the complete AI processing pipeline:
    1. Update status to "processing"
    2. Remove background from image
    3. Generate thumbnail
    4. Detect clothing attributes with Gemini API
    5. Add to Weaviate for vector search
    6. Update database with results
    7. Set status to "completed" or "failed"

    Args:
        item_id: UUID of the wardrobe item
        user_id: UUID of the user
        original_image_path: Path to the original uploaded image
        db: Database session
    """
    logger.info(f"Starting image processing for item {item_id}")

    processed_image_path = None
    thumbnail_path = None

    try:
        # Step 1: Update status to "processing"
        await wardrobe_crud.update_processing_status(db, item_id, "processing")
        logger.info(f"Item {item_id} status updated to processing")

        # Step 2: Remove background
        try:
            # Determine processed image path
            original_path = Path(original_image_path)
            processed_filename = original_path.name.replace(
                original_path.suffix, f"_processed{original_path.suffix}"
            )
            processed_image_path = str(file_storage.processed_dir / processed_filename)

            # Remove background
            background_removal_service.remove_background(original_image_path, processed_image_path)
            logger.info(f"Background removed for item {item_id}")

            # Get URL for processed image
            processed_image_url = file_storage.get_file_url(processed_image_path)

        except Exception as e:
            logger.warning(f"Background removal failed for item {item_id}: {str(e)}")
            # Continue with original image if background removal fails
            processed_image_path = original_image_path
            processed_image_url = file_storage.get_file_url(original_image_path)

        # Step 3: Generate thumbnail
        try:
            thumbnail_path, thumbnail_url = file_storage.generate_thumbnail(
                processed_image_path,
                str(user_id),  # Convert UUID to string
                size=300,
            )
            logger.info(f"Thumbnail generated for item {item_id}")
        except Exception as e:
            logger.warning(f"Thumbnail generation failed for item {item_id}: {str(e)}")
            thumbnail_url = None

        # Step 4: Detect clothing attributes
        try:
            detection_result = await clothing_detection_service.detect_clothing(
                processed_image_path
            )
            logger.info(f"Clothing detection completed for item {item_id}: {detection_result}")
        except Exception as e:
            logger.error(f"Clothing detection failed for item {item_id}: {str(e)}")
            # Use empty detection result
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

        # Step 5: Add to Weaviate
        try:
            if weaviate_service.is_connected():
                # Ensure schema exists
                weaviate_service.init_schema()

                # Add item to Weaviate
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

        # Step 6: Update database with results
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
            "processing_status": "completed",
        }

        await wardrobe_crud.update(db, item_id, update_data)
        logger.info(f"Item {item_id} processing completed successfully")

    except Exception as e:
        logger.error(f"Image processing failed for item {item_id}: {str(e)}")

        # Update status to failed
        try:
            await wardrobe_crud.update_processing_status(db, item_id, "failed")
        except Exception as update_error:
            logger.error(
                f"Failed to update status to 'failed' for item {item_id}: {str(update_error)}"
            )
