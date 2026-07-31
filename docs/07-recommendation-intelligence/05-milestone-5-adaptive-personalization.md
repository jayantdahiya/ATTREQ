# RI-5 — Adaptive Personalization (Learned Weights & Priors)

> **Goal:** The quiz becomes a Bayesian prior that fades as behavior accumulates, the hand-tuned scoring weights are replaced by weights fitted on real accept/reject pairs, and two lightweight surfaces (swipe deck, morning vibe prompt) densify the feedback the learner eats.
> **Depends on:** RI-1 (preference pairs accumulating in production), RI-4 (final score components to fit over)
> **Status:** Not started

## Context (self-contained)

- Scoring today hard-switches weight schemes (`apps/api/src/attreq_api/services/recommendation/algorithm.py` ~lines 600–606): without a Style DNA profile `color 0.4 + formality 0.4 + preference 0.2`; with one, `color 0.20 + formality 0.20 + style_dna 0.40 + behaviour 0.20`. Both sets are hand-tuned constants. Every factorized-scoring paper in the research base (OCMCF, LMLMO-line, DPO) shows **learned aggregation weights beat fixed ones** — this is the pipeline's single weakest link.
- The Style DNA quiz (`services/style_dna/style_dna_service.py`, `endpoints/style_dna.py`) seeds a profile once; behavior weights (`calculate_behaviour_score` in `services/style_dna/scoring.py`) update from feedback, but the quiz's influence never fades — a day-1 quiz answer outweighs a month of contrary behavior.
- Since RI-1, every recommendation writes `shown` events with **per-component scores**, and accepts/rejects/wears are captured with reasons. Preference pairs (chosen A vs skipped B in the same batch) are derivable by query. Walmart's DPO result (compatibility AUC 57.9% → 81.0% from preference pairs) and Stitch Fix's 10B-rating Style Shuffle game both indicate pairwise signal is the highest-value data at small scale; ~30–50 decisions per user suffice for *reweighting* (not full model training).
- Nothing elicits context at decision time: the daily recommendation guesses occasion. RI-4's `plan_slots(context, …)` already accepts an `occasion` input.

## Decisions (pre-made)

