"""Personal color-affinity vector (RI-3) — pure helpers, no DB access.

~12 coarse color families, built from the **real 16-name classifier vocab**
(`services/ai/prompt_text.py`), stored as the `color_affinity` key inside
`users.style_preferences` JSON (no migration — same JSON-string column RI-2's
`personal_color` key also lives in, see `services/style_dna/personal_color.py`).

DB-touching orchestration (`update_color_affinity`, which loads the outfit's
items, mutates and persists `style_preferences`) intentionally lives in
`services/style_dna/style_dna_service.py` alongside `update_behaviour_weights`
(same shape, same call sites) rather than here — this module stays pure so it
can be unit-tested without a database.
"""

from __future__ import annotations

# Dominant color-family buckets. "multi" is reserved for future multi-color/
# patterned-item aggregation (not populated by `color_family_for_name`, which
# only maps single named colors) — kept in the vocabulary list for forward
# compatibility with RI-4+.
COLOR_FAMILIES: tuple[str, ...] = (
    "black",
    "white",
    "gray",
    "navy",
    "beige_tan",
    "brown",
    "red",
    "pink_purple",
    "blue",
    "green",
    "yellow_orange",
    "multi",
)

NAMED_COLOR_TO_FAMILY: dict[str, str] = {
    "black": "black",
    "white": "white",
    "gray": "gray",
    "grey": "gray",
    "navy": "navy",
    "beige": "beige_tan",
    "tan": "beige_tan",
    "cream": "beige_tan",
    "brown": "brown",
    "red": "red",
    "maroon": "red",
    "pink": "pink_purple",
    "purple": "pink_purple",
    "blue": "blue",
    "green": "green",
    "yellow": "yellow_orange",
    "orange": "yellow_orange",
}

MAX_AFFINITY_INFLUENCE = 0.10
AFFINITY_CLAMP_MIN = 0.7
AFFINITY_CLAMP_MAX = 1.3
AFFINITY_SEED_DOMINANT = 1.2
AFFINITY_SEED_ACCENT = 1.05
AFFINITY_SEED_AVOID = 0.8
AFFINITY_UPDATE_DELTA = 0.02  # slower than behaviour_weights' 0.05 (coarser signal)


def color_family_for_name(name: str | None) -> str | None:
    """Map a single classifier color name to its family bucket, or `None` if
    unmapped/absent."""
    if not name:
        return None
    return NAMED_COLOR_TO_FAMILY.get(name.strip().lower())


def _clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


def seed_color_affinity(style_dna: dict) -> dict[str, float]:
    """Seed the affinity vector from the Style DNA quiz's color palette
    (`color_palette.dominant/accent/avoids`, already synthesized by the LLM —
    see `services/style_dna/prompts.py::SYNTHESIS_PROMPT`).

    dominant -> 1.2, accent -> 1.05 (only if not already seeded higher by a
    dominant hit), avoids -> 0.8, everything else implicitly 1.0 (absent key).
    """
    palette = (style_dna or {}).get("color_palette", {}) or {}
    dominant = palette.get("dominant", []) or []
    accent = palette.get("accent", []) or []
    avoids = palette.get("avoids", []) or []

    affinity: dict[str, float] = {}
    for name in dominant:
        family = color_family_for_name(name)
        if family:
            affinity[family] = AFFINITY_SEED_DOMINANT
    for name in accent:
        family = color_family_for_name(name)
        if family and affinity.get(family, 1.0) < AFFINITY_SEED_ACCENT:
            affinity[family] = AFFINITY_SEED_ACCENT
    for name in avoids:
        family = color_family_for_name(name)
        if family:
            affinity[family] = AFFINITY_SEED_AVOID

    return affinity


def bump_affinity(affinity: dict[str, float], family: str, signal: str) -> dict[str, float]:
    """Apply one coarse `worn`/`liked`/`disliked` counting update to `family`,
    clamped to `[0.7, 1.3]`. Returns a new dict (does not mutate `affinity`).

    Reuses the coarse worn/liked/disliked signal `update_behaviour_weights`
    already receives — RI-1's `dislike_item` granularity (per-item, not
    per-outfit) can upgrade this to a finer signal later without changing the
    stored shape.
    """
    delta = AFFINITY_UPDATE_DELTA if signal in ("worn", "liked", "accepted") else -AFFINITY_UPDATE_DELTA
    updated = dict(affinity)
    current = updated.get(family, 1.0)
    updated[family] = round(_clamp(current + delta, AFFINITY_CLAMP_MIN, AFFINITY_CLAMP_MAX), 4)
    return updated


def affinity_adjustment(family: str | None, color_affinity: dict) -> float:
    """Affinity deviation from neutral (1.0), clamped to ±`MAX_AFFINITY_INFLUENCE`.

    One half of the C6 combined-clamp fix (see `personal_color.apply_personal_color_adjustment`)
    — this alone is bounded to ±10%, but callers must jointly clamp it together
    with the personal-color adjustment to a single ±10% envelope, not stack
    two independent ±10% adjustments multiplicatively.
    """
    if not family:
        return 0.0
    value = float((color_affinity or {}).get(family, 1.0))
    return _clamp(value - 1.0, -MAX_AFFINITY_INFLUENCE, MAX_AFFINITY_INFLUENCE)
