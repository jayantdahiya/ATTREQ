"""Shared attribute-vocabulary enums for wardrobe classifier schema v2 (RI-2).

Single source of truth for the v2 fixed-vocabulary attributes. Consumed by:
- `services/ai/prompt_text.py` (builds the one shared classifier prompt from
  the `*_VALUES` lists below, so the prompt can never drift from the enums)
- `services/ai/schema_mapper.py` (coerces raw LLM strings into these enums)
- `schemas/wardrobe.py` (Pydantic response/update typing + validators)
- `tests/test_wardrobe_enums.py` (prompt/enum parity assertions)
- `scripts/gen_swift_enums.py` (generates the iOS mirror,
  `apps/ios/ATTREQ/Core/Models/WardrobeEnums.swift`)

Uses `class X(str, Enum)` rather than `StrEnum` so values serialize as bare
strings under Pydantic v2, matching the existing free-string storage idiom
used by `category`/`pattern`/etc.
"""

import logging
from enum import Enum
from typing import TypeVar

logger = logging.getLogger(__name__)

_E = TypeVar("_E", bound=Enum)


class Texture(str, Enum):
    """Fabric/material texture. `other` is the coercion fallback."""

    SMOOTH = "smooth"
    KNIT = "knit"
    DENIM = "denim"
    LEATHER = "leather"
    LACE = "lace"
    SILK_SATIN = "silk_satin"
    LINEN = "linen"
    CORDUROY = "corduroy"
    WOOL = "wool"
    FLEECE = "fleece"
    SHEER = "sheer"
    OTHER = "other"


class Silhouette(str, Enum):
    """Garment fit/cut."""

    FITTED = "fitted"
    REGULAR = "regular"
    RELAXED = "relaxed"
    OVERSIZED = "oversized"
    A_LINE = "a_line"
    STRAIGHT = "straight"
    SKINNY = "skinny"
    WIDE = "wide"
    CROP = "crop"
    LONGLINE = "longline"


class Neckline(str, Enum):
    """Neckline shape. Only meaningful for tops/fullbody garments — `n_a` is a
    legal, expected answer for bottoms/footwear (see
    `NECKLINE_APPLICABLE_CATEGORIES`)."""

    CREW = "crew"
    V_NECK = "v_neck"
    SCOOP = "scoop"
    COLLARED = "collared"
    TURTLENECK = "turtleneck"
    BOAT = "boat"
    SQUARE = "square"
    OFF_SHOULDER = "off_shoulder"
    HOODED = "hooded"
    OTHER = "other"
    N_A = "n_a"


class SleeveLength(str, Enum):
    """Sleeve length. Only meaningful for tops/outerwear/fullbody garments —
    `n_a` is a legal, expected answer for bottoms/footwear (see
    `SLEEVE_APPLICABLE_CATEGORIES`)."""

    SLEEVELESS = "sleeveless"
    SHORT = "short"
    THREE_QUARTER = "three_quarter"
    LONG = "long"
    N_A = "n_a"


class StatementLevel(str, Enum):
    """How much visual attention the item commands."""

    BASIC = "basic"
    STANDARD = "standard"
    STATEMENT = "statement"


TEXTURE_VALUES: list[str] = [e.value for e in Texture]
SILHOUETTE_VALUES: list[str] = [e.value for e in Silhouette]
NECKLINE_VALUES: list[str] = [e.value for e in Neckline]
SLEEVE_LENGTH_VALUES: list[str] = [e.value for e in SleeveLength]
STATEMENT_LEVEL_VALUES: list[str] = [e.value for e in StatementLevel]

FORMALITY_SCORE_RANGE = range(1, 5)  # 1..4 inclusive

# Server-side source of truth for `is_fullbody` — categories that cannot be
# paired top x bottom. See `schema_mapper.map_classifier_result_to_wardrobe_schema`.
FULLBODY_CATEGORIES: set[str] = {"dress", "jumpsuit", "romper"}

# Stopgap substring heuristics over the free-text `category` field, used only
# to soften eval/UI leniency (the LLM is still always asked for both fields;
# `n_a` is always a legal answer). Replace with launch-M2's `slot_of()` once
# the slot-prefixed category taxonomy lands.
NECKLINE_APPLICABLE_CATEGORIES: tuple[str, ...] = (
    "dress",
    "shirt",
    "blouse",
    "sweater",
    "t-shirt",
    "tank-top",
    "polo",
    "hoodie",
    "cardigan",
    "jacket",
    "coat",
    "blazer",
    "jumpsuit",
    "romper",
)
SLEEVE_APPLICABLE_CATEGORIES: tuple[str, ...] = (
    "dress",
    "shirt",
    "blouse",
    "sweater",
    "t-shirt",
    "tank-top",
    "polo",
    "hoodie",
    "cardigan",
    "jacket",
    "coat",
    "blazer",
    "jumpsuit",
    "romper",
)


def coerce_enum(value: object, enum_cls: type[_E], fallback: _E) -> _E:
    """Case-insensitive, whitespace-trimmed coercion of a raw LLM value into
    `enum_cls`. On a miss (out-of-vocabulary, wrong type, `None`), logs a
    warning and returns `fallback` — raw LLM strings are never stored.
    """
    if isinstance(value, str):
        candidate = value.strip().lower()
        for member in enum_cls:
            if member.value == candidate:
                return member

    logger.warning(
        "coerce_enum: out-of-vocabulary value for %s: %r — falling back to %s",
        enum_cls.__name__,
        value,
        fallback.value,
    )
    return fallback
