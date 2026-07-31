"""Schema mapping utilities for converting raw classifier JSON to WardrobeItem format.

Single shared mapper for all four backends (`groq`, `claude`, `openai`, `gemini`)
— previously each classifier carried its own byte-identical private
`_map_to_wardrobe_schema()`; those are deleted in favor of this one function
(RI-2). `classify_single_image` in each of the four classifiers, plus Gemini's
`classify_batch_images`, all call `map_classifier_result_to_wardrobe_schema`.

Boundary: this module owns *attribute* mapping only. Color-palette fields
(`color_palette`, `color_extraction_source`) are deliberately never set here —
they come from pixel extraction (`services/ai/color_extraction.py`), which the
image-processing workers run separately and merge in via
`build_wardrobe_update_payload` below.
"""

from typing import Any

from attreq_api.schemas.wardrobe_enums import (
    FORMALITY_SCORE_RANGE,
    FULLBODY_CATEGORIES,
    Neckline,
    Silhouette,
    SleeveLength,
    StatementLevel,
    Texture,
    coerce_enum,
)

# The 9 fields the v2 prompt asks for a per-attribute confidence on. Any of
# these missing/invalid in the backend's `attribute_confidence` block falls
# back to the top-level `detection_confidence`.
_ATTRIBUTE_CONFIDENCE_KEYS = (
    "category",
    "color_primary",
    "pattern",
    "season",
    "occasion",
    "texture",
    "silhouette",
    "neckline",
    "sleeve_length",
)


def _coerce_formality(value: Any) -> int | None:
    """Clamp the LLM's formality judgment to `FORMALITY_SCORE_RANGE`.

    Never fabricates a default — an out-of-range or non-numeric value maps to
    `None`, not e.g. 1 or 4.
    """
    if isinstance(value, bool):  # bool is an int subclass — reject explicitly
        return None
    if isinstance(value, (int, float)):
        as_int = int(value)
        if as_int in FORMALITY_SCORE_RANGE:
            return as_int
    return None


def _coerce_bool(value: Any) -> bool:
    """Loosely coerce a possibly-stringy LLM boolean. Defaults `False`."""
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in ("true", "yes", "1")
    if isinstance(value, (int, float)):
        return bool(value)
    return False


def _derive_is_fullbody(raw: dict[str, Any], category: str | None) -> bool:
    """`is_fullbody` is derived from `category` server-side, not trusted from
    an independent LLM boolean — the category vocabulary already distinguishes
    dress/jumpsuit/romper, and an independent boolean can contradict it.

    Falls back to a loosely-coerced LLM `is_fullbody` only when `category` is
    unrecognized/missing; defaults `False`.
    """
    if category and category.lower() in FULLBODY_CATEGORIES:
        return True
    if category:
        # Category is recognized but not full-body — trust that over the LLM.
        return False
    return _coerce_bool(raw.get("is_fullbody"))


def _build_attribute_confidence(raw: dict[str, Any]) -> dict[str, float]:
    detection_confidence = raw.get("detection_confidence", 0.0)
    if not isinstance(detection_confidence, (int, float)):
        detection_confidence = 0.0
    fallback = float(detection_confidence)

    raw_block = raw.get("attribute_confidence")
    if not isinstance(raw_block, dict):
        raw_block = {}

    result: dict[str, float] = {}
    for key in _ATTRIBUTE_CONFIDENCE_KEYS:
        value = raw_block.get(key)
        if isinstance(value, (int, float)) and not isinstance(value, bool) and 0.0 <= value <= 1.0:
            result[key] = float(value)
        else:
            result[key] = fallback
    return result


