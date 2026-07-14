# Milestone 3 — Complete Outfits (Recommendation Quality)

> **Goal:** Recommendations include scored footwear in every outfit and outerwear whenever weather demands it — no more top+bottom+random-accessory outfits.
> **Depends on:** Milestone 2 (slot-prefixed category taxonomy — slot pools are unidentifiable on free-text categories)
> **Status:** Not started

## Context (self-contained)

- `Outfit` model (`apps/api/src/attreq_api/models/outfit.py`) has first-class `top_item_id` and `bottom_item_id` FKs plus a JSON `accessory_ids` list. **No footwear or outerwear fields exist**, so cold-weather recommendations can't include a coat and no outfit includes shoes.
- The recommendation algorithm (`apps/api/src/attreq_api/services/recommendation/algorithm.py`) after M2:
  - Builds `tops` / `bottoms` / `accessories` pools by category prefix.
  - Scores top×bottom pairs: default weights `color_harmony 0.4 + formality 0.4 + preference 0.2`; with Style DNA available, `color 0.20 + formality 0.20 + style_dna 0.40 + behaviour 0.20`.
  - `calculate_formality_score(items)` (line ~238) takes a list of items and scores formality consistency via variance — it already generalizes to >2 items.
  - Accessories are appended via `random.choice(available_accessories)` (~line 611) — unscored.
  - `calculate_color_harmony` scores a pair of colors; recently-worn exclusion comes from `get_recently_worn_items`.
- Weather context (temp, condition) is already available in the recommendation flow (OpenWeather; `weather_unavailable` flag from M2 when absent).
- Taxonomy slots from M2: `footwear.*` (`sneakers`, `boots`, `dress_shoes`, `sandals`, `unknown`) and `outerwear.*` (`jacket`, `coat`, `blazer`, `unknown`). M2's formality map already contains `outerwear.blazer: 3`; this milestone adds the remaining footwear/outerwear entries.
- Mobile renders outfit cards from the daily-recommendation payload and materializes accepted outfits via `POST /api/v1/outfits/` (contract documented in `docs/api-contract.md` from M2).

## Decisions (pre-made)

- **Footwear is always included** when the user owns any footwear; outfits without footwear are still valid for users who haven't uploaded shoes (nullable FK).
- **Outerwear is weather-gated**: included **iff** `temp < 15°C` **or** condition is rain/snow. When gated-in and the user owns outerwear, it is required in the outfit and participates in scoring.
- **Accessories stay in `accessory_ids` JSON** (no schema change) but selection becomes color-harmony-ranked instead of random.
- Total-score weight structure is unchanged; the per-outfit color/formality components simply cover more items.

## Tasks

### 3.1 Schema: outfit slots

1. **Alembic migration** (chain after current head): add to `outfits`:
   - `footwear_item_id` — nullable `UUID`, FK → `wardrobe_items.id`, `ondelete="SET NULL"`
   - `outerwear_item_id` — same shape
2. `models/outfit.py`: columns + relationships (`footwear_item`, `outerwear_item`); `models/wardrobe.py`: back-populates (`outfits_as_footwear`, `outfits_as_outerwear`) consistent with existing top/bottom relationship style.
3. Outfit Pydantic schemas (`apps/api/src/attreq_api/schemas/`): add both fields (nullable) to create/read shapes; update `POST /api/v1/outfits/` materialization in `endpoints/outfits.py`.
4. `get_recently_worn_items` in `algorithm.py`: include footwear/outerwear IDs so recently worn shoes/coats are also rotated out.

### 3.2 Algorithm: slot pools + scoring (`algorithm.py`)

1. **Pools**: `footwear = [i for i in occasion_filtered if i.category.startswith("footwear.")]`, `outerwear = [... "outerwear."]` (exclude recently worn, same as tops/bottoms).
2. **Formality map additions**: `footwear.dress_shoes: 3, footwear.boots: 2, footwear.sneakers: 1, footwear.sandals: 1, outerwear.coat: 2, outerwear.jacket: 1` (blazer=3 exists from M2).
3. **Footwear selection** — per top×bottom candidate pair, pick the best shoe by:
   `shoe_score = 0.5 * avg(color_harmony(shoe, top), color_harmony(shoe, bottom)) + 0.5 * formality_fit`, where `formality_fit = calculate_formality_score([top, bottom, shoe])`. The chosen shoe then joins the pair's formality calculation so the outfit-level `formality_score` covers `[top, bottom, shoe]`.
4. **Outerwear gating** — compute `needs_outerwear = (weather present) and (temp_c < 15 or condition in {rain, snow})`. If `needs_outerwear` and the `outerwear` pool is non-empty: pick best coat by the same color+formality rule against the full base `[top, bottom, shoe]`; coat joins the formality list and contributes its color score. If the pool is empty, proceed without (don't fail the recommendation).
5. **Accessory ranking** — replace `random.choice` (~line 611) with: rank `available_accessories` by `color_harmony(accessory, top)` (tie-break by least-recently-worn) and take the top one. Small change, real quality gain.
6. **Payload**: outfit candidate dicts gain `footwear_item_id`/`footwear_item` and `outerwear_item_id`/`outerwear_item` blocks mirroring the existing `top_item` shape (id, category, color_primary, pattern, image_url, thumbnail_url — run through `resolve_image_url` from M1).

### 3.3 Mobile + contract

1. Outfit/recommendation card components (`apps/mobile/src/`): render footwear and (conditionally) outerwear slots; handle null slots gracefully.
2. Materialization & mutations: pass `footwear_item_id`/`outerwear_item_id` through `POST /outfits/` and wear/feedback calls.
3. Update `docs/api-contract.md` (new fields, nullability, gating semantics) and the assertions in `apps/api/tests/test_client_contracts.py`.

## Out of scope

- Layering beyond one outerwear piece (no base-layer/mid-layer modeling). Suit modeling as a single garment. Shoe-color theory beyond the existing color-harmony function. Web dashboard updates (`apps/web` is legacy).

## Exit criteria

- A recommendation generated with `temp < 15°C` (or rain/snow) for a user who owns outerwear includes an outerwear item.
- Every recommendation for a user who owns footwear includes a scored shoe.
- Accepted outfits persist footwear/outerwear IDs; wear tracking covers them.

## Verification

```bash
cd apps/api
PYTHONPATH=src ../../.venv/bin/alembic upgrade head
PYTHONPATH=src ../../.venv/bin/pytest tests/ -k "algorithm or outfit or contract"
```

New algorithm unit tests with **synthetic wardrobes** (fixtures, mocked weather):
- Cold-day wardrobe containing a coat → recommendation includes `outerwear_item_id`.
- Warm-day → no outerwear even though one is owned.
- Formal occasion with both sneakers and dress shoes owned → dress shoes chosen (no sneakers-with-blazer outfit at formality 3).
- User with zero footwear → recommendation still succeeds with `footwear_item_id: null`.

Manual device pass against the prod VPS: cold-weather city → coat card renders; accept outfit → outfit row in DB has footwear/outerwear IDs.

```bash
cd apps/mobile && npm run typecheck && npm test
```
