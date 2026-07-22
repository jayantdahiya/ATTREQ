"""User model for ATTREQ application."""

import uuid

from sqlalchemy import Boolean, Column, DateTime, Float, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from attreq_api.config.database import Base


class User(Base):
    """User model representing application users."""

    __tablename__ = "users"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)

    # Authentication fields
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)

    # Profile fields
    full_name = Column(String(255), nullable=True)
    location = Column(String(255), nullable=True)

    # Location fields for weather-based recommendations
    saved_latitude = Column(Float, nullable=True)
    saved_longitude = Column(Float, nullable=True)
    saved_city = Column(String(255), nullable=True)

    # Account status
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
    last_login = Column(DateTime(timezone=True), nullable=True)

    # OAuth fields (for future Google OAuth integration)
    oauth_provider = Column(String(50), nullable=True)  # 'google', 'facebook', etc.
    oauth_id = Column(String(255), nullable=True)

    # Style DNA
    style_preferences = Column(Text, nullable=True)  # JSON string — synthesized Style DNA profile

    # RI-6: FashionCLIP style centroid — {"vector": [512 floats, UNNORMALIZED
    # running mean], "n_items": int, "updated_at": iso str}. Kept out of the
    # `style_preferences` blob to avoid round-trip-parsing 512 floats on every
    # Style DNA read. Updated online from "liked"/"worn" signals only (see
    # services/style_dna/scoring.py::update_style_dna_centroid); normalized
    # only at scoring time (services/recommendation/similarity.py::centroid_score).
    style_dna_centroid = Column(JSONB, nullable=True)

    # Onboarding state — steps: pending | style_dna_upload | review | complete
    onboarding_completed = Column(Boolean, default=False, nullable=False)
    onboarding_step = Column(String(50), default="pending", nullable=True)

    # Relationships
    wardrobe_items = relationship(
        "WardrobeItem", back_populates="user", cascade="all, delete-orphan"
    )
    outfits = relationship("Outfit", back_populates="user", cascade="all, delete-orphan")
    style_dna_photos = relationship(
        "StyleDnaPhoto", back_populates="user", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email}, full_name={self.full_name})>"

    @property
    def is_authenticated(self) -> bool:
        """Check if user is authenticated."""
        return self.is_active and self.is_verified
