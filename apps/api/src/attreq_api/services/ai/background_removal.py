"""Background removal service using rembg library."""

import asyncio
import logging
from pathlib import Path
from typing import Any
from uuid import UUID

from rembg import remove

from attreq_api.services.storage.file_handler import file_storage

logger = logging.getLogger(__name__)


class BackgroundRemovalService:
    """Service for removing backgrounds from clothing images."""

    def remove_background(self, input_path: str, output_path: str) -> str:
        """Remove background from an image.

        Args:
            input_path: Path to the input image
            output_path: Path where processed image will be saved

        Returns:
            Path to the processed image

        Raises:
            FileNotFoundError: If input image doesn't exist
            Exception: If background removal fails
        """
        try:
            # Validate input file exists
            if not Path(input_path).exists():
                raise FileNotFoundError(f"Input image not found: {input_path}")

            # Read input image
            with open(input_path, "rb") as input_file:
                input_data = input_file.read()

            # Remove background
            logger.info(f"Removing background from {input_path}")
            output_data = remove(input_data)

            # Save output image
            with open(output_path, "wb") as output_file:
                output_file.write(output_data)

            logger.info(f"Background removed successfully. Saved to {output_path}")
            return output_path

        except FileNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Failed to remove background: {str(e)}")
            raise Exception(f"Background removal failed: {str(e)}") from e


# Global instance
background_removal_service = BackgroundRemovalService()


async def generate_processed_and_thumbnail(
    original_image_path: str, user_id: UUID, log_ref: Any = None
) -> tuple[str, str | None, str | None]:
    """Run background removal + thumbnail generation with per-step fallback.

    Shared by the single-upload, batch-upload, and additional-photo pipelines
    (previously inlined separately in each — RI-7 refactor). On background
    removal failure, falls back to the original image path/URL. On thumbnail
    generation failure, thumbnail_url is None. Neither failure raises.

    Args:
        original_image_path: Path to the original uploaded image
        user_id: UUID of the user (used for thumbnail filename generation)
        log_ref: Optional identifier (item/photo id) used only in log messages

    Returns:
        Tuple of (processed_image_path, processed_image_url, thumbnail_url)
    """
    processed_image_path = original_image_path
    processed_image_url = file_storage.get_file_url(original_image_path)

    try:
        original_path = Path(original_image_path)
        processed_filename = original_path.name.replace(
            original_path.suffix, f"_processed{original_path.suffix}"
        )
        candidate_path = str(file_storage.processed_dir / processed_filename)

        await asyncio.to_thread(
            background_removal_service.remove_background,
            original_image_path,
            candidate_path,
        )
        processed_image_path = candidate_path
        processed_image_url = file_storage.get_file_url(candidate_path)
        logger.info(f"Background removal completed for {log_ref or original_image_path}")
    except Exception as e:
        logger.warning(f"Background removal failed for {log_ref or original_image_path}: {str(e)}")
        processed_image_path = original_image_path
        processed_image_url = file_storage.get_file_url(original_image_path)

    thumbnail_url = None
    try:
        _, thumbnail_url = await asyncio.to_thread(
            file_storage.generate_thumbnail,
            processed_image_path,
            str(user_id),
            300,
        )
        logger.info(f"Thumbnail generation completed for {log_ref or original_image_path}")
    except Exception as e:
        logger.warning(f"Thumbnail generation failed for {log_ref or original_image_path}: {str(e)}")

    return processed_image_path, processed_image_url, thumbnail_url
