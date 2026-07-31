# RI-1 — Feedback Telemetry & Evaluation Harness

> **Goal:** Every recommendation shown to a user produces durable preference data (shown / accepted / rejected / worn, with reasons), and classifier + recommendation quality are measurable offline — before any algorithm tuning happens.
> **Depends on:** Nothing. Start first; every later milestone consumes this data.
> **Status:** Not started

## Context (self-contained)

- The recommendation endpoint (`apps/api/src/attreq_api/api/v1/endpoints/recommendations.py`) generates daily outfit candidates via `generate_daily_outfits` in `apps/api/src/attreq_api/services/recommendation/algorithm.py` and returns them to the client. **Nothing records which candidates were shown.** Only when a user accepts does a row appear — the client materializes an outfit via `POST /api/v1/outfits/` (`endpoints/outfits.py`), which also owns wear tracking and thumbs-style feedback endpoints.
- Consequence: the single highest-value learning signal at small scale — *"user picked/wore outfit A over shown-but-skipped outfit B"* — is currently discarded. Walmart's DPO study showed preference pairs lift compatibility AUC from 57.9% → 81.0%; Stitch Fix built its whole personalization engine on 10B binary ratings.
- The classifier pipeline (`services/ai/clothing_detection.py` → backend chosen by `services/ai/classifier_factory.py`; live backend is Groq Llama 4 Scout in `groq_classifier.py`, with Claude/OpenAI/Gemini alternates) has **no quantitative accuracy evaluation**. Prompt changes ship blind.
- `WardrobeItem` (`models/wardrobe.py`) already has `wear_count` and `last_worn` — wear telemetry exists at item level; what's missing is recommendation-level and outfit-level event capture.
- Free ground-truth data exists: **DeepFashion-MultiModal** (github.com/yumingj/deepfashion-multimodal) has 44K images with manual shape (12 dims), fabric, and color/pattern labels — ideal for scoring a prompted-LLM tagger on people-wearing-clothes photos.

## Decisions (pre-made)

- **Log shown-but-rejected as first-class data, not analytics exhaust.** New tables, not a logging sidecar — this is training data for RI-5. *Basis: DPO (Walmart) AUC 57.9→81.0 from preference pairs; Stitch Fix Style Shuffle; knowledge-base Tier 1 #4.*
- **Model the user as an ordered event stream.** One `user_events` append-only table (event_type + JSON payload) rather than scattering columns — the Stitch Fix CTSM pattern, and time-safe for backtesting later. *Basis: Stitch Fix Client Time Series Model.*
- **Eval harness = offline metrics + human judgments + engagement**, the Pinterest triangle. At current scale "human judgments" means founder/beta-user labeling sessions, scripted. *Basis: Pinterest Shop The Look (>160% cumulative relevance gain from eval-driven iteration).*
- **Benchmark images come from DeepFashion-MultiModal (~500 sampled)**, stored outside the repo (script downloads); ground-truth CSV checked in.
- **Store rejection reasons as a fixed enum** (`too_formal`, `too_casual`, `dont_like_combo`, `weather_wrong`, `wore_recently`, `dislike_item`, `other`) — free text optional. Enum reasons are directly usable as labeled features; they also double as Style DNA feedback.

## Tasks

### 1.1 Schema: recommendation events + preference pairs

1. **Alembic migration** (chain after current head) adding:
   - `recommendation_events`: `id` UUID PK, `user_id` FK, `recommendation_id` UUID (groups one generation batch), `outfit_payload` JSONB (item IDs per slot + all component scores as generated), `rank_shown` int, `event_type` enum (`shown`, `accepted`, `rejected`, `swapped`, `worn`), `rejection_reason` nullable enum (values above), `rejection_note` nullable text, `context` JSONB (weather, occasion, date), `created_at`.
   - `user_events`: `id`, `user_id`, `event_type` (`item_added`, `item_corrected`, `outfit_shown`, `outfit_accepted`, `outfit_rejected`, `outfit_worn`, `style_dna_updated`, …), `payload` JSONB, `created_at`. Append-only; index `(user_id, created_at)`.
2. `models/` + `schemas/`: SQLAlchemy models and Pydantic shapes for both.
3. **Basis:** preference pairs (DPO, Style Shuffle), event-stream user model (Stitch Fix CTSM) — knowledge base §4, §6.

### 1.2 Capture points (backend)

