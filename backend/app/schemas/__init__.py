"""Pydantic schemas for API validation."""

from app.schemas.project import (
    ProjectCreate,
    ProjectUpdate,
    ProjectResponse,
    ProjectListResponse,
)
from app.schemas.script import (
    ScriptCreate,
    ScriptUpdate,
    ScriptResponse,
    SegmentCreate,
    SegmentUpdate,
    SegmentResponse,
)
from app.schemas.generation import (
    GenerationStart,
    GenerationResponse,
    GenerationProgress,
    PreviewRequest,
)
from app.schemas.voice import VoiceInfo, VoiceListResponse
from app.schemas.template import (
    TemplateCreate,
    TemplateUpdate,
    TemplateResponse,
)

__all__ = [
    "ProjectCreate",
    "ProjectUpdate",
    "ProjectResponse",
    "ProjectListResponse",
    "ScriptCreate",
    "ScriptUpdate",
    "ScriptResponse",
    "SegmentCreate",
    "SegmentUpdate",
    "SegmentResponse",
    "GenerationStart",
    "GenerationResponse",
    "GenerationProgress",
    "PreviewRequest",
    "VoiceInfo",
    "VoiceListResponse",
    "TemplateCreate",
    "TemplateUpdate",
    "TemplateResponse",
]
