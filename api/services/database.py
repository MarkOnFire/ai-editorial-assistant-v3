"""Database service layer for Editorial Assistant v3.0.

Provides async database operations using SQLAlchemy 2.0+ with aiosqlite.
Thread-safe connection pool and CRUD operations for jobs, events, and config.
"""
import json
import os
from datetime import datetime, timezone
from typing import Optional, List
from contextlib import asynccontextmanager

from sqlalchemy import (
    select,
    update,
    delete,
    func,
    and_,
    desc,
    MetaData,
    Table,
    Column,
    Integer,
    Text,
    Float,
    DateTime,
    ForeignKey,
)
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
)

from api.models.job import Job, JobCreate, JobUpdate, JobStatus
from api.models.events import SessionEvent, EventCreate, EventData, EventType
from api.models.config import ConfigItem, ConfigValueType


# Global engine and session factory
_engine: Optional[AsyncEngine] = None
_async_session_factory: Optional[async_sessionmaker[AsyncSession]] = None

# SQLAlchemy metadata and table definitions
metadata = MetaData()

# Define jobs table
jobs_table = Table(
    "jobs",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("project_path", Text, nullable=False),
    Column("transcript_file", Text, nullable=False),
    Column("status", Text, nullable=False, server_default="pending"),
    Column("priority", Integer, nullable=False, server_default="0"),
    Column("queued_at", DateTime, server_default=func.current_timestamp()),
    Column("started_at", DateTime, nullable=True),
    Column("completed_at", DateTime, nullable=True),
    Column("estimated_cost", Float, server_default="0.0"),
    Column("actual_cost", Float, server_default="0.0"),
    Column("agent_phases", Text, server_default='["analyst", "formatter"]'),
    Column("current_phase", Text, nullable=True),
    Column("retry_count", Integer, server_default="0"),
    Column("max_retries", Integer, server_default="3"),
    Column("error_message", Text, nullable=True),
    Column("error_timestamp", DateTime, nullable=True),
    Column("manifest_path", Text, nullable=True),
    Column("logs_path", Text, nullable=True),
    Column("last_heartbeat", DateTime, nullable=True),
)

# Define session_stats table
session_stats_table = Table(
    "session_stats",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("job_id", Integer, ForeignKey("jobs.id"), nullable=True),
    Column("timestamp", DateTime, server_default=func.current_timestamp()),
    Column("event_type", Text, nullable=False),
    Column("data", Text, nullable=True),
)

# Define config table
config_table = Table(
    "config",
    metadata,
    Column("key", Text, primary_key=True),
    Column("value", Text, nullable=False),
    Column("value_type", Text, server_default="string"),
    Column("description", Text, nullable=True),
    Column("updated_at", DateTime, server_default=func.current_timestamp()),
)


def get_db_url() -> str:
    """Return SQLite database URL from environment or default."""
    db_path = os.getenv("DATABASE_PATH", "./dashboard.db")
    return f"sqlite+aiosqlite:///{db_path}"


async def init_db() -> None:
    """Initialize database connection pool.

    Creates async engine and session factory.
    Should be called once at application startup.
    """
    global _engine, _async_session_factory

    if _engine is not None:
        # Already initialized
        return

    db_url = get_db_url()

    # Create async engine with connection pooling
    _engine = create_async_engine(
        db_url,
        echo=False,  # Set to True for SQL debug logging
        pool_size=5,
        max_overflow=10,
        pool_pre_ping=True,  # Verify connections before use
        connect_args={"check_same_thread": False},  # SQLite specific
    )

    # Create session factory
    _async_session_factory = async_sessionmaker(
        _engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )


async def close_db() -> None:
    """Close database connections and cleanup resources.

    Should be called at application shutdown.
    """
    global _engine, _async_session_factory

    if _engine is not None:
        await _engine.dispose()
        _engine = None
        _async_session_factory = None


@asynccontextmanager
async def get_session():
    """Get async database session context manager.

    Usage:
        async with get_session() as session:
            result = await session.execute(...)
    """
    if _async_session_factory is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")

    async with _async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


# ============================================================================
# Job CRUD Operations
# ============================================================================


