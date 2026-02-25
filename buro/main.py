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

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Why separate routers: Domain-driven organization
# Benefits: Independent testing, cleaner code, scalable when app grows
from api import auth, issues, projects, users, analytics
from core.database import engine
from models import Base

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
    version="0.1.0",
    lifespan=lifespan
)

# CORS configuration for development
# Why: Allows web browser communication from different origins
# Security note: In production, specify allowed origins explicitly
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "*",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001",
        "http://localhost:3002",
        "http://127.0.0.1:3002",
        "http://localhost:4000",
        "http://127.0.0.1:4000",
        "http://localhost:5000",
        "http://127.0.0.1:5000",
        "http://localhost:6000",
        "http://127.0.0.1:6000"
    ],  # Wildcard + specific React dev server on multiple ports
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

# Root endpoint for health checks and API discovery
@app.get("/", tags=["health"])
async def root():
    """Health check endpoint for monitoring and discovery.

    Why GET / endpoint: Standard practice for service health checks.
    Returns basic API information for developers.

    Educational Note: Health checks are essential for:
    - Load balancer health monitoring
    - Container orchestration systems (Kubernetes, Docker Compose)
    - Monitoring dashboards
    """
    return {
        "name": "Buro API",
        "version": "0.1.0",
        "description": "Agile project management API",
        "docs": "/docs",         # Interactive Swagger UI
        "redoc": "/redoc",       # ReDoc documentation
        "openapi": "/openapi.json"  # OpenAPI spec
    }

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