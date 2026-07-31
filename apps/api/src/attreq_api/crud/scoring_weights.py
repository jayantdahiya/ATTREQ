"""CRUD operations for scoring_weights (RI-5, Task 5.2).

Write methods commit internally (see crud/recommendation_event.py docstring
for why — `get_db` never commits on its own).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import select, update

from attreq_api.models.scoring_weights import ScoringWeights

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


class ScoringWeightsCRUD:
    """CRUD operations for scoring_weights."""

    async def get_active(self, db: AsyncSession, *, scope: str) -> ScoringWeights | None:
        """O(1) indexed read of the active row for one scope (`ix_scoring_weights_scope_active`).

        Never raises on "not found" — returns `None`, which callers
        (`weight_fitting.get_active_weights`) treat as "fall through to the
        next precedence tier".
        """
        query = select(ScoringWeights).where(
            ScoringWeights.scope == scope, ScoringWeights.is_active.is_(True)
        )
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def publish(
        self,
        db: AsyncSession,
        *,
        scope: str,
        weights: dict[str, float],
        fitted_on_n_pairs: int,
        holdout_user_auc: float,
    ) -> ScoringWeights:
        """Deactivate the prior active row (if any) for this scope and insert
        the new one as active, in one transaction.

        Callers (the fit script) must have already applied the publish guard
        (new holdout AUC beats the baseline) before calling this — this
        method does not re-check it, it only performs the atomic swap.
        """
        await db.execute(
            update(ScoringWeights)
            .where(ScoringWeights.scope == scope, ScoringWeights.is_active.is_(True))
            .values(is_active=False)
        )
        row = ScoringWeights(
            scope=scope,
            weights=weights,
            fitted_on_n_pairs=fitted_on_n_pairs,
            holdout_user_auc=holdout_user_auc,
            is_active=True,
        )
        db.add(row)
        await db.commit()
        await db.refresh(row)
        return row

    async def record_refused(
        self,
        db: AsyncSession,
        *,
        scope: str,
        weights: dict[str, float],
        fitted_on_n_pairs: int,
        holdout_user_auc: float,
    ) -> ScoringWeights:
        """Audit row for a fit attempt that failed the publish guard —
        `is_active=False`, never touches the currently-active row for this scope.
        """
        row = ScoringWeights(
            scope=scope,
            weights=weights,
            fitted_on_n_pairs=fitted_on_n_pairs,
            holdout_user_auc=holdout_user_auc,
            is_active=False,
        )
        db.add(row)
        await db.commit()
        await db.refresh(row)
        return row


# Global instance
scoring_weights_crud = ScoringWeightsCRUD()
