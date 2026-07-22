"""CRUD operations for wardrobe item photos (multi-photo gallery)."""

from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from attreq_api.models.wardrobe_photo import WardrobeItemPhoto


class WardrobeItemPhotoCRUD:
    """CRUD operations for wardrobe item photos."""

    async def create(
        self, db: AsyncSession, item_id: UUID, original_image_url: str
    ) -> WardrobeItemPhoto:
        """Create a new photo row for a wardrobe item (always non-primary)."""
        photo = WardrobeItemPhoto(
            item_id=item_id,
            original_image_url=original_image_url,
            is_primary=False,
        )
        db.add(photo)
        await db.commit()
        await db.refresh(photo)
        return photo

    async def get_by_id(
        self, db: AsyncSession, photo_id: UUID, item_id: UUID | None = None
    ) -> WardrobeItemPhoto | None:
        """Get a photo by ID, optionally scoped to a specific item."""
        query = select(WardrobeItemPhoto).where(WardrobeItemPhoto.id == photo_id)
        if item_id is not None:
            query = query.where(WardrobeItemPhoto.item_id == item_id)
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def get_by_item(self, db: AsyncSession, item_id: UUID) -> list[WardrobeItemPhoto]:
        """Get all photos for a wardrobe item, oldest first."""
        query = (
            select(WardrobeItemPhoto)
            .where(WardrobeItemPhoto.item_id == item_id)
            .order_by(WardrobeItemPhoto.created_at)
        )
        result = await db.execute(query)
        return list(result.scalars().all())

    async def update(
        self, db: AsyncSession, photo_id: UUID, update_data: dict[str, Any]
    ) -> WardrobeItemPhoto | None:
        """Update fields on a photo row (e.g. processed/thumbnail URLs)."""
        photo = await self.get_by_id(db, photo_id)
        if not photo:
            return None

        for field, value in update_data.items():
            if hasattr(photo, field):
                setattr(photo, field, value)

        await db.commit()
        await db.refresh(photo)
        return photo

    async def delete(self, db: AsyncSession, photo_id: UUID) -> bool:
        """Delete a photo row."""
        photo = await self.get_by_id(db, photo_id)
        if not photo:
            return False

        await db.delete(photo)
        await db.commit()
        return True


# Global instance
wardrobe_photo_crud = WardrobeItemPhotoCRUD()
