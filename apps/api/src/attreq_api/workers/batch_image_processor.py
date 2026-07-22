"""Batch image processing worker for wardrobe items using Groq API."""

import asyncio
import logging
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from attreq_api.config.database import AsyncSessionLocal
from attreq_api.config.settings import settings
from attreq_api.crud.wardrobe import wardrobe_crud
from attreq_api.services.ai.background_removal import generate_processed_and_thumbnail
from attreq_api.services.ai.clothing_detection import clothing_detection_service
from attreq_api.services.ai.embeddings import weaviate_service
from attreq_api.services.stats.wardrobe_stats import invalidate_wardrobe_stats_cache

logger = logging.getLogger(__name__)


async def process_batch_wardrobe_images(
    item_ids: list[UUID], user_id: UUID, image_paths: list[str]
) -> None:
    """Process multiple wardrobe images concurrently (bounded) using Groq API.

    Each item gets its OWN `AsyncSession` opened inside the bounded task —
    SQLAlchemy async sessions forbid concurrent interleaved awaits on a single
    shared session, so a session shared across `asyncio.gather` tasks would
    corrupt state. This was the real bug in the previous sequential-with-one-
    shared-session implementation (see RI-7 plan, "Shared-AsyncSession
    concurrency bug").

    One bad image never fails the whole batch — failures are caught per-item
    and the item is marked "failed" independently.

    Args:
        item_ids: List of wardrobe item IDs to process
        user_id: User ID who owns the items
        image_paths: List of image file paths
    """
    if len(item_ids) != len(image_paths):
        raise ValueError("Item IDs and image paths must have the same length")

    logger.info(f"Processing batch of {len(image_paths)} wardrobe images for user {user_id}")

    semaphore = asyncio.Semaphore(settings.wardrobe_batch_processing_concurrency)

    async def _bounded(item_id: UUID, image_path: str) -> None:
        async with semaphore, AsyncSessionLocal() as db:  # one session per item — REQUIRED
            try:
                await _process_single_item(
                    item_id=item_id,
                    image_path=image_path,
                    user_id=user_id,
                    db=db,
                )
                logger.info(f"Successfully processed item {item_id}")
            except Exception as e:
                logger.error(f"Failed to process item {item_id}: {str(e)}")
                try:
                    await wardrobe_crud.update(
                        db=db, item_id=item_id, update_data={"processing_status": "failed"}
                    )
                except Exception as update_error:
                    logger.error(
                        f"Failed to mark item {item_id} as failed: {str(update_error)}"
                    )

    await asyncio.gather(
        *(
            _bounded(item_id, image_path)
            for item_id, image_path in zip(item_ids, image_paths, strict=True)
        )
    )

    try:
        await invalidate_wardrobe_stats_cache(user_id)
    except Exception as e:
        logger.warning(f"Failed to invalidate stats cache for user {user_id}: {str(e)}")

    logger.info(f"Completed batch processing of {len(image_paths)} images for user {user_id}")


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
        db: Database session (must be exclusive to this task — see caller)
    """
    try:
        # Background removal + thumbnail generation (shared helper). Falls
        # back to the original path/URL internally if bg removal fails, so
        # `processed_image_path` is always a valid file to classify against.
        processed_image_path, processed_image_url, thumbnail_url = (
            await generate_processed_and_thumbnail(
                image_path, user_id, log_ref=f"item {item_id}"
            )
        )

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
