"""Groq API service for wardrobe classification using Llama 4 Scout vision model."""

import base64
import json
import logging
from pathlib import Path
from typing import Any

import httpx

from attreq_api.config.settings import settings

logger = logging.getLogger(__name__)

CLASSIFICATION_PROMPT = """You are a wardrobe classification expert. Analyze the clothing item in the image and return ONLY a JSON object with these exact fields:

{
  "category": "<specific type: shirt, jeans, dress, jacket, sweater, pants, coat, blouse, skirt, shorts, t-shirt, hoodie, blazer, cardigan, tank-top, polo, chinos, leggings, jumpsuit, romper>",
  "color_primary": "<main color: black, white, blue, red, green, brown, beige, gray, navy, maroon, pink, purple, yellow, orange, tan, cream>",
  "color_secondary": "<second color or null>",
  "pattern": "<solid, striped, polka-dot, floral, plaid, checkered, paisley, geometric, abstract, printed, embroidered, textured>",
  "season": ["<summer|winter|fall|spring|all>"],
  "occasion": ["<casual|formal|business|party>"],
  "detection_confidence": <0.0 to 1.0>,
  "processing_status": "completed"
}

Return ONLY the JSON object, no markdown, no explanation."""


class GroqClassifierService:
    """Service for classifying wardrobe items using Groq's Llama 4 Scout vision model."""

    BASE_URL = "https://api.groq.com/openai/v1/chat/completions"

    def __init__(self):
        self.api_key = settings.groq_api_key
        self.model_name = settings.groq_model_name

    async def classify_single_image(self, image_path: str) -> dict[str, Any]:
        """Classify a wardrobe image using Groq Llama 4 Scout.

        Raises:
            FileNotFoundError: If image doesn't exist
            ValueError: If API key not configured or response invalid
            httpx.HTTPError: If API request fails
        """
        if not Path(image_path).exists():
            raise FileNotFoundError(f"Image not found: {image_path}")
        if not self.api_key:
            raise ValueError("Groq API key not configured")

        base64_data = self._encode_image_to_base64(image_path)
        mime_type = self._get_mime_type(image_path)

        payload = {
            "model": self.model_name,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:{mime_type};base64,{base64_data}"},
                        },
                        {"type": "text", "text": CLASSIFICATION_PROMPT},
                    ],
                }
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.1,
        }

        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(self.BASE_URL, headers=headers, json=payload)
                response.raise_for_status()
                data = response.json()

            text = data["choices"][0]["message"]["content"]
            result = json.loads(text)
            return self._map_to_wardrobe_schema(result)

        except Exception as e:
            logger.error(f"Groq single image classification failed: {str(e)}")
            raise

    def _encode_image_to_base64(self, image_path: str) -> str:
        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")

    def _get_mime_type(self, image_path: str) -> str:
        mime_types = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".gif": "image/gif",
            ".webp": "image/webp",
        }
        return mime_types.get(Path(image_path).suffix.lower(), "image/jpeg")

    def _map_to_wardrobe_schema(self, result: dict[str, Any]) -> dict[str, Any]:
        return {
            "category": result.get("category"),
            "color_primary": result.get("color_primary"),
            "color_secondary": result.get("color_secondary"),
            "pattern": result.get("pattern"),
            "season": result.get("season", []),
            "occasion": result.get("occasion", []),
            "detection_confidence": result.get("detection_confidence", 0.0),
            "processing_status": result.get("processing_status", "completed"),
        }


groq_classifier_service = GroqClassifierService()
