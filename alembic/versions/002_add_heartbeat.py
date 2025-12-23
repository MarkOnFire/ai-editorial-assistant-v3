"""Add heartbeat tracking to jobs table

Revision ID: 002
Revises: 001
Create Date: 2024-12-23 14:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = '002'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add last_heartbeat column to jobs table
    op.add_column(
        'jobs',
        sa.Column('last_heartbeat', sa.DateTime(), nullable=True)
    )

    # Create index for heartbeat queries
    op.create_index('idx_jobs_heartbeat', 'jobs', ['status', 'last_heartbeat'])


def downgrade() -> None:
    op.drop_index('idx_jobs_heartbeat', table_name='jobs')
    op.drop_column('jobs', 'last_heartbeat')
