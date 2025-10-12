"""CRUD operations for outfits."""

from datetime import date as date_type
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.outfit import Outfit


class OutfitCRUD:
    """CRUD operations for outfits."""

    async def create(
        self,
        db: AsyncSession,
        user_id: UUID,
        top_item_id: UUID | None = None,
        bottom_item_id: UUID | None = None,
        accessory_ids: list[UUID] | None = None,
        occasion_context: str | None = None,
        weather_context: dict | None = None,
    ) -> Outfit:
        """Create a new outfit.

        Args:
            db: Database session
            user_id: UUID of the user
            top_item_id: UUID of the top clothing item
            bottom_item_id: UUID of the bottom clothing item
            accessory_ids: List of accessory item UUIDs
            occasion_context: Occasion description
            weather_context: Weather data as dict

        Returns:
            Created outfit
        """
        outfit = Outfit(
            user_id=user_id,
            top_item_id=top_item_id,
            bottom_item_id=bottom_item_id,
            accessory_ids=accessory_ids,
            occasion_context=occasion_context,
            weather_context=weather_context,
        )

        db.add(outfit)
        await db.commit()
        await db.refresh(outfit)

        return outfit

    async def get_by_id(
        self,
        db: AsyncSession,
        outfit_id: UUID,
        user_id: UUID | None = None,
        load_items: bool = False
    ) -> Outfit | None:
        """Get an outfit by ID.

        Args:
            db: Database session
            outfit_id: UUID of the outfit
            user_id: Optional user ID to verify ownership
            load_items: Whether to eagerly load related items

        Returns:
            Outfit or None if not found
        """
        query = select(Outfit).where(Outfit.id == outfit_id)

        if user_id:
            query = query.where(Outfit.user_id == user_id)

        if load_items:
            query = query.options(
                selectinload(Outfit.top_item),
                selectinload(Outfit.bottom_item)
            )

        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def get_by_user(
        self,
        db: AsyncSession,
        user_id: UUID,
        skip: int = 0,
        limit: int = 100,
        load_items: bool = False
    ) -> tuple[list[Outfit], int]:
        """Get all outfits for a user.

        Args:
            db: Database session
            user_id: UUID of the user
            skip: Number of items to skip (for pagination)
            limit: Maximum number of items to return
            load_items: Whether to eagerly load related items

        Returns:
            Tuple of (list of outfits, total count)
        """
        # Base query
        query = select(Outfit).where(Outfit.user_id == user_id)

        if load_items:
            query = query.options(
                selectinload(Outfit.top_item),
                selectinload(Outfit.bottom_item)
            )

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar_one()

        # Apply pagination and ordering
        query = query.order_by(Outfit.created_at.desc()).offset(skip).limit(limit)

        result = await db.execute(query)
        outfits = result.scalars().all()

        return list(outfits), total

    async def update_feedback(
        self,
        db: AsyncSession,
        outfit_id: UUID,
        feedback_score: int
    ) -> Outfit | None:
        """Update feedback score for an outfit.

        Args:
            db: Database session
            outfit_id: UUID of the outfit
            feedback_score: Feedback score (-1, 0, 1)

        Returns:
            Updated outfit or None if not found
        """
        outfit = await self.get_by_id(db, outfit_id)

        if not outfit:
            return None

        outfit.feedback_score = feedback_score
        await db.commit()
        await db.refresh(outfit)

        return outfit

    async def mark_as_worn(
        self,
        db: AsyncSession,
        outfit_id: UUID,
        worn_date: date_type | None = None
    ) -> Outfit | None:
        """Mark an outfit as worn on a specific date.

        Args:
            db: Database session
            outfit_id: UUID of the outfit
            worn_date: Date when outfit was worn (defaults to today)

        Returns:
            Updated outfit or None if not found
        """
        outfit = await self.get_by_id(db, outfit_id)

        if not outfit:
            return None

        outfit.worn_date = worn_date or date_type.today()
        await db.commit()
        await db.refresh(outfit)

        return outfit

    async def delete(
        self,
        db: AsyncSession,
        outfit_id: UUID,
        user_id: UUID
    ) -> bool:
        """Delete an outfit.

        Args:
            db: Database session
            outfit_id: UUID of the outfit
            user_id: UUID of the user (for ownership verification)

        Returns:
            True if outfit was deleted, False if not found
        """
        outfit = await self.get_by_id(db, outfit_id, user_id)

        if not outfit:
            return False

        await db.delete(outfit)
        await db.commit()

        return True


# Global instance
outfit_crud = OutfitCRUD()

