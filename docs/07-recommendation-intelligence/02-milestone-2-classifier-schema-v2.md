# RI-2 — Classifier Schema v2 & Deterministic Color Extraction

> **Goal:** Every wardrobe item carries a rich, fixed-vocabulary attribute set (texture, silhouette, neckline, sleeve, statement-vs-basic, per-attribute confidence) and a trustworthy CIELAB color palette extracted from pixels — not from the LLM.
> **Depends on:** RI-1 (tagging benchmark exists, so schema changes are measured, not guessed)
> **Status:** Not started

## Context (self-contained)

- The classifier prompt (identical intent across `apps/api/src/attreq_api/services/ai/{groq,claude,openai,gemini}_classifier.py`; live backend Groq Llama 4 Scout, normalized via `schema_mapper.py`) currently extracts: `category` (flat 20-value list), `color_primary`/`color_secondary` (named colors, **LLM-judged**), `pattern`, `season[]`, `occasion[]`, one global `detection_confidence`.
- `WardrobeItem` (`models/wardrobe.py`) stores those fields as strings/arrays. There is **no texture, silhouette/fit, neckline, sleeve-length, or statement-vs-basic field**, and no per-attribute confidence.
- Color is the least reliable attribute in every model tested (70.3% accuracy even in a dedicated classifier with engineered color features) — yet ATTREQ's `color_harmony` term (40% of the default score) rests entirely on the LLM's named-color guess.
- The image pipeline (`workers/image_processor.py`, `workers/batch_image_processor.py`) already performs background removal (`services/ai/background_removal.py`) before classification — so garment-only pixels are available for deterministic color extraction.
- DeepFashion's ablations rank **texture/pattern and part attributes (neckline, sleeve length, fit) as the most discriminative for downstream tasks; vague "style" adjectives least**. LMLMO's ablation shows *which attributes you ask the LLM for* materially changes downstream compatibility accuracy.
- The launch roadmap's M2 (`docs/05-roadmap/02-milestone-2-data-model-contracts.md`) introduces the slot-prefixed category taxonomy (`tops.*`, `bottoms.*`, `footwear.*`, `outerwear.*`, `fullbody.*`). If M2 is already done, extend it; if not, this milestone must not conflict with it — categories stay out of scope here except the `fullbody` flag below.

## Decisions (pre-made)

- **All new attributes are fixed enums, requested in the same single structured call**, with a per-attribute `confidence` (0–1) block. Multi-task extraction in one call is both cheaper and more accurate than separate calls. *Basis: LMLMO (attribute selection is a first-class modeling decision), FashionNet (multi-task supervision helps every task), M2Fashion (category and attributes mutually reinforcing).*
- **New attribute set** (knowledge-base-derived, prioritizing what carries compatibility signal):
  - `texture`: `smooth | knit | denim | leather | lace | silk_satin | linen | corduroy | wool | fleece | sheer | other`
  - `silhouette`: `fitted | regular | relaxed | oversized | a_line | straight | skinny | wide | crop | longline`
  - `neckline` (tops/fullbody only): `crew | v_neck | scoop | collared | turtleneck | boat | square | off_shoulder | hooded | other | n_a`
  - `sleeve_length` (tops/outerwear/fullbody): `sleeveless | short | three_quarter | long | n_a`
  - `statement_level`: `basic | standard | statement`
  - `formality_score`: integer 1–4 (the LLM's judgment; the algorithm's category-based tiers remain authoritative until RI-5 learns weights)
  - `is_fullbody`: boolean (dress/jumpsuit/romper — cannot be paired top×bottom; consumed by RI-4)
  *Basis: DeepFashion supplementary ablations (texture 59.3% / part 60.2% most discriminative vs style 54.9%); DeepFashion-MultiModal's 12 shape dims as the sanity-check taxonomy scale.*
- **Color moves to pixels.** K-means (k=3) in **CIELAB** over foreground pixels of the background-removed image → 3-color palette with pixel-share weights; `neutral` flag when dominant color has chroma C\* < 15. LLM `color_primary` is kept as a human-readable descriptor and fallback when background removal fails. *Basis: USC/Adobe 2007.02388 (Lab 3-color palettes, chosen for illumination invariance; palettes alone reach 0.84 AUC); fashion-attribute-lab (color = worst LLM/classifier attribute); IJERCSE failure modes (hue undefined on neutrals).*
- **Vocabulary is identical across all four classifier backends** and versioned: add `schema_version` to the classifier output and `wardrobe_items`, so RI-1's benchmark can compare v1 vs v2 and old rows are identifiable. *Basis: LMLMO — the value of LLM tags is that they're standardized.*
- **Expect imperfect tags; design for correction.** Even a good multi-head model gets all attributes right on only ~42% of items. Correction UX must extend to the new fields; corrections emit `item_corrected` events (RI-1) — they are labeled training/eval data. *Basis: fashion-attribute-lab exact-match 41.75%; Pinterest human-in-the-loop.*

