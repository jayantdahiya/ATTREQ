"""add_wardrobe_archive_price_photos

Revision ID: a1b2c3d4e5f6
Revises: 898625dd314d
Create Date: 2026-07-23 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = '898625dd314d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'wardrobe_items',
        sa.Column('status', sa.String(length=20), nullable=False, server_default='active'),
    )
    op.create_index(op.f('ix_wardrobe_items_status'), 'wardrobe_items', ['status'])
    op.add_column(
        'wardrobe_items', sa.Column('purchase_price', sa.Numeric(10, 2), nullable=True)
    )
    op.add_column('wardrobe_items', sa.Column('brand', sa.String(length=100), nullable=True))
    # NOTE: no index on brand — per-user brand grouping is tiny (see RI-7 plan finding D)

    op.create_table(
        'wardrobe_item_photos',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('item_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('original_image_url', sa.String(length=500), nullable=False),
        sa.Column('processed_image_url', sa.String(length=500), nullable=True),
        sa.Column('thumbnail_url', sa.String(length=500), nullable=True),
        sa.Column('is_primary', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column(
            'created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False
        ),
        sa.ForeignKeyConstraint(['item_id'], ['wardrobe_items.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        op.f('ix_wardrobe_item_photos_item_id'), 'wardrobe_item_photos', ['item_id'], unique=False
    )


def downgrade() -> None:
    op.drop_index(op.f('ix_wardrobe_item_photos_item_id'), table_name='wardrobe_item_photos')
    op.drop_table('wardrobe_item_photos')
    op.drop_column('wardrobe_items', 'brand')
    op.drop_column('wardrobe_items', 'purchase_price')
    op.drop_index(op.f('ix_wardrobe_items_status'), table_name='wardrobe_items')
    op.drop_column('wardrobe_items', 'status')
