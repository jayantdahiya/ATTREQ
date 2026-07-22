"""RecommendationEvent model — append-only telemetry for shown/accepted/rejected/swapped/worn outfits."""

import uuid

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.sql import func

from attreq_api.config.database import Base


class RecommendationEvent(Base):
    """One row per candidate outfit shown to a user, plus one row per feedback action.

    Append-only: rows are never updated or deleted by application code. Feedback
    (accepted/rejected/swapped/worn) is always a *new* row referencing the same
    (recommendation_id, outfit_index) as the original `shown` row, not an update to it.

    No ORM relationship to User — all queries filter by user_id directly, keeping
    this additive-only with respect to models/user.py.
    """

    __tablename__ = "recommendation_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # Groups one generation batch (one /daily call == one recommendation_id).
    recommendation_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    # 0-based display position within the batch; the value the feedback body addresses.
    outfit_index = Column(Integer, nullable=False)

    # {top_item_id, bottom_item_id, accessory_item_id (nullable),
    #  scores: {color_harmony, formality, preference_bonus, style_dna, behaviour, total}}
    # Built from the raw candidate dict, not the serialized response.
    outfit_payload = Column(JSONB, nullable=False)

    # shown | accepted | rejected | swapped | worn
    event_type = Column(String(20), nullable=False)

    # Only set when event_type == "rejected".
    rejection_reason = Column(String(30), nullable=True)
    rejection_note = Column(Text, nullable=True)

    # {weather: {...}, occasion: str, date: "YYYY-MM-DD"}
    context = Column(JSONB, nullable=True)

    # RI-4: the composed template explanation and confidence hedge shown to
    # the user for this candidate at generation time. Only ever set on
    # `shown` rows (the payload actually rendered) — feedback rows copy them
    # from the originating `shown` row for self-description, same as
    # `outfit_payload`/`context`.
    explanation = Column(Text, nullable=True)
    confidence = Column(String(10), nullable=True)  # "low" | "normal"

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    def __repr__(self) -> str:
        return (
            f"<RecommendationEvent(id={self.id}, recommendation_id={self.recommendation_id}, "
            f"outfit_index={self.outfit_index}, event_type={self.event_type})>"
        )
