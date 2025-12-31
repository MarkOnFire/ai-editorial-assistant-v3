"""Add Airtable fields to jobs table

Revision ID: 004
Revises: 003
Create Date: 2025-12-30 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = '004'
down_revision: Union[str, None] = '003'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add Airtable integration fields to jobs table
    op.add_column(
        'jobs',
        sa.Column('airtable_record_id', sa.String(), nullable=True)
    )
    op.add_column(
        'jobs',
        sa.Column('airtable_url', sa.String(), nullable=True)
    )
    op.add_column(
        'jobs',
        sa.Column('media_id', sa.String(), nullable=True)
    )

    # Create index for media_id lookups (useful for finding jobs by media ID)
    op.create_index('idx_jobs_media_id', 'jobs', ['media_id'])


def downgrade() -> None:
    op.drop_index('idx_jobs_media_id', table_name='jobs')
    op.drop_column('jobs', 'media_id')
    op.drop_column('jobs', 'airtable_url')
    op.drop_column('jobs', 'airtable_record_id')
