"""add_review_and_duplicate_to_wardrobe_items

Revision ID: a3b4c5d6e7f8
Revises: f1a2b3c4d5e6
Create Date: 2026-07-23 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = 'a3b4c5d6e7f8'
down_revision: Union[str, Sequence[str], None] = 'f1a2b3c4d5e6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'wardrobe_items',
        sa.Column('needs_review', sa.Boolean(), nullable=False, server_default='false'),
    )
    op.add_column(
        'wardrobe_items',
        sa.Column('review_reason', sa.String(length=255), nullable=True),
    )
    op.add_column(
        'wardrobe_items',
        sa.Column('possible_duplicate_of', postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        'fk_wardrobe_items_possible_duplicate_of',
        'wardrobe_items',
        'wardrobe_items',
        ['possible_duplicate_of'],
        ['id'],
        ondelete='SET NULL',
    )


def downgrade() -> None:
    op.drop_constraint(
        'fk_wardrobe_items_possible_duplicate_of', 'wardrobe_items', type_='foreignkey'
    )
    op.drop_column('wardrobe_items', 'possible_duplicate_of')
    op.drop_column('wardrobe_items', 'review_reason')
    op.drop_column('wardrobe_items', 'needs_review')
