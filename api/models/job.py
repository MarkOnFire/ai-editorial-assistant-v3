"""Job models for Editorial Assistant v3.0 API."""
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum
from typing import Optional, List


class JobStatus(str, Enum):
    """Valid job status values matching database CHECK constraint."""
    pending = "pending"
    in_progress = "in_progress"
    completed = "completed"
    failed = "failed"
    cancelled = "cancelled"
    paused = "paused"


class JobBase(BaseModel):
    """Base job schema with common fields."""
    project_path: str = Field(..., description="Path to project directory")
    transcript_file: str = Field(..., description="Path to transcript file")
    priority: int = Field(default=0, description="Job priority (higher = sooner)")
    max_retries: int = Field(default=3, description="Maximum retry attempts")


class JobCreate(BaseModel):
    """Schema for creating a new job (POST /queue)."""
    project_path: str = Field(..., description="Path to project directory")
    transcript_file: str = Field(..., description="Path to transcript file")
    priority: Optional[int] = Field(default=0, description="Job priority (higher = sooner)")


class JobUpdate(BaseModel):
    """Schema for partial job updates (PATCH /jobs/{id})."""
    status: Optional[JobStatus] = None
    priority: Optional[int] = None
    current_phase: Optional[str] = None
    error_message: Optional[str] = None
    estimated_cost: Optional[float] = None
    actual_cost: Optional[float] = None
    manifest_path: Optional[str] = None
    logs_path: Optional[str] = None
    last_heartbeat: Optional[datetime] = None


class Job(BaseModel):
    """Complete job record including all database fields."""
    id: int
    project_path: str
    transcript_file: str
    project_name: Optional[str] = Field(None, description="Computed from project_path")
    status: JobStatus
    priority: int
    queued_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    estimated_cost: float
    actual_cost: float
    agent_phases: List[str] = Field(default_factory=lambda: ["analyst", "formatter"])
    current_phase: Optional[str] = None
    retry_count: int
    max_retries: int
    error_message: Optional[str] = None
    error_timestamp: Optional[datetime] = None
    manifest_path: Optional[str] = None
    logs_path: Optional[str] = None
    last_heartbeat: Optional[datetime] = None

    class Config:
        from_attributes = True


class JobList(BaseModel):
    """Paginated job list response."""
    jobs: List[Job]
    total: int
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=50, ge=1, le=100)
    total_pages: int
