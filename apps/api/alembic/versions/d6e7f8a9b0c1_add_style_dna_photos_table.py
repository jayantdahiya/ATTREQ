"""add_style_dna_photos_table

Revision ID: d6e7f8a9b0c1
Revises: b1c2d3e4f5a6
Create Date: 2026-05-02 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = 'd6e7f8a9b0c1'
down_revision: Union[str, Sequence[str], None] = 'b1c2d3e4f5a6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'style_dna_photos',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('file_path', sa.String(length=500), nullable=False),
        sa.Column('file_url', sa.String(length=500), nullable=False),
        sa.Column('quality_ok', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('quality_reason', sa.String(length=100), nullable=True),
        sa.Column('per_photo_extraction', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_style_dna_photos_user_id'), 'style_dna_photos', ['user_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_style_dna_photos_user_id'), table_name='style_dna_photos')
    op.drop_table('style_dna_photos')
