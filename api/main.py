"""
Editorial Assistant v3.0 - FastAPI Application

Main entry point for the API server.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Editorial Assistant API",
    description="API for PBS Wisconsin Editorial Assistant v3.0",
    version="3.0.0-dev",
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
    """System health check endpoint."""
    return {"status": "ok"}


# Routers will be added here as they're implemented:
# from api.routers import queue, jobs, system, config, analytics
# app.include_router(queue.router, prefix="/api/queue", tags=["queue"])
# app.include_router(jobs.router, prefix="/api/jobs", tags=["jobs"])
# app.include_router(system.router, prefix="/api/system", tags=["system"])
# app.include_router(config.router, prefix="/api/config", tags=["config"])
# app.include_router(analytics.router, prefix="/api/analytics", tags=["analytics"])
