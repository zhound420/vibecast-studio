"""Health check endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.models.database import get_db
from app.config import settings

router = APIRouter()


@router.get("/health")
async def health_check():
    """Basic health check endpoint."""
    return {
        "status": "healthy",
        "app": settings.app_name,
        "version": "0.1.0",
    }


@router.get("/health/detailed")
async def detailed_health_check(db: AsyncSession = Depends(get_db)):
    """Detailed health check with dependency status."""
    status = {
        "status": "healthy",
        "app": settings.app_name,
        "version": "0.1.0",
        "components": {},
    }

    # Check database
    try:
        await db.execute(text("SELECT 1"))
        status["components"]["database"] = {"status": "healthy"}
    except Exception as e:
        status["components"]["database"] = {"status": "unhealthy", "error": str(e)}
        status["status"] = "degraded"

    # Check storage directories
    try:
        if settings.storage_path.exists():
            status["components"]["storage"] = {"status": "healthy"}
        else:
            status["components"]["storage"] = {"status": "unhealthy", "error": "Storage path not found"}
            status["status"] = "degraded"
    except Exception as e:
        status["components"]["storage"] = {"status": "unhealthy", "error": str(e)}
        status["status"] = "degraded"

    # Check Redis (via Celery)
    try:
        from app.workers.celery_app import celery_app
        celery_app.control.ping(timeout=1)
        status["components"]["redis"] = {"status": "healthy"}
    except Exception:
        status["components"]["redis"] = {"status": "unknown", "error": "Could not ping workers"}

    return status
