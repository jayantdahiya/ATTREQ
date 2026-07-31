"""add_classifier_schema_v2_and_color_palette

Revision ID: d7ea1fb6a91a
Revises: a1b2c3d4e5f6
Create Date: 2026-07-23 00:00:00.000000

RI-2: adds the v2 fixed-vocabulary attributes (texture, silhouette, neckline,
sleeve_length, statement_level, llm_formality, is_fullbody), the deterministic
CIELAB color palette (color_palette, color_extraction_source), the per-attribute
confidence block (attribute_confidence), and schema_version (default 1; new
v2 writes set 2 explicitly in the application layer).

Adds alongside RI-7's status/purchase_price/brand/wardrobe_item_photos
(already on `wardrobe_items` as of `a1b2c3d4e5f6`) — does not touch them.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = 'd7ea1fb6a91a'
down_revision: Union[str, Sequence[str], None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('wardrobe_items', sa.Column('texture', sa.String(length=20), nullable=True))
    op.add_column('wardrobe_items', sa.Column('silhouette', sa.String(length=20), nullable=True))
    op.add_column('wardrobe_items', sa.Column('neckline', sa.String(length=20), nullable=True))
    op.add_column('wardrobe_items', sa.Column('sleeve_length', sa.String(length=20), nullable=True))
    op.add_column('wardrobe_items', sa.Column('statement_level', sa.String(length=20), nullable=True))
    op.add_column('wardrobe_items', sa.Column('llm_formality', sa.SmallInteger(), nullable=True))
    op.add_column(
        'wardrobe_items',
        sa.Column('is_fullbody', sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column(
        'wardrobe_items', sa.Column('color_palette', postgresql.JSONB(), nullable=True)
    )
    op.add_column(
        'wardrobe_items', sa.Column('color_extraction_source', sa.String(length=20), nullable=True)
    )
    op.add_column(
        'wardrobe_items', sa.Column('attribute_confidence', postgresql.JSONB(), nullable=True)
    )
    op.add_column(
        'wardrobe_items',
        sa.Column('schema_version', sa.Integer(), nullable=False, server_default='1'),
    )


def downgrade() -> None:
    op.drop_column('wardrobe_items', 'schema_version')
    op.drop_column('wardrobe_items', 'attribute_confidence')
    op.drop_column('wardrobe_items', 'color_extraction_source')
    op.drop_column('wardrobe_items', 'color_palette')
    op.drop_column('wardrobe_items', 'is_fullbody')
    op.drop_column('wardrobe_items', 'llm_formality')
    op.drop_column('wardrobe_items', 'statement_level')
    op.drop_column('wardrobe_items', 'sleeve_length')
    op.drop_column('wardrobe_items', 'neckline')
    op.drop_column('wardrobe_items', 'silhouette')
    op.drop_column('wardrobe_items', 'texture')
