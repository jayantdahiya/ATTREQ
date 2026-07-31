"""Legacy named-color -> Lab bridge (RI-3) **[BOOTSTRAP for `schema_version < 2`]**.

At RI-3 completion, items backfilled by RI-2's pixel extraction
(`schema_version == 2`, real `color_palette`) skip this module entirely —
see `algorithm._load_palette`. This bridge exists only so pre-RI-2 rows (and
any row where pixel extraction fell back, `color_palette is None`) still get
a real CIELAB point to feed `color_harmony.harmony()`, instead of reverting to
the old name-pair lookup table.

Built for the **actual classifier vocabulary only** — `black, white, blue,
red, green, brown, beige, gray, grey, navy, maroon, pink, purple, yellow,
orange, tan, cream` (all four `services/ai/*_classifier.py` prompts share the
single `CLASSIFICATION_PROMPT` built from `schemas/wardrobe_enums.py` /
`services/ai/prompt_text.py`, which prompts for exactly these 16 names;
`grey` is a spelling synonym for `gray` no LLM emits but that user-corrected
data or CSV imports could carry).

Reuses `services/ai/color_extraction`'s `_NAMED_COLOR_RGB` table and
`srgb_to_lab` conversion rather than maintaining a second, independently-typed
hex table that could silently drift from RI-2's pixel-vs-LLM eval comparisons
(that module's own docstring calls out this exact vocab-parity concern).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

from attreq_api.services.ai.color_extraction import _NAMED_COLOR_RGB, srgb_to_lab
from attreq_api.services.recommendation.color_harmony import PaletteColor

if TYPE_CHECKING:
    from attreq_api.models.wardrobe import WardrobeItem

# Fashion-neutral names (F3) — curated, NOT chroma-derived. Real navy
# ((L,a,b) ~= (13, 47.5, -64.7), chroma ~80) and maroon/brown/tan all exceed
# any reasonable chroma-only neutral cutoff despite being neutrals in
# wardrobe terms, so a chroma threshold on the single-point legacy Lab would
# misclassify them (see F3 in the finalized RI-3 plan). The chroma-or-dark
# rule (`color_harmony.is_functional_neutral`) is reserved for the real RI-2
# pixel palette only.
NEUTRAL_NAMES: frozenset[str] = frozenset(
    {"black", "white", "gray", "grey", "navy", "beige", "cream", "tan", "brown", "maroon"}
)

# Any unmapped/unexpected name (should not occur against the current 16-name
# vocab + grey) falls back to a mid-lightness, zero-chroma point — never raises.
DEFAULT_UNKNOWN_LAB: tuple[float, float, float] = (55.0, 0.0, 0.0)

_ALIASES: dict[str, str] = {"grey": "gray"}


def _build_legacy_color_lab() -> dict[str, tuple[float, float, float]]:
    table: dict[str, tuple[float, float, float]] = {}
    for name, rgb in _NAMED_COLOR_RGB.items():
        lab = srgb_to_lab(np.array(rgb, dtype=float))
        table[name] = (float(lab[0]), float(lab[1]), float(lab[2]))
    for alias, canonical in _ALIASES.items():
        table[alias] = table[canonical]
    return table


# Computed once at import (mirrors `color_extraction._NAMED_COLOR_LAB`'s own
# pattern — pure numpy arithmetic over a fixed 16-entry table, not per-call).
LEGACY_COLOR_LAB: dict[str, tuple[float, float, float]] = _build_legacy_color_lab()


def _lab_for_name(name: str) -> tuple[float, float, float]:
    return LEGACY_COLOR_LAB.get(name.strip().lower(), DEFAULT_UNKNOWN_LAB)


def _is_neutral_name(name: str) -> bool:
    return name.strip().lower() in NEUTRAL_NAMES


def legacy_palette_for_item(item: WardrobeItem) -> list[PaletteColor]:
    """Build a `PaletteColor` list from `color_primary`/`color_secondary`.

    `color_primary` gets share 0.7 (1.0 if there's no secondary), `color_secondary`
    gets share 0.3. An item with neither color set returns an empty list —
    callers (`algorithm.calculate_color_harmony_detailed`) treat that as the old
    "unknown color" 0.5 fallback.
    """
    colors: list[PaletteColor] = []
    primary = getattr(item, "color_primary", None)
    secondary = getattr(item, "color_secondary", None)

    if primary:
        colors.append(
            PaletteColor(
                lab=_lab_for_name(primary),
                is_neutral=_is_neutral_name(primary),
                share=0.7 if secondary else 1.0,
            )
        )
    if secondary:
        colors.append(
            PaletteColor(
                lab=_lab_for_name(secondary),
                is_neutral=_is_neutral_name(secondary),
                share=0.3,
            )
        )
    return colors
