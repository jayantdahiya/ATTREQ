# Roadmap — Recommendation Intelligence (Phase after Beta Launch) — Overview

> **Status:** Active roadmap (created 2026-07-22)
> **Audience:** Any LLM or developer executing a milestone. Read this file + the single milestone file you are executing. Each milestone file is self-contained — no chat history or other docs needed.
> **Research basis:** Every task in this roadmap is derived from [`docs/04-research/wardrobe-ai-knowledge-base.md`](../04-research/wardrobe-ai-knowledge-base.md) (~75 fetched-and-analyzed sources: papers, engineering blogs, datasets, competitor reviews). Each task cites its evidence as **Basis:** so the reasoning survives without re-reading the research doc.

## Goal of this phase

Take ATTREQ's recommendation engine from "hand-tuned heuristic that works on day 1" to "research-grounded engine that survives the 7-day test":

- **Measure before tuning** — a tagging benchmark and outfit-quality eval harness, plus preference-pair telemetry from day one (the data every later milestone consumes)
- **Tag richer, tag consistently** — expanded fixed-enum classifier schema (texture, silhouette, neckline, sleeve, statement-vs-basic) + deterministic CIELAB color extraction from pixels
- **Score with real color science** — CIELAB tonal/neutral-contrast harmony replacing hue-wheel rules; occasion-dominant context weighting
- **Compose complete, non-repeating outfits with explanations** — seeded greedy generation, anti-repetition, grey-inventory resurfacing, one-line feature-importance explanations
- **Learn instead of hardcode** — Bayesian quiz-prior blend, logistic-regression-fitted scoring weights, swipe deck, morning vibe prompt
- **Add the embedding layer** — FashionCLIP vectors per item (similarity, feedback propagation, tag cross-check) and an optional LLM re-ranker
- **Earn retention** — wardrobe stats (cost-per-wear, forgotten items), multi-photo items, archive-don't-delete, batch capture onboarding

