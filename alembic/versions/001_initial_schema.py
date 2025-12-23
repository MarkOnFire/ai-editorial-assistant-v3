"""Initial database schema

Revision ID: 001
Revises:
Create Date: 2024-12-23 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create jobs table
    op.create_table(
        'jobs',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('project_path', sa.Text(), nullable=False),
        sa.Column('transcript_file', sa.Text(), nullable=False),
        sa.Column('status', sa.Text(), nullable=False, server_default='pending'),
        sa.Column('priority', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('queued_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('estimated_cost', sa.Float(), server_default='0.0'),
        sa.Column('actual_cost', sa.Float(), server_default='0.0'),
        sa.Column('agent_phases', sa.Text(), server_default='["analyst", "formatter"]'),
        sa.Column('current_phase', sa.Text(), nullable=True),
        sa.Column('retry_count', sa.Integer(), server_default='0'),
        sa.Column('max_retries', sa.Integer(), server_default='3'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('error_timestamp', sa.DateTime(), nullable=True),
        sa.Column('manifest_path', sa.Text(), nullable=True),
        sa.Column('logs_path', sa.Text(), nullable=True),
    )

    # Create indexes for jobs table
    op.create_index('idx_jobs_status', 'jobs', ['status'])
    op.create_index('idx_jobs_priority', 'jobs', ['priority', 'id'])
    op.create_index('idx_jobs_queued_at', 'jobs', ['queued_at'])

    # Create session_stats table
    op.create_table(
        'session_stats',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('job_id', sa.Integer(), sa.ForeignKey('jobs.id'), nullable=True),
        sa.Column('timestamp', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('event_type', sa.Text(), nullable=False),
        sa.Column('data', sa.Text(), nullable=True),
    )

    # Create indexes for session_stats table
    op.create_index('idx_session_stats_job', 'session_stats', ['job_id'])
    op.create_index('idx_session_stats_type', 'session_stats', ['event_type'])
    op.create_index('idx_session_stats_timestamp', 'session_stats', ['timestamp'])

    # Create config table
    op.create_table(
        'config',
        sa.Column('key', sa.Text(), primary_key=True),
        sa.Column('value', sa.Text(), nullable=False),
        sa.Column('value_type', sa.Text(), server_default='string'),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
    )


def downgrade() -> None:
    op.drop_table('config')
    op.drop_table('session_stats')
    op.drop_table('jobs')
