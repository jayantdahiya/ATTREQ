"""Factory for selecting the active classifier based on CLASSIFIER_PROVIDER env var."""

from typing import Any, Protocol

from attreq_api.config.settings import settings


class ClassifierService(Protocol):
    async def classify_single_image(self, image_path: str) -> dict[str, Any]: ...
    async def analyze_image(self, image_path: str, prompt: str) -> dict[str, Any]: ...
    async def analyze_text(self, prompt: str) -> dict[str, Any]: ...


def get_classifier() -> ClassifierService:
    """Return classifier service instance based on settings.classifier_provider.

    Supported values: groq, claude, openai, gemini (default: groq)
    """
    provider = settings.classifier_provider.lower()

    if provider == "claude":
        from attreq_api.services.ai.claude_classifier import claude_classifier_service
        return claude_classifier_service
    elif provider == "openai":
        from attreq_api.services.ai.openai_classifier import openai_classifier_service
        return openai_classifier_service
    elif provider == "gemini":
        from attreq_api.services.ai.gemini_classifier import gemini_classifier_service
        return gemini_classifier_service
    else:
        from attreq_api.services.ai.groq_classifier import groq_classifier_service
        return groq_classifier_service