async def create_job(job: JobCreate) -> Job:
    """Create a new job in the database.

    Args:
        job: Job creation schema with required fields

    Returns:
        Complete Job record with generated ID and defaults
    """
    async with get_session() as session:
        # Prepare values
        values = {
            "project_path": job.project_path,
            "transcript_file": job.transcript_file,
            "priority": job.priority,
            "status": JobStatus.pending.value,
            "queued_at": datetime.now(timezone.utc),
            "estimated_cost": 0.0,
            "actual_cost": 0.0,
            "agent_phases": json.dumps(["analyst", "formatter"]),
            "retry_count": 0,
            "max_retries": 3,
        }

        # Insert job
        stmt = jobs_table.insert().values(**values)
        result = await session.execute(stmt)
        job_id = result.inserted_primary_key[0]

        # Fetch and return complete job (within same session)
        stmt = select(jobs_table).where(jobs_table.c.id == job_id)
        result = await session.execute(stmt)
        row = result.fetchone()

        return _row_to_job(row)


async def get_job(job_id: int) -> Optional[Job]:
    """Retrieve a job by ID.

    Args:
        job_id: Job ID to retrieve

    Returns:
        Job record or None if not found
    """
    async with get_session() as session:
        stmt = select(jobs_table).where(jobs_table.c.id == job_id)
        result = await session.execute(stmt)
        row = result.fetchone()

        if row is None:
            return None

        return _row_to_job(row)


async def list_jobs(
    status: Optional[JobStatus] = None,
    limit: int = 50,
    offset: int = 0,
) -> List[Job]:
    """List jobs with optional filtering and pagination.

    Args:
        status: Filter by job status (None = all statuses)
        limit: Maximum number of jobs to return
        offset: Number of jobs to skip

    Returns:
        List of Job records ordered by priority desc, then ID
    """
    async with get_session() as session:
        stmt = select(jobs_table)

        # Apply status filter
        if status is not None:
            stmt = stmt.where(jobs_table.c.status == status.value)

        # Order by priority (descending) then ID
        stmt = stmt.order_by(desc(jobs_table.c.priority), jobs_table.c.id)

        # Apply pagination
        stmt = stmt.limit(limit).offset(offset)

        result = await session.execute(stmt)
        rows = result.fetchall()

        return [_row_to_job(row) for row in rows]


async def update_job(job_id: int, job_update: JobUpdate) -> Optional[Job]:
    """Update a job with partial fields.

    Args:
        job_id: Job ID to update
        job_update: Partial update schema with optional fields

    Returns:
        Updated Job record or None if not found
    """
    async with get_session() as session:
        # Build update dict from non-None fields
        update_values = {}

        if job_update.status is not None:
            update_values["status"] = job_update.status.value

            # Auto-set timestamps based on status
            if job_update.status == JobStatus.in_progress and "started_at" not in update_values:
                update_values["started_at"] = datetime.now(timezone.utc)
            elif job_update.status in (JobStatus.completed, JobStatus.failed, JobStatus.cancelled):
                if "completed_at" not in update_values:
                    update_values["completed_at"] = datetime.now(timezone.utc)

        if job_update.priority is not None:
            update_values["priority"] = job_update.priority

        if job_update.current_phase is not None:
            update_values["current_phase"] = job_update.current_phase

        if job_update.error_message is not None:
            update_values["error_message"] = job_update.error_message
            update_values["error_timestamp"] = datetime.now(timezone.utc)

        if job_update.estimated_cost is not None:
            update_values["estimated_cost"] = job_update.estimated_cost

        if job_update.actual_cost is not None:
            update_values["actual_cost"] = job_update.actual_cost

        if job_update.manifest_path is not None:
            update_values["manifest_path"] = job_update.manifest_path

        if job_update.logs_path is not None:
            update_values["logs_path"] = job_update.logs_path

        if job_update.last_heartbeat is not None:
            update_values["last_heartbeat"] = job_update.last_heartbeat

        if not update_values:
            # No fields to update, just fetch and return current state
            stmt = select(jobs_table).where(jobs_table.c.id == job_id)
            result = await session.execute(stmt)
            row = result.fetchone()
            return _row_to_job(row) if row else None

        # Execute update
        stmt = (
            update(jobs_table)
            .where(jobs_table.c.id == job_id)
            .values(**update_values)
        )
        result = await session.execute(stmt)

        if result.rowcount == 0:
            return None

        # Fetch and return updated job (within same session)
        stmt = select(jobs_table).where(jobs_table.c.id == job_id)
        result = await session.execute(stmt)
        row = result.fetchone()

        return _row_to_job(row)


