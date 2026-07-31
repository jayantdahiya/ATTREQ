"""Groq API service for wardrobe classification using Llama 4 Scout vision model."""

import asyncio
import base64
import json
import logging
import os
from pathlib import Path
from typing import Any

import httpx

from attreq_api.config.settings import settings
from attreq_api.services.ai.prompt_text import CLASSIFICATION_PROMPT
from attreq_api.services.ai.schema_mapper import map_classifier_result_to_wardrobe_schema

logger = logging.getLogger(__name__)


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
        if not await asyncio.to_thread(os.path.exists, image_path):
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
            return map_classifier_result_to_wardrobe_schema(result)

        except Exception as e:
            logger.error(f"Groq single image classification failed: {str(e)}")
            raise

    async def analyze_image(self, image_path: str, prompt: str) -> dict[str, Any]:
        """Call Groq vision with a custom prompt. Returns raw JSON dict."""
        if not await asyncio.to_thread(os.path.exists, image_path):
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
                        {"type": "text", "text": prompt},
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
            async with httpx.AsyncClient(timeout=90.0) as client:
                response = await client.post(self.BASE_URL, headers=headers, json=payload)
                response.raise_for_status()
                data = response.json()

            text = data["choices"][0]["message"]["content"]
            return json.loads(text)

        except Exception as e:
            logger.error(f"Groq analyze_image failed: {str(e)}")
            raise

    async def analyze_text(self, prompt: str) -> dict[str, Any]:
        """Call Groq text-only with a custom prompt. Returns raw JSON dict."""
        if not self.api_key:
            raise ValueError("Groq API key not configured")

        payload = {
            "model": self.model_name,
            "messages": [{"role": "user", "content": prompt}],
            "response_format": {"type": "json_object"},
            "temperature": 0.1,
        }

        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }
            async with httpx.AsyncClient(timeout=90.0) as client:
                response = await client.post(self.BASE_URL, headers=headers, json=payload)
                response.raise_for_status()
                data = response.json()

            text = data["choices"][0]["message"]["content"]
            return json.loads(text)

        except Exception as e:
            logger.error(f"Groq analyze_text failed: {str(e)}")
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


groq_classifier_service = GroqClassifierService()
