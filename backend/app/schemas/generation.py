"""Pydantic schemas for Generation API."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.models.generation import GenerationStatus


class GenerationStart(BaseModel):
    """Schema for starting a generation job."""
    project_id: str = Field(..., description="Project ID to generate audio for")
    voice_mapping: Optional[dict[int, str]] = Field(
        None,
        description="Override voice mapping for this generation"
    )
    options: Optional[dict] = Field(
        default_factory=dict,
        description="Generation options"
    )


class GenerationProgress(BaseModel):
    """Schema for generation progress updates."""
    job_id: str
    status: GenerationStatus
    progress: float = Field(ge=0, le=100, description="Overall progress percentage")
    current_chunk: int
    total_chunks: int
    chunk_progress: float = Field(ge=0, le=100, description="Current chunk progress")
    estimated_time_remaining: Optional[int] = Field(None, description="Seconds remaining")
    error_message: Optional[str] = None


class GenerationResponse(BaseModel):
    """Schema for generation job response."""
    id: str
    project_id: str
    status: GenerationStatus
    progress: float
    current_chunk: int
    total_chunks: int
    output_path: Optional[str]
    error_message: Optional[str]
    audio_duration: Optional[int]
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True


class PreviewRequest(BaseModel):
    """Schema for quick preview generation."""
    text: str = Field(..., max_length=5000, description="Text to preview")
    voice_id: str = Field("en-Carter_man", description="Voice to use for preview")


class QueueStatus(BaseModel):
    """Schema for queue status response."""
    position: int = Field(description="Position in queue (0 = processing)")
    estimated_wait: Optional[int] = Field(None, description="Estimated wait in seconds")
    active_jobs: int
    queued_jobs: int