def map_classifier_result_to_wardrobe_schema(raw: dict[str, Any]) -> dict[str, Any]:
    """Map a raw classifier JSON response (v1 or v2 shape) to WardrobeItem fields.

    v1 fields (`category`, `color_primary`, `color_secondary`, `pattern`,
    `season`, `occasion`, `detection_confidence`, `processing_status`) pass
    through unchanged — regression safety for callers still on the v1 prompt
    (the eval gate's `--schema v1` path).

    v2 fields are coerced defensively: unknown/out-of-vocabulary enum strings
    from the LLM fall back to `other`/`n_a` (never stored raw) and log a
    warning; `formality_score` clamps to 1-4 or becomes `None`; `is_fullbody`
    is derived from `category`, not trusted independently from the LLM.

    Always sets `schema_version=2` — this function is only ever called from
    the v2-prompt code path.
    """
    category = raw.get("category")

    return {
        "category": category,
        "color_primary": raw.get("color_primary"),
        "color_secondary": raw.get("color_secondary"),
        "pattern": raw.get("pattern"),
        "season": raw.get("season", []),
        "occasion": raw.get("occasion", []),
        "detection_confidence": raw.get("detection_confidence", 0.0),
        "processing_status": raw.get("processing_status", "completed"),
        "texture": coerce_enum(raw.get("texture"), Texture, Texture.OTHER).value,
        "silhouette": coerce_enum(raw.get("silhouette"), Silhouette, Silhouette.REGULAR).value,
        "neckline": coerce_enum(raw.get("neckline"), Neckline, Neckline.N_A).value,
        "sleeve_length": coerce_enum(raw.get("sleeve_length"), SleeveLength, SleeveLength.N_A).value,
        "statement_level": coerce_enum(
            raw.get("statement_level"), StatementLevel, StatementLevel.STANDARD
        ).value,
        "llm_formality": _coerce_formality(raw.get("formality_score")),
        "is_fullbody": _derive_is_fullbody(raw, category),
        "attribute_confidence": _build_attribute_confidence(raw),
        "schema_version": 2,
    }


def build_wardrobe_update_payload(
    detection_result: dict[str, Any],
    palette: Any,
    color_extraction_source: str,
    processed_image_url: str | None,
    thumbnail_url: str | None,
) -> dict[str, Any]:
    """Build the `wardrobe_crud.update()` payload shared by both image workers.

    `image_processor.py` and `workers/batch_image_processor.py` were
    near-duplicating this dict construction; this is the same drift class the
    classifier-mapper consolidation addresses, so it's factored out once here.

    Args:
        detection_result: Output of `clothing_detection_service.detect_clothing`
            — already run through `map_classifier_result_to_wardrobe_schema`
            (v2) via the classifier, or a v1-shaped fallback dict.
        palette: A `color_extraction.ColorPalette` or `None` (extraction failed
            or was skipped).
        color_extraction_source: `"pixel"` or `"llm_fallback"`.
        processed_image_url: Resolved processed-image URL (already
            fallen-back to the original if bg removal failed).
        thumbnail_url: Resolved thumbnail URL, or `None`.
    """
    payload: dict[str, Any] = {
        "processed_image_url": processed_image_url,
        "thumbnail_url": thumbnail_url,
        "category": detection_result.get("category"),
        "color_primary": detection_result.get("color_primary"),
        "color_secondary": detection_result.get("color_secondary"),
        "pattern": detection_result.get("pattern"),
        "season": detection_result.get("season", []),
        "occasion": detection_result.get("occasion", []),
        "detection_confidence": detection_result.get("detection_confidence", 0.0),
        "classification_source": detection_result.get("classification_source"),
        "processing_status": "completed",
        "color_extraction_source": color_extraction_source,
        "color_palette": [
            {
                "lab": list(color.lab),
                "hex": color.hex,
                "share": color.share,
                "is_neutral": color.is_neutral,
                "name": color.name,
            }
            for color in palette.colors
        ]
        if palette is not None
        else None,
    }

    # v2-only fields — present when the classifier ran through the mapper
    # above; absent on a v1-shaped fallback dict (e.g. classifier unconfigured).
    if "schema_version" in detection_result:
        payload["texture"] = detection_result.get("texture")
        payload["silhouette"] = detection_result.get("silhouette")
        payload["neckline"] = detection_result.get("neckline")
        payload["sleeve_length"] = detection_result.get("sleeve_length")
        payload["statement_level"] = detection_result.get("statement_level")
        payload["llm_formality"] = detection_result.get("llm_formality")
        payload["is_fullbody"] = detection_result.get("is_fullbody", False)
        payload["attribute_confidence"] = detection_result.get("attribute_confidence")
        payload["schema_version"] = detection_result.get("schema_version", 2)

    return payload
