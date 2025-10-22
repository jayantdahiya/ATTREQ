"""Clothing detection service using Google Gemini API."""

import logging
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image
from sklearn.cluster import KMeans

from app.core.config import settings
from app.services.ai.gemini_classifier import gemini_classifier_service

logger = logging.getLogger(__name__)


class ClothingDetectionService:
    """Service for detecting clothing attributes using Google Gemini API."""

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
        """Detect clothing attributes from an image using Gemini API.

        Args:
            image_path: Path to the image file

        Returns:
            Dictionary containing detected attributes:
                - category: Clothing category (shirt, jeans, dress, etc.)
                - color_primary: Primary color detected
                - color_secondary: Secondary color (optional)
                - pattern: Pattern type (solid, striped, etc.)
                - season: List of seasons (summer, winter, fall, spring, all)
                - occasion: List of occasions (casual, formal, party, business, etc.)
                - detection_confidence: Detection confidence score (0-1)
                - processing_status: Status of processing

        Raises:
            FileNotFoundError: If image doesn't exist
            Exception: If detection fails
        """
        # Validate input file exists
        if not Path(image_path).exists():
            raise FileNotFoundError(f"Image not found: {image_path}")

        # Check if Gemini API key is configured
        if not settings.gemini_api_key:
            logger.warning("Gemini API key not configured. Using fallback color detection only.")
            return await self._fallback_detection(image_path)

        try:
            logger.info("Using Gemini API for clothing detection")
            return await gemini_classifier_service.classify_single_image(image_path)
        except Exception as e:
            logger.error(f"Gemini API failed: {str(e)}")
            # Fall back to color-only detection
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
                "category": None,  # Cannot detect without Gemini API
                "color_primary": color_primary,
                "color_secondary": color_secondary,
                "pattern": pattern,
                "season": [],
                "occasion": [],
                "detection_confidence": 0.0,
                "processing_status": "completed"
            }
        except Exception as e:
            logger.error(f"Fallback detection failed: {str(e)}")
            return {
                "category": None,
                "color_primary": None,
                "color_secondary": None,
                "pattern": None,
                "season": [],
                "occasion": [],
                "detection_confidence": 0.0,
                "processing_status": "failed"
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

