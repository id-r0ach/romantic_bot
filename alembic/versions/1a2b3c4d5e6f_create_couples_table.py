"""create couples table

Revision ID: 1a2b3c4d5e6f
Revises: 64d5e3550fb9
Create Date: 2026-08-09 12:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = '1a2b3c4d5e6f'
down_revision: Union[str, Sequence[str], None] = '64d5e3550fb9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('couples',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user1_id', sa.BigInteger(), nullable=False),
        sa.Column('user2_id', sa.BigInteger(), nullable=True),
        sa.Column('status', sa.String(length=10), nullable=False),
        sa.Column('invite_code', sa.String(length=6), nullable=False),
        sa.Column('invite_expires', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('activated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user1_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['user2_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_couples_invite_code'), 'couples', ['invite_code'], unique=True)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_couples_invite_code'), table_name='couples')
    op.drop_table('couples')