"""Background removal service using rembg library."""

import asyncio
import logging
import shutil
import tempfile
from pathlib import Path
from typing import Any
from uuid import UUID

from rembg import remove

from attreq_api.services.storage import get_storage
from attreq_api.services.storage.base import get_file_extension

logger = logging.getLogger(__name__)

# Prefix for temp dirs created by `generate_processed_and_thumbnail`, so
# `cleanup_classification_tempdir` only ever removes directories it created
# itself — never an arbitrary caller-supplied (or test-doubled) path's parent.
_TEMP_DIR_PREFIX = "attreq_img_"


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
    original_image_ref: str, user_id: UUID, log_ref: Any = None
) -> tuple[str, str | None, str | None]:
    """Fetch an original image from storage, remove its background, and
    generate a thumbnail — with per-step fallback.

    Shared by the single-upload, batch-upload, and additional-photo
    pipelines (RI-7 refactor; previously inlined separately in each).
    Storage-backend agnostic (local disk or S3-compatible) via
    `get_storage()` — this is the seam that keeps every caller working
    under either `STORAGE_BACKEND` setting.

    Args:
        original_image_ref: Storage reference of the original upload
            (local path or S3 object key — NOT necessarily a URL)
        user_id: UUID of the user (used for generated filenames)
        log_ref: Optional identifier (item/photo id) used only in log
            messages

    Returns:
        Tuple of ``(classification_path, processed_image_url, thumbnail_url)``.

        - ``classification_path`` is a local filesystem path suitable for
          the clothing classifier. It lives in a temp directory created by
          this call that is deliberately **not** cleaned up here — the
          caller must remove ``Path(classification_path).parent`` once it
          is done (classification happens after this returns).
        - ``processed_image_url`` is ``None`` if background removal failed.
          Callers must fall back to their own already-known original URL in
          that case rather than deriving one via ``storage.get_file_url``,
          which would mint (and, if persisted, permanently store) a
          presigned URL under the S3 backend.
        - ``thumbnail_url`` is ``None`` if thumbnail generation failed.

        Neither failure raises — both are logged and degrade gracefully.
    """
    storage = get_storage()
    original_bytes = await storage.get_file_bytes(original_image_ref)
    extension = get_file_extension(original_image_ref)

    tmpdir = tempfile.mkdtemp(prefix=_TEMP_DIR_PREFIX)
    original_tmp = str(Path(tmpdir) / f"original.{extension}")
    await asyncio.to_thread(Path(original_tmp).write_bytes, original_bytes)

    classification_path = original_tmp
    processed_image_url: str | None = None
    thumbnail_source, thumbnail_ext = original_bytes, extension

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
        logger.info(f"Background removal completed for {log_ref or original_image_ref}")
    except Exception as e:
        logger.warning(f"Background removal failed for {log_ref or original_image_ref}: {str(e)}")

    thumbnail_url = None
    try:
        _, thumbnail_url = await storage.generate_thumbnail(
            thumbnail_source, user_id, 300, thumbnail_ext
        )
        logger.info(f"Thumbnail generation completed for {log_ref or original_image_ref}")
    except Exception as e:
        logger.warning(f"Thumbnail generation failed for {log_ref or original_image_ref}: {str(e)}")

    return classification_path, processed_image_url, thumbnail_url


def cleanup_classification_tempdir(classification_path: str) -> None:
    """Remove the temp directory created by `generate_processed_and_thumbnail`.

    Callers invoke this once they're done with `classification_path` (e.g.
    after classification). Only removes directories bearing our own
    `_TEMP_DIR_PREFIX` — a no-op for any other path (including whatever a
    test double hands back), so it can never sweep up an unrelated
    directory such as the system `/tmp` root.
    """
    directory = Path(classification_path).parent
    if directory.name.startswith(_TEMP_DIR_PREFIX):
        shutil.rmtree(directory, ignore_errors=True)