**The benchmark to pass** (the de facto review-video test that killed Acloset and Whering's credibility): 7 consecutive days of practical, non-repeating, weather-appropriate, explained recommendations.

## Relationship to other roadmaps

- [`docs/05-roadmap/`](../05-roadmap/00-roadmap-overview.md) (beta-launch infrastructure) **remains the prerequisite track**. This roadmap assumes its M1 (production backend + R2 storage), M2 (slot-prefixed category taxonomy), and M3 (footwear/outerwear outfit slots) are complete before RI-4 begins. RI-1 and RI-2 can start immediately — they don't depend on the launch roadmap.
- [`docs/06-ios-native/`](../06-ios-native/00-goal.md) is complete; `apps/ios/` (SwiftUI) is the primary client for new UI surfaces, `apps/mobile/` (Expo RN) mirrors where still maintained.

## Milestones

| # | File | Goal (one line) | Depends on | Status |
|---|------|-----------------|------------|--------|
| RI-1 | [01-milestone-1-telemetry-eval-harness.md](01-milestone-1-telemetry-eval-harness.md) | Preference-pair logging, event stream, tagging benchmark, labeled outfit eval set | — | Not started |
| RI-2 | [02-milestone-2-classifier-schema-v2.md](02-milestone-2-classifier-schema-v2.md) | Expanded fixed-enum tag schema + deterministic CIELAB pixel color extraction | RI-1 (benchmark to regression-test against) | Not started |
| RI-3 | [03-milestone-3-color-context-scoring.md](03-milestone-3-color-context-scoring.md) | CIELAB color harmony (tonal / neutral-contrast / hue), personal-color prior, occasion-dominant context weights | RI-2 (Lab colors stored) | Not started |
| RI-4 | [04-milestone-4-composition-explanations.md](04-milestone-4-composition-explanations.md) | Seeded greedy outfit generation, full-body branch, anti-repetition, grey-inventory resurfacing, calibrated explanations | RI-3 + launch roadmap M3 (slots) | Not started |
| RI-5 | [05-milestone-5-adaptive-personalization.md](05-milestone-5-adaptive-personalization.md) | Bayesian quiz-prior blend, fitted scoring weights from preference pairs, swipe deck, morning vibe prompt | RI-1 (accumulated pairs) + RI-4 | Not started |
| RI-6 | [06-milestone-6-embeddings-reranker.md](06-milestone-6-embeddings-reranker.md) | FashionCLIP embedding per item (Weaviate), similarity term, feedback propagation, tag cross-check, optional LLM re-ranker | RI-2; parallel with RI-5 | Not started |
| RI-7 | [07-milestone-7-retention-trust.md](07-milestone-7-retention-trust.md) | Wardrobe stats, multi-photo items, archive-don't-delete, batch-capture onboarding, positioning copy | RI-1 (wear events); parallel with RI-5/RI-6 | Not started |

## Sequencing rationale

1. **RI-1 first, always.** Pinterest's >160% relevance gain came from eval-driven iteration, not one clever model — and every learning milestone (RI-5, RI-6) is starved without preference pairs logged from day one. Telemetry is also the cheapest milestone; nothing else is blocked while it runs.
2. **RI-2 before RI-3.** The CIELAB harmony rewrite scores Lab palettes that don't exist until the extraction pipeline stores them. Both papers behind these milestones agree the classifier schema is a first-class modeling decision — get the inputs right before touching the scoring math.
3. **RI-3 before RI-4.** Composition (greedy slot-filling) calls the pair scorer in a loop; ship the corrected scorer first so composition is tuned against final scoring behavior.
4. **RI-5 after RI-4 and only once RI-1 data has accumulated.** Fitting weights needs ~30–50 accept/reject decisions per user (pooled globally sooner). The Bayesian blend and swipe deck can ship earlier within the milestone; the fitted weights land last.
5. **RI-6 and RI-7 parallelize.** Embeddings touch the upload pipeline + scorer; retention/stats touch clients + read-only queries. Neither blocks the other.

## What NOT to build (explicitly contraindicated at ATTREQ's scale — from the research)

- Per-user GNN/transformer compatibility training (needs tens of thousands of outfits; wardrobes of 50–300 items are 100× too sparse)
- Per-user LLM fine-tuning
- Cross-user matrix factorization before ~hundreds of active users (revisit as Tier-3 once beta cohort exists)
- LLM calls inside the O(tops×bottoms) scoring loop — tag once per item, explain once per recommendation, never per pair
- Ambient/always-on capture, streak mechanics, ad/affiliate-driven recommendations, self-declared color-season as a hard filter

## Tier-3 outlook (not scheduled; revisit after this phase)

Global learned pair-scorer (Polyvore-pretrained OutfitTransformer-style, watching phone-photo domain shift; bootstrap labels via VICTOR's same-category-swap degradation, target = 1 − r/n) · global DPO / biased matrix factorization over pooled feedback · Stitch-Fix-style event-stream user model (CTSM) · pre-purchase "does this fit my wardrobe?" check · concierge digitization tier · human-stylist premium layer · resale/declutter flows.

## Conventions for executing a milestone

- Each milestone file has: **Context** (current state, restated — no chat history needed), **Decisions** (pre-made, with research basis), **Tasks** with exact file paths, **Out of scope**, **Exit criteria**, and **Verification** with concrete commands.
- Every task carries a **Basis:** line naming the research evidence (source + finding) so future maintainers can challenge or update it.
- When a milestone completes: update its Status in the table above.
- Backend commands run from `apps/api/` (pytest, alembic, ruff). iOS builds from `apps/ios/` (Xcode / `xcodebuild`), RN from `apps/mobile/` (`npm run typecheck`, `npm test`). CI must stay green: `.github/workflows/backend-ci.yml`, `.github/workflows/mobile-ci.yml`.
- `apps/web` (Next.js) is **legacy** — no milestone invests in it.
- Keep classifier prompts and enum vocabularies **identical across all classifier backends** (`groq_classifier.py`, `claude_classifier.py`, `openai_classifier.py`, `gemini_classifier.py`) — standardized tags are the property that makes downstream scoring work (LMLMO finding).
