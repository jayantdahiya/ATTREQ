"""Morning vibe prompt (RI-5, Task 5.4) — one-tap Sharp/Relaxed/Bold context hint.

Maps a `occasion_hint` query param on `GET /recommendations/daily` to a soft
additive bias on the formality target used inside
`context_scoring.calculate_context_score` (via `composition._base_compatibility`
-> `_apply_weights`'s `formality` slot). Deliberately a *hint*, not a hard
filter — see finalized RI-5 plan Correction 4: "bold" has no natural
formality mapping (party/creative energy isn't a formality axis), so it is
recorded faithfully but mapped near-neutral so it cannot inject noise into a
formality-only interface.
"""

from __future__ import annotations

VALID_OCCASION_HINTS = frozenset({"sharp", "relaxed", "bold"})

# Additive bias on the formality target, roughly in [-1, 1]. Applied inside
# `context_scoring._formality_hint_alignment` as `target = 1.5 + bias * 1.5`
# (0-3 formality scale, 1.5 = neutral midpoint).
VIBE_FORMALITY_BIAS: dict[str, float] = {
    "sharp": 0.6,
    "relaxed": -0.6,
    "bold": 0.1,
}


def formality_bias_for_hint(occasion_hint: str | None) -> float:
    """Resolve a client-supplied `occasion_hint` to its formality bias.

    Unknown/absent/malformed hints resolve to `0.0` (no-op) rather than
    raising — the vibe prompt is optional and skippable by design, so an
    unrecognized value must never break generation.
    """
    if not occasion_hint:
        return 0.0
    return VIBE_FORMALITY_BIAS.get(occasion_hint.lower().strip(), 0.0)
