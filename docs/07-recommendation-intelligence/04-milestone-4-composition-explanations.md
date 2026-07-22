# RI-4 — Composition Engine & Calibrated Explanations

> **Goal:** Outfits are *generated* (anchor → greedy slot-fill with an explicit composition step), never repeat within a week, deliberately resurface neglected items, handle dresses as first-class outfits — and every recommendation ships a one-line, honestly calibrated explanation.
> **Depends on:** RI-3 (final pair scorer) + launch roadmap M3 (`docs/05-roadmap/03-milestone-3-complete-outfits.md` — footwear/outerwear slots and pools)
> **Status:** Not started

## Context (self-contained)

- After launch-M3, `generate_daily_outfits` (`apps/api/src/attreq_api/services/recommendation/algorithm.py`) scores top×bottom pairs, then attaches footwear/outerwear/accessories per pair. It enumerates **all pairs symmetrically** — there is no anchoring, no explicit decision of *which slots today's outfit needs*, and dresses/jumpsuits (RI-2's `is_fullbody`) have no path at all: they sit in no pool or wrongly in tops.
- Recently-worn exclusion exists (`get_recently_worn_items`, 14-day window) but nothing penalizes *recommending* similar combos on consecutive days, and nothing ever *promotes* neglected items. Competitor evidence says this is the churn point: Acloset's AI degrades into "increasingly unusable combinations" by days 5–7; Whering's Dress Me is dismissed as "a slot wheel". The de facto review benchmark is **"AI dressed me for a week."**
- Recommendations return scores but **no human-readable reason**. XAI research: feature-importance explanations measurably raise acceptance and trust — but explanations of *bad* picks cause overreliance, so low-confidence picks must hedge honestly.
- ~25% of a typical closet is never worn ("grey inventory" — Indyx's published wardrobe data). Resurfacing it is simultaneously recommendation novelty, a sustainability story, and a differentiator.
- RI-1 logs every shown/rejected/worn event; RI-3's `harmony()` returns the winning branch name (`tonal` / `neutral_contrast` / `hue_rule`); Style DNA stores the user's declared style values.

## Decisions (pre-made)

- **Composition before retrieval.** Stage 1 decides today's slot list from context (always top+bottom+footwear-if-owned; outerwear iff temp < 15°C or rain/snow per launch-M3; `fullbody` replaces top+bottom when a dress anchors). Stage 2 fills slots. *Basis: Text2Outfit (composition-generation-then-retrieval); TGNN.*
- **Seeded greedy generation.** Pick 3–5 diverse **anchor items** (weather/occasion-fit, spread across colors/categories, at least one grey-inventory anchor when available), then for each anchor argmax-fill remaining slots with the RI-3 pair scorer (`harmony_against_set` + formality + Style DNA terms). Works with any scorer; no new ML. *Basis: TGNN autoregressive seeded generation; Text2Outfit seed-to-outfit mode.*
- **Full-body branch:** items with `is_fullbody=true` form their own anchor pool; a fullbody anchor consumes both top and bottom slots and pairs only with footwear/outerwear/accessories. *Basis: DeepFashion taxonomy (upper/lower/full-body split — full-body items are not top×bottom pairable).*
- **Anti-repetition is score-level, not just exclusion:** decay penalty on exact items worn/accepted in the last 7 days (beyond the existing 14-day exclusion, which stays) **and** on same top+bottom *combination* in the last 14 days. **Grey-inventory bonus:** items with `wear_count=0` or `last_worn` > 60 days get a bounded promotion (≤ +0.05 total score) and at most one "rediscovery" outfit per day marked as such. *Basis: Acloset day-5–7 decay (churn evidence); Indyx grey inventory (~25% never worn).*
- **Explanations are feature-importance style, from the top 1–2 winning score components, phrased in the user's declared Style DNA values — never counterfactual, never a naked percentage.** Examples: "22°C and sunny + your Classic palette + not worn in 3 weeks", "Navy + camel: strong neutral contrast". *Basis: XAI trust studies (feature-importance > counterfactual; explanations raise acceptance); value-alignment study (match reasoning style to the user's declared values); Wiley CPE survey.*
- **Calibrate, don't inflate.** When total score is below a confidence threshold (sparse wardrobe, forced picks), the explanation hedges: "Experimental pick — tell us what you think", and the payload carries `confidence: low|normal`. *Basis: de Brito Duarte et al. — explanations on unreliable outputs cause overreliance.*
- **Explanations are template-composed server-side from score components — no LLM call.** (An LLM-written rationale is RI-6's optional re-ranker.) Keeps latency flat and the LLM out of the hot loop.
- **Cold-start new garments:** items with no wear/feedback history get scored with a small content-similarity prior toward the user's most-worn items (same category/color-family) instead of neutral defaults. *Basis: DIF (cold items via content similarity to warm items), right-sized to a lookup.*

## Tasks

### 4.1 Composition + generation (`algorithm.py`)

1. New `services/recommendation/composition.py`: `plan_slots(context, wardrobe) -> SlotPlan` (which slots today, fullbody-or-pair decision) and `generate_outfits(slot_plan, pools, scorer, k=3..5)` implementing anchor selection + greedy fill. `generate_daily_outfits` becomes: filters → pools → `plan_slots` → `generate_outfits` → payload.
2. Anchor diversity rule: no two anchors share the same dominant color family and category; at least one grey-inventory anchor when the pool allows.
3. Full-body pool + branch per the decision above; `Outfit` rows for fullbody outfits store the item as `top_item_id` with `bottom_item_id=null` **only if** launch-M3 didn't already add a dedicated column — check the migration head first and prefer a `fullbody_item_id` column if the schema is still open here.

### 4.2 Anti-repetition + grey inventory

1. `services/recommendation/rotation.py`: `repetition_penalty(item_ids, recent_events)` (7-day item decay, 14-day combo match from RI-1 `recommendation_events`/`outfit` history) and `rediscovery_bonus(item)` (wear_count/last_worn based, capped).
2. Wire both into the greedy fill scoring; mark rediscovery outfits in the payload (`rediscovery: true`, with the neglected item id).

### 4.3 Explanations

1. `services/recommendation/explanations.py`: `explain(outfit_candidate, score_components, context, style_dna) -> {text, confidence}`. Ranks components (color branch name from RI-3, formality/occasion fit, weather, rediscovery, Style DNA match), takes top 2, composes from templates keyed by component + user's declared style values; hedging template below threshold.
2. `schemas/recommendation.py`: add `explanation: str`, `confidence: "low"|"normal"`, `rediscovery: bool` to outfit candidate payloads; persist them in RI-1's `shown` events (explanation shown is part of the experiment record).

### 4.4 Clients

1. `apps/ios/` Today screen: render the explanation line under each outfit card; distinct visual treatment for `confidence=low` (hedged copy already in `text`) and for rediscovery outfits ("Not worn in a while — try it with…"). Mirror in `apps/mobile/` if maintained.
2. No new interactions required — reject/accept/swap from RI-1 already capture the response.

### 4.5 The 7-day test (eval gate)

1. New `apps/api/scripts/eval_seven_day.py`: simulate 7 consecutive daily generations for synthetic wardrobes (small 15-item, medium 60, large 200; mocked weather sequence incl. a cold/rainy day), asserting: no repeated top+bottom combo, every outfit weather-valid, footwear present when owned, outerwear present on the cold day, ≥1 rediscovery outfit across the week when grey inventory exists, every outfit has a non-empty explanation.
2. Re-run `scripts/eval_outfits.py`; composition must not regress pair-scorer AUC (it shouldn't touch it — this catches accidental coupling).

## Out of scope

- LLM-written rationales and LLM re-ranking (RI-6). Learned weights (RI-5). Layering beyond one outerwear piece. Packing lists / capsules (RI-7 backlog). Morning vibe prompt (RI-5 — but `plan_slots` takes an `occasion` input now so RI-5 plugs in cleanly).

## Exit criteria

- `eval_seven_day.py` passes for all three synthetic wardrobe sizes.
- A wardrobe containing a dress can receive a dress-anchored outfit (no phantom bottom).
- Every recommendation payload carries `explanation` + `confidence`; low-score picks hedge.
- A never-worn item appears as a marked rediscovery recommendation within the simulated week.

## Verification

```bash
cd apps/api
PYTHONPATH=src ../../.venv/bin/pytest tests/ -k "composition or rotation or explanation or seven_day"
PYTHONPATH=src ../../.venv/bin/python scripts/eval_seven_day.py
PYTHONPATH=src ../../.venv/bin/python scripts/eval_outfits.py --compare cielab,composed
```

New tests: `plan_slots` gates outerwear on temp/condition; fullbody anchor never pairs with a bottom; repetition penalty decays over 7 days and detects repeated combos; rediscovery bonus capped and only for stale items; explanation template selection matches the top-ranked components; hedged copy below threshold.

Manual device pass: 3 consecutive days of real recommendations on iOS → no identical combos, explanation line renders, reject-with-reason still logs (RI-1), a long-unworn item eventually surfaces with rediscovery copy.
