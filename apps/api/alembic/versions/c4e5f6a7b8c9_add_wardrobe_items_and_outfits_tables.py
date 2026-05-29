"""add_wardrobe_items_and_outfits_tables

Revision ID: c4e5f6a7b8c9
Revises: 3a686a89c4c2
Create Date: 2026-05-02 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = 'c4e5f6a7b8c9'
down_revision: Union[str, Sequence[str], None] = '3a686a89c4c2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'wardrobe_items',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('original_image_url', sa.String(length=500), nullable=False),
        sa.Column('processed_image_url', sa.String(length=500), nullable=True),
        sa.Column('thumbnail_url', sa.String(length=500), nullable=True),
        sa.Column('category', sa.String(length=100), nullable=True),
        sa.Column('color_primary', sa.String(length=50), nullable=True),
        sa.Column('color_secondary', sa.String(length=50), nullable=True),
        sa.Column('pattern', sa.String(length=50), nullable=True),
        sa.Column('season', sa.ARRAY(sa.String()), nullable=True),
        sa.Column('occasion', sa.ARRAY(sa.String()), nullable=True),
        sa.Column('detection_confidence', sa.Float(), nullable=True),
        sa.Column('processing_status', sa.String(length=20), nullable=False, server_default='pending'),
        sa.Column('wear_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('last_worn', sa.Date(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_wardrobe_items_id'), 'wardrobe_items', ['id'], unique=False)
    op.create_index(op.f('ix_wardrobe_items_user_id'), 'wardrobe_items', ['user_id'], unique=False)
    op.create_index(op.f('ix_wardrobe_items_category'), 'wardrobe_items', ['category'], unique=False)
    op.create_index(op.f('ix_wardrobe_items_color_primary'), 'wardrobe_items', ['color_primary'], unique=False)
    op.create_index(op.f('ix_wardrobe_items_processing_status'), 'wardrobe_items', ['processing_status'], unique=False)

    op.create_table(
        'outfits',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('top_item_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('bottom_item_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('accessory_ids', postgresql.ARRAY(postgresql.UUID(as_uuid=True)), nullable=True),
        sa.Column('worn_date', sa.Date(), nullable=True),
        sa.Column('feedback_score', sa.Integer(), nullable=True),
        sa.Column('weather_context', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('occasion_context', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['top_item_id'], ['wardrobe_items.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['bottom_item_id'], ['wardrobe_items.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_outfits_id'), 'outfits', ['id'], unique=False)
    op.create_index(op.f('ix_outfits_user_id'), 'outfits', ['user_id'], unique=False)
    op.create_index(op.f('ix_outfits_worn_date'), 'outfits', ['worn_date'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_outfits_worn_date'), table_name='outfits')
    op.drop_index(op.f('ix_outfits_user_id'), table_name='outfits')
    op.drop_index(op.f('ix_outfits_id'), table_name='outfits')
    op.drop_table('outfits')

    op.drop_index(op.f('ix_wardrobe_items_processing_status'), table_name='wardrobe_items')
    op.drop_index(op.f('ix_wardrobe_items_color_primary'), table_name='wardrobe_items')
    op.drop_index(op.f('ix_wardrobe_items_category'), table_name='wardrobe_items')
    op.drop_index(op.f('ix_wardrobe_items_user_id'), table_name='wardrobe_items')
    op.drop_index(op.f('ix_wardrobe_items_id'), table_name='wardrobe_items')
    op.drop_table('wardrobe_items')
