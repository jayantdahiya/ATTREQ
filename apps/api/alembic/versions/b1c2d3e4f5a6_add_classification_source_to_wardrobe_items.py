"""add_classification_source_to_wardrobe_items

Revision ID: b1c2d3e4f5a6
Revises: 3a686a89c4c2
Create Date: 2026-05-01 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = 'b1c2d3e4f5a6'
down_revision: Union[str, Sequence[str], None] = '3a686a89c4c2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('wardrobe_items', sa.Column('classification_source', sa.String(length=20), nullable=True))


def downgrade() -> None:
    op.drop_column('wardrobe_items', 'classification_source')
