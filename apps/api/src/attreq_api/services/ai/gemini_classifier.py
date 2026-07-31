"""Gemini API service for wardrobe classification with batch processing support."""

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


class GeminiClassifierService:
    """Service for classifying wardrobe items using Google Gemini API."""

    def __init__(self):
        self.api_key = settings.gemini_api_key
        self.model_name = settings.gemini_model_name
        self.batch_size = settings.gemini_batch_size
        self.base_url = "https://generativelanguage.googleapis.com/v1beta/models"

    async def classify_single_image(self, image_path: str) -> dict[str, Any]:
        """Classify a wardrobe image using Gemini.

        Raises:
            FileNotFoundError: If image doesn't exist
            ValueError: If API key not configured or response invalid
            httpx.HTTPError: If API request fails
        """
        if not await asyncio.to_thread(os.path.exists, image_path):
            raise FileNotFoundError(f"Image not found: {image_path}")
        if not self.api_key:
            raise ValueError("Gemini API key not configured")

        base64_data = self._encode_image_to_base64(image_path)
        mime_type = self._get_mime_type(image_path)

        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": CLASSIFICATION_PROMPT},
                        {"inline_data": {"mime_type": mime_type, "data": base64_data}},
                    ]
                }
            ]
        }

        try:
            response = await self._make_api_request(payload)
            result = self._parse_response(response)
            return map_classifier_result_to_wardrobe_schema(result)
        except Exception as e:
            logger.error(f"Gemini single image classification failed: {str(e)}")
            raise

    async def classify_batch_images(self, image_paths: list[str]) -> list[dict[str, Any]]:
        """Classify multiple wardrobe images in a single batch request.

        Raises:
            ValueError: If no API key configured or too many images
            FileNotFoundError: If any image doesn't exist
            httpx.HTTPError: If API request fails
        """
        if not self.api_key:
            raise ValueError("Gemini API key not configured")
        if len(image_paths) > self.batch_size:
            raise ValueError(f"Too many images. Maximum batch size is {self.batch_size}")

        for path in image_paths:
            if not await asyncio.to_thread(os.path.exists, path):
                raise FileNotFoundError(f"Image not found: {path}")

        try:
            parts = [{"text": CLASSIFICATION_PROMPT}]
            for image_path in image_paths:
                base64_data = self._encode_image_to_base64(image_path)
                mime_type = self._get_mime_type(image_path)
                parts.append({"inline_data": {"mime_type": mime_type, "data": base64_data}})

            payload = {"contents": [{"parts": parts}]}
            response = await self._make_api_request(payload)
            results = self._parse_response(response)

            if not isinstance(results, list):
                results = [results]

            return [map_classifier_result_to_wardrobe_schema(r) for r in results]
        except Exception as e:
            logger.error(f"Gemini batch classification failed: {str(e)}")
            raise

    async def analyze_image(self, image_path: str, prompt: str) -> dict[str, Any]:
        """Call Gemini vision with a custom prompt. Returns raw JSON dict."""
        if not await asyncio.to_thread(os.path.exists, image_path):
            raise FileNotFoundError(f"Image not found: {image_path}")
        if not self.api_key:
            raise ValueError("Gemini API key not configured")

        base64_data = self._encode_image_to_base64(image_path)
        mime_type = self._get_mime_type(image_path)

        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": prompt},
                        {"inline_data": {"mime_type": mime_type, "data": base64_data}},
                    ]
                }
            ]
        }

        try:
            response = await self._make_api_request(payload)
            return self._parse_response(response)
        except Exception as e:
            logger.error(f"Gemini analyze_image failed: {str(e)}")
            raise

    async def analyze_text(self, prompt: str) -> dict[str, Any]:
        """Call Gemini text-only with a custom prompt. Returns raw JSON dict."""
        if not self.api_key:
            raise ValueError("Gemini API key not configured")

        payload = {"contents": [{"parts": [{"text": prompt}]}]}

        try:
            response = await self._make_api_request(payload)
            return self._parse_response(response)
        except Exception as e:
            logger.error(f"Gemini analyze_text failed: {str(e)}")
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

    async def _make_api_request(self, payload: dict) -> dict:
        url = f"{self.base_url}/{self.model_name}:generateContent"
        headers = {"Content-Type": "application/json", "X-goog-api-key": self.api_key}

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            return response.json()

    def _parse_response(self, response: dict) -> Any:
        candidates = response.get("candidates", [])
        if not candidates:
            raise ValueError("No candidates in Gemini response")

        text = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "")
        if not text:
            raise ValueError("No text content in Gemini response")

        text = text.strip()
        if text.startswith("```json"):
            text = text[7:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()

        try:
            return json.loads(text)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in Gemini response: {e}") from e


gemini_classifier_service = GeminiClassifierService()
