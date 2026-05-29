"""CRUD operations for StyleDnaPhoto model."""

from typing import Any
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from attreq_api.models.style_dna import StyleDnaPhoto


class StyleDnaCRUD:
    async def create_photo(
        self,
        db: AsyncSession,
        user_id: UUID,
        file_path: str,
        file_url: str,
        quality_ok: bool,
        quality_reason: str | None,
        extraction: dict[str, Any] | None,
    ) -> StyleDnaPhoto:
        photo = StyleDnaPhoto(
            user_id=user_id,
            file_path=file_path,
            file_url=file_url,
            quality_ok=quality_ok,
            quality_reason=quality_reason,
            per_photo_extraction=extraction,
        )
        db.add(photo)
        await db.commit()
        await db.refresh(photo)
        return photo

    async def get_photos_by_user(self, db: AsyncSession, user_id: UUID) -> list[StyleDnaPhoto]:
        result = await db.execute(
            select(StyleDnaPhoto).where(StyleDnaPhoto.user_id == user_id)
        )
        return list(result.scalars().all())

    async def delete_photos_by_user(self, db: AsyncSession, user_id: UUID) -> int:
        result = await db.execute(
            delete(StyleDnaPhoto).where(StyleDnaPhoto.user_id == user_id)
        )
        await db.commit()
        return result.rowcount


style_dna_crud = StyleDnaCRUD()
