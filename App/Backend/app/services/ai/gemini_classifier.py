"""Gemini API service for wardrobe classification with batch processing support."""

import base64
import json
import logging
from pathlib import Path
from typing import Any

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


class GeminiClassifierService:
    """Service for classifying wardrobe items using Google Gemini API with batch processing."""

    def __init__(self):
        """Initialize the Gemini classifier service."""
        self.api_key = settings.gemini_api_key
        self.model_name = settings.gemini_model_name
        self.batch_size = settings.gemini_batch_size
        self.base_url = "https://generativelanguage.googleapis.com/v1beta/models"

    async def classify_single_image(self, image_path: str) -> dict[str, Any]:
        """Classify a single wardrobe image using Gemini API.

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
            Exception: If classification fails
        """
        # Validate input file exists
        if not Path(image_path).exists():
            raise FileNotFoundError(f"Image not found: {image_path}")

        if not self.api_key:
            raise ValueError("Gemini API key not configured")

        try:
            # Encode image to base64
            base64_data = self._encode_image_to_base64(image_path)
            mime_type = self._get_mime_type(image_path)

            # Build request payload
            payload = {
                "contents": [
                    {
                        "parts": [
                            {"text": self._build_classification_prompt()},
                            {
                                "inline_data": {
                                    "mime_type": mime_type,
                                    "data": base64_data
                                }
                            }
                        ]
                    }
                ]
            }

            # Make API request
            response = await self._make_api_request(payload)
            
            # Parse response
            result = self._parse_gemini_response(response)
            
            # Map to wardrobe schema
            return self._map_to_wardrobe_schema(result)

        except Exception as e:
            logger.error(f"Gemini single image classification failed: {str(e)}")
            raise

    async def classify_batch_images(self, image_paths: list[str]) -> list[dict[str, Any]]:
        """Classify multiple wardrobe images in a single batch request.

        Args:
            image_paths: List of image file paths (max 5 recommended)

        Returns:
            List of dictionaries containing detected attributes for each image

        Raises:
            ValueError: If no API key configured or too many images
            Exception: If batch classification fails
        """
        if not self.api_key:
            raise ValueError("Gemini API key not configured")

        if len(image_paths) > self.batch_size:
            raise ValueError(f"Too many images. Maximum batch size is {self.batch_size}")

        # Validate all files exist
        for path in image_paths:
            if not Path(path).exists():
                raise FileNotFoundError(f"Image not found: {path}")

        try:
            # Build request parts
            parts = [{"text": self._build_classification_prompt()}]

            # Add all images to request
            for image_path in image_paths:
                base64_data = self._encode_image_to_base64(image_path)
                mime_type = self._get_mime_type(image_path)

                parts.append({
                    "inline_data": {
                        "mime_type": mime_type,
                        "data": base64_data
                    }
                })

            # Build request payload
            payload = {"contents": [{"parts": parts}]}

            # Make API request
            response = await self._make_api_request(payload)
            
            # Parse response (should be array of results)
            results = self._parse_gemini_response(response)
            
            # Ensure we have a list of results
            if not isinstance(results, list):
                results = [results]

            # Map each result to wardrobe schema
            mapped_results = []
            for result in results:
                mapped_result = self._map_to_wardrobe_schema(result)
                mapped_results.append(mapped_result)

            return mapped_results

        except Exception as e:
            logger.error(f"Gemini batch classification failed: {str(e)}")
            raise

    def _encode_image_to_base64(self, image_path: str) -> str:
        """Convert image file to base64 string.

        Args:
            image_path: Path to the image file

        Returns:
            Base64 encoded string
        """
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")

    def _get_mime_type(self, image_path: str) -> str:
        """Get MIME type for image file.

        Args:
            image_path: Path to the image file

        Returns:
            MIME type string
        """
        extension = Path(image_path).suffix.lower()
        mime_types = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".gif": "image/gif",
            ".webp": "image/webp"
        }
        return mime_types.get(extension, "image/jpeg")

    def _build_classification_prompt(self) -> str:
        """Build the classification prompt for Gemini API.

        Returns:
            Formatted prompt string
        """
        return """You are an AI wardrobe classification expert. Analyze the clothing items in the images and provide detailed classifications in JSON format for EACH item.

For each clothing item detected, provide:
- category: Specific clothing type (e.g., "shirt", "jeans", "dress", "jacket", "sweater", "pants", "coat", "blouse", "skirt", "shorts", "t-shirt", "hoodie", "blazer", "cardigan", "tank-top", "polo", "chinos", "leggings", "jumpsuit", "romper")
- color_primary: Primary color (e.g., "black", "white", "blue", "red", "green", "brown", "beige", "gray", "navy", "maroon", "pink", "purple", "yellow", "orange", "tan", "cream")
- color_secondary: Secondary color if present, null if not
- pattern: Pattern type (e.g., "solid", "striped", "polka-dot", "floral", "plaid", "checkered", "paisley", "geometric", "abstract", "printed", "embroidered", "textured")
- season: Array of applicable seasons (e.g., ["summer"], ["winter"], ["fall", "winter"], ["spring", "fall"], ["all"])
- occasion: Array of suitable occasions (e.g., ["casual"], ["formal"], ["business"], ["party"], ["casual", "business"], ["formal", "party"])
- detection_confidence: Confidence score between 0.0 and 1.0
- processing_status: Always "completed"

Return ONLY valid JSON array format. Example:
[
  {
    "category": "coat",
    "color_primary": "beige",
    "color_secondary": null,
    "pattern": "solid",
    "season": ["fall", "winter"],
    "occasion": ["casual", "business"],
    "detection_confidence": 0.95,
    "processing_status": "completed"
  }
]

If multiple items are in one image, return separate objects for each item."""

    async def _make_api_request(self, payload: dict) -> dict:
        """Make API request to Gemini.

        Args:
            payload: Request payload

        Returns:
            API response data

        Raises:
            httpx.HTTPError: If API request fails
        """
        url = f"{self.base_url}/{self.model_name}:generateContent"
        headers = {
            "Content-Type": "application/json",
            "X-goog-api-key": self.api_key
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            return response.json()

    def _parse_gemini_response(self, response: dict) -> list[dict[str, Any]]:
        """Parse Gemini API response and extract classification results.

        Args:
            response: Raw API response

        Returns:
            List of classification results

        Raises:
            ValueError: If response format is invalid
        """
        try:
            # Extract text content from response
            candidates = response.get("candidates", [])
            if not candidates:
                raise ValueError("No candidates in response")

            content = candidates[0].get("content", {})
            parts = content.get("parts", [])
            if not parts:
                raise ValueError("No parts in response content")

            text_content = parts[0].get("text", "")
            if not text_content:
                raise ValueError("No text content in response")

            # Parse JSON from text content
            # Clean up any markdown formatting
            text_content = text_content.strip()
            if text_content.startswith("```json"):
                text_content = text_content[7:]
            if text_content.endswith("```"):
                text_content = text_content[:-3]
            text_content = text_content.strip()

            # Parse JSON
            try:
                results = json.loads(text_content)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON from Gemini response: {e}")
                logger.error(f"Response text: {text_content}")
                raise ValueError(f"Invalid JSON in response: {e}")

            # Ensure we have a list
            if not isinstance(results, list):
                results = [results]

            return results

        except Exception as e:
            logger.error(f"Failed to parse Gemini response: {e}")
            logger.error(f"Raw response: {response}")
            raise ValueError(f"Failed to parse response: {e}")

    def _map_to_wardrobe_schema(self, gemini_result: dict[str, Any]) -> dict[str, Any]:
        """Map Gemini API response to WardrobeItem schema format.

        Args:
            gemini_result: Single result from Gemini API

        Returns:
            Dictionary ready for WardrobeItem model
        """
        return {
            "category": gemini_result.get("category"),
            "color_primary": gemini_result.get("color_primary"),
            "color_secondary": gemini_result.get("color_secondary"),
            "pattern": gemini_result.get("pattern"),
            "season": gemini_result.get("season", []),
            "occasion": gemini_result.get("occasion", []),
            "detection_confidence": gemini_result.get("detection_confidence", 0.0),
            "processing_status": gemini_result.get("processing_status", "completed")
        }


# Global instance
gemini_classifier_service = GeminiClassifierService()
