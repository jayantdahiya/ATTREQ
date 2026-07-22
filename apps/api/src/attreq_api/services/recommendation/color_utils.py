"""Shared color/category classification constants for recommendation + stats.

Extracted from `algorithm.calculate_color_harmony_score` so `services/stats`
can group items by color family without importing the recommendation
algorithm module (avoids a stats -> algorithm import coupling).
"""

NEUTRAL_COLORS = {"white", "black", "gray", "grey", "beige", "cream", "brown"}
WARM_COLORS = {"red", "orange", "yellow", "pink", "coral"}
COOL_COLORS = {"blue", "green", "purple", "teal", "turquoise"}


def color_family(color: str | None) -> str:
    """Classify a color name into a coarse family bucket.

    Returns one of "neutral", "warm", "cool", "other", "unknown".
    """
    c = (color or "").strip().lower()
    if not c:
        return "unknown"
    if c in NEUTRAL_COLORS:
        return "neutral"
    if c in WARM_COLORS:
        return "warm"
    if c in COOL_COLORS:
        return "cool"
    return "other"
