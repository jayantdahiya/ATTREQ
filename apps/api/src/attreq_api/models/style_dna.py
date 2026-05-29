"""StyleDnaPhoto model."""

import uuid

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from attreq_api.config.database import Base


class StyleDnaPhoto(Base):
    __tablename__ = "style_dna_photos"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    file_path = Column(String(500), nullable=False)
    file_url = Column(String(500), nullable=False)

    quality_ok = Column(Boolean, default=True, nullable=False)
    quality_reason = Column(String(100), nullable=True)

    # Dual-purpose extraction: {style_signals: {...}, wardrobe_items_detected: [...]}
    per_photo_extraction = Column(JSONB, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    user = relationship("User", back_populates="style_dna_photos")

    def __repr__(self) -> str:
        return f"<StyleDnaPhoto(id={self.id}, user_id={self.user_id}, quality_ok={self.quality_ok})>"
