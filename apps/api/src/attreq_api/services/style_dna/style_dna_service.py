"""Style DNA orchestrator service."""

import asyncio
import json
import logging
import uuid
from typing import Any

from fastapi import HTTPException, UploadFile
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from attreq_api.config.settings import settings
from attreq_api.crud.style_dna import style_dna_crud
from attreq_api.models.user import User
from attreq_api.models.wardrobe import WardrobeItem
from attreq_api.services.ai.classifier_factory import get_classifier
from attreq_api.services.storage.file_handler import file_storage
from attreq_api.services.style_dna.prompts import EXTRACTION_PROMPT, SYNTHESIS_PROMPT

logger = logging.getLogger(__name__)


async def process_style_photos(
    db: AsyncSession,
    user: User,
    photo_files: list[UploadFile],
) -> dict[str, Any]:
    """Orchestrate dual-purpose Style DNA extraction + wardrobe seeding.

    Returns dict matching StyleDnaUploadResponse fields.
    """
    if len(photo_files) < settings.style_dna_min_photos:
        raise HTTPException(
            status_code=422,
            detail=f"At least {settings.style_dna_min_photos} photos required",
        )
    if len(photo_files) > settings.style_dna_max_photos:
        raise HTTPException(
            status_code=422,
            detail=f"Maximum {settings.style_dna_max_photos} photos allowed",
        )

    classifier = get_classifier()

    # 1. Save all photos to uploads/style-dna/
    saved_paths: list[tuple[str, str]] = []  # (file_path, file_url)
    for photo in photo_files:
        try:
            file_path, file_url = await file_storage.save_upload_file(
                photo, user.id, subdirectory="style-dna"
            )
            saved_paths.append((file_path, file_url))
        except Exception as e:
            logger.error(f"Failed to save style DNA photo: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to save photo: {str(e)}")

    # 2. Parallel dual-purpose extraction with concurrency cap
    semaphore = asyncio.Semaphore(settings.style_dna_llm_concurrency)

    async def extract(file_path: str) -> dict[str, Any]:
        async with semaphore:
            return await classifier.analyze_image(file_path, EXTRACTION_PROMPT)

    try:
        raw_extractions = await asyncio.gather(
            *[extract(fp) for fp, _ in saved_paths], return_exceptions=True
        )
    except Exception as e:
        logger.error(f"Style DNA extraction failed: {e}")
        raise HTTPException(status_code=500, detail="Style DNA extraction failed")

    # 3. Persist per-photo records
    photo_records = []
    for i, ((file_path, file_url), extraction_result) in enumerate(
        zip(saved_paths, raw_extractions)
    ):
        if isinstance(extraction_result, Exception):
            logger.warning(f"Extraction failed for photo {i}: {extraction_result}")
            photo = await style_dna_crud.create_photo(
                db=db,
                user_id=user.id,
                file_path=file_path,
                file_url=file_url,
                quality_ok=False,
                quality_reason="Extraction failed",
                extraction=None,
            )
        else:
            quality_ok = extraction_result.get("usable", True)
            quality_reason = extraction_result.get("quality_reason")
            photo = await style_dna_crud.create_photo(
                db=db,
                user_id=user.id,
                file_path=file_path,
                file_url=file_url,
                quality_ok=quality_ok,
                quality_reason=quality_reason,
                extraction=extraction_result,
            )
        photo_records.append((extraction_result, photo))

    # 4. Filter usable extractions
    usable_extractions = [
        ext
        for ext, _ in photo_records
        if not isinstance(ext, Exception) and ext.get("usable", True)
    ]

    if len(usable_extractions) < settings.style_dna_min_photos:
        raise HTTPException(
            status_code=422,
            detail=(
                f"Only {len(usable_extractions)} of {len(photo_files)} photos were usable. "
                f"Need at least {settings.style_dna_min_photos}. "
                "Please upload clearer outfit photos."
            ),
        )

    # 5. Synthesis (text-only call using style_signals from usable photos)
    style_signals_list = [e["style_signals"] for e in usable_extractions if "style_signals" in e]
    synthesis_prompt = SYNTHESIS_PROMPT.format(
        n=len(style_signals_list), data=json.dumps(style_signals_list, indent=2)
    )

    try:
        style_dna = await classifier.analyze_text(synthesis_prompt)
    except Exception as e:
        logger.error(f"Style DNA synthesis failed: {e}")
        raise HTTPException(status_code=500, detail="Style DNA synthesis failed")

    # 6. Bulk-insert detected wardrobe items with classification_source = "style_dna_seed"
    all_detected_items = [
        item
        for e in usable_extractions
        for item in e.get("wardrobe_items_detected", [])
        if item.get("confidence", 0) >= 0.6  # only high-confidence items
    ]
    seeded_count = await _bulk_seed_wardrobe(db, user.id, all_detected_items)

    # 7. Write synthesized Style DNA to user.style_preferences
    # 8. Update onboarding_step
    new_step = "review" if not user.onboarding_completed else user.onboarding_step
    await db.execute(
        update(User)
        .where(User.id == user.id)
        .values(
            style_preferences=json.dumps(style_dna),
            onboarding_step=new_step,
        )
    )
    await db.commit()

    # Build photo response list
    photo_response_list = [
        {
            "id": str(p.id),
            "user_id": str(p.user_id),
            "file_path": p.file_path,
            "file_url": p.file_url,
            "quality_ok": p.quality_ok,
            "quality_reason": p.quality_reason,
            "per_photo_extraction": p.per_photo_extraction,
            "created_at": p.created_at,
        }
        for _, p in photo_records
    ]

    return {
        "photos_processed": len(usable_extractions),
        "photos_skipped": len(photo_files) - len(usable_extractions),
        "wardrobe_items_seeded": seeded_count,
        "style_dna": style_dna,
        "photos": photo_response_list,
    }