async def delete_job(job_id: int) -> bool:
    """Delete a job from the database.

    Args:
        job_id: Job ID to delete

    Returns:
        True if deleted, False if not found
    """
    async with get_session() as session:
        stmt = delete(jobs_table).where(jobs_table.c.id == job_id)
        result = await session.execute(stmt)
        return result.rowcount > 0


async def get_next_pending_job() -> Optional[Job]:
    """Get the next pending job to process.

    Returns highest priority pending job, or earliest queued if priorities equal.

    Returns:
        Next job to process or None if queue is empty
    """
    async with get_session() as session:
        stmt = (
            select(jobs_table)
            .where(jobs_table.c.status == JobStatus.pending.value)
            .order_by(desc(jobs_table.c.priority), jobs_table.c.queued_at)
            .limit(1)
        )
        result = await session.execute(stmt)
        row = result.fetchone()

        if row is None:
            return None

        return _row_to_job(row)


async def update_heartbeat(job_id: int) -> bool:
    """Update the last_heartbeat timestamp for a job.

    Should be called periodically during long processing operations.

    Args:
        job_id: Job ID to update heartbeat for

    Returns:
        True if updated, False if job not found
    """
    async with get_session() as session:
        stmt = (
            update(jobs_table)
            .where(jobs_table.c.id == job_id)
            .values(last_heartbeat=datetime.now(timezone.utc))
        )
        result = await session.execute(stmt)
        return result.rowcount > 0


async def get_stale_jobs(threshold_minutes: int = 10) -> List[Job]:
    """Get jobs that are in_progress but haven't had a heartbeat update within threshold_minutes.

    Returns list of jobs that may be stuck.

    Args:
        threshold_minutes: Minutes since last heartbeat to consider job stale

    Returns:
        List of jobs with stale heartbeats
    """
    async with get_session() as session:
        # Calculate cutoff time
        from datetime import timedelta
        cutoff_time = datetime.now(timezone.utc) - timedelta(minutes=threshold_minutes)

        # Find in_progress jobs with stale or null heartbeat
        stmt = (
            select(jobs_table)
            .where(
                and_(
                    jobs_table.c.status == JobStatus.in_progress.value,
                    func.coalesce(jobs_table.c.last_heartbeat, datetime.min.replace(tzinfo=timezone.utc)) < cutoff_time
                )
            )
            .order_by(jobs_table.c.id)
        )
        result = await session.execute(stmt)
        rows = result.fetchall()

        return [_row_to_job(row) for row in rows]


