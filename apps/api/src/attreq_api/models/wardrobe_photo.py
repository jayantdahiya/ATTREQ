"""WardrobeItemPhoto model — additional photos for a wardrobe item."""

import uuid

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from attreq_api.config.database import Base


class WardrobeItemPhoto(Base):
    """Additional photo attached to a wardrobe item (multi-photo gallery)."""

    __tablename__ = "wardrobe_item_photos"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    item_id = Column(
        UUID(as_uuid=True),
        ForeignKey("wardrobe_items.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    original_image_url = Column(String(500), nullable=False)
    processed_image_url = Column(String(500), nullable=True)
    thumbnail_url = Column(String(500), nullable=True)

    # Reserved for future "promote to primary" UI; not used this milestone.
    is_primary = Column(Boolean, nullable=False, default=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    item = relationship("WardrobeItem", back_populates="photos")

    def __repr__(self) -> str:
        return f"<WardrobeItemPhoto(id={self.id}, item_id={self.item_id})>"
