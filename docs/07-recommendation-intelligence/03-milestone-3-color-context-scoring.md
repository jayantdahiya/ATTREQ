# RI-3 — Color Harmony v2 (CIELAB) & Context Weighting

> **Goal:** `color_harmony` scores pairs the way real outfits actually work — tonal similarity and neutral-anchored contrast in CIELAB — and the context portion of scoring follows the empirically validated occasion > weather > time split.
> **Depends on:** RI-2 (Lab palettes + neutral flags stored on items)
> **Status:** Not started

## Context (self-contained)

- `calculate_color_harmony_score(item1, item2)` (`apps/api/src/attreq_api/services/recommendation/algorithm.py`, ~line 177) currently scores the LLM's **named colors** with hand-authored color-wheel-style rules. Total pair score (~lines 600–606): `color 0.4 + formality 0.4 + preference 0.2` (no Style DNA) or `color 0.20 + formality 0.20 + style_dna 0.40 + behaviour 0.20`.
- The USC/Adobe study of ~53K real outfits found hand-crafted hue templates (Itten/Matsuda) **"deviate significantly" from human judgments**. The two dominant real-world harmony patterns are (1) **tonal similarity** and (2) **contrast anchored by a neutral**. Hue-wheel logic breaks exactly on neutrals (hue undefined at low saturation) — and neutrals (black, white, gray, navy, beige) dominate real closets.
- Weather filtering exists (`filter_items_by_weather`, ~line 30, OpenWeatherMap-driven) and occasion filtering exists (`filter_items_by_occasion`, ~line 89), but there is no principled weighting between occasion, weather, and time-of-day inside the score.
- Style DNA (`services/style_dna/`) stores quiz-derived profile data. There is **no personal-color (undertone) prior** anywhere. Research warns: self-declared color seasons are wrong ~80% of the time for most seasons (KCI study) — a selfie-derived estimate with confidence, or near-zero weight, is the only defensible design.
- After RI-2, every item has `color_palette` (Lab, dominant-first, `is_neutral` flags).

## Decisions (pre-made)

- **`color_harmony = max(tonal, neutral_contrast, hue_rule)`** over dominant palette colors:
  1. **`tonal`** — small hue/chroma difference with adequate lightness contrast: reward when Δh\* and ΔC\* are small **and** 20 ≤ ΔL\* ≤ 60 (same-color-different-shade wins; identical L\* is flat, extreme ΔL\* is fine but scores under neutral_contrast anyway).
  2. **`neutral_contrast`** — if ≥1 item `is_neutral`: score **purely on lightness contrast** (skip hue math entirely). This should be the most common winner — neutrals pair with everything.
  3. **`hue_rule`** — only when **both** items are chromatic: mild bonus for analogous (Δh < 40°) or complementary (150–210°) hues, scaled by chroma. **This branch's ceiling stays below the other two** (cap ~0.85 of max) because wheel templates deviate from real human data.
  *Basis: USC/Adobe 2007.02388 (learned harmony templates from 53K outfits; Matsuda templates rejected); IJERCSE (hue undefined on neutrals — branch on chroma first); RISS EEG study (perceptual response driven by lightness/saturation as much as hue → weight ΔL\* on par with hue).*
- **Secondary palette colors matter for patterned items**: for items whose `pattern != solid`, score against the best-matching palette color, weighted by pixel share.
- **Context mass split: occasion ≈ 0.55, weather ≈ 0.35, time-of-day ≈ 0.10** within whatever weight the context terms carry; weather remains **partly a hard filter** (no shorts at 5°C — keep `filter_items_by_weather`) and partly a score. *Basis: SMARTWEAR — published weights event 50 / weather 30 / age 15 / time 5, 92.4% precision over 600 scenarios; age dropped (Style DNA personalizes instead).*
- **Personal-color prior: two continuous axes (warm↔cool, light↔deep), never four season buckets, total influence ≤ ±10% of `color_harmony`, applied to tops/near-face items only.** Estimated from an optional selfie via the vision classifier **with confidence**; at low confidence the weight stays near zero. **Never from a self-declared season.** *Basis: KCI self-diagnosis study (<20% accuracy for 3 of 4 seasons, systematic warm bias); Ewha line (seasons = warm/cool × light/deep axes measured in Lab); RISS (undertone physiologically grounded, needs photo analysis).*
- **Personal color-preference vector (~12 color families)**: per-user multiplicative affinity, seeded from the Style DNA quiz's loved/avoided colors, updated by simple counting over wear/thumb events per color family (events exist from RI-1). *Basis: Shamoi fuzzy color-aesthetics — personal preference and universal harmony are separable and composable.*
- **Top-level weights stay fixed in this milestone** (0.4/0.4/0.2 and 0.2/0.2/0.4/0.2). Learning them is RI-5; changing inputs and weights simultaneously would make the eval unreadable.

