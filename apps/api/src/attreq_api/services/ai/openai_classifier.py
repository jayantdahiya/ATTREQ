"""OpenAI API service for wardrobe classification."""

import asyncio
import base64
import json
import logging
import os
from pathlib import Path
from typing import Any

import openai

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


class OpenAIClassifierService:
    """Service for classifying wardrobe items using OpenAI GPT-4o vision models."""

    def __init__(self):
        self.api_key = settings.openai_api_key
        self.model_name = settings.openai_model_name

    async def classify_single_image(self, image_path: str) -> dict[str, Any]:
        """Classify a wardrobe image using OpenAI GPT-4o.

        Raises:
            FileNotFoundError: If image doesn't exist
            ValueError: If API key not configured or response invalid
            openai.APIError: If API request fails
        """
        if not await asyncio.to_thread(os.path.exists, image_path):
            raise FileNotFoundError(f"Image not found: {image_path}")
        if not self.api_key:
            raise ValueError("OpenAI API key not configured")

        base64_data = self._encode_image_to_base64(image_path)
        mime_type = self._get_mime_type(image_path)

        try:
            client = openai.AsyncOpenAI(api_key=self.api_key)
            response = await client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:{mime_type};base64,{base64_data}"
                                },
                            },
                            {"type": "text", "text": CLASSIFICATION_PROMPT},
                        ],
                    }
                ],
                response_format={"type": "json_object"},
                temperature=0.1,
                max_tokens=512,
            )

            text = response.choices[0].message.content
            result = json.loads(text)
            return self._map_to_wardrobe_schema(result)

        except Exception as e:
            logger.error(f"OpenAI single image classification failed: {str(e)}")
            raise

    async def analyze_image(self, image_path: str, prompt: str) -> dict[str, Any]:
        """Call OpenAI vision with a custom prompt. Returns raw JSON dict."""
        if not await asyncio.to_thread(os.path.exists, image_path):
            raise FileNotFoundError(f"Image not found: {image_path}")
        if not self.api_key:
            raise ValueError("OpenAI API key not configured")

        base64_data = self._encode_image_to_base64(image_path)
        mime_type = self._get_mime_type(image_path)

        try:
            client = openai.AsyncOpenAI(api_key=self.api_key)
            response = await client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image_url",
                                "image_url": {"url": f"data:{mime_type};base64,{base64_data}"},
                            },
                            {"type": "text", "text": prompt},
                        ],
                    }
                ],
                response_format={"type": "json_object"},
                temperature=0.1,
                max_tokens=1024,
            )
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            logger.error(f"OpenAI analyze_image failed: {str(e)}")
            raise

    async def analyze_text(self, prompt: str) -> dict[str, Any]:
        """Call OpenAI text-only with a custom prompt. Returns raw JSON dict."""
        if not self.api_key:
            raise ValueError("OpenAI API key not configured")

        try:
            client = openai.AsyncOpenAI(api_key=self.api_key)
            response = await client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                temperature=0.1,
                max_tokens=2048,
            )
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            logger.error(f"OpenAI analyze_text failed: {str(e)}")
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


openai_classifier_service = OpenAIClassifierService()
