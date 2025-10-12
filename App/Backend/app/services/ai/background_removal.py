"""Background removal service using rembg library."""

import logging
from pathlib import Path

from rembg import remove

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

