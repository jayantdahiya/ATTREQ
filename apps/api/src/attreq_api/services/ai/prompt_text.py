"""Shared classifier prompt — single source of truth for all four backends.

`CLASSIFICATION_PROMPT` (v2) is built once from `schemas.wardrobe_enums.*_VALUES`
so the enum lists can never drift from what's actually sent to the LLM — a unit
test (`tests/test_wardrobe_enums.py`) asserts every enum value appears in the
prompt text, and asserts all four classifier modules import this exact object
(`is`, not just equal).

`CLASSIFICATION_PROMPT_V1` is the frozen pre-RI-2 prompt (byte-identical to
what shipped before this milestone), kept only for the RI-1 v1-vs-v2 merge gate
in `scripts/eval_tagging.py` (`--schema v1`) — it measures whether adding the 9
new v2 fields regresses accuracy on the five original fields. Nothing in
production sends `CLASSIFICATION_PROMPT_V1` — do not wire it into a classifier.

Color fields (`color_palette`, `color_extraction_source`) are deliberately
never requested here — color is pixel-derived (`services/ai/color_extraction.py`).
`schema_version` is also never requested — it's a mapper-assigned constant.
"""

from attreq_api.schemas.wardrobe_enums import (
    NECKLINE_VALUES,
    SILHOUETTE_VALUES,
    SLEEVE_LENGTH_VALUES,
    STATEMENT_LEVEL_VALUES,
    TEXTURE_VALUES,
)

CLASSIFICATION_PROMPT_V1 = """You are a wardrobe classification expert. Analyze the clothing item in the image and return ONLY a JSON object with these exact fields:

{
  "category": "<specific type: shirt, jeans, dress, jacket, sweater, pants, coat, blouse, skirt, shorts, t-shirt, hoodie, blazer, cardigan, tank-top, polo, chinos, leggings, jumpsuit, romper>",
  "color_primary": "<main color: black, white, blue, red, green, brown, beige, gray, navy, maroon, pink, purple, yellow, orange, tan, cream>",
  "color_secondary": "<second color or null>",
  "pattern": "<solid, striped, polka-dot, floral, plaid, checkered, paisley, geometric, abstract, printed, embroidered, textured>",
  "season": ["<summer|winter|fall|spring|all>"],
  "occasion": ["<casual|formal|business|party>"],
  "detection_confidence": <0.0 to 1.0>,
  "processing_status": "completed"
}

Return ONLY the JSON object, no markdown, no explanation."""


def _build_v2_prompt() -> str:
    texture_options = " | ".join(TEXTURE_VALUES)
    silhouette_options = " | ".join(SILHOUETTE_VALUES)
    neckline_options = " | ".join(NECKLINE_VALUES)
    sleeve_options = " | ".join(SLEEVE_LENGTH_VALUES)
    statement_options = " | ".join(STATEMENT_LEVEL_VALUES)

    return f"""You are a wardrobe classification expert. Analyze the clothing item in the image and return ONLY a JSON object with these exact fields.

Reason about category first, then attributes — the category conditions how you should interpret texture, silhouette, neckline, and sleeve length (e.g. a "pants" category means neckline/sleeve_length are "n_a").

{{
  "category": "<specific type: shirt, jeans, dress, jacket, sweater, pants, coat, blouse, skirt, shorts, t-shirt, hoodie, blazer, cardigan, tank-top, polo, chinos, leggings, jumpsuit, romper>",
  "color_primary": "<main color: black, white, blue, red, green, brown, beige, gray, navy, maroon, pink, purple, yellow, orange, tan, cream>",
  "color_secondary": "<second color or null>",
  "pattern": "<solid, striped, polka-dot, floral, plaid, checkered, paisley, geometric, abstract, printed, embroidered, textured>",
  "season": ["<summer|winter|fall|spring|all>"],
  "occasion": ["<casual|formal|business|party>"],
  "texture": "<{texture_options}>",
  "silhouette": "<{silhouette_options}>",
  "neckline": "<{neckline_options}> (use n_a for bottoms/footwear/non-neckline garments)",
  "sleeve_length": "<{sleeve_options}> (use n_a for bottoms/footwear/non-sleeved garments)",
  "statement_level": "<{statement_options}>",
  "formality_score": <integer 1-4, 1=very casual, 4=very formal>,
  "is_fullbody": <true if the garment is a single one-piece item covering both top and bottom (e.g. dress, jumpsuit, romper), else false>,
  "detection_confidence": <0.0 to 1.0>,
  "attribute_confidence": {{
    "category": <0.0 to 1.0>,
    "color_primary": <0.0 to 1.0>,
    "pattern": <0.0 to 1.0>,
    "season": <0.0 to 1.0>,
    "occasion": <0.0 to 1.0>,
    "texture": <0.0 to 1.0>,
    "silhouette": <0.0 to 1.0>,
    "neckline": <0.0 to 1.0>,
    "sleeve_length": <0.0 to 1.0>
  }},
  "processing_status": "completed"
}}

Return ONLY the JSON object, no markdown, no explanation."""


CLASSIFICATION_PROMPT: str = _build_v2_prompt()
