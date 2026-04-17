"""Outfit model for ATTREQ application."""

import uuid

from sqlalchemy import Column, Date, DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import ARRAY, JSON, UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from attreq_api.config.database import Base


class Outfit(Base):
    """Outfit model representing combinations of clothing items."""

    __tablename__ = "outfits"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)

    # Foreign key to user
    user_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Clothing item references
    top_item_id = Column(
        UUID(as_uuid=True), ForeignKey("wardrobe_items.id", ondelete="SET NULL"), nullable=True
    )
    bottom_item_id = Column(
        UUID(as_uuid=True), ForeignKey("wardrobe_items.id", ondelete="SET NULL"), nullable=True
    )
    accessory_ids = Column(ARRAY(UUID), nullable=True)  # Array of wardrobe item IDs

    # Outfit metadata
    worn_date = Column(Date, nullable=True, index=True)
    feedback_score = Column(Integer, nullable=True)  # -1 (dislike), 0 (neutral), 1 (like)
    weather_context = Column(JSON, nullable=True)  # Store weather data as JSON
    occasion_context = Column(String(100), nullable=True)  # casual, formal, meeting, party, etc.

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    user = relationship("User", back_populates="outfits")
    top_item = relationship(
        "WardrobeItem", foreign_keys=[top_item_id], back_populates="outfits_as_top"
    )
    bottom_item = relationship(
        "WardrobeItem", foreign_keys=[bottom_item_id], back_populates="outfits_as_bottom"
    )

    def __repr__(self) -> str:
        return (
            f"<Outfit(id={self.id}, user_id={self.user_id}, "
            f"worn_date={self.worn_date}, feedback={self.feedback_score})>"
        )
