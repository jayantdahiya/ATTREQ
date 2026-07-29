"""Calibrated, template-composed explanations (RI-4).

No LLM call — pure f-string templates keyed by score-component name, ranked
by the component's own value. Confidence is calibrated off the POSITIVE
compatibility base (`base_compatibility`: color + formality/context +
style_dna + behaviour), never the rotation-penalized `total` — a good outfit
that merely repeats must not be mislabeled "Experimental" (see
`composition.py`'s score contract, section 5.5 of the finalized plan).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from attreq_api.services.recommendation.composition import OutfitCandidate

CONFIDENCE_THRESHOLD = 0.45  # tuned against base_compatibility; revisit with RI-1 telemetry
LOW_CONFIDENCE_TEXT = "Experimental pick — tell us what you think."

# Only these components are eligible to drive the explanation clause —
# deliberately excludes the aggregate `formality`/`base_compatibility` (would
# duplicate `occasion_fit`/`weather_score`), `time_score` (weakest-evidence,
# low-value copy per context_scoring.py), and the additive adjustment terms
# (`cold_start_bonus`, `rediscovery_bonus`, `rotation_penalty`, `total`) —
# those are surfaced via the rediscovery clause / confidence hedge instead.
RANKABLE_KEYS: tuple[str, ...] = (
    "color_harmony",
    "occasion_fit",
    "weather_score",
    "style_dna",
    "behaviour",
    "preference_bonus",
)

_BRANCH_COPY = {
    "tonal": "a tonal match",
    "neutral_contrast": "strong neutral contrast",
    "hue_rule": "a considered color pairing",
    "none": "an easy color combination",
}


@dataclass(frozen=True)
class ExplanationResult:
    text: str
    confidence: str  # "low" | "normal"


def _core_colors(candidate: OutfitCandidate) -> list[str]:
    if candidate.top_item is not None and candidate.bottom_item is not None:
        colors = [candidate.top_item.color_primary, candidate.bottom_item.color_primary]
    elif candidate.fullbody_item is not None:
        colors = [candidate.fullbody_item.color_primary]
    else:
        colors = []
    return [c for c in colors if c]


def _color_harmony_phrase(candidate: OutfitCandidate, context: dict[str, Any], style_dna: Any) -> str | None:
    colors = _core_colors(candidate)
    branch_copy = _BRANCH_COPY.get(candidate.color_harmony_branch, "a good color combination")
    if len(colors) >= 2:
        pair = f"{colors[0].capitalize()} + {colors[1].capitalize()}"
        return f"{pair}: {branch_copy}"
    if colors:
        return f"{colors[0].capitalize()}: {branch_copy}"
    return branch_copy


def _occasion_fit_phrase(candidate: OutfitCandidate, context: dict[str, Any], style_dna: Any) -> str | None:
    occasion = context.get("occasion") or candidate.occasion
    return f"dialed in for {occasion}" if occasion else None


def _weather_score_phrase(candidate: OutfitCandidate, context: dict[str, Any], style_dna: Any) -> str | None:
    weather = context.get("weather") or candidate.weather or {}
    temp = weather.get("temp")
    condition = weather.get("condition")
    if temp is None:
        return None
    if condition:
        return f"{round(temp)}°C and {condition.lower()}"
    return f"{round(temp)}°C"


def _style_dna_phrase(candidate: OutfitCandidate, context: dict[str, Any], style_dna: Any) -> str | None:
    if not style_dna or not isinstance(style_dna, dict):
        return None
    palette = style_dna.get("color_palette")
    if isinstance(palette, dict):
        dominant = palette.get("dominant")
        if dominant:
            return f"your {dominant[0]} palette"
    aesthetic = style_dna.get("aesthetic")
    if isinstance(aesthetic, dict) and aesthetic.get("label"):
        return f"your {aesthetic['label']} style"
    return "your Style DNA"


def _behaviour_phrase(candidate: OutfitCandidate, context: dict[str, Any], style_dna: Any) -> str | None:
    return "matches how you usually dress"


def _preference_bonus_phrase(candidate: OutfitCandidate, context: dict[str, Any], style_dna: Any) -> str | None:
    return "one of your go-to colors"


_PHRASE_BUILDERS = {
    "color_harmony": _color_harmony_phrase,
    "occasion_fit": _occasion_fit_phrase,
    "weather_score": _weather_score_phrase,
    "style_dna": _style_dna_phrase,
    "behaviour": _behaviour_phrase,
    "preference_bonus": _preference_bonus_phrase,
}


def _rediscovery_phrase(candidate: OutfitCandidate) -> str:
    return "not worn in a while — try it with this"


def explain(
    candidate: OutfitCandidate,
    context: dict[str, Any] | None = None,
    style_dna: Any = None,
) -> ExplanationResult:
    """Rank `candidate.score_components` (restricted to `RANKABLE_KEYS`),
    compose the top 1-2 into a clause each, and append a rediscovery clause
    when the candidate is marked as such. Below `CONFIDENCE_THRESHOLD` on
    `base_compatibility`, returns the hedged copy and `confidence="low"`
    instead — ranking is skipped entirely in that case.
    """
    context = context or {}
    base = candidate.score_components.get("base_compatibility", 0.0)
    if base < CONFIDENCE_THRESHOLD:
        return ExplanationResult(LOW_CONFIDENCE_TEXT, "low")

    ranked = [k for k in RANKABLE_KEYS if k in candidate.score_components]
    ranked.sort(key=lambda k: candidate.score_components[k], reverse=True)
    top_two = ranked[:2]

    clauses: list[str] = []
    for key in top_two:
        clause = _PHRASE_BUILDERS[key](candidate, context, style_dna)
        if clause:
            clauses.append(clause)

    if candidate.rediscovery and candidate.rediscovery_item_id:
        clauses.append(_rediscovery_phrase(candidate))

    text = " + ".join(clauses) if clauses else "A solid pick for today."
    return ExplanationResult(text, "normal")