1. `endpoints/recommendations.py`: after generating candidates, write one `shown` event per candidate (batch insert, same `recommendation_id`), including each candidate's component scores (`color`, `formality`, `style_dna`, `behaviour`, total) — these become regression features in RI-5.
2. New endpoint `POST /api/v1/recommendations/{recommendation_id}/feedback`: body `{outfit_index, action: accepted|rejected|swapped, rejection_reason?, rejection_note?, swapped_item_ids?}`. Writes the matching event. Accepting continues to also materialize via `POST /outfits/` (unchanged contract).
3. `endpoints/outfits.py` wear endpoint: additionally emit `outfit_worn` to `user_events`.
4. **Derivation, not duplication:** preference *pairs* (accepted A vs shown-but-skipped B from the same `recommendation_id`) are derived by query at training time — no separate pairs table to keep consistent.

### 1.3 Capture points (clients)

1. `apps/ios/` (primary, SwiftUI): on the Today screen, call the feedback endpoint on reject/skip/swap; add the rejection-reason sheet (one tap, enum chips, optional note). Mirror in `apps/mobile/` if still maintained.
2. Rejection UI must be skippable (a bare `rejected` with no reason is still a valid pair).

### 1.4 Tagging benchmark (offline script, no runtime coupling)

1. New `apps/api/scripts/eval_tagging.py`:
   - Downloads/caches ~500 sampled DeepFashion-MultiModal images + ground-truth labels (sample stratified across shape/fabric/color-pattern classes; seed fixed; manifest CSV checked into `apps/api/tests/fixtures/eval/`).
   - Runs any configured classifier backend (`--backend groq|claude|openai|gemini`) over the sample via the existing `classifier_factory`.
   - Reports **per-field accuracy** (category, color_primary, pattern, season, occasion — and RI-2's new fields once they exist), exact-match rate, and per-field confusion summaries; writes JSON to `apps/api/eval_results/`.
2. Document the baseline numbers in this file when first run (expect color to be the worst field — it was 70.3% even in a dedicated multi-head classifier).
3. **Basis:** DeepFashion/DeepFashion-MultiModal as free eval data; "build the eval triangle before tuning" (Pinterest); fashion-attribute-lab (color worst attribute, exact-match ~42%) — knowledge base §2.

### 1.5 Outfit-quality eval set (human judgments)

1. New `apps/api/scripts/eval_outfits.py`: generates N top×bottom pairs from a seeded synthetic wardrobe (fixtures), renders a labeling CSV/HTML sheet, ingests human good/bad labels back, and reports the current scorer's AUC against those labels.
2. Seed with ~100 founder-labeled pairs; store labels in `apps/api/tests/fixtures/eval/outfit_labels.csv`. Re-run after every scorer change (RI-3, RI-4, RI-5) — this is the regression gate.
3. **Basis:** GPT-4V study methodology (pairwise human judgments as ground truth); Pinterest human-relevance judgments — knowledge base §3, §6.

## Out of scope

- Any change to scoring weights or the algorithm itself (RI-3+). Any model training on the collected pairs (RI-5). Analytics dashboards (RI-7 surfaces stats to users; internal BI is not needed yet). Swipe deck (RI-5).

## Exit criteria

- Generating a daily recommendation writes `shown` events with component scores; rejecting one in the iOS app writes a `rejected` event with an enum reason; wearing writes `worn`.
- A preference-pair query (accepted vs skipped within one `recommendation_id`) returns correct pairs on test data.
- `eval_tagging.py --backend groq` produces per-field accuracy numbers on the 500-image benchmark; results reproducible (fixed seed).
- `eval_outfits.py` reports scorer AUC against ≥100 human labels.

## Verification

```bash
cd apps/api
PYTHONPATH=src ../../.venv/bin/alembic upgrade head
PYTHONPATH=src ../../.venv/bin/pytest tests/ -k "event or telemetry or feedback"
PYTHONPATH=src ../../.venv/bin/python scripts/eval_tagging.py --backend groq --limit 25   # smoke run
```

New tests: recommendation generation inserts one `shown` row per candidate with scores; feedback endpoint validates enum reasons and rejects unknown `recommendation_id`; preference-pair derivation query on a fixture with 1 accepted + 2 shown returns exactly 2 pairs; `user_events` rows are append-only (no update path exposed).

Manual device pass: reject an outfit on the Today screen with reason "too formal" → row visible in `recommendation_events` with `rejection_reason='too_formal'`.