async def reset_stuck_jobs(threshold_minutes: int = 10) -> List[Job]:
    """Find and reset jobs that have been in_progress for longer than
    threshold_minutes without a heartbeat update.

    For each stuck job:
    - Set status back to 'pending'
    - Increment retry_count
    - Clear started_at and current_phase
    - Log the reset event to session_stats

    Returns list of jobs that were reset.
    """
    from datetime import timedelta

    async with get_session() as session:
        # Calculate threshold timestamp
        threshold_time = datetime.now(timezone.utc) - timedelta(minutes=threshold_minutes)

        # Find stuck jobs - in_progress with old heartbeat or no heartbeat
        stmt = (
            select(jobs_table)
            .where(
                and_(
                    jobs_table.c.status == JobStatus.in_progress.value,
                    func.coalesce(jobs_table.c.last_heartbeat, jobs_table.c.started_at) < threshold_time
                )
            )
        )
        result = await session.execute(stmt)
        stuck_rows = result.fetchall()

        reset_jobs = []

        for row in stuck_rows:
            job_id = row.id
            new_retry_count = row.retry_count + 1

            # Determine new status based on retry count
            if new_retry_count >= row.max_retries:
                # Max retries exceeded - mark as failed
                update_values = {
                    "status": JobStatus.failed.value,
                    "error_message": "Max retries exceeded after stuck job reset",
                    "error_timestamp": datetime.now(timezone.utc),
                    "retry_count": new_retry_count,
                    "completed_at": datetime.now(timezone.utc),
                }

                # Log job_failed event
                event_data_dict = {
                    "job_id": job_id,
                    "reason": "stuck_job_reset_max_retries",
                    "threshold_minutes": threshold_minutes,
                    "retry_count": new_retry_count,
                    "max_retries": row.max_retries,
                }
                event_values = {
                    "job_id": job_id,
                    "timestamp": datetime.now(timezone.utc),
                    "event_type": EventType.job_failed.value,
                    "data": json.dumps(event_data_dict),
                }
                stmt_event = session_stats_table.insert().values(**event_values)
                await session.execute(stmt_event)
            else:
                # Reset to pending
                update_values = {
                    "status": JobStatus.pending.value,
                    "started_at": None,
                    "current_phase": None,
                    "retry_count": new_retry_count,
                }

                # Log system_error event
                event_data_dict = {
                    "job_id": job_id,
                    "reason": "stuck_job_reset",
                    "threshold_minutes": threshold_minutes,
                    "retry_count": new_retry_count,
                }
                event_values = {
                    "job_id": job_id,
                    "timestamp": datetime.now(timezone.utc),
                    "event_type": EventType.system_error.value,
                    "data": json.dumps(event_data_dict),
                }
                stmt_event = session_stats_table.insert().values(**event_values)
                await session.execute(stmt_event)

            # Update job
            stmt_update = (
                update(jobs_table)
                .where(jobs_table.c.id == job_id)
                .values(**update_values)
            )
            await session.execute(stmt_update)

            # Fetch updated job
            stmt_fetch = select(jobs_table).where(jobs_table.c.id == job_id)
            result_fetch = await session.execute(stmt_fetch)
            updated_row = result_fetch.fetchone()
            reset_jobs.append(_row_to_job(updated_row))

        return reset_jobs


async def run_stuck_job_cleanup(threshold_minutes: int = 10) -> dict:
    """Run the stuck job cleanup routine.

    Returns summary dict with:
    - reset_count: Number of jobs reset to pending
    - failed_count: Number of jobs that exceeded max retries
    - job_ids: List of affected job IDs
    """
    reset_jobs = await reset_stuck_jobs(threshold_minutes)

    reset_count = sum(1 for job in reset_jobs if job.status == JobStatus.pending)
    failed_count = sum(1 for job in reset_jobs if job.status == JobStatus.failed)
    job_ids = [job.id for job in reset_jobs]

    return {
        "reset_count": reset_count,
        "failed_count": failed_count,
        "job_ids": job_ids,
    }


# ============================================================================
# Event Logging Operations
# ============================================================================


async def log_event(event: EventCreate) -> SessionEvent:
    """Log a session event to the database.

    Args:
        event: Event creation schema

    Returns:
        Complete SessionEvent record with generated ID
    """
    async with get_session() as session:
        # Serialize event data to JSON
        data_json = None
        if event.data is not None:
            data_json = event.data.model_dump_json(exclude_none=True)

        values = {
            "job_id": event.job_id,
            "timestamp": datetime.now(timezone.utc),
            "event_type": event.event_type.value,
            "data": data_json,
        }

        stmt = session_stats_table.insert().values(**values)
        result = await session.execute(stmt)
        event_id = result.inserted_primary_key[0]

        # Fetch and return complete event
        stmt = select(session_stats_table).where(session_stats_table.c.id == event_id)
        result = await session.execute(stmt)
        row = result.fetchone()

        return _row_to_event(row)


async def get_events_for_job(job_id: int) -> List[SessionEvent]:
    """Retrieve all events for a specific job.

    Args:
        job_id: Job ID to get events for

    Returns:
        List of SessionEvent records ordered by timestamp
    """
    async with get_session() as session:
        stmt = (
            select(session_stats_table)
            .where(session_stats_table.c.job_id == job_id)
            .order_by(session_stats_table.c.timestamp)
        )
        result = await session.execute(stmt)
        rows = result.fetchall()

        return [_row_to_event(row) for row in rows]


