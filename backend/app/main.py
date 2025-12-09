"""FastAPI application entry point."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.api.routes import projects, scripts, generation, voices, content, templates, export, health
from app.api.websockets import progress, preview
from app.models.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup/shutdown events."""
    # Startup
    settings.ensure_directories()
    await init_db()
    yield
    # Shutdown
    pass


app = FastAPI(
    title=settings.app_name,
    description="Multi-speaker TTS content creation using VibeVoice models",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API routes
app.include_router(health.router, prefix="/api/v1", tags=["Health"])
app.include_router(projects.router, prefix="/api/v1/projects", tags=["Projects"])
app.include_router(scripts.router, prefix="/api/v1/scripts", tags=["Scripts"])
app.include_router(generation.router, prefix="/api/v1/generation", tags=["Generation"])
app.include_router(voices.router, prefix="/api/v1/voices", tags=["Voices"])
app.include_router(content.router, prefix="/api/v1/content", tags=["Content"])
app.include_router(templates.router, prefix="/api/v1/templates", tags=["Templates"])
app.include_router(export.router, prefix="/api/v1/export", tags=["Export"])

# WebSocket routes
app.include_router(progress.router, prefix="/api/v1/ws", tags=["WebSocket"])
app.include_router(preview.router, prefix="/api/v1/ws", tags=["WebSocket"])


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler for unhandled errors."""
    return JSONResponse(
        status_code=500,
        content={
            "detail": "An internal error occurred",
            "type": type(exc).__name__,
        },
    )
