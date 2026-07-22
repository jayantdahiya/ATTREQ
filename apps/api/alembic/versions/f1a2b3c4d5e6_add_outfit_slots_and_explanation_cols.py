"""add_outfit_slots_and_explanation_cols

Revision ID: f1a2b3c4d5e6
Revises: d7ea1fb6a91a
Create Date: 2026-07-23 00:00:00.000000

RI-4 (Composition Engine & Calibrated Explanations):

- `outfits.footwear_item_id` / `outerwear_item_id` / `fullbody_item_id` —
  nullable FKs to `wardrobe_items`, `ondelete="SET NULL"` (mirrors the
  existing `top_item_id`/`bottom_item_id` style). This satisfies launch-M3
  section 3.1 (footwear/outerwear slots) for real, plus the fullbody anchor
  slot RI-4 itself needs (`wardrobe_items.is_fullbody` already exists as of
  `d7ea1fb6a91a` / RI-2 — not re-added here).
- `recommendation_events.explanation` / `.confidence` — ALTER onto the table
  RI-1 already merged (`898625dd314d`), so the composed explanation shown to
  the user is captured on the same telemetry row as the score breakdown.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = 'f1a2b3c4d5e6'
down_revision: Union[str, Sequence[str], None] = 'd7ea1fb6a91a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'outfits',
        sa.Column('footwear_item_id', postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.add_column(
        'outfits',
        sa.Column('outerwear_item_id', postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.add_column(
        'outfits',
        sa.Column('fullbody_item_id', postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        'fk_outfits_footwear_item_id_wardrobe_items',
        'outfits',
        'wardrobe_items',
        ['footwear_item_id'],
        ['id'],
        ondelete='SET NULL',
    )
    op.create_foreign_key(
        'fk_outfits_outerwear_item_id_wardrobe_items',
        'outfits',
        'wardrobe_items',
        ['outerwear_item_id'],
        ['id'],
        ondelete='SET NULL',
    )
    op.create_foreign_key(
        'fk_outfits_fullbody_item_id_wardrobe_items',
        'outfits',
        'wardrobe_items',
        ['fullbody_item_id'],
        ['id'],
        ondelete='SET NULL',
    )

    op.add_column('recommendation_events', sa.Column('explanation', sa.Text(), nullable=True))
    op.add_column(
        'recommendation_events', sa.Column('confidence', sa.String(length=10), nullable=True)
    )


def downgrade() -> None:
    op.drop_column('recommendation_events', 'confidence')
    op.drop_column('recommendation_events', 'explanation')

    op.drop_constraint(
        'fk_outfits_fullbody_item_id_wardrobe_items', 'outfits', type_='foreignkey'
    )
    op.drop_constraint(
        'fk_outfits_outerwear_item_id_wardrobe_items', 'outfits', type_='foreignkey'
    )
    op.drop_constraint(
        'fk_outfits_footwear_item_id_wardrobe_items', 'outfits', type_='foreignkey'
    )
    op.drop_column('outfits', 'fullbody_item_id')
    op.drop_column('outfits', 'outerwear_item_id')
    op.drop_column('outfits', 'footwear_item_id')
