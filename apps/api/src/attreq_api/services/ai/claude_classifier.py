"""Anthropic Claude API service for wardrobe classification."""

import asyncio
import base64
import json
import logging
import os
from pathlib import Path
from typing import Any

import anthropic

from attreq_api.config.settings import settings
from attreq_api.services.ai.prompt_text import CLASSIFICATION_PROMPT
from attreq_api.services.ai.schema_mapper import map_classifier_result_to_wardrobe_schema

logger = logging.getLogger(__name__)


class ClaudeClassifierService:
    """Service for classifying wardrobe items using Anthropic Claude vision models."""

    def __init__(self):
        self.api_key = settings.claude_api_key
        self.model_name = settings.claude_model_name

    async def classify_single_image(self, image_path: str) -> dict[str, Any]:
        """Classify a wardrobe image using Claude.

        Raises:
            FileNotFoundError: If image doesn't exist
            ValueError: If API key not configured or response invalid
            anthropic.APIError: If API request fails
        """
        if not await asyncio.to_thread(os.path.exists, image_path):
            raise FileNotFoundError(f"Image not found: {image_path}")
        if not self.api_key:
            raise ValueError("Claude API key not configured")

        base64_data = self._encode_image_to_base64(image_path)
        media_type = self._get_media_type(image_path)

        try:
            client = anthropic.AsyncAnthropic(api_key=self.api_key)
            message = await client.messages.create(
                model=self.model_name,
                max_tokens=1024,
                temperature=0.1,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": CLASSIFICATION_PROMPT},
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": media_type,
                                    "data": base64_data,
                                },
                            },
                        ],
                    }
                ],
            )

            text = message.content[0].text
            result = self._parse_json(text)
            return map_classifier_result_to_wardrobe_schema(result)

        except Exception as e:
            logger.error(f"Claude single image classification failed: {str(e)}")
            raise

    async def analyze_image(self, image_path: str, prompt: str) -> dict[str, Any]:
        """Call Claude vision with a custom prompt. Returns raw JSON dict."""
        if not await asyncio.to_thread(os.path.exists, image_path):
            raise FileNotFoundError(f"Image not found: {image_path}")
        if not self.api_key:
            raise ValueError("Claude API key not configured")

        base64_data = self._encode_image_to_base64(image_path)
        media_type = self._get_media_type(image_path)

        try:
            client = anthropic.AsyncAnthropic(api_key=self.api_key)
            message = await client.messages.create(
                model=self.model_name,
                max_tokens=1024,
                temperature=0.1,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": media_type,
                                    "data": base64_data,
                                },
                            },
                        ],
                    }
                ],
            )
            return self._parse_json(message.content[0].text)
        except Exception as e:
            logger.error(f"Claude analyze_image failed: {str(e)}")
            raise

    async def analyze_text(self, prompt: str) -> dict[str, Any]:
        """Call Claude text-only with a custom prompt. Returns raw JSON dict."""
        if not self.api_key:
            raise ValueError("Claude API key not configured")

        try:
            client = anthropic.AsyncAnthropic(api_key=self.api_key)
            message = await client.messages.create(
                model=self.model_name,
                max_tokens=2048,
                temperature=0.1,
                messages=[{"role": "user", "content": prompt}],
            )
            return self._parse_json(message.content[0].text)
        except Exception as e:
            logger.error(f"Claude analyze_text failed: {str(e)}")
            raise

    def _encode_image_to_base64(self, image_path: str) -> str:
        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")

    def _get_media_type(self, image_path: str) -> str:
        media_types = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".gif": "image/gif",
            ".webp": "image/webp",
        }
        return media_types.get(Path(image_path).suffix.lower(), "image/jpeg")

    def _parse_json(self, text: str) -> dict[str, Any]:
        text = text.strip()
        if text.startswith("```json"):
            text = text[7:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()

        try:
            return json.loads(text)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in Claude response: {e}") from e


claude_classifier_service = ClaudeClassifierService()
