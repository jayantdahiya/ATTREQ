#!/usr/bin/env python
"""RI-6 backfill: compute FashionCLIP embeddings for existing wardrobe items
that predate this milestone (or were uploaded while EMBEDDINGS_ENABLED was
false).

Targets rows where `processing_status == "completed"`, ordered by
`created_at`. For each: resolves `processed_image_url` (falling back to
`original_image_url` when absent — matches the worker's own fallback
convention), fetches the bytes from the configured storage backend, writes
them to a temp file, runs `fashion_embeddings_service.embed_image`, and
upserts the vector into the `ClothingItemVector` Weaviate collection
(`services/ai/embeddings.py`). Idempotent — `upsert_vector` is a
delete-then-insert, so re-running this script is always safe.

Runtime note: model load is a one-time ~5-15s cost; inference is
~100-300ms/image after that. A few hundred items run in roughly 2-10 minutes
on a laptop CPU, mostly I/O-bound on the storage fetch (S3 latency
dominates local disk).

This script loads the real FashionCLIP model (via
`fashion_embeddings_service`) and therefore requires `EMBEDDINGS_ENABLED`-
compatible dependencies (torch/transformers) to actually be installed. It is
NEVER run in CI (would trigger a ~600MB Hugging Face Hub download on first
use) — integration smoke test only, run manually against a real environment.

Usage:
    python scripts/backfill_embeddings.py --dry-run
    python scripts/backfill_embeddings.py --limit 100
    python scripts/backfill_embeddings.py --user-id <uuid>
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import sys
import tempfile
from pathlib import Path
from uuid import UUID

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

logger = logging.getLogger("backfill_embeddings")


async def _run(args: argparse.Namespace) -> dict[str, int]:
    from sqlalchemy import select

    from attreq_api.config.database import AsyncSessionLocal
    from attreq_api.models.wardrobe import WardrobeItem
    from attreq_api.services.ai.embeddings import weaviate_service
    from attreq_api.services.ai.fashion_embeddings import fashion_embeddings_service
    from attreq_api.services.storage import get_storage

    counts = {"processed": 0, "embedded": 0, "skipped": 0, "errors": 0}

    async with AsyncSessionLocal() as db:
        query = select(WardrobeItem).where(WardrobeItem.processing_status == "completed")
        if args.user_id:
            query = query.where(WardrobeItem.user_id == UUID(args.user_id))
        query = query.order_by(WardrobeItem.created_at.asc())
        if args.limit:
            query = query.limit(args.limit)

        result = await db.execute(query)
        items = list(result.scalars().all())

        logger.info("Found %d completed wardrobe item(s) to consider for embedding", len(items))

        if args.dry_run:
            logger.info("[dry-run] would attempt to embed %d item(s); model not loaded", len(items))
            counts["processed"] = len(items)
            return counts

        storage = get_storage()
        if weaviate_service.is_connected():
            weaviate_service.init_vector_schema()

        for item in items:
            counts["processed"] += 1
            image_ref = item.processed_image_url or item.original_image_url
            if not image_ref:
                counts["skipped"] += 1
                continue

            try:
                image_bytes = await storage.get_file_bytes(image_ref)
                with tempfile.TemporaryDirectory(prefix="attreq_embed_backfill_") as tmpdir:
                    tmp_path = str(Path(tmpdir) / "item.png")
                    await asyncio.to_thread(Path(tmp_path).write_bytes, image_bytes)
                    vector = await asyncio.to_thread(
                        fashion_embeddings_service.embed_image, tmp_path
                    )

                if vector is None:
                    counts["skipped"] += 1
                    continue

                if not weaviate_service.is_connected():
                    counts["skipped"] += 1
                    continue

                ok = weaviate_service.upsert_vector(
                    item_id=item.id,
                    user_id=item.user_id,
                    category=item.category,
                    vector=vector,
                )
                if ok:
                    counts["embedded"] += 1
                else:
                    counts["errors"] += 1

                if counts["processed"] % 25 == 0:
                    logger.info(
                        "Progress: %d/%d processed (%d embedded, %d skipped, %d errors)",
                        counts["processed"],
                        len(items),
                        counts["embedded"],
                        counts["skipped"],
                        counts["errors"],
                    )

            except Exception as e:
                counts["errors"] += 1
                logger.warning("Failed to embed item %s: %s", item.id, e)

        logger.info("Backfill complete: %s", counts)

    return counts


def main() -> None:
    parser = argparse.ArgumentParser(description="RI-6 FashionCLIP embedding backfill")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Count candidates without loading the model or calling Weaviate",
    )
    parser.add_argument("--limit", type=int, default=None, help="Max number of items to process")
    parser.add_argument("--user-id", default=None, help="Restrict to a single user's items")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)
    asyncio.run(_run(args))


if __name__ == "__main__":
    main()
