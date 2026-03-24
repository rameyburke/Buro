# buro/main.py
#
# Main FastAPI application entry point for Buro.
#
# Educational Notes for Junior Developers:
# - Single app instance: FastAPI creates one application object for the entire server.
#   Tradeoff: Global state vs. cleaner dependency management.
# - Router organization: Separate routers for different domains (auth, issues, etc.)
#   Why routers: Modular code organization, easier testing, scalable architecture.
# - CORS setup: Essential for web app communication during development.
#   In production: Restrict origins for security.

import os
import re
import sys
from pathlib import Path
from typing import Optional
sys.path.insert(0, str(Path(__file__).parent))

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from sqlalchemy import inspect, text
import uvicorn

# Why separate routers: Domain-driven organization
# Benefits: Independent testing, cleaner code, scalable when app grows
from buro.api import analytics, auth, issues, projects, users
from buro.core.database import engine
from buro.models import Base

# Why lifespan context manager: Modern FastAPI approach for startup/shutdown
# Replaces on_event("startup"/"shutdown") - cleaner async handling
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for setup and cleanup.

    Why contextmanager: Ensures proper resource management.
    Startup: Initialize database connections, services
    Shutdown: Clean up resources, close connections

    Educational Note: Resource lifecycle management is crucial for
    production applications. Async context managers provide a clean pattern.
    """
    print("🚀 Starting Buro application...")

    # Startup logic
    try:
        # Verify database connectivity during startup
        # Why: Fail fast if database is unavailable
        # Alternative: Lazy connection (runtime errors instead of startup errors)
        async with engine.begin() as conn:
            pass  # Simple connectivity test
        print("✅ Database connected successfully")

        yield  # Application runs here

    except Exception as e:
        print(f"❌ Startup failed: {e}")
        raise

    finally:
        # Shutdown logic
        print("🛑 Shutting down Buro application...")
        await engine.dispose()  # Cleanly close database connections
        print("✅ Database connections closed")

# Why FastAPI constructor with lifespan:
# - Modern startup/shutdown management
# - Async context manager integration
# - Cleaner than event-based approach
app = FastAPI(
    title="Buro - Agile Project Management",
    description="Jira-like agile project management application built with FastAPI and React",
    version="0.1.0"
    # lifespan=lifespan  # Temporarily disabled for debugging
)

# CORS configuration for development
# Why: Allows web browser communication from different origins
# Security note: In production, specify allowed origins explicitly
# Note: Cannot use "*" when allow_credentials=True
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001",
        "http://localhost:3002",
        "http://127.0.0.1:3002",
        "http://localhost:4000",
        "http://127.0.0.1:4000",
        "http://localhost:4173",
        "http://127.0.0.1:4173",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "http://localhost:5000",
        "http://127.0.0.1:5000",
        "http://localhost:6000",
        "http://127.0.0.1:6000"
    ],  # Specific React dev server on multiple ports - no wildcard when credentials allowed
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD", "PATCH"],
    allow_headers=[
        "*",
        "Authorization",
        "Content-Type",
        "Accept",
        "Origin",
        "X-Requested-With"
    ],
)

# Include API routers with prefixes and tags
# Why prefixes: Clear API organization, version-friendly (v1, v2)
# Why tags: Groups routes in documentation, improves discoverability
app.include_router(
    auth.router,
    prefix="/api/auth",
    tags=["authentication"]
)

app.include_router(
    users.router,
    prefix="/api/users",
    tags=["users"]
)

app.include_router(
    projects.router,
    prefix="/api/projects",
    tags=["projects"]
)

app.include_router(
    issues.router,
    prefix="/api/issues",
    tags=["issues"]
)

app.include_router(
    analytics.router,
    prefix="/api/analytics",
    tags=["analytics"]
)


@app.on_event("startup")
async def ensure_user_theme_preference_column() -> None:
    """Backfill schema for theme preferences without separate migration script.

    Learning note: This keeps local/dev environments compatible when schema
    evolves quickly. Tradeoff: startup performs a tiny schema check query.
    """

    def _sync_ensure_column(sync_conn) -> None:
        inspector = inspect(sync_conn)
        if "users" not in inspector.get_table_names():
            return
        column_names = {column["name"] for column in inspector.get_columns("users")}
        if "theme" not in column_names:
            sync_conn.execute(
                text("ALTER TABLE users ADD COLUMN theme VARCHAR(20) DEFAULT 'light'")
            )
        sync_conn.execute(text("UPDATE users SET theme='light' WHERE theme IS NULL"))

    async with engine.begin() as conn:
        await conn.run_sync(_sync_ensure_column)

def _api_metadata() -> dict:
    return {
        "name": "Buro API",
        "version": "0.1.0",
        "description": "Agile project management API",
        "docs": "/docs",
        "redoc": "/redoc",
        "openapi": "/openapi.json",
    }


@app.get("/api/health", tags=["health"])
async def health_check():
    """Health check endpoint for monitoring and API discovery."""

    return _api_metadata()

# Serve frontend static files from same origin to avoid CORS
# Only in development mode (when FRONTEND_BUILD_PATH is set)
frontend_build_path = os.getenv("FRONTEND_BUILD_PATH")
if frontend_build_path and Path(frontend_build_path).exists():
    build_root = Path(frontend_build_path)

    _HASHED_ASSET_PATTERN = re.compile(
        r"^(?P<prefix>.+)\.(?P<hash>[0-9a-f]{8,})\.(?P<ext>css|js)$"
    )

    def _resolve_hashed_asset_fallback(asset_path: Path) -> Optional[Path]:
        """Map stale hashed bundle requests to the latest matching build asset."""
        match = _HASHED_ASSET_PATTERN.match(asset_path.name)
        if not match:
            return None

        prefix = match.group("prefix")
        extension = match.group("ext")
        candidates = sorted(
            asset_path.parent.glob(f"{prefix}.*.{extension}"),
            key=lambda candidate: candidate.stat().st_mtime,
            reverse=True,
        )
        return candidates[0] if candidates else None

    @app.get("/", include_in_schema=False)
    async def serve_frontend_root():
        index_path = build_root / "index.html"
        if index_path.exists():
            return FileResponse(index_path, headers={"Cache-Control": "no-cache"})
        return _api_metadata()

    @app.get("/{path:path}")
    async def serve_frontend(path: str = ""):
        """Serve frontend for any non-API route."""
        from fastapi.responses import JSONResponse
        
        # Serve static files directly
        if path.startswith("static/") or path.startswith("favicon"):
            file_path = build_root / path
            if file_path.exists():
                return FileResponse(file_path)

            fallback_file = _resolve_hashed_asset_fallback(file_path)
            if fallback_file:
                return FileResponse(fallback_file)
            return JSONResponse({"error": "Static file not found"}, status_code=404)
        
        # Don't interfere with API routes
        if path.startswith("api/"):
            return JSONResponse({"error": "API route not found"}, status_code=404)
        
        # Serve index.html for SPA routing
        index_path = build_root / "index.html"
        if index_path.exists():
            return FileResponse(index_path, headers={"Cache-Control": "no-cache"})
        return JSONResponse({"error": "Frontend not found"}, status_code=404)


if __name__ == "__main__":
    # Why uvicorn.run(): Production-ready ASGI server
    # Why reload=True: Development convenience for hot reloading
    # Security note: Configure host/port for your environment
    uvicorn.run(
        "buro.main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        log_level="info"
    )
