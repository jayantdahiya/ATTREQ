# RI-6 — FashionCLIP Embeddings & Optional LLM Re-ranker

> **Goal:** Every wardrobe item gets a FashionCLIP embedding at upload (stored in Weaviate), powering a similarity/complementarity scoring term, feedback propagation to near-duplicates, zero-shot tag cross-checks, and a Style-DNA-as-centroid representation — plus an optional bounded LLM re-ranker over the heuristic top-5.
> **Depends on:** RI-2 (background-removed images + v2 tags). Runs in parallel with RI-5/RI-7.
> **Status:** Not started

## Context (self-contained)

- ATTREQ already runs Weaviate: `services/ai/embeddings.py` (`WeaviateEmbeddingsService`, collection `ClothingItem`) connects via `settings.weaviate_host/port`; the compose stack (`infra/docker/compose.api.yml`) includes the service with filesystem backups. What's missing is a **meaningful vector**: no image embedding model is wired into the upload pipeline.
- **FashionCLIP** (Chia et al., Scientific Reports 2022) is CLIP fine-tuned on ~800K Farfetch fashion image–text pairs; open checkpoint `patrickjohncyh/fashion-clip` on Hugging Face, pip package `fashion-clip`; best current checkpoint is **FashionCLIP 2.0** (laion/CLIP-ViT-B-32-laion2B fine-tune). CPU inference is fine at wardrobe scale (one image per upload). It was trained on **white-background product shots** — ATTREQ's background removal (already in `workers/image_processor.py`) is exactly the right preprocessing.
- Research findings this milestone rests on: better item embeddings dominate architecture choice (ViT>CNN replication; CLIP lifting AUC 0.93→0.95 on the same transformer); embeddings enable propagating sparse feedback to visually similar items (Pinterest); **compatibility ≠ similarity** — Zalando's similarity-based pairing drew explicit customer complaints, so the similarity term must be bounded and complementary-aware, never the scorer; LLM judges are usable **re-rankers, not rankers** (GPT-4V only better-than-chance, position-biased).
- Multi-garment/worn photos degrade tagging; DeepFashion2-trained detectors (YOLO/Detectron2 ports) can crop the garment before classification.

## Decisions (pre-made)

- **Model: FashionCLIP 2.0 via the `fashion-clip` pip package**, loaded once per worker process, CPU (or MPS locally). Embed the **background-removed** image. Store the 512-d vector in the existing Weaviate `ClothingItem` collection alongside item id/category. *Basis: FashionCLIP paper + 2.0 checkpoint; trained on clean product shots → background removal first.*
- **Embedding uses, in priority order:**
  1. **Thumbs propagation** — a strong reject (`dislike_item`) softly penalizes cosine-neighbors (top-5, similarity > 0.85) of the disliked item; likes propagate half as strongly. Bounded (≤ ±5% of total score). *Basis: Pinterest visual embeddings; FashionCLIP small-data generalization.*
  2. **Style DNA centroid** — maintain per-user centroid(s) of liked/worn item embeddings (updated online); a candidate item's cosine to the centroid becomes an additional component score, entering the weight fit of RI-5 like any other component. *Basis: FashionCLIP (style vector from 10–20 liked items).*
  3. **Zero-shot tag cross-check** — offline job classifies items zero-shot against the RI-2 enum vocabularies (text prompts per enum value); disagreements with the LLM tags above a margin flag the item for the low-confidence correction UI (RI-2). Not a runtime gate. *Basis: Teaching CLIP some fashion (arbitrary label sets without retraining; hybrid LLM+CLIP pattern).*
  4. **Near-duplicate detection** at upload (similarity > 0.97 warning: "Looks like an item you already have") — protects stat integrity (RI-7). *Basis: Stitch Fix embedding reuse; competitor churn evidence on duplicate items corrupting stats.*
- **No pair-compatibility MLP over embeddings in this milestone.** Similarity is not compatibility (Zalando); a learned pair-scorer over concatenated embeddings is the documented Tier-3 next step once labeled pairs accumulate.
- **LLM re-ranker is optional, feature-flagged, and bounded:** heuristic top-5 candidates → **one** LLM call (existing classifier-factory backend) with each outfit's tags + day context → re-rank + one-sentence rationale. Strict JSON output with validation and one retry (expect ~5–10% malformed); for pairwise judgments evaluate **both orderings** and treat disagreement as a tie; fall back silently to heuristic order + RI-4 template explanation on any failure. Never inside the O(pairs) loop. *Basis: GPT-4V study (weak but real signal; position bias — both-order eval), Amazon EMNLP (strict formats, malformed-output rates, ground output to real item IDs), KG+RAG retrieve-then-rerank.*
- **Garment-detector crop (DeepFashion2-trained, off-the-shelf) ships behind a quality gate:** only applied when the photo contains multiple garments/a worn photo (detector finds >1 box or box ≪ image). Log photo-quality signals per upload either way. *Basis: DeepFashion2 (photo condition drives error; consumer↔shop gap), knowledge base Tier 2 #19.*

