"""Clothing detection service using Roboflow API."""

import logging
from pathlib import Path
from typing import Any

import aiofiles
import httpx
import numpy as np
from PIL import Image
from sklearn.cluster import KMeans

from app.core.config import settings

logger = logging.getLogger(__name__)


class ClothingDetectionService:
    """Service for detecting clothing attributes using Roboflow API."""

    # Color name mapping for RGB values
    COLOR_NAMES = {
        "red": (255, 0, 0),
        "green": (0, 255, 0),
        "blue": (0, 0, 255),
        "yellow": (255, 255, 0),
        "orange": (255, 165, 0),
        "purple": (128, 0, 128),
        "pink": (255, 192, 203),
        "brown": (165, 42, 42),
        "black": (0, 0, 0),
        "white": (255, 255, 255),
        "gray": (128, 128, 128),
        "beige": (245, 245, 220),
        "navy": (0, 0, 128),
        "maroon": (128, 0, 0),
        "teal": (0, 128, 128),
    }

    async def detect_clothing(self, image_path: str) -> dict[str, Any]:
        """Detect clothing attributes from an image using Roboflow API.

        Args:
            image_path: Path to the image file

        Returns:
            Dictionary containing detected attributes:
                - category: Clothing category (shirt, jeans, dress, etc.)
                - color_primary: Primary color detected
                - color_secondary: Secondary color (optional)
                - pattern: Pattern type (solid, striped, etc.)
                - confidence: Detection confidence score (0-100)

        Raises:
            FileNotFoundError: If image doesn't exist
            Exception: If detection fails
        """
        # Validate input file exists
        if not Path(image_path).exists():
            raise FileNotFoundError(f"Image not found: {image_path}")

        # Check if Roboflow API key is configured
        if not settings.roboflow_api_key:
            logger.warning("Roboflow API key not configured. Using fallback color detection only.")
            return await self._fallback_detection(image_path)

        try:
            # Call Roboflow API
            url = f"https://detect.roboflow.com/{settings.roboflow_project}/{settings.roboflow_model_id}"

            async with aiofiles.open(image_path, "rb") as image_file:
                image_data = await image_file.read()
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.post(
                        url,
                        params={"api_key": settings.roboflow_api_key},
                        files={"file": ("image.jpg", image_data, "image/jpeg")}
                    )

            if response.status_code == 200:
                data = response.json()

                # Parse Roboflow response
                if data.get("predictions") and len(data["predictions"]) > 0:
                    prediction = data["predictions"][0]

                    # Extract category from prediction
                    category = prediction.get("class", "unknown").lower()
                    confidence = prediction.get("confidence", 0) * 100

                    # Extract colors from image
                    color_primary, color_secondary = self._extract_dominant_colors(image_path)

                    # Detect pattern (basic heuristic)
                    pattern = self._detect_pattern(image_path)

                    return {
                        "category": category,
                        "color_primary": color_primary,
                        "color_secondary": color_secondary,
                        "pattern": pattern,
                        "confidence": confidence
                    }
                logger.warning("No predictions returned from Roboflow API")
                return await self._fallback_detection(image_path)
            logger.error(f"Roboflow API error: {response.status_code} - {response.text}")
            return await self._fallback_detection(image_path)

        except Exception as e:
            logger.error(f"Clothing detection failed: {str(e)}")
            # Fall back to basic color detection
            return await self._fallback_detection(image_path)

    async def _fallback_detection(self, image_path: str) -> dict[str, Any]:
        """Fallback detection using only color extraction.

        Args:
            image_path: Path to the image file

        Returns:
            Dictionary with basic detection results
        """
        try:
            color_primary, color_secondary = self._extract_dominant_colors(image_path)
            pattern = self._detect_pattern(image_path)

            return {
                "category": None,  # Cannot detect without Roboflow
                "color_primary": color_primary,
                "color_secondary": color_secondary,
                "pattern": pattern,
                "confidence": 0.0
            }
        except Exception as e:
            logger.error(f"Fallback detection failed: {str(e)}")
            return {
                "category": None,
                "color_primary": None,
                "color_secondary": None,
                "pattern": None,
                "confidence": 0.0
            }

    def _extract_dominant_colors(self, image_path: str, n_colors: int = 2) -> tuple[str | None, str | None]:
        """Extract dominant colors from an image using K-means clustering.

        Args:
            image_path: Path to the image file
            n_colors: Number of dominant colors to extract

        Returns:
            Tuple of (primary_color_name, secondary_color_name)
        """
        try:
            # Load image
            img = Image.open(image_path).convert("RGB")

            # Resize for faster processing
            img = img.resize((150, 150))

            # Convert to numpy array and reshape
            pixels = np.array(img).reshape(-1, 3)

            # Remove black and white pixels (likely background)
            # Keep pixels that are not too dark or too bright
            mask = (
                (pixels.sum(axis=1) > 30) &  # Not too dark
                (pixels.sum(axis=1) < 720)   # Not too bright
            )
            filtered_pixels = pixels[mask]

            if len(filtered_pixels) == 0:
                return None, None

            # Use K-means to find dominant colors
            kmeans = KMeans(n_clusters=min(n_colors, len(filtered_pixels)), random_state=42, n_init=10)
            kmeans.fit(filtered_pixels)

            # Get cluster centers (dominant colors)
            dominant_colors = kmeans.cluster_centers_.astype(int)

            # Map to color names
            color_names = [self._rgb_to_color_name(tuple(color)) for color in dominant_colors]

            # Return primary and secondary colors
            primary = color_names[0] if len(color_names) > 0 else None
            secondary = color_names[1] if len(color_names) > 1 else None

            return primary, secondary

        except Exception as e:
            logger.error(f"Color extraction failed: {str(e)}")
            return None, None

    def _rgb_to_color_name(self, rgb: tuple[int, int, int]) -> str:
        """Map RGB values to the closest color name.

        Args:
            rgb: Tuple of (r, g, b) values

        Returns:
            Color name
        """
        min_distance = float("inf")
        closest_color = "unknown"

        for color_name, color_rgb in self.COLOR_NAMES.items():
            # Calculate Euclidean distance
            distance = sum((a - b) ** 2 for a, b in zip(rgb, color_rgb, strict=False)) ** 0.5

            if distance < min_distance:
                min_distance = distance
                closest_color = color_name

        return closest_color

    def _detect_pattern(self, image_path: str) -> str:
        """Detect basic patterns in an image (simple heuristic).

        Args:
            image_path: Path to the image file

        Returns:
            Pattern name (solid, striped, etc.)
        """
        try:
            # Load image in grayscale
            img = Image.open(image_path).convert("L")
            img = img.resize((100, 100))

            # Convert to numpy array
            pixels = np.array(img)

            # Calculate standard deviation of pixel values
            std = np.std(pixels)

            # Simple heuristic: low std = solid, high std = patterned
            if std < 30:
                return "solid"
            if std > 60:
                return "patterned"
            return "textured"

        except Exception as e:
            logger.error(f"Pattern detection failed: {str(e)}")
            return "solid"


# Global instance
clothing_detection_service = ClothingDetectionService()

