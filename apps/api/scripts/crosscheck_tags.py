#!/usr/bin/env python
"""RI-6 zero-shot cross-check: flag wardrobe items whose LLM-classified
`category`/`pattern` disagrees with a FashionCLIP zero-shot label.

Scoped to `category` and `pattern` ONLY (an intentional scoping choice, not
an oversight): these are the two v1 free-string fields short zero-shot
prompts ("a photo of a <label>") work well against. `season`/`occasion` are
multi-label and noisier for a single-label zero-shot comparison; `texture`
is an RI-2 field with its own fixed vocabulary better checked by a dedicated
future pass, not bundled in here.

The candidate vocabularies below are literal copies of the value lists
already sent to every classifier backend in
`services/ai/prompt_text.py::_build_v2_prompt` (category/pattern are
identical there across all four backends — this script doubles as a
consistency check on that claim). TODO(RI-2): once category/pattern get a
real fixed-vocabulary enum (mirroring texture/silhouette/etc in
`schemas/wardrobe_enums.py`), swap these hardcoded lists for that enum.

Disagreement rule: for a given field, the FashionCLIP top-1 zero-shot label
differs from the stored label AND (top1_similarity - stored_label_similarity)
exceeds `--margin` (default 0.05). A stored label that isn't itself one of
the candidates (off-vocabulary) is treated as similarity 0.0 — see
`check_disagreement`'s docstring for why. Flagged items get
`needs_review=True` and a human-readable `review_reason`.

This script loads the real FashionCLIP model (via
`fashion_embeddings_service`) and is NEVER run in CI (would trigger a first-
use Hugging Face Hub download). It has not been executed against real data
in this sandbox — the compare logic (`check_disagreement`) is unit-tested in
isolation (`tests/test_crosscheck_tags.py`) with fabricated similarity
scores, never a real model. Do not fabricate an agreement-rate baseline;
`eval_results/crosscheck_<timestamp>.json` is only written by an actual run.

Usage:
    python scripts/crosscheck_tags.py --dry-run
    python scripts/crosscheck_tags.py --limit 25 --margin 0.05
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import sys
import time
from pathlib import Path
from uuid import UUID

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

logger = logging.getLogger("crosscheck_tags")

# Keep in sync with services/ai/prompt_text.py::_build_v2_prompt's "category"
# field — identical across all four classifier backends (see module docstring).
CATEGORY_CANDIDATES = [
    "shirt", "jeans", "dress", "jacket", "sweater", "pants", "coat", "blouse",
    "skirt", "shorts", "t-shirt", "hoodie", "blazer", "cardigan", "tank-top",
    "polo", "chinos", "leggings", "jumpsuit", "romper",
]

# Keep in sync with the same prompt's "pattern" field.
PATTERN_CANDIDATES = [
    "solid", "striped", "polka-dot", "floral", "plaid", "checkered",
    "paisley", "geometric", "abstract", "printed", "embroidered", "textured",
]


def check_disagreement(
    stored_label: str | None,
    candidate_sims: dict[str, float],
    margin: float = 0.05,
) -> tuple[bool, str | None]:
    """Pure zero-shot disagreement check — no model, no I/O, unit-testable
    with fabricated similarity scores.

    `candidate_sims` maps each candidate label (lowercased) to its cosine
    similarity against one item's FashionCLIP image embedding. Disagreement
    = the top-1 candidate differs from `stored_label` AND the margin
    (top1_sim - stored_label_sim) exceeds `margin`.

    A `stored_label` that isn't itself in `candidate_sims` (off-vocabulary,
    e.g. free-text drift) is treated as similarity `0.0` — it can't be
    scored against the vocab, so any real top-1 match trivially clears the
    margin and the item gets flagged for review.

    Returns `(disagreement, reason)` — `reason` is a human-readable string
    when `disagreement` is True, else `None`.
    """
    if not candidate_sims:
        return False, None

    top1_label, top1_sim = max(candidate_sims.items(), key=lambda kv: kv[1])
    stored_label_norm = (stored_label or "").strip().lower()
    stored_sim = candidate_sims.get(stored_label_norm, 0.0)

    if top1_label == stored_label_norm:
        return False, None

    if (top1_sim - stored_sim) > margin:
        reason = (
            f"stored={stored_label!r} (sim={stored_sim:.3f}) vs "
            f"top1={top1_label!r} (sim={top1_sim:.3f})"
        )
        return True, reason

    return False, None


def _cosine_sims(image_vector: list[float], label_vectors: dict[str, list[float]]) -> dict[str, float]:
    """Both `fashion_embeddings_service.embed_image`/`embed_texts` L2-normalize
    their output, so cosine similarity is a plain dot product."""
    import numpy as np

    img = np.asarray(image_vector, dtype=float)
    return {label: float(np.dot(img, np.asarray(vec, dtype=float))) for label, vec in label_vectors.items()}


async def _run(args: argparse.Namespace) -> dict:
    from sqlalchemy import select

    from attreq_api.config.database import AsyncSessionLocal
    from attreq_api.models.wardrobe import WardrobeItem
    from attreq_api.services.ai.fashion_embeddings import fashion_embeddings_service
    from attreq_api.services.storage import get_storage

    summary = {"total": 0, "flagged": 0, "category_disagreements": 0, "pattern_disagreements": 0}

    async with AsyncSessionLocal() as db:
        query = select(WardrobeItem).where(WardrobeItem.processing_status == "completed")
        if args.user_id:
            query = query.where(WardrobeItem.user_id == UUID(args.user_id))
        query = query.order_by(WardrobeItem.created_at.asc())
        if args.limit:
            query = query.limit(args.limit)

        result = await db.execute(query)
        items = list(result.scalars().all())
        summary["total"] = len(items)
        logger.info("Found %d completed wardrobe item(s) to cross-check", len(items))

        if args.dry_run:
            logger.info("[dry-run] would cross-check %d item(s); model not loaded", len(items))
            return summary

        storage = get_storage()

        # Text embeddings computed once, cached across every item.
        category_vectors_list = fashion_embeddings_service.embed_texts(
            [f"a photo of a {label}" for label in CATEGORY_CANDIDATES]
        )
        pattern_vectors_list = fashion_embeddings_service.embed_texts(
            [f"a photo of {label} clothing" for label in PATTERN_CANDIDATES]
        )
        if not category_vectors_list or not pattern_vectors_list:
            logger.error("FashionCLIP text embedding failed — aborting cross-check")
            return summary

        category_vectors = dict(zip(CATEGORY_CANDIDATES, category_vectors_list, strict=True))
        pattern_vectors = dict(zip(PATTERN_CANDIDATES, pattern_vectors_list, strict=True))

        import tempfile

        for item in items:
            image_ref = item.processed_image_url or item.original_image_url
            if not image_ref:
                continue
            try:
                image_bytes = await storage.get_file_bytes(image_ref)
                with tempfile.TemporaryDirectory(prefix="attreq_crosscheck_") as tmpdir:
                    tmp_path = str(Path(tmpdir) / "item.png")
                    await asyncio.to_thread(Path(tmp_path).write_bytes, image_bytes)
                    image_vector = await asyncio.to_thread(
                        fashion_embeddings_service.embed_image, tmp_path
                    )
                if image_vector is None:
                    continue

                category_sims = _cosine_sims(image_vector, category_vectors)
                pattern_sims = _cosine_sims(image_vector, pattern_vectors)

                cat_flag, cat_reason = check_disagreement(item.category, category_sims, args.margin)
                pat_flag, pat_reason = check_disagreement(item.pattern, pattern_sims, args.margin)

                if cat_flag:
                    summary["category_disagreements"] += 1
                if pat_flag:
                    summary["pattern_disagreements"] += 1

                if cat_flag or pat_flag:
                    summary["flagged"] += 1
                    reasons = [r for r in (cat_reason, pat_reason) if r]
                    item.needs_review = True
                    item.review_reason = "; ".join(reasons)[:255]

            except Exception as e:
                logger.warning("Failed to cross-check item %s: %s", item.id, e)

        await db.commit()

    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="RI-6 zero-shot tag cross-check")
    parser.add_argument(
        "--dry-run", action="store_true", help="Count candidates without loading the model"
    )
    parser.add_argument("--limit", type=int, default=None, help="Max number of items to process")
    parser.add_argument("--user-id", default=None, help="Restrict to a single user's items")
    parser.add_argument(
        "--margin",
        type=float,
        default=0.05,
        help="Similarity margin required to flag a disagreement (default: 0.05)",
    )
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)
    summary = asyncio.run(_run(args))

    if not args.dry_run:
        results_dir = Path(__file__).resolve().parent.parent / "eval_results"
        results_dir.mkdir(exist_ok=True)
        out_path = results_dir / f"crosscheck_{int(time.time())}.json"
        out_path.write_text(json.dumps(summary, indent=2))
        logger.info("Wrote results to %s", out_path)

    logger.info("Cross-check complete: %s", summary)


if __name__ == "__main__":
    main()