## Tasks

### 3.1 Rewrite color scoring (`algorithm.py`)

1. New module `services/recommendation/color_harmony.py`: `harmony(palette_a, palette_b) -> HarmonyResult` implementing the three-branch max, returning the score **and the winning branch name** (RI-4 explanations consume it). Pure functions over Lab tuples; no DB access.
2. Replace the body of `calculate_color_harmony_score` to read `color_palette` (fallback: legacy named-color path for `schema_version=1` items until backfill completes).
3. Multi-item usage (accessories now; footwear/outerwear after launch-M3): expose `harmony_against_set(item, items)` = mean pairwise harmony, for slot-fill scoring.

### 3.2 Context weighting

1. In `generate_daily_outfits`: introduce an explicit `context_score = 0.55*occasion_match + 0.35*weather_score + 0.10*time_score` where `occasion_match` is formality/occasion-tag fit to the day's occasion, `weather_score` grades season-tag fit for items that *passed* the hard filter, `time_score` is a coarse day/evening factor.
2. Formality-to-occasion match remains the heaviest context term; document in code where `context_score` sits inside the existing weight structure (it refines what `formality`+filters expressed, it does not add a new top-level weight in this milestone).

### 3.3 Personal-color prior

1. `services/style_dna/personal_color.py`: store `undertone_warm_cool: float [-1,1]`, `depth_light_deep: float [-1,1]`, `confidence: float` on the Style DNA profile (migration on the style-DNA table).
2. Optional selfie step in Style DNA onboarding (iOS first): one classifier call (same backend factory) prompted to estimate the two axes + confidence from a face photo; store, never expose as a "season" label. Photo is processed and discarded — not stored (privacy: Echo Look anti-lesson).
3. Apply in scoring: multiplicative adjustment to `color_harmony` for top/outerwear/fullbody items only, magnitude ≤ 0.10 × axis-agreement × confidence.

### 3.4 Personal color-affinity vector

1. On the Style DNA profile: `color_affinity` JSONB (~12 color families: black/white/gray/navy/beige-tan/brown/red/pink-purple/blue/green/yellow-orange/multi). Seed from quiz color questions (`style_dna_service.py`); update with counters from RI-1 events (worn/accepted +1, rejected with `dislike_item` −1) on a nightly job or on-write.
2. Multiply into the pair score the same bounded way (≤ ±10%).

### 3.5 Eval gate

1. Re-run `scripts/eval_outfits.py` (RI-1): the CIELAB scorer must beat the legacy scorer's AUC on the ≥100 human-labeled pairs. Record both numbers here.
2. Add unit fixtures for the canonical cases: black+anything (neutral_contrast wins), navy+camel (neutral contrast, high), burgundy+forest (hue_rule, moderate), light-blue+dark-blue (tonal wins), red+orange low-chroma vs high-chroma.

## Out of scope

- Learned/fitted weights (RI-5). Seeded greedy composition and explanations (RI-4 — but return the winning branch name now). FashionCLIP similarity term (RI-6). Any hue-template expansion beyond the three branches.

## Exit criteria

- `color_harmony` runs on Lab palettes with the neutral-first branch; legacy named-color path only for un-backfilled items.
- Outfit-eval AUC ≥ legacy scorer's AUC on the human-labeled set (numbers recorded in this file).
- A user with a low-confidence or absent selfie gets effectively zero personal-color influence; with high confidence, influence is visible but ≤10%.
- Context scoring follows 0.55/0.35/0.10 and weather hard-filtering still applies.

## Verification

```bash
cd apps/api
PYTHONPATH=src ../../.venv/bin/alembic upgrade head
PYTHONPATH=src ../../.venv/bin/pytest tests/ -k "color_harmony or context or personal_color"
PYTHONPATH=src ../../.venv/bin/python scripts/eval_outfits.py --compare legacy,cielab
```

New tests: three-branch max picks the expected branch per fixture pair above; neutral flag short-circuits hue math; hue_rule ceiling < tonal/neutral ceilings; personal-color adjustment bounded at ±10% and scales with confidence; affinity counter updates from synthetic events.

Manual: wardrobe of mostly black/white/denim → recommendations no longer score near-uniformly (the old wheel logic's degenerate case); a beige chino + white tee pair explains as neutral contrast (branch name present in payload for RI-4).
