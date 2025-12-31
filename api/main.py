"""
Editorial Assistant v3.0 - FastAPI Application

Main entry point for the API server.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.services import database
from api.services.llm import get_llm_client, close_llm_client
from api.services.logging import setup_logging, get_logger


# Initialize logging for API
setup_logging(log_file="api.log")
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan events.

    Initializes database connection pool and LLM client on startup,
    closes connections on shutdown.
    """
    # Startup: Initialize database and LLM client
    logger.info("Starting Editorial Assistant API v3.0")
    await database.init_db()
    logger.info("Database initialized")
    get_llm_client()  # Initialize LLM client
    logger.info("LLM client initialized")
    yield
    # Shutdown: Close connections
    logger.info("Shutting down API server")
    await close_llm_client()
    await database.close_db()
    logger.info("Shutdown complete")


app = FastAPI(
    title="Editorial Assistant API",
    description="API for PBS Wisconsin Editorial Assistant v3.0",
    version="3.0.0-dev",
    lifespan=lifespan,
)

# CORS middleware for web dashboard
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # React dev server
        "http://localhost:5173",  # Vite dev server
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Health check endpoint."""
    return {"status": "ok", "version": "3.0.0-dev"}


@app.get("/api/system/health")
async def health():
    """Enhanced system health check endpoint.

    Returns system status including:
    - Basic health status
    - Queue statistics (pending, in_progress counts)
    - Active LLM model/preset info
    - Last run cost totals
    """
    from api.models.job import JobStatus

    # Get queue stats
    pending_jobs = await database.list_jobs(status=JobStatus.pending, limit=1000)
    in_progress_jobs = await database.list_jobs(status=JobStatus.in_progress, limit=1000)

    queue_stats = {
        "pending": len(pending_jobs),
        "in_progress": len(in_progress_jobs),
    }

    # Get LLM status
    llm_client = get_llm_client()
    llm_status = llm_client.get_status()

    return {
        "status": "ok",
        "queue": queue_stats,
        "llm": {
            "active_backend": llm_status.get("active_backend"),
            "active_model": llm_status.get("active_model"),
            "active_preset": llm_status.get("active_preset"),
            "primary_backend": llm_status.get("primary_backend"),
            "configured_preset": llm_status.get("configured_preset"),
            "fallback_model": llm_status.get("fallback_model"),
            "phase_backends": llm_status.get("phase_backends"),
            "openrouter_presets": llm_status.get("openrouter_presets"),
        },
        "last_run": llm_status.get("last_run_totals"),
    }


# Register routers
from api.routers import jobs, queue, config
app.include_router(queue.router, prefix="/api/queue", tags=["queue"])
app.include_router(jobs.router, prefix="/api/jobs", tags=["jobs"])
app.include_router(config.router, prefix="/api", tags=["config"])

# Additional routers will be added here as they're implemented:
# from api.routers import system, analytics
# app.include_router(system.router, prefix="/api/system", tags=["system"])
# app.include_router(analytics.router, prefix="/api/analytics", tags=["analytics"])
