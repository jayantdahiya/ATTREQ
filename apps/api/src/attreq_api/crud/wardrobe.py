"""CRUD operations for wardrobe items."""

from typing import Any
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from attreq_api.models.wardrobe import WardrobeItem


class WardrobeCRUD:
    """CRUD operations for wardrobe items."""

    async def create(
        self, db: AsyncSession, user_id: UUID, original_image_url: str, **kwargs: Any
    ) -> WardrobeItem:
        """Create a new wardrobe item.

        Args:
            db: Database session
            user_id: UUID of the user
            original_image_url: URL of the original uploaded image
            **kwargs: Additional item attributes

        Returns:
            Created wardrobe item
        """
        item = WardrobeItem(
            user_id=user_id,
            original_image_url=original_image_url,
            processing_status="pending",
            **kwargs,
        )

        db.add(item)
        await db.commit()
        await db.refresh(item)

        return item

    async def get_by_id(
        self, db: AsyncSession, item_id: UUID, user_id: UUID | None = None
    ) -> WardrobeItem | None:
        """Get a wardrobe item by ID.

        Args:
            db: Database session
            item_id: UUID of the item
            user_id: Optional user ID to verify ownership

        Returns:
            Wardrobe item or None if not found
        """
        query = select(WardrobeItem).where(WardrobeItem.id == item_id)

        if user_id:
            query = query.where(WardrobeItem.user_id == user_id)

        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def get_by_user(
        self,
        db: AsyncSession,
        user_id: UUID,
        category: str | None = None,
        color: str | None = None,
        season: str | None = None,
        occasion: str | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[list[WardrobeItem], int]:
        """Get all wardrobe items for a user with optional filters.

        Args:
            db: Database session
            user_id: UUID of the user
            category: Optional category filter
            color: Optional color filter (searches both primary and secondary)
            season: Optional season filter
            occasion: Optional occasion filter
            skip: Number of items to skip (for pagination)
            limit: Maximum number of items to return

        Returns:
            Tuple of (list of items, total count)
        """
        # Base query
        query = select(WardrobeItem).where(WardrobeItem.user_id == user_id)

        # Apply filters
        if category:
            query = query.where(WardrobeItem.category == category)

        if color:
            query = query.where(
                or_(WardrobeItem.color_primary == color, WardrobeItem.color_secondary == color)
            )

        if season:
            # PostgreSQL array contains operator
            query = query.where(WardrobeItem.season.contains([season]))

        if occasion:
            # PostgreSQL array contains operator
            query = query.where(WardrobeItem.occasion.contains([occasion]))

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar_one()

        # Apply pagination and ordering
        query = query.order_by(WardrobeItem.created_at.desc()).offset(skip).limit(limit)

        result = await db.execute(query)
        items = result.scalars().all()

        return list(items), total

    async def update(
        self, db: AsyncSession, item_id: UUID, update_data: dict[str, Any]
    ) -> WardrobeItem | None:
        """Update a wardrobe item.

        Args:
            db: Database session
            item_id: UUID of the item
            update_data: Dictionary of fields to update

        Returns:
            Updated item or None if not found
        """
        item = await self.get_by_id(db, item_id)

        if not item:
            return None

        # Update fields
        for field, value in update_data.items():
            if hasattr(item, field):
                setattr(item, field, value)

        await db.commit()
        await db.refresh(item)

        return item

    async def update_processing_status(
        self, db: AsyncSession, item_id: UUID, status: str
    ) -> WardrobeItem | None:
        """Update the processing status of an item.

        Args:
            db: Database session
            item_id: UUID of the item
            status: New status (pending, processing, completed, failed)

        Returns:
            Updated item or None if not found
        """
        return await self.update(db, item_id, {"processing_status": status})

    async def delete(self, db: AsyncSession, item_id: UUID, user_id: UUID) -> bool:
        """Delete a wardrobe item.

        Args:
            db: Database session
            item_id: UUID of the item
            user_id: UUID of the user (for ownership verification)

        Returns:
            True if item was deleted, False if not found
        """
        item = await self.get_by_id(db, item_id, user_id)

        if not item:
            return False

        await db.delete(item)
        await db.commit()

        return True

    async def increment_wear_count(self, db: AsyncSession, item_id: UUID) -> WardrobeItem | None:
        """Increment the wear count for an item.

        Args:
            db: Database session
            item_id: UUID of the item

        Returns:
            Updated item or None if not found
        """
        item = await self.get_by_id(db, item_id)

        if not item:
            return None

        item.wear_count += 1
        await db.commit()
        await db.refresh(item)

        return item


# Global instance
wardrobe_crud = WardrobeCRUD()
