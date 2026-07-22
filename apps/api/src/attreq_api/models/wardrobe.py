"""Wardrobe item model for ATTREQ application."""

import uuid

from sqlalchemy import (
    ARRAY,
    Boolean,
    Column,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    Numeric,
    SmallInteger,
    String,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
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
    classification_source = Column(String(20), nullable=True)  # "ai" | "fallback"
    processing_status = Column(
        String(20), nullable=False, default="pending", index=True
    )  # pending, processing, completed, failed

    # Usage tracking
    wear_count = Column(Integer, nullable=False, default=0)
    last_worn = Column(Date, nullable=True)

    # Retention / trust surfaces (RI-7)
    status = Column(String(20), nullable=False, default="active", index=True)  # active|archived
    purchase_price = Column(Numeric(10, 2), nullable=True)
    brand = Column(String(100), nullable=True)  # no index — per-user grouping is tiny

    # Classifier schema v2 (RI-2) — fixed-vocabulary attributes. Stored as
    # plain strings (enum `.value`), matching the existing free-string
    # category/pattern idiom (avoids PG-enum ALTER TYPE pain). See
    # `schemas/wardrobe_enums.py` for the vocabularies.
    texture = Column(String(20), nullable=True)
    silhouette = Column(String(20), nullable=True)
    neckline = Column(String(20), nullable=True)
    sleeve_length = Column(String(20), nullable=True)
    statement_level = Column(String(20), nullable=True)
    llm_formality = Column(SmallInteger, nullable=True)  # LLM's 1-4 formality judgment
    is_fullbody = Column(
        Boolean, nullable=False, default=False
    )  # derived server-side from category (dress/jumpsuit/romper)

    # Deterministic CIELAB color palette (RI-2) — always pixel-derived when
    # present; see `services/ai/color_extraction.py`. `color_primary` above
    # remains the LLM's human-readable descriptor/fallback.
    color_palette = Column(JSONB, nullable=True)  # [{lab, hex, share, is_neutral, name}], dominant first
    color_extraction_source = Column(String(20), nullable=True)  # "pixel" | "llm_fallback"

    attribute_confidence = Column(JSONB, nullable=True)  # per-attribute 0-1 confidence, v2 only
    schema_version = Column(Integer, nullable=False, default=1)  # 1 = pre-RI-2, 2 = v2 attributes

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    user = relationship("User", back_populates="wardrobe_items")
    photos = relationship(
        "WardrobeItemPhoto",
        back_populates="item",
        cascade="all, delete-orphan",
        order_by="WardrobeItemPhoto.created_at",
    )

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

    # RI-4 outfit slots — mirrors the top/bottom relationship style above.
    outfits_as_footwear = relationship(
        "Outfit",
        foreign_keys="Outfit.footwear_item_id",
        back_populates="footwear_item",
        cascade="all, delete-orphan",
    )
    outfits_as_outerwear = relationship(
        "Outfit",
        foreign_keys="Outfit.outerwear_item_id",
        back_populates="outerwear_item",
        cascade="all, delete-orphan",
    )
    outfits_as_fullbody = relationship(
        "Outfit",
        foreign_keys="Outfit.fullbody_item_id",
        back_populates="fullbody_item",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return (
            f"<WardrobeItem(id={self.id}, user_id={self.user_id}, "
            f"category={self.category}, status={self.processing_status})>"
        )
