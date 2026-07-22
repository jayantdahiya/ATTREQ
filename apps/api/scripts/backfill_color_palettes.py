#!/usr/bin/env python
"""RI-2 backfill: extract deterministic CIELAB color palettes for existing
wardrobe items that predate pixel color extraction.

Targets rows where `color_palette IS NULL AND processed_image_url IS NOT NULL
AND processing_status = 'completed'` — i.e. items that finished the AI
pipeline before this milestone shipped. For each, fetches the already
background-removed `processed_image_url` from storage, runs
`extract_palette`, and writes `color_palette` + `color_extraction_source =
"pixel"` back.

Deliberately does NOT bump `schema_version` — that field tracks the
*attribute* schema (texture/silhouette/etc, which this backfill does not
populate), not the color source. A color-only-backfilled row stays
`schema_version=1` until it's re-classified with the v2 prompt.

Also (optionally) recomputes `is_fullbody` from `category` for existing rows,
since that's a pure function of already-stored data and costs nothing extra
to backfill alongside the color pass.

Writing to the ORM object directly (not via `wardrobe_crud.update()`) still
triggers the `updated_at` column's `onupdate=func.now()` default on flush —
this backfill accepts that "recently added" wardrobe views will re-sort
accordingly (the plan's documented alternative to fighting the ORM's dirty-
tracking to preserve the old timestamp, which is fragile: reassigning the
same value doesn't reliably suppress `onupdate` across SQLAlchemy versions).

Pure local CPU work (PIL + numpy + scikit-learn) — no rate limiting needed.

Usage:
    python scripts/backfill_color_palettes.py --dry-run
    python scripts/backfill_color_palettes.py --limit 100
    python scripts/backfill_color_palettes.py --user-id <uuid>
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

logger = logging.getLogger("backfill_color_palettes")

_COMMIT_EVERY = 50


async def _run(args: argparse.Namespace) -> None:
    from sqlalchemy import select

    from attreq_api.config.database import AsyncSessionLocal
    from attreq_api.models.wardrobe import WardrobeItem
    from attreq_api.schemas.wardrobe_enums import FULLBODY_CATEGORIES
    from attreq_api.services.ai.color_extraction import extract_palette
    from attreq_api.services.storage import get_storage

    storage = get_storage()

    async with AsyncSessionLocal() as db:
        query = select(WardrobeItem).where(
            WardrobeItem.color_palette.is_(None),
            WardrobeItem.processed_image_url.isnot(None),
            WardrobeItem.processing_status == "completed",
        )
        if args.user_id:
            query = query.where(WardrobeItem.user_id == UUID(args.user_id))
        query = query.order_by(WardrobeItem.created_at.asc())
        if args.limit:
            query = query.limit(args.limit)

        result = await db.execute(query)
        items = list(result.scalars().all())

        logger.info("Found %d wardrobe item(s) needing a color-palette backfill", len(items))

        processed = 0
        failed = 0
        since_commit = 0

        for item in items:
            try:
                image_bytes = await storage.get_file_bytes(item.processed_image_url)
                with tempfile.TemporaryDirectory(prefix="attreq_backfill_") as tmpdir:
                    tmp_path = str(Path(tmpdir) / "processed.png")
                    await asyncio.to_thread(Path(tmp_path).write_bytes, image_bytes)
                    palette = await asyncio.to_thread(extract_palette, tmp_path)

                color_palette_json = [
                    {
                        "lab": list(color.lab),
                        "hex": color.hex,
                        "share": color.share,
                        "is_neutral": color.is_neutral,
                        "name": color.name,
                    }
                    for color in palette.colors
                ]

                is_fullbody = bool(
                    item.category and item.category.lower() in FULLBODY_CATEGORIES
                )

                if args.dry_run:
                    logger.info(
                        "[dry-run] item %s -> dominant=%s share=%.2f is_neutral=%s",
                        item.id,
                        color_palette_json[0]["name"] if color_palette_json else None,
                        color_palette_json[0]["share"] if color_palette_json else 0.0,
                        color_palette_json[0]["is_neutral"] if color_palette_json else None,
                    )
                else:
                    item.color_palette = color_palette_json
                    item.color_extraction_source = "pixel"
                    item.is_fullbody = is_fullbody
                    since_commit += 1
                    if since_commit >= _COMMIT_EVERY:
                        await db.commit()
                        since_commit = 0

                processed += 1
                if processed % 25 == 0:
                    logger.info("Progress: %d/%d processed (%d failed)", processed, len(items), failed)

            except Exception as e:
                failed += 1
                logger.warning("Failed to backfill item %s: %s", item.id, e)

        if not args.dry_run and since_commit > 0:
            await db.commit()

        logger.info(
            "Backfill complete: %d processed, %d failed, dry_run=%s",
            processed,
            failed,
            args.dry_run,
        )


def main() -> None:
    parser = argparse.ArgumentParser(description="RI-2 color-palette backfill")
    parser.add_argument("--dry-run", action="store_true", help="Log what would change, write nothing")
    parser.add_argument("--limit", type=int, default=None, help="Max number of items to process")
    parser.add_argument("--user-id", default=None, help="Restrict to a single user's items")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)
    asyncio.run(_run(args))


if __name__ == "__main__":
    main()
