"""Schema mapping utilities for converting Gemini API responses to WardrobeItem format."""

from typing import Any


def map_gemini_to_wardrobe_schema(gemini_result: dict[str, Any]) -> dict[str, Any]:
    """Map Gemini API response to WardrobeItem schema format.

    Args:
        gemini_result: Single result from Gemini API

    Returns:
        Dictionary ready for WardrobeItem model

    Example:
        Gemini response:
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

        Returns dict ready for WardrobeItem model
    """
    return {
        "category": gemini_result.get("category"),
        "color_primary": gemini_result.get("color_primary"),
        "color_secondary": gemini_result.get("color_secondary"),
        "pattern": gemini_result.get("pattern"),
        "season": gemini_result.get("season", []),
        "occasion": gemini_result.get("occasion", []),
        "detection_confidence": gemini_result.get("detection_confidence", 0.0),
        "processing_status": gemini_result.get("processing_status", "completed"),
    }


def validate_gemini_result(gemini_result: dict[str, Any]) -> bool:
    """Validate that Gemini result has required fields.

    Args:
        gemini_result: Single result from Gemini API

    Returns:
        True if valid, False otherwise
    """
    required_fields = ["category", "color_primary", "pattern", "season", "occasion"]

    for field in required_fields:
        if field not in gemini_result:
            return False

    # Validate season and occasion are lists
    if not isinstance(gemini_result.get("season"), list):
        return False
    if not isinstance(gemini_result.get("occasion"), list):
        return False

    # Validate confidence is a number between 0 and 1
    confidence = gemini_result.get("detection_confidence", 0.0)
    return isinstance(confidence, (int, float)) and 0.0 <= confidence <= 1.0


def normalize_gemini_result(gemini_result: dict[str, Any]) -> dict[str, Any]:
    """Normalize Gemini result to ensure consistent format.

    Args:
        gemini_result: Single result from Gemini API

    Returns:
        Normalized result dictionary
    """
    normalized = gemini_result.copy()

    # Ensure season and occasion are lists
    if not isinstance(normalized.get("season"), list):
        normalized["season"] = []
    if not isinstance(normalized.get("occasion"), list):
        normalized["occasion"] = []

    # Ensure confidence is a float
    confidence = normalized.get("detection_confidence", 0.0)
    if not isinstance(confidence, (int, float)):
        normalized["detection_confidence"] = 0.0
    else:
        normalized["detection_confidence"] = float(confidence)

    # Ensure processing_status is set
    if not normalized.get("processing_status"):
        normalized["processing_status"] = "completed"

    return normalized