async def _bulk_seed_wardrobe(
    db: AsyncSession, user_id: uuid.UUID, detected_items: list[dict[str, Any]]
) -> int:
    """Bulk-insert detected wardrobe items from Style DNA photos."""
    if not detected_items:
        return 0

    # Map category hierarchy to WardrobeItem.category field
    category_map = {
        "top": lambda sub: sub or "top",
        "bottom": lambda sub: sub or "bottom",
        "outerwear": lambda sub: sub or "jacket",
        "footwear": lambda sub: sub or "sneakers",
        "accessory": lambda sub: sub or "accessory",
        "dress": lambda sub: "dress",
        "jumpsuit": lambda sub: "jumpsuit",
    }

    items_to_add = []
    for detected in detected_items:
        category = detected.get("category", "top")
        subcategory = detected.get("subcategory", "")
        mapper = category_map.get(category, lambda sub: sub or category)

        item = WardrobeItem(
            user_id=user_id,
            original_image_url="/uploads/style-dna/placeholder.jpg",
            category=mapper(subcategory),
            color_primary=detected.get("color_primary"),
            color_secondary=detected.get("color_secondary"),
            pattern=detected.get("pattern"),
            season=detected.get("season", ["all"]),
            occasion=detected.get("occasion", ["casual"]),
            detection_confidence=detected.get("confidence", 0.7),
            classification_source="style_dna_seed",
            processing_status="completed",
        )
        items_to_add.append(item)

    for item in items_to_add:
        db.add(item)
    await db.commit()

    return len(items_to_add)


async def update_behaviour_weights(
    db: AsyncSession, user_id: uuid.UUID, outfit_id: uuid.UUID, signal: str
) -> bool:
    """Update behaviour_weights in style_preferences JSON based on feedback signal.

    signal: "liked" | "disliked" | "worn"

    Returns:
        True only when the weights were actually mutated and committed; False on
        every early-return (no user, no style_preferences, no outfit, no items).
        Callers use this to decide whether to emit a `style_dna_updated` user event —
        this is a persistence helper, not scoring/algorithm logic.
    """
    from sqlalchemy import select

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user or not user.style_preferences:
        return False

    try:
        style_dna = json.loads(user.style_preferences)
    except (json.JSONDecodeError, TypeError):
        return False

    # Load outfit items
    from attreq_api.models.outfit import Outfit

    outfit_result = await db.execute(select(Outfit).where(Outfit.id == outfit_id))
    outfit = outfit_result.scalar_one_or_none()
    if not outfit:
        return False

    from attreq_api.models.wardrobe import WardrobeItem as WI

    item_ids = [
        i for i in [outfit.top_item_id, outfit.bottom_item_id] if i is not None
    ]
    if not item_ids:
        return False

    items_result = await db.execute(select(WI).where(WI.id.in_(item_ids)))
    items = items_result.scalars().all()

    weights = style_dna.setdefault("behaviour_weights", {})
    category_likes = weights.setdefault("category_likes", {})
    color_likes = weights.setdefault("color_likes", {})
    pattern_likes = weights.setdefault("pattern_likes", {})

    delta = 0.05 if signal in ("liked", "worn") else -0.05

    for item in items:
        if item.category:
            cat = item.category.lower()
            category_likes[cat] = round(
                max(0.0, min(1.0, category_likes.get(cat, 0.5) + delta)), 4
            )
        if item.color_primary:
            col = item.color_primary.lower()
            color_likes[col] = round(
                max(0.0, min(1.0, color_likes.get(col, 0.5) + delta)), 4
            )
        if item.pattern:
            pat = item.pattern.lower()
            pattern_likes[pat] = round(
                max(0.0, min(1.0, pattern_likes.get(pat, 0.5) + delta)), 4
            )

    await db.execute(
        update(User)
        .where(User.id == user_id)
        .values(style_preferences=json.dumps(style_dna))
    )
    await db.commit()

    return True
