"""Wardrobe item model for ATTREQ application."""

import uuid

from sqlalchemy import ARRAY, Column, Date, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from attreq_api.config.database import Base


class WardrobeItem(Base):
    """WardrobeItem model representing clothing items in user's wardrobe."""

    __tablename__ = "wardrobe_items"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)

    # Foreign key to user
    user_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Image URLs
    original_image_url = Column(String(500), nullable=False)
    processed_image_url = Column(String(500), nullable=True)
    thumbnail_url = Column(String(500), nullable=True)

    # AI-detected attributes
    category = Column(String(100), nullable=True, index=True)  # shirt, jeans, dress, etc.
    color_primary = Column(String(50), nullable=True, index=True)
    color_secondary = Column(String(50), nullable=True)
    pattern = Column(String(50), nullable=True)  # solid, striped, floral, etc.
    season = Column(ARRAY(String), nullable=True)  # summer, winter, monsoon, all
    occasion = Column(ARRAY(String), nullable=True)  # casual, formal, party

    # AI processing metadata
    detection_confidence = Column(Float, nullable=True)
    processing_status = Column(
        String(20), nullable=False, default="pending", index=True
    )  # pending, processing, completed, failed

    # Usage tracking
    wear_count = Column(Integer, nullable=False, default=0)
    last_worn = Column(Date, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    user = relationship("User", back_populates="wardrobe_items")

    # Outfits where this item is the top
    outfits_as_top = relationship(
        "Outfit",
        foreign_keys="Outfit.top_item_id",
        back_populates="top_item",
        cascade="all, delete-orphan",
    )

    # Outfits where this item is the bottom
    outfits_as_bottom = relationship(
        "Outfit",
        foreign_keys="Outfit.bottom_item_id",
        back_populates="bottom_item",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return (
            f"<WardrobeItem(id={self.id}, user_id={self.user_id}, "
            f"category={self.category}, status={self.processing_status})>"
        )
