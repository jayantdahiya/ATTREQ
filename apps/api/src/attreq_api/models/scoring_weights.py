"""ScoringWeights model — published aggregation-weight sets (RI-5, Task 5.2).

Append-mostly: a new row is inserted per fit/publish attempt; `is_active` is
flipped `False` on the prior active row for the same `scope` in the same
transaction (`crud/scoring_weights.py::publish`), never updated/deleted
otherwise — this keeps a full audit trail of every fit attempt, including
refused ones (which insert a row with `is_active=False` and never touch the
currently-active row).
"""

import uuid

from sqlalchemy import Boolean, Column, DateTime, Float, Index, Integer, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.sql import func

from attreq_api.config.database import Base


class ScoringWeights(Base):
    """One published (or attempted) aggregation weight set.

    `scope`: `"global"` or a stringified user UUID (per-user override).
    `weights`: JSONB dict over `weight_fitting.COMPONENT_KEYS_FULL`, summing
    to 1.0. `is_active`: at most one active row per scope at a time —
    enforced at the application layer (`crud.scoring_weights.publish`), not a
    DB constraint (a partial unique index would be the natural DB-level
    enforcement but is deferred — low write volume, single writer script).
    """

    __tablename__ = "scoring_weights"
    __table_args__ = (Index("ix_scoring_weights_scope_active", "scope", "is_active"),)

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    scope = Column(String(64), nullable=False)
    weights = Column(JSONB, nullable=False)
    fitted_on_n_pairs = Column(Integer, nullable=False)
    holdout_user_auc = Column(Float, nullable=False)
    is_active = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    def __repr__(self) -> str:
        return (
            f"<ScoringWeights(id={self.id}, scope={self.scope}, "
            f"is_active={self.is_active}, holdout_user_auc={self.holdout_user_auc})>"
        )
