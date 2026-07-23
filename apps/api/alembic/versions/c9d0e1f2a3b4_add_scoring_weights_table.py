"""add_scoring_weights_table

Revision ID: c9d0e1f2a3b4
Revises: b4c5d6e7f8a9
Create Date: 2026-07-23 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = 'c9d0e1f2a3b4'
down_revision: Union[str, Sequence[str], None] = 'b4c5d6e7f8a9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'scoring_weights',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('scope', sa.String(length=64), nullable=False),
        sa.Column('weights', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('fitted_on_n_pairs', sa.Integer(), nullable=False),
        sa.Column('holdout_user_auc', sa.Float(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        'ix_scoring_weights_scope_active', 'scoring_weights', ['scope', 'is_active'], unique=False
    )


def downgrade() -> None:
    op.drop_index('ix_scoring_weights_scope_active', table_name='scoring_weights')
    op.drop_table('scoring_weights')