## Tasks

### 2.1 Schema + migration

1. **Alembic migration**: add to `wardrobe_items`: `texture`, `silhouette`, `neckline`, `sleeve_length`, `statement_level`, `llm_formality` (smallint), `is_fullbody` (bool), `color_palette` JSONB (`[{lab: [L,a,b], hex, share, is_neutral}]`, dominant first), `color_extraction_source` (`pixel | llm_fallback`), `attribute_confidence` JSONB, `schema_version` (int, default 1; new writes = 2).
2. `models/wardrobe.py`, `schemas/wardrobe.py`: columns + Pydantic enums (single source of truth for the vocabularies in `apps/api/src/attreq_api/schemas/wardrobe_enums.py`, imported by classifiers, schema_mapper, and validators). Unknown enum values from the LLM are coerced to `other`/`n_a` and logged — never stored raw.

### 2.2 Prompt + backends

1. Update `CLASSIFICATION_PROMPT` in all four backend files (`groq_classifier.py`, `claude_classifier.py`, `openai_classifier.py`, `gemini_classifier.py`) to request the v2 fields with the exact enum lists and a `confidence` object per attribute. Ask for category first, then attributes (category conditions attribute reasoning — M2Fashion).
2. `schema_mapper.py`: normalize/validate v2 outputs; per-attribute confidence defaults to `detection_confidence` when a backend omits it.
3. Keep prompts byte-identical in vocabulary across backends; a unit test asserts the enum lists in every prompt match `wardrobe_enums.py`.

### 2.3 Deterministic color extraction

1. New `services/ai/color_extraction.py`: `extract_palette(image_path) -> ColorPalette` — load background-removed RGBA, drop transparent pixels, convert sRGB→CIELAB (implement or use `scikit-image`/`colormath`; add to `apps/api/requirements.txt`), K-means k=3 (fixed seed), output palette with shares, `is_neutral` per color (C\* = √(a\*²+b\*²) < 15), and nearest named color (small Lab-distance lookup table) for display.
2. Wire into `workers/image_processor.py` and `workers/batch_image_processor.py` **after** background removal, **before/parallel with** classification; on background-removal failure fall back to LLM color (`color_extraction_source='llm_fallback'`).
3. Backfill script `apps/api/scripts/backfill_color_palettes.py` for existing items with processed images.

### 2.4 Measure (gate for merging)

1. Extend `scripts/eval_tagging.py` (RI-1) to score the v2 fields against DeepFashion-MultiModal ground truth (shape → silhouette/neckline/sleeve mapping documented in the script).
2. Run v1 vs v2 on the same 500 images, same backend. **Merge rule:** v2 must not regress category/pattern accuracy; record per-field numbers here.
3. Sanity-check pixel color: on ≥50 benchmark images, nearest-named-color from the palette must beat the LLM's `color_primary` against ground truth.

### 2.5 Clients: correction UX for new fields

1. `apps/ios/` item detail/edit screen: editable chips for the new enums (picker per field); corrections `PATCH /api/v1/wardrobe/{id}` and emit `item_corrected` user events. Mirror in `apps/mobile/` if maintained.
2. Low-confidence attributes (< 0.6) render visually flagged ("tap to confirm") — correction-first, not correction-forced; users may skip (noisy labels are acceptable in aggregate — Corbière et al.).

## Out of scope

- Category taxonomy itself (launch roadmap M2). Scoring changes consuming the new fields (RI-3/RI-4). FashionCLIP zero-shot cross-check (RI-6). Garment-detector cropping for multi-garment photos (RI-6). Selfie/undertone analysis (RI-3).

## Exit criteria

- New uploads store v2 attributes + pixel-derived Lab palette + per-attribute confidence; `schema_version=2`.
- All four classifier backends emit the identical vocabulary; the enum-consistency unit test passes.
- Benchmark report exists comparing v1 vs v2 per-field accuracy, with pixel color beating LLM color.
- An item's texture/silhouette is user-correctable on iOS and the correction lands in `user_events`.

## Verification

```bash
cd apps/api
PYTHONPATH=src ../../.venv/bin/alembic upgrade head
PYTHONPATH=src ../../.venv/bin/pytest tests/ -k "classif or color_extraction or schema_mapper or enums"
PYTHONPATH=src ../../.venv/bin/python scripts/eval_tagging.py --backend groq --schema v2 --limit 25
```

New tests: sRGB→Lab conversion against known reference values; neutral flag fires for black/white/gray/navy swatches and not for saturated red; K-means palette deterministic under fixed seed; classifier v2 JSON with an out-of-vocabulary value coerces to `other` and logs; prompt-enum consistency test across the four backends.

Manual: upload a striped navy tee → palette shows navy (neutral-ish/low chroma handled correctly), `pattern=striped`, `sleeve_length=short`, editable in the iOS item screen.