## Tasks

### 6.1 Embedding pipeline

1. Add `fashion-clip` (and its torch dependency) to `apps/api/requirements.txt`; new `services/ai/fashion_embeddings.py`: lazy-singleton model load, `embed_image(path) -> list[float]`, `embed_texts(labels) -> ...`.
2. Wire into `workers/image_processor.py` / `batch_image_processor.py` after background removal; upsert vector + item metadata via `services/ai/embeddings.py` (extend the collection schema if needed: item_id, user_id, category, schema_version).
3. Backfill script `apps/api/scripts/backfill_embeddings.py` for existing processed images. Document expected runtime (~minutes on CPU for a few hundred items).

### 6.2 Scoring integrations

1. `services/recommendation/similarity.py`: `neighbors(item_id, k, min_sim)` (Weaviate query), `centroid_score(item, user_centroid)`.
2. Thumbs propagation: consume RI-1 `dislike_item` rejections; penalty map cached per user, applied in the pair scorer (bounded ±5%).
3. Style DNA centroid: maintained on the Style DNA profile (migration: `embedding_centroid` JSONB or Weaviate-side); exposed as a new component score entering RI-5's weight fitting (retrain gate applies).
4. Near-duplicate check in the upload endpoint (`endpoints/wardrobe.py`): warning field in the upload response; client shows a non-blocking "possible duplicate" notice with a merge-photos option (ties into RI-7 multi-photo).

### 6.3 Zero-shot cross-check (offline)

1. `apps/api/scripts/crosscheck_tags.py`: for each item, zero-shot classify category/pattern/texture against enum text prompts; write disagreements (margin > threshold) to a `needs_review` flag on `wardrobe_items`; RI-2's low-confidence UI picks it up.
2. Report cross-check agreement rates against the RI-1 benchmark to decide per-field trust (some fields may be better zero-shot than via LLM — record findings here).

### 6.4 LLM re-ranker (feature-flagged)

1. `services/recommendation/reranker.py`: `rerank(top5_candidates, context) -> ordered + rationales`; settings flag `RERANKER_ENABLED` (default off), strict schema validation + single retry, both-order pairwise tie rule, hard 1-call-per-recommendation budget, full fallback path.
2. When enabled, the LLM rationale replaces RI-4's template explanation **only if** it passes validation and mentions no item the user doesn't own (resolve against candidate item IDs).
3. A/B hook: `shown` events (RI-1) record whether reranker order served, so acceptance rates are comparable.

### 6.5 Garment-detector crop (stretch, gated)

1. Evaluate one off-the-shelf DeepFashion2-trained detector; if quality on ~50 real worn-photo uploads is convincing, wire as a conditional pre-classification crop in `image_processor.py`; else document the negative result here and drop.

## Out of scope

- Learned pair-compatibility MLP / OutfitTransformer-style scorer (Tier-3). Polyvore pretraining. pgvector migration (Weaviate already deployed — don't churn storage). Re-ranking beyond top-5. Any embedding lookup inside the O(tops×bottoms) enumeration (neighbor/centroid scores are precomputed per item per generation, not per pair).

## Exit criteria

- New uploads produce a Weaviate vector; backfill completed for existing items.
- Rejecting an item with `dislike_item` measurably lowers near-duplicate candidates' scores next generation (test with a planted duplicate).
- Centroid component appears in score payloads and in RI-5's fitting features.
- Cross-check job flags LLM/CLIP disagreements into the review UI.
- With the flag on, re-ranker failures never break a recommendation (fallback verified); with it off, zero LLM calls at recommendation time.

## Verification

```bash
cd apps/api
PYTHONPATH=src ../../.venv/bin/pytest tests/ -k "embedding or similarity or centroid or reranker or duplicate"
PYTHONPATH=src ../../.venv/bin/python scripts/backfill_embeddings.py --limit 10
PYTHONPATH=src ../../.venv/bin/python scripts/crosscheck_tags.py --limit 25
```

New tests (Weaviate mocked or test-container): embed→upsert→neighbor roundtrip; propagation bounded and decaying with similarity; centroid update math; reranker malformed-JSON fallback; both-order disagreement → tie; near-duplicate threshold.

Manual: upload the same shirt photo twice → duplicate warning; enable reranker flag locally → rationale text serves, disable → template explanations return.
