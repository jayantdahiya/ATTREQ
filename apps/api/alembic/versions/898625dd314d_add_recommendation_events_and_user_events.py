"""add_recommendation_events_and_user_events

Revision ID: 898625dd314d
Revises: e7f8a9b0c1d2
Create Date: 2026-07-22 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = '898625dd314d'
down_revision: Union[str, Sequence[str], None] = 'e7f8a9b0c1d2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'recommendation_events',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('recommendation_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('outfit_index', sa.Integer(), nullable=False),
        sa.Column('outfit_payload', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('event_type', sa.String(length=20), nullable=False),
        sa.Column('rejection_reason', sa.String(length=30), nullable=True),
        sa.Column('rejection_note', sa.Text(), nullable=True),
        sa.Column('context', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        op.f('ix_recommendation_events_user_id'), 'recommendation_events', ['user_id'], unique=False
    )
    op.create_index(
        op.f('ix_recommendation_events_recommendation_id'),
        'recommendation_events',
        ['recommendation_id'],
        unique=False,
    )
    op.create_index(
        'ix_recommendation_events_rec_id_outfit_index',
        'recommendation_events',
        ['recommendation_id', 'outfit_index'],
        unique=False,
    )

    op.create_table(
        'user_events',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('event_type', sa.String(length=30), nullable=False),
        sa.Column('payload', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        'ix_user_events_user_id_created_at', 'user_events', ['user_id', 'created_at'], unique=False
    )


def downgrade() -> None:
    op.drop_index('ix_user_events_user_id_created_at', table_name='user_events')
    op.drop_table('user_events')

    op.drop_index('ix_recommendation_events_rec_id_outfit_index', table_name='recommendation_events')
    op.drop_index(op.f('ix_recommendation_events_recommendation_id'), table_name='recommendation_events')
    op.drop_index(op.f('ix_recommendation_events_user_id'), table_name='recommendation_events')
    op.drop_table('recommendation_events')
