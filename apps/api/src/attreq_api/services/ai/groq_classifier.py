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

# Groq's per-minute rate limit is easily tripped when several photos are
# classified concurrently (see style_dna_service's semaphore). Retry 429s
# (and transient 5xx) with backoff instead of failing the whole request on
# the first hiccup.
MAX_RETRIES = 4
BASE_BACKOFF_SECONDS = 1.5
# Cap each wait so a heavily-throttled provider (or a large Retry-After header)
# can't stretch a single call's total retry time unbounded — the mobile client
# has a finite request timeout, so worst-case backend time must stay bounded.
MAX_BACKOFF_SECONDS = 15.0
RETRYABLE_STATUS_CODES = {429, 502, 503, 504}

# Reasoning models (e.g. this env's GROQ_MODEL_NAME=qwen/qwen3.6-27b) spend
# their completion-token budget on an internal chain-of-thought before ever
# writing the JSON answer — with a long enough prompt (e.g. synthesizing
# several photos' worth of style signals) the budget runs out mid-thought and
# Groq rejects the truncated, non-JSON output with a 400 json_validate_failed
# even though nothing about the request itself was invalid. Disabling
# reasoning for the models that support the flag avoids this entirely; see
# https://console.groq.com/docs/reasoning. `none` is currently supported by
# Qwen 3.6 27B, while GPT-OSS accepts only low/medium/high, so gate narrowly
# rather than sending an invalid field to other models.
REASONING_DISABLED_MODEL_MARKERS = ("qwen3.6-27b",)


class GroqClassifierService:
    """Service for classifying wardrobe items using Groq's Llama 4 Scout vision model."""

    BASE_URL = "https://api.groq.com/openai/v1/chat/completions"

    def __init__(self):
        self.api_key = settings.groq_api_key
        self.model_name = settings.groq_model_name

    def _base_payload(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "model": self.model_name,
            "response_format": {"type": "json_object"},
            "temperature": 0.1,
        }
        if any(
            marker in self.model_name.lower()
            for marker in REASONING_DISABLED_MODEL_MARKERS
        ):
            payload["reasoning_effort"] = "none"
        return payload

    async def _post_with_retry(
        self, client: httpx.AsyncClient, headers: dict, payload: dict
    ) -> dict[str, Any]:
        """POST to the Groq chat completions endpoint, retrying 429/5xx with backoff."""
        last_error: Exception | None = None
        for attempt in range(MAX_RETRIES + 1):
            try:
                response = await client.post(self.BASE_URL, headers=headers, json=payload)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                last_error = e
                if e.response.status_code not in RETRYABLE_STATUS_CODES or attempt == MAX_RETRIES:
                    raise
                fallback_delay = BASE_BACKOFF_SECONDS * (2**attempt)
                retry_after = e.response.headers.get("retry-after")
                try:
                    delay = float(retry_after) if retry_after else fallback_delay
                except ValueError:
                    logger.warning("Groq returned an invalid Retry-After header; using backoff")
                    delay = fallback_delay
                delay = max(0.0, min(delay, MAX_BACKOFF_SECONDS))
                logger.warning(
                    f"Groq request got {e.response.status_code}, "
                    f"retrying in {delay:.1f}s (attempt {attempt + 1}/{MAX_RETRIES})"
                )
                await asyncio.sleep(delay)
        raise last_error  # pragma: no cover - loop always returns or raises

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
            **self._base_payload(),
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
        }

        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }
            async with httpx.AsyncClient(timeout=60.0) as client:
                data = await self._post_with_retry(client, headers, payload)

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
            **self._base_payload(),
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
        }

        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }
            async with httpx.AsyncClient(timeout=90.0) as client:
                data = await self._post_with_retry(client, headers, payload)

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
            **self._base_payload(),
            "messages": [{"role": "user", "content": prompt}],
        }

        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }
            async with httpx.AsyncClient(timeout=90.0) as client:
                data = await self._post_with_retry(client, headers, payload)

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
