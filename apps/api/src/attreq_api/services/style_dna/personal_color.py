"""Personal-color prior (RI-3) — two continuous axes, never a season label.

Stored as the `personal_color` key inside `users.style_preferences` JSON
(no migration — same free-form JSON string column as everything else in
Style DNA): `{"undertone_warm_cool": [-1,1], "depth_light_deep": [-1,1],
"confidence": [0,1]}`.

Estimated from an *optional*, *opt-in* selfie (see the privacy-gated
`POST /users/style-dna/selfie` route in `api/v1/endpoints/style_dna.py`) via
one `analyze_image` call on the existing classifier factory — never from a
self-declared "season" (KCI study: self-diagnosis is wrong >80% of the time
for 3 of 4 seasons, systematic warm bias).

Total influence on `color_harmony` is bounded to ±10%, combined jointly with
the color-affinity adjustment (`services/style_dna/color_families.py`) into a
*single* ±10% envelope (C6 fix) — NOT two independent ±10% adjustments
multiplied together (which would compound to ~21%, `1.10 * 1.10`).
"""

from __future__ import annotations

from typing import Any, Protocol

from attreq_api.services.style_dna.color_families import affinity_adjustment

MAX_INFLUENCE = 0.10
MIN_CONFIDENCE = 0.5  # below this, personal-color influence is exactly zero

# Categories personal color is meaningful for (near-face garments). Not
# currently enforced inside this module — `algorithm.generate_daily_outfits`
# only ever passes the `top` item's dominant Lab in this milestone (bottoms
# excluded per the finalized RI-3 plan's Task 8) — kept here so RI-4+ can
# extend to outerwear/fullbody slots without re-deriving the eligible set.
PERSONAL_COLOR_ELIGIBLE_CATEGORIES = frozenset({"top", "outerwear", "fullbody"})


class _SelfieClassifier(Protocol):
    async def analyze_image(self, image_path: str, prompt: str) -> dict[str, Any]: ...


def is_eligible_slot(role: str) -> bool:
    """Whether a garment role is eligible for the personal-color adjustment."""
    return role in PERSONAL_COLOR_ELIGIBLE_CATEGORIES


def _clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


async def estimate_personal_color(classifier: _SelfieClassifier, selfie_path: str) -> dict[str, float]:
    """One vision-classifier call estimating the two continuous axes + confidence
    from a face photo. All three outputs are clamped defensively regardless of
    what the LLM returns — never trust an unclamped model output into scoring.
    """
    from attreq_api.services.style_dna.prompts import SELFIE_COLOR_PROMPT

    raw = await classifier.analyze_image(selfie_path, SELFIE_COLOR_PROMPT)

    undertone = _clamp(float(raw.get("undertone_warm_cool", 0.0) or 0.0), -1.0, 1.0)
    depth = _clamp(float(raw.get("depth_light_deep", 0.0) or 0.0), -1.0, 1.0)
    confidence = _clamp(float(raw.get("confidence", 0.0) or 0.0), 0.0, 1.0)

    return {
        "undertone_warm_cool": undertone,
        "depth_light_deep": depth,
        "confidence": confidence,
    }


def _item_axis_values(lab: tuple[float, float, float]) -> tuple[float, float]:
    """Cheap Lab -> (undertone, depth) proxy for a single dominant color.

    `b*` sign/magnitude proxies warm (positive, yellow-leaning) vs cool
    (negative, blue-leaning); `L*` proxies light vs deep, using the same
    [-1, 1] convention as the stored `personal_color` axes (+1 = deep/warm,
    -1 = light/cool). Deliberately crude — a single dominant swatch, not a
    full undertone analysis; the ±10% overall cap keeps any error small.
    """
    l_star, _a, b_star = lab
    item_undertone = _clamp(b_star / 60.0, -1.0, 1.0)
    item_depth = _clamp((50.0 - l_star) / 50.0, -1.0, 1.0)
    return item_undertone, item_depth


def _axis_agreement(
    lab: tuple[float, float, float], undertone_pref: float, depth_pref: float
) -> float:
    """Continuous agreement in [-1, 1] between the item's color and the
    user's personal-color axes (cosine-like average, not a hard match/no-match)."""
    item_undertone, item_depth = _item_axis_values(lab)
    agreement = (item_undertone * undertone_pref + item_depth * depth_pref) / 2.0
    return _clamp(agreement, -1.0, 1.0)


def personal_color_adjustment(
    dominant_lab: tuple[float, float, float] | None, personal_color: dict | None
) -> float:
    """pc_adj = MAX_INFLUENCE * axis_agreement * confidence, in [-0.10, 0.10].

    Confidence < `MIN_CONFIDENCE` (or no `personal_color` profile, or no
    dominant Lab to compare against) -> exactly 0.0 — the exit criterion
    ("low/absent-confidence selfie => ~zero personal influence").
    """
    if not personal_color or dominant_lab is None:
        return 0.0

    confidence = float(personal_color.get("confidence", 0.0) or 0.0)
    if confidence < MIN_CONFIDENCE:
        return 0.0

    undertone_pref = float(personal_color.get("undertone_warm_cool", 0.0) or 0.0)
    depth_pref = float(personal_color.get("depth_light_deep", 0.0) or 0.0)

    agreement = _axis_agreement(dominant_lab, undertone_pref, depth_pref)
    adj = MAX_INFLUENCE * agreement * confidence
    return _clamp(adj, -MAX_INFLUENCE, MAX_INFLUENCE)


def apply_personal_color_adjustment(
    base_score: float,
    dominant_lab: tuple[float, float, float] | None,
    color_family: str | None,
    style_dna: dict | None,
) -> float:
    """Combined, jointly-clamped adjustment (C6 fix) applied once to `color_harmony`.

    ```
    pc_adj    = MAX_INFLUENCE * axis_agreement * confidence   # in [-0.10, 0.10]
    aff_adj   = clamp(affinity[family] - 1.0, -0.10, 0.10)
    total_adj = clamp(pc_adj + aff_adj, -0.10, 0.10)           # single ±10% envelope
    adjusted  = clamp(base_score * (1.0 + total_adj), 0.0, 1.0)
    ```

    Worst case (both maxima, same sign) is exactly ±10% — never the ~21% that
    two independent multiplicative ±10% adjustments would compound to
    (`1.10 * 1.10 = 1.21`). Safe to call with `style_dna=None`/empty — returns
    `base_score` unchanged.
    """
    style_dna = style_dna or {}
    personal_color = style_dna.get("personal_color")
    color_affinity = style_dna.get("color_affinity") or {}

    pc_adj = personal_color_adjustment(dominant_lab, personal_color)
    aff_adj = affinity_adjustment(color_family, color_affinity)

    total_adj = _clamp(pc_adj + aff_adj, -MAX_INFLUENCE, MAX_INFLUENCE)
    return _clamp(base_score * (1.0 + total_adj), 0.0, 1.0)
