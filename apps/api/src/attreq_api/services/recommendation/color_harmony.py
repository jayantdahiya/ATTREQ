"""Color harmony v2 (CIELAB) — RI-3.

Pure functions over CIELAB `(L*, a*, b*)` tuples. No DB access, no `models/`
import — callers (`algorithm._load_palette`) are responsible for turning a
`WardrobeItem` into `PaletteColor`s, either from the real RI-2 pixel palette
(`item.color_palette`, `schema_version == 2`) or from the legacy named-color
bridge (`legacy_color_lab.legacy_palette_for_item`, `schema_version == 1`).

Three-branch max, per the USC/Adobe 2007.02388 finding that hand-crafted hue
templates deviate from real human judgments, and that the two dominant
real-world patterns are tonal similarity and neutral-anchored contrast:

1. `tonal`            — same-hue(ish), different-shade: small Δh*/ΔC* with a
                         meaningful ΔL* (20–60).
2. `neutral_contrast`  — either color is neutral: score purely on lightness
                         contrast, skipping hue math entirely (hue is
                         undefined at low saturation — IJERCSE). This is the
                         most common winner in practice; neutrals dominate
                         real closets and pair with everything.
3. `hue_rule`          — both colors chromatic: mild analogous/complementary
                         hue bonus, scaled by chroma. Ceiling capped below the
                         other two branches (wheel templates are the weakest
                         evidence per the study above).

When both colors are chromatic but eligible for neither `tonal` nor
`hue_rule`, `harmony()` returns a mild flat fallback with `branch="none"`
(never mislabelled as `hue_rule` — RI-4's explanations consume `branch`).

All thresholds below (`HUE_TOL_TONAL`, `CHROMA_TOL_TONAL`, the tonal L*-band,
`HUE_RULE_CEILING`, the analogous/complementary hue windows) are empirical
tuning constants, not physical constants — they encode the qualitative
invariant the unit tests check: `tonal` and `neutral_contrast` can reach a
score of 1.0; `hue_rule`'s ceiling keeps it strictly below both.

IMPORTANT (documented once, here): because named-color inputs collapse an
entire color name to one representative Lab point, two same-named items
always have ΔL*=0 and never satisfy the tonal L*-band — the `tonal` branch is
therefore *dormant* on the legacy bridge and is validated only via synthetic
`PaletteColor` fixtures with hand-set, distinct L* values (see
`tests/test_color_harmony.py`). The genuine tonal win requires RI-2's
pixel-derived per-item L*, which is already live for `schema_version == 2`
rows.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any

# ---------------------------------------------------------------------------
# Tunable constants — empirical, not physical. See module docstring.
# ---------------------------------------------------------------------------

HUE_TOL_TONAL = 35.0
CHROMA_TOL_TONAL = 25.0
TONAL_DL_MIN = 20.0
TONAL_DL_MAX = 60.0

HUE_RULE_CEILING = 0.85
ANALOGOUS_HUE_MAX = 40.0
COMPLEMENTARY_HUE_MIN = 150.0
COMPLEMENTARY_HUE_MAX = 210.0
HUE_RULE_CHROMA_SATURATION = 50.0  # avg chroma at/above this gets full chroma credit

NEUTRAL_CONTRAST_FLOOR = 0.6

FALLBACK_SCORE = 0.35

# Reserved for the RI-2 pixel path only (real `color_palette` rows) — NOT used
# by the legacy named-color bridge, where neutrality is name-based (F3).
# Perceptual-achromatic cutoff (chroma < 15) OR "dark, moderately-saturated
# colors read as functional neutrals" (chroma < 35 and L* < 25). Known
# limitation, stated plainly: real pixel-extracted navy has chroma ~80 (see
# `services/ai/color_extraction.py`), which exceeds even the darker/looser
# threshold here — this heuristic catches dark browns/maroons/near-blacks,
# not saturated navy. Revisit in RI-4/5 if it matters in practice.
FUNCTIONAL_NEUTRAL_CHROMA = 15.0
FUNCTIONAL_NEUTRAL_DARK_CHROMA = 35.0
FUNCTIONAL_NEUTRAL_DARK_L = 25.0


@dataclass(frozen=True)
class PaletteColor:
    """One color, reduced to what harmony scoring needs.

    Deliberately separate from `services/ai/color_extraction.PaletteColor`
    (which also carries `hex`/`name` for display) — this is the pure scoring
    input, built by `algorithm._load_palette` from either source.
    """

    lab: tuple[float, float, float]
    is_neutral: bool
    share: float = 1.0


@dataclass(frozen=True)
class HarmonyResult:
    """Score + the winning branch name (RI-4 explanations consume `branch`)."""

    score: float
    branch: str  # "tonal" | "neutral_contrast" | "hue_rule" | "none"
    detail: dict[str, Any] = field(default_factory=dict)


def lab_chroma(lab: tuple[float, float, float]) -> float:
    """C* = sqrt(a*^2 + b*^2)."""
    _l, a, b = lab
    return math.sqrt(a * a + b * b)


def lab_hue_deg(lab: tuple[float, float, float]) -> float:
    """Hue angle in degrees [0, 360). Undefined (returns 0.0) at zero chroma —
    callers must branch on `is_neutral`/chroma before trusting this."""
    _l, a, b = lab
    return math.degrees(math.atan2(b, a)) % 360.0


def _hue_delta(h1: float, h2: float) -> float:
    """Minimal circular distance between two hue angles, in [0, 180]."""
    d = abs(h1 - h2) % 360.0
    return min(d, 360.0 - d)


def is_functional_neutral(lab: tuple[float, float, float]) -> bool:
    """Broader "reads as neutral in a wardrobe" rule for real pixel palettes.

    Only ever applied to `schema_version == 2` rows (see `algorithm._load_palette`)
    on top of the stored `is_neutral` flag (which is the strict
    perceptual-achromatic `chroma < 15` cutoff computed at extraction time).
    """
    chroma = lab_chroma(lab)
    l_star = lab[0]
    if chroma < FUNCTIONAL_NEUTRAL_CHROMA:
        return True
    return chroma < FUNCTIONAL_NEUTRAL_DARK_CHROMA and l_star < FUNCTIONAL_NEUTRAL_DARK_L


def _tonal_score(a: PaletteColor, b: PaletteColor) -> HarmonyResult | None:
    """Same-hue-different-shade. Eligible only when Δh*, ΔC* are small AND
    ΔL* falls in the [20, 60] band (identical L* is flat; extreme ΔL* is fine
    but scores under `neutral_contrast` anyway). Defensively returns `None`
    whenever either color is neutral (hue is undefined at low saturation) —
    `harmony()` already routes neutral pairs to `_neutral_contrast_score`
    before ever calling this, but this guard makes the function safe to call
    directly (e.g. from tests) without relying on that dispatch order."""
    if a.is_neutral or b.is_neutral:
        return None

    delta_l = abs(a.lab[0] - b.lab[0])
    if not (TONAL_DL_MIN <= delta_l <= TONAL_DL_MAX):
        return None

    delta_h = _hue_delta(lab_hue_deg(a.lab), lab_hue_deg(b.lab))
    if delta_h > HUE_TOL_TONAL:
        return None

    delta_c = abs(lab_chroma(a.lab) - lab_chroma(b.lab))
    if delta_c > CHROMA_TOL_TONAL:
        return None

    hue_component = 1.0 - (delta_h / HUE_TOL_TONAL) * 0.5  # in [0.5, 1.0]
    chroma_component = 1.0 - (delta_c / CHROMA_TOL_TONAL) * 0.3  # in [0.7, 1.0]

    center = (TONAL_DL_MIN + TONAL_DL_MAX) / 2.0
    half_width = (TONAL_DL_MAX - TONAL_DL_MIN) / 2.0
    l_component = 1.0 - (abs(delta_l - center) / half_width) * 0.2  # in [0.8, 1.0]

    score = hue_component * chroma_component * l_component
    return HarmonyResult(
        round(min(1.0, score), 4),
        "tonal",
        {"delta_l": round(delta_l, 3), "delta_h": round(delta_h, 3), "delta_c": round(delta_c, 3)},
    )


def _neutral_contrast_score(a: PaletteColor, b: PaletteColor) -> HarmonyResult:
    """Purely lightness-driven — no hue math (hue is undefined on neutrals).
    Floor of 0.6 so a neutral pairs reasonably with anything (they dominate
    real closets); reaches 1.0 only at the maximal ΔL* (e.g. black vs white)."""
    delta_l = abs(a.lab[0] - b.lab[0])
    score = NEUTRAL_CONTRAST_FLOOR + (1.0 - NEUTRAL_CONTRAST_FLOOR) * (min(delta_l, 100.0) / 100.0)
    return HarmonyResult(round(min(1.0, score), 4), "neutral_contrast", {"delta_l": round(delta_l, 3)})


def _hue_rule_score(a: PaletteColor, b: PaletteColor) -> HarmonyResult | None:
    """Mild analogous/complementary bonus for two chromatic colors, scaled by
    average chroma. Ceiling stays below `tonal`/`neutral_contrast` (wheel
    templates deviate from real human judgments — USC/Adobe 2007.02388).
    Defensively returns `None` when either color is neutral — see
    `_tonal_score`'s docstring for why this guard exists here too."""
    if a.is_neutral or b.is_neutral:
        return None

    delta_h = _hue_delta(lab_hue_deg(a.lab), lab_hue_deg(b.lab))
    avg_chroma = (lab_chroma(a.lab) + lab_chroma(b.lab)) / 2.0
    chroma_factor = min(1.0, avg_chroma / HUE_RULE_CHROMA_SATURATION)

    if delta_h <= ANALOGOUS_HUE_MAX:
        base = 1.0 - (delta_h / ANALOGOUS_HUE_MAX) * 0.3
    elif COMPLEMENTARY_HUE_MIN <= delta_h <= COMPLEMENTARY_HUE_MAX:
        mid = (COMPLEMENTARY_HUE_MIN + COMPLEMENTARY_HUE_MAX) / 2.0
        half = (COMPLEMENTARY_HUE_MAX - COMPLEMENTARY_HUE_MIN) / 2.0
        base = 1.0 - (abs(delta_h - mid) / half) * 0.3
    else:
        return None  # dead zone — deviates from every learned harmony template

    score = base * chroma_factor * HUE_RULE_CEILING
    return HarmonyResult(
        round(min(HUE_RULE_CEILING, score), 4),
        "hue_rule",
        {"delta_h": round(delta_h, 3), "avg_chroma": round(avg_chroma, 3)},
    )


def harmony(a: PaletteColor, b: PaletteColor) -> HarmonyResult:
    """`max(tonal, neutral_contrast, hue_rule)` — returns score AND branch name."""
    if a.is_neutral or b.is_neutral:
        return _neutral_contrast_score(a, b)

    tonal = _tonal_score(a, b)
    hue_rule = _hue_rule_score(a, b)
    candidates = [c for c in (tonal, hue_rule) if c is not None]
    if not candidates:
        return HarmonyResult(FALLBACK_SCORE, "none", {})

    return max(candidates, key=lambda r: r.score)


def harmony_against_set(color: PaletteColor, others: list[PaletteColor]) -> float:
    """Mean pairwise harmony of `color` against a set of other colors.

    Slot-fill scoring surface (accessories, footwear/outerwear) per the
    Sonnet plan structure — not wired into `generate_daily_outfits` in this
    milestone (accessory scoring stays random-choice; see RI-3 plan "out of
    scope"), but exposed and tested so RI-4/RI-6 can use it directly.
    """
    if not others:
        return 0.5
    scores = [harmony(color, other).score for other in others]
    return round(sum(scores) / len(scores), 4)
