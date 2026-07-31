"""CRUD operations for user_events.

Append-only: no update()/delete() methods exposed. Write methods commit internally
(see crud/recommendation_event.py docstring for why — get_db never commits).
"""

import uuid
from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from attreq_api.models.user_event import UserEvent


class UserEventCRUD:
    """CRUD operations for user_events."""

    async def create(
        self,
        db: AsyncSession,
        *,
        user_id: UUID,
        event_type: str,
        payload: dict[str, Any] | None = None,
    ) -> UserEvent:
        """Insert a new user event row. Commits internally."""
        event = UserEvent(
            id=uuid.uuid4(),
            user_id=user_id,
            event_type=event_type,
            payload=payload,
        )
        db.add(event)
        await db.commit()
        await db.refresh(event)

        return event

    async def list_for_user(
        self,
        db: AsyncSession,
        *,
        user_id: UUID,
        since: datetime | None = None,
        event_types: list[str] | None = None,
        limit: int = 100,
    ) -> list[UserEvent]:
        """List a user's event stream, optionally filtered and limited."""
        query = select(UserEvent).where(UserEvent.user_id == user_id)

        if since is not None:
            query = query.where(UserEvent.created_at >= since)
        if event_types:
            query = query.where(UserEvent.event_type.in_(event_types))

        query = query.order_by(UserEvent.created_at.desc()).limit(limit)

        result = await db.execute(query)
        return list(result.scalars().all())


# Global instance
user_event_crud = UserEventCRUD()