# ============================================================================
# Config Operations
# ============================================================================


async def get_config(key: str) -> Optional[ConfigItem]:
    """Retrieve a configuration value by key.

    Args:
        key: Configuration key

    Returns:
        ConfigItem or None if not found
    """
    async with get_session() as session:
        stmt = select(config_table).where(config_table.c.key == key)
        result = await session.execute(stmt)
        row = result.fetchone()

        if row is None:
            return None

        return _row_to_config(row)


async def set_config(
    key: str,
    value: str,
    value_type: str = "string",
    description: Optional[str] = None,
) -> ConfigItem:
    """Set or update a configuration value.

    Args:
        key: Configuration key
        value: Configuration value (as string)
        value_type: Type of value (string, int, float, bool, json)
        description: Optional description of config item

    Returns:
        Updated or created ConfigItem
    """
    async with get_session() as session:
        # Check if key exists
        stmt = select(config_table).where(config_table.c.key == key)
        result = await session.execute(stmt)
        existing = result.fetchone()

        if existing is not None:
            # Update existing
            update_values = {
                "value": value,
                "value_type": value_type,
                "updated_at": datetime.now(timezone.utc),
            }
            if description is not None:
                update_values["description"] = description

            stmt = (
                update(config_table)
                .where(config_table.c.key == key)
                .values(**update_values)
            )
            await session.execute(stmt)
        else:
            # Insert new
            values = {
                "key": key,
                "value": value,
                "value_type": value_type,
                "description": description,
                "updated_at": datetime.now(timezone.utc),
            }
            stmt = config_table.insert().values(**values)
            await session.execute(stmt)

        # Fetch and return (within same session)
        stmt = select(config_table).where(config_table.c.key == key)
        result = await session.execute(stmt)
        row = result.fetchone()

        return _row_to_config(row)


async def list_config() -> List[ConfigItem]:
    """List all configuration items.

    Returns:
        List of all ConfigItem records
    """
    async with get_session() as session:
        stmt = select(config_table).order_by(config_table.c.key)
        result = await session.execute(stmt)
        rows = result.fetchall()

        return [_row_to_config(row) for row in rows]


# ============================================================================
# Helper Functions
# ============================================================================


def _row_to_job(row) -> Job:
    """Convert database row to Job model.

    Handles JSON deserialization for agent_phases field and
    derives project_name from project_path.
    """
    # Parse agent_phases JSON
    agent_phases = json.loads(row.agent_phases)

    # Derive project_name from project_path
    project_name = os.path.basename(row.project_path.rstrip('/'))

    return Job(
        id=row.id,
        project_path=row.project_path,
        transcript_file=row.transcript_file,
        project_name=project_name,
        status=JobStatus(row.status),
        priority=row.priority,
        queued_at=row.queued_at,
        started_at=row.started_at,
        completed_at=row.completed_at,
        estimated_cost=row.estimated_cost,
        actual_cost=row.actual_cost,
        agent_phases=agent_phases,
        current_phase=row.current_phase,
        retry_count=row.retry_count,
        max_retries=row.max_retries,
        error_message=row.error_message,
        error_timestamp=row.error_timestamp,
        manifest_path=row.manifest_path,
        logs_path=row.logs_path,
        last_heartbeat=row.last_heartbeat,
    )


def _row_to_event(row) -> SessionEvent:
    """Convert database row to SessionEvent model.

    Handles JSON deserialization for data field.
    """
    # Parse data JSON if present
    event_data = None
    if row.data is not None:
        event_data = EventData.model_validate_json(row.data)

    return SessionEvent(
        id=row.id,
        job_id=row.job_id,
        timestamp=row.timestamp,
        event_type=EventType(row.event_type),
        data=event_data,
    )


def _row_to_config(row) -> ConfigItem:
    """Convert database row to ConfigItem model."""
    return ConfigItem(
        key=row.key,
        value=row.value,
        value_type=ConfigValueType(row.value_type),
        description=row.description,
        updated_at=row.updated_at,
    )
