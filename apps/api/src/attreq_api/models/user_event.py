"""UserEvent model — append-only event stream for the user (Stitch Fix CTSM pattern)."""

import uuid

from sqlalchemy import Column, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.sql import func

from attreq_api.config.database import Base


class UserEvent(Base):
    """One row per user-level lifecycle event.

    Open string `event_type` set — new event types need no migration. Known values
    (not enforced at the DB level): item_added, item_corrected, outfit_shown,
    outfit_accepted, outfit_rejected, outfit_swapped, outfit_worn, style_dna_updated.

    Append-only: no update/delete CRUD, no PUT/PATCH route.
    """

    __tablename__ = "user_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    event_type = Column(String(30), nullable=False)
    payload = Column(JSONB, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    def __repr__(self) -> str:
        return f"<UserEvent(id={self.id}, user_id={self.user_id}, event_type={self.event_type})>"
