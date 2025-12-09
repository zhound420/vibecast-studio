"""Audio export API routes."""

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import get_db
from app.models.generation import GenerationJob, GenerationStatus
from app.config import settings

router = APIRouter()


class ExportRequest(BaseModel):
    """Request schema for audio export."""
    job_id: str = Field(..., description="Generation job ID to export")
    format: str = Field("mp3", description="Export format: mp3, wav")
    quality: str = Field("high", description="Quality: low, medium, high")
    include_chapters: bool = Field(True, description="Include chapter markers")
    include_metadata: bool = Field(True, description="Include metadata tags")


class ExportResponse(BaseModel):
    """Response schema for export."""
    export_id: str
    status: str
    format: str
    estimated_size_mb: float


class ExportStatusResponse(BaseModel):
    """Response schema for export status."""
    export_id: str
    status: str
    progress: float
    output_path: str | None
    error_message: str | None


@router.post("", response_model=ExportResponse, status_code=201)
async def start_export(
    request: ExportRequest,
    db: AsyncSession = Depends(get_db),
):
    """Start an audio export job."""
    # Verify generation job exists and is completed
    query = select(GenerationJob).where(GenerationJob.id == request.job_id)
    result = await db.execute(query)
    job = result.scalar_one_or_none()

    if not job:
        raise HTTPException(status_code=404, detail="Generation job not found")

    if job.status != GenerationStatus.COMPLETED:
        raise HTTPException(
            status_code=400,
            detail="Generation job not completed"
        )

    if not job.output_path:
        raise HTTPException(
            status_code=400,
            detail="No output file available"
        )

    # Check if source file exists
    source_path = Path(job.output_path)
    if not source_path.exists():
        raise HTTPException(
            status_code=404,
            detail="Source audio file not found"
        )

    # For now, return immediate response for direct conversion
    # In production, this would queue a Celery task
    from uuid import uuid4
    export_id = str(uuid4())

    # Estimate size based on duration and format
    duration_seconds = job.audio_duration or 0
    if request.format == "mp3":
        # ~1.5 MB per minute at high quality
        bitrate_factor = {"low": 0.5, "medium": 1.0, "high": 1.5}
        estimated_size = (duration_seconds / 60) * bitrate_factor.get(request.quality, 1.0)
    else:
        # WAV: ~10 MB per minute at 24kHz mono
        estimated_size = (duration_seconds / 60) * 10

    return ExportResponse(
        export_id=export_id,
        status="processing",
        format=request.format,
        estimated_size_mb=round(estimated_size, 2),
    )


@router.get("/{export_id}", response_model=ExportStatusResponse)
async def get_export_status(
    export_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get the status of an export job."""
    # In production, this would check a database record
    # For now, return a mock response
    return ExportStatusResponse(
        export_id=export_id,
        status="completed",
        progress=100.0,
        output_path=None,
        error_message=None,
    )


@router.get("/{export_id}/download")
async def download_export(
    export_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Download an exported audio file."""
    # In production, this would look up the export record
    # and return the actual file

    # For now, return a 404 as no exports exist yet
    raise HTTPException(
        status_code=404,
        detail="Export file not found"
    )


@router.get("/job/{job_id}/download")
async def download_generation_output(
    job_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Download the raw output from a generation job."""
    query = select(GenerationJob).where(GenerationJob.id == job_id)
    result = await db.execute(query)
    job = result.scalar_one_or_none()

    if not job:
        raise HTTPException(status_code=404, detail="Generation job not found")

    if job.status != GenerationStatus.COMPLETED:
        raise HTTPException(
            status_code=400,
            detail="Generation job not completed"
        )

    if not job.output_path:
        raise HTTPException(
            status_code=404,
            detail="No output file available"
        )

    output_path = Path(job.output_path)
    if not output_path.exists():
        raise HTTPException(
            status_code=404,
            detail="Output file not found on disk"
        )

    return FileResponse(
        path=output_path,
        media_type="audio/wav",
        filename=f"vibecast_{job_id}.wav",
    )
