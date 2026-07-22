"""Frozen pre-RI-3 scorer — verbatim copy of
`algorithm.calculate_color_harmony_score`'s body as it stood before the RI-3
CIELAB rewrite, kept ONLY so `scripts/eval_outfits.py --compare legacy,branched`
can report an honest before/after AUC comparison.

Do not "fix" or tune this file — its entire value is being an unchanged
snapshot of the old name-pair-table logic. Real logic changes belong in
`services/recommendation/color_harmony.py` / `algorithm.py`.
"""

from __future__ import annotations

NEUTRAL_COLORS = {"white", "black", "gray", "grey", "beige", "cream", "brown"}
WARM_COLORS = {"red", "orange", "yellow", "pink", "coral"}
COOL_COLORS = {"blue", "green", "purple", "teal", "turquoise"}

_COMPLEMENTARY = {
    ("red", "green"),
    ("blue", "orange"),
    ("yellow", "purple"),
    ("pink", "green"),
}


def legacy_color_harmony_score(color1: str | None, color2: str | None) -> float:
    """Verbatim pre-RI-3 logic, adapted to take raw color-name strings instead
    of `WardrobeItem`s (the eval harness only ever had names anyway — see
    `_SCORER_FIELDS` in `eval_outfits.py`)."""
    color1 = (color1 or "").lower()
    color2 = (color2 or "").lower()

    if not color1 or not color2:
        return 0.5

    if color1 == color2:
        return 0.6

    if color1 in NEUTRAL_COLORS or color2 in NEUTRAL_COLORS:
        return 0.7

    if (color1, color2) in _COMPLEMENTARY or (color2, color1) in _COMPLEMENTARY:
        return 0.9

    if (color1 in WARM_COLORS and color2 in WARM_COLORS) or (
        color1 in COOL_COLORS and color2 in COOL_COLORS
    ):
        return 0.8

    return 0.3
