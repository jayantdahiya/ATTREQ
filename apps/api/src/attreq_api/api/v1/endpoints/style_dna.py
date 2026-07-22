"""Style DNA endpoints."""

import contextlib
import json
import logging
import os
import tempfile

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from attreq_api.api.v1.deps import get_current_active_user
from attreq_api.config.database import get_db
from attreq_api.config.settings import settings
from attreq_api.crud.style_dna import style_dna_crud
from attreq_api.models.user import User
from attreq_api.schemas.style_dna import (
    StyleDnaCorrection,
    StyleDnaPhotoResponse,
    StyleDnaProfileResponse,
    StyleDnaUploadResponse,
)
from attreq_api.services.ai.classifier_factory import get_classifier
from attreq_api.services.storage.base import get_file_extension
from attreq_api.services.style_dna.personal_color import estimate_personal_color
from attreq_api.services.style_dna.style_dna_service import process_style_photos

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post(
    "/style-dna/upload",
    response_model=StyleDnaUploadResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_style_photos(
    files: list[UploadFile] = File(..., description="3–8 outfit photos"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Upload outfit photos to extract Style DNA profile and seed wardrobe.

    Accepts 3–8 photos. Each photo undergoes dual-purpose LLM analysis:
    - Style signals extraction (builds the Style DNA profile)
    - Wardrobe item detection (seeds the wardrobe with found items)
    """
    for f in files:
        if not f.content_type or not f.content_type.startswith("image/"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File '{f.filename}' is not an image",
            )

    result = await process_style_photos(db=db, user=current_user, photo_files=files)
    return result


@router.get("/style-dna", response_model=StyleDnaProfileResponse)
async def get_style_dna(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get current Style DNA profile and associated seed photos."""
    style_dna = None
    if current_user.style_preferences:
        try:
            style_dna = json.loads(current_user.style_preferences)
        except (json.JSONDecodeError, TypeError):
            style_dna = None

    photos = await style_dna_crud.get_photos_by_user(db, current_user.id)

    return StyleDnaProfileResponse(
        style_dna=style_dna,
        photos=[StyleDnaPhotoResponse.model_validate(p) for p in photos],
    )


@router.patch("/style-dna", response_model=StyleDnaProfileResponse)
async def update_style_dna(
    correction: StyleDnaCorrection,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Apply manual corrections to the Style DNA profile."""
    if not current_user.style_preferences:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No Style DNA profile found. Upload photos first.",
        )

    try:
        style_dna = json.loads(current_user.style_preferences)
    except (json.JSONDecodeError, TypeError) as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Corrupt Style DNA data") from e

    # Deep merge corrections into existing style_dna
    _deep_merge(style_dna, correction.corrections)

    await db.execute(
        update(User)
        .where(User.id == current_user.id)
        .values(style_preferences=json.dumps(style_dna))
    )
    await db.commit()

    photos = await style_dna_crud.get_photos_by_user(db, current_user.id)
    return StyleDnaProfileResponse(
        style_dna=style_dna,
        photos=[StyleDnaPhotoResponse.model_validate(p) for p in photos],
    )


@router.delete("/style-dna/photos", status_code=status.HTTP_204_NO_CONTENT)
async def delete_style_photos(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Delete all Style DNA seed photos (before re-upload)."""
    deleted = await style_dna_crud.delete_photos_by_user(db, current_user.id)
    logger.info(f"Deleted {deleted} style DNA photos for user {current_user.id}")


@router.post("/style-dna/regenerate", response_model=StyleDnaUploadResponse)
async def regenerate_style_dna(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Re-trigger synthesis from existing stored photos (no new uploads needed)."""
    photos = await style_dna_crud.get_photos_by_user(db, current_user.id)
    usable = [p for p in photos if p.quality_ok and p.per_photo_extraction]

    if len(usable) < settings.style_dna_min_photos:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Only {len(usable)} usable photos stored. Upload new photos first.",
        )

    from attreq_api.services.ai.classifier_factory import get_classifier
    from attreq_api.services.style_dna.prompts import SYNTHESIS_PROMPT

    classifier = get_classifier()
    style_signals_list = [
        p.per_photo_extraction["style_signals"]
        for p in usable
        if "style_signals" in (p.per_photo_extraction or {})
    ]

    import json as _json
    synthesis_prompt = SYNTHESIS_PROMPT.format(
        n=len(style_signals_list), data=_json.dumps(style_signals_list, indent=2)
    )

    try:
        style_dna = await classifier.analyze_text(synthesis_prompt)
    except Exception as e:
        logger.error(f"Style DNA regeneration failed: {e}")
        raise HTTPException(status_code=500, detail="Style DNA synthesis failed") from e

    await db.execute(
        update(User)
        .where(User.id == current_user.id)
        .values(style_preferences=json.dumps(style_dna))
    )
    await db.commit()

    return StyleDnaUploadResponse(
        photos_processed=len(usable),
        photos_skipped=len(photos) - len(usable),
        wardrobe_items_seeded=0,
        style_dna=style_dna,
        photos=[StyleDnaPhotoResponse.model_validate(p) for p in photos],
    )


@router.post("/style-dna/selfie", response_model=StyleDnaProfileResponse)
async def estimate_personal_color_selfie(
    file: UploadFile = File(
        ..., description="A single face photo — analyzed once, then discarded, never stored"
    ),
    consent: bool = Form(
        ...,
        description=(
            "Explicit consent: the photo will be sent to the configured third-party "
            "LLM vendor for one-time undertone/depth analysis and is never persisted"
        ),
    ),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Optional, skippable personal-color estimation from a selfie (RI-3).

    Estimates two continuous axes (warm<->cool undertone, light<->deep) plus a
    confidence score, merged into `style_dna.personal_color`. Confidence-gated
    at scoring time — skipping this step, or a low-confidence result, costs
    the user nothing (influence on recommendations is ~0 either way).

    PRIVACY — read before wiring any client to this route:
    - This is opt-in and feature-flagged (`ENABLE_PERSONAL_COLOR_SELFIE`); the
      caller must also pass explicit per-request `consent=true`.
    - The uploaded photo is a face photo — biometric/sensitive data (GDPR
      special category / BIPA considerations). It IS transmitted to the
      configured third-party classifier vendor (`CLASSIFIER_PROVIDER`) for a
      single analysis call.
    - The photo is NEVER persisted: no `storage.save_image_from_bytes` call
      (contrast with `process_style_photos`, which does store outfit photos),
      no DB row. It is written to a process-local temp file only for the
      duration of the classifier call and deleted in a `finally` block on
      every path, including exceptions.
    - Image bytes and the temp file path are never logged.
    """
    if not settings.enable_personal_color_selfie:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Personal-color selfie estimation is not enabled",
        )
    if not consent:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Explicit consent is required to analyze a selfie photo",
        )
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File must be an image")

    content = await file.read()
    extension = get_file_extension(file.filename or "selfie.jpg")
    tmp_path: str | None = None
    try:
        with tempfile.NamedTemporaryFile(suffix=f".{extension}", delete=False) as tmp:
            tmp.write(content)
            tmp_path = tmp.name

        classifier = get_classifier()
        estimate = await estimate_personal_color(classifier, tmp_path)
    except Exception as e:
        logger.error(
            f"Personal-color selfie estimation failed for user {current_user.id}: {type(e).__name__}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Personal-color estimation failed",
        ) from e
    finally:
        # Never store the photo — delete the temp file on every path, and drop
        # the in-memory bytes reference promptly. Never log `tmp_path` or `content`.
        if tmp_path is not None:
            with contextlib.suppress(OSError):
                os.remove(tmp_path)
        del content

    style_dna: dict = {}
    if current_user.style_preferences:
        try:
            style_dna = json.loads(current_user.style_preferences)
        except (json.JSONDecodeError, TypeError):
            style_dna = {}

    _deep_merge(style_dna, {"personal_color": estimate})

    await db.execute(
        update(User)
        .where(User.id == current_user.id)
        .values(style_preferences=json.dumps(style_dna))
    )
    await db.commit()

    photos = await style_dna_crud.get_photos_by_user(db, current_user.id)
    return StyleDnaProfileResponse(
        style_dna=style_dna,
        photos=[StyleDnaPhotoResponse.model_validate(p) for p in photos],
    )


def _deep_merge(base: dict, updates: dict) -> None:
    """Recursively merge updates into base dict in-place."""
    for key, value in updates.items():
        if key in base and isinstance(base[key], dict) and isinstance(value, dict):
            _deep_merge(base[key], value)
        else:
            base[key] = value