- **Quiz → Bayesian prior blend:** `effective_pref = (k·quiz_vector + n·behaviour_vector) / (k + n)` with **k = 15 pseudo-observations** (mid of the research's 10–20 range), n = count of feedback events. Quiz dominates day 1, fades automatically; no hard switch, no cliff. Applied wherever the profile feeds `calculate_style_dna_score`/`calculate_behaviour_score`. *Basis: HBMFSI (side information as prior on latent factors, largest gains at fewest observations); knowledge base Tier 2 #13.*
- **Fit the aggregation weights with Bradley–Terry / logistic regression over score-component differences.** For each preference pair (A chosen over B), the feature vector is `components(A) − components(B)` (color, formality, style_dna, behaviour, context, rediscovery); fit logistic regression; the learned coefficients (normalized, non-negative-clipped) become the scoring weights. **Global (pooled anonymized) first**; per-user refit only for users with ≥ 30 decisions, shrunk toward the global weights. *Basis: OCMCF (learned per-factor aggregation beats fixed weighted sum); DPO/Decoding Style; Understanding Latent Style (per-user evaluation discipline); "~30–50 decisions is enough for reweighting".*
- **Weights update offline, ship as data.** A scheduled job (or manually-run script at beta scale) refits and writes a `scoring_weights` row (global) / per-user override; the algorithm reads current weights with the hand-tuned constants as fallback. **No fitting in the request path.** *Basis: keep the LLM/ML out of the hot loop (VICTOR cost-profile lesson).*
- **Swipe deck ("rate 5 outfits")**: a daily, optional, seconds-long deck of generated outfit pairs to rate 👍/👎. Each rating is a `user_events` row and a preference observation with **equal weight for negative signal**. No streaks, no guilt mechanics. *Basis: Stitch Fix Style Shuffle (10B ratings; players measurably more satisfied; positive and negative weighted equally); competitor evidence — streaks "create unnecessary pressure".*
- **One-tap morning vibe prompt** on the Today screen: "Today's vibe: Sharp / Relaxed / Bold?" (skippable, remembered per day). Maps to the `occasion`/formality context input of RI-4's `plan_slots`; each answer is also a labeled preference event. *Basis: Computer Journal LLM+KG (conversational elicitation sidesteps decision-time cold start); knowledge base Tier 2 #18.*
- **Per-category-pair weight sets are deferred** until pooled data volume justifies them (Tier-3 candidate). *Basis: type-specific compatibility spaces (KU Leuven) — right idea, needs more data than beta provides.*
- **Evaluate per-user, not globally:** the eval metric is user-conditioned AUC on held-out pairs (a model that only learns popularity must not look good). *Basis: Stitch Fix Latent Style evaluation discipline.*

## Tasks

### 5.1 Bayesian quiz blend

1. `services/style_dna/scoring.py`: refactor profile consumption to compute `effective_pref` from `(quiz_vector, behaviour_vector, n_events, k=15)`; `n_events` counted from RI-1 `user_events` (cached on profile, incremented on write).
2. Remove the hard weight-scheme switch predicated on "profile exists": the Style DNA term is always present, its *content* blends; users with no quiz get `quiz_vector = neutral`, so behavior alone drives it.
3. Unit-test the blend limits: n=0 → pure quiz; n→large → behavior dominates; k=15 crossover behavior.

### 5.2 Fitted scoring weights

1. New `services/recommendation/weight_fitting.py` + script `apps/api/scripts/fit_scoring_weights.py`:
   - Query preference pairs from `recommendation_events` (accepted/worn vs shown-but-skipped within batch; rejects with reason `weather_wrong` excluded — that's a context failure, not a taste signal).
   - Build component-difference features (components stored on `shown` events by RI-1), fit sklearn `LogisticRegression` (add `scikit-learn` to `apps/api/requirements.txt`; already required if RI-2 used scikit-image K-means — verify), clip negatives, normalize to sum 1.
   - Write to new `scoring_weights` table (migration): `scope` (`global` | user_id), `weights` JSONB, `fitted_on_n_pairs`, `holdout_user_auc`, `created_at`. Refuse to publish if holdout user-conditioned AUC ≤ the current active weights' AUC.
2. `algorithm.py`: read active weights (global, overridden per-user when present) with the current constants as ultimate fallback; log which weight set served each recommendation into the `shown` event context.
3. Per-user refit: only ≥30 decisions; shrink toward global: `w_user = (m·w_fit + λ·w_global)/(m+λ)`, λ=20.

### 5.3 Swipe deck

1. Backend: `GET /api/v1/recommendations/swipe-deck` (5 generated outfit candidates, reusing RI-4 generation with diversity turned up and repetition rules relaxed) and ratings posted through the RI-1 feedback endpoint (`action: liked|disliked`, new enum values on `recommendation_events.event_type` or reuse accepted/rejected with `source: swipe_deck` in context).
2. `apps/ios/`: swipe/tap deck surface (entry point on Today screen, "Rate a few looks"), hard-capped at 5/day, closable mid-deck. Mirror in `apps/mobile/` if maintained.

### 5.4 Morning vibe prompt

1. `apps/ios/` Today screen: one-tap chip row (Sharp / Relaxed / Bold / skip) before first generation of the day; selection passed as `occasion_hint` query param to the recommendation endpoint.
2. Backend: `occasion_hint` maps to formality targets in RI-4's `plan_slots` context; the answer is stored in the day's `shown` events context and as a `user_events` row.

### 5.5 Eval gate

1. Extend `scripts/eval_outfits.py` with `--weights fitted`: fitted weights must beat hand-tuned weights on held-out preference pairs (user-conditioned AUC), and must not regress the human-labeled outfit set. Record both numbers here before enabling fitted weights by default.

## Out of scope

- DPO / matrix-factorization / any neural model over pooled feedback (Tier-3; needs hundreds of active users). Per-user LLM anything. Per-category-pair weights (deferred, above). Embedding-based feedback propagation (RI-6).

## Exit criteria

- A new user's recommendations are quiz-driven; after ~50 feedback events the behavior vector demonstrably dominates (blend test).
- `fit_scoring_weights.py` produces global weights with holdout user-AUC > hand-tuned baseline, and the serving path uses them (with fallback).
- Swipe deck ratings and vibe answers land as events and enter the next fit.
- No fitting/training happens in any request path.

## Verification

```bash
cd apps/api
PYTHONPATH=src ../../.venv/bin/alembic upgrade head
PYTHONPATH=src ../../.venv/bin/pytest tests/ -k "blend or weight_fitting or swipe or vibe"
PYTHONPATH=src ../../.venv/bin/python scripts/fit_scoring_weights.py --dry-run   # on seeded synthetic pairs
PYTHONPATH=src ../../.venv/bin/python scripts/eval_outfits.py --weights fitted --metric user_auc
```

New tests: blend math at n=0/15/1000; pair extraction excludes `weather_wrong` rejects; fitting on synthetic pairs with a known planted preference recovers the planted weight ordering; publish-guard refuses on AUC regression; per-user shrinkage bounded; `occasion_hint` shifts formality targets in `plan_slots`.

Manual device pass: answer "Sharp" → visibly more formal candidates; rate a swipe deck → events present; run the fit script → new `scoring_weights` row with metrics.
