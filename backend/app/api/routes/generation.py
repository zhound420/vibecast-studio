"""Generation API routes."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import get_db
from app.models.project import Project
from app.models.script import Script, Segment
from app.models.generation import GenerationJob, GenerationStatus
from app.schemas.generation import (
    GenerationStart,
    GenerationResponse,
    PreviewRequest,
    QueueStatus,
)

router = APIRouter()


@router.post("/start", response_model=GenerationResponse, status_code=201)
async def start_generation(
    request: GenerationStart,
    db: AsyncSession = Depends(get_db),
):
    """Start a new generation job."""
    # Verify project exists
    query = select(Project).where(Project.id == request.project_id)
    result = await db.execute(query)
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Get script and segments
    script_query = select(Script).where(Script.project_id == request.project_id)
    result = await db.execute(script_query)
    script = result.scalar_one_or_none()

    if not script:
        raise HTTPException(status_code=400, detail="No script found for project")

    segments_query = (
        select(Segment)
        .where(Segment.script_id == script.id)
        .order_by(Segment.order)
    )
    result = await db.execute(segments_query)
    segments = result.scalars().all()

    if not segments:
        raise HTTPException(status_code=400, detail="No segments in script")

    # Determine voice mapping
    voice_mapping = request.voice_mapping or project.voice_mapping or {}

    # Create generation job
    job = GenerationJob(
        project_id=request.project_id,
        status=GenerationStatus.QUEUED,
        voice_mapping=voice_mapping,
        options=request.options or {},
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)

    # Queue the Celery task
    try:
        from app.workers.tasks.generation import generate_audio_task

        # Prepare segments data for Celery
        segments_data = [
            {
                "id": seg.id,
                "text": seg.text,
                "speaker_id": seg.speaker_id,
                "speaker_name": seg.speaker_name,
                "voice_id": seg.voice_id,
                "order": seg.order,
            }
            for seg in segments
        ]

        task = generate_audio_task.delay(
            job_id=job.id,
            script_segments=segments_data,
            voice_mapping=voice_mapping,
            options=request.options or {},
        )

        # Update job with Celery task ID
        job.celery_task_id = task.id
        await db.commit()
        await db.refresh(job)

    except Exception as e:
        job.status = GenerationStatus.FAILED
        job.error_message = f"Failed to queue task: {str(e)}"
        await db.commit()
        raise HTTPException(status_code=500, detail=str(e))

    return GenerationResponse.model_validate(job)


@router.get("/{job_id}", response_model=GenerationResponse)
async def get_generation_status(
    job_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get the status of a generation job."""
    query = select(GenerationJob).where(GenerationJob.id == job_id)
    result = await db.execute(query)
    job = result.scalar_one_or_none()

    if not job:
        raise HTTPException(status_code=404, detail="Generation job not found")

    return GenerationResponse.model_validate(job)


@router.post("/{job_id}/cancel", response_model=GenerationResponse)
async def cancel_generation(
    job_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Cancel a generation job."""
    query = select(GenerationJob).where(GenerationJob.id == job_id)
    result = await db.execute(query)
    job = result.scalar_one_or_none()

    if not job:
        raise HTTPException(status_code=404, detail="Generation job not found")

    if job.status in [GenerationStatus.COMPLETED, GenerationStatus.FAILED, GenerationStatus.CANCELLED]:
        raise HTTPException(status_code=400, detail="Job already finished")

    # Revoke the Celery task
    if job.celery_task_id:
        try:
            from app.workers.celery_app import celery_app
            celery_app.control.revoke(job.celery_task_id, terminate=True)
        except Exception:
            pass  # Task may already be done

    job.status = GenerationStatus.CANCELLED
    await db.commit()
    await db.refresh(job)

    return GenerationResponse.model_validate(job)


@router.get("/queue/status", response_model=QueueStatus)
async def get_queue_status(
    db: AsyncSession = Depends(get_db),
):
    """Get the current queue status."""
    # Count active and queued jobs
    active_query = select(GenerationJob).where(
        GenerationJob.status.in_([
            GenerationStatus.LOADING_MODEL,
            GenerationStatus.GENERATING,
            GenerationStatus.STITCHING,
        ])
    )
    result = await db.execute(active_query)
    active_jobs = len(result.scalars().all())

    queued_query = select(GenerationJob).where(
        GenerationJob.status == GenerationStatus.QUEUED
    )
    result = await db.execute(queued_query)
    queued_jobs = len(result.scalars().all())

    # Estimate wait time (~10 min per job)
    estimated_wait = (active_jobs + queued_jobs) * 600 if queued_jobs > 0 else None

    return QueueStatus(
        position=queued_jobs,
        estimated_wait=estimated_wait,
        active_jobs=active_jobs,
        queued_jobs=queued_jobs,
    )


@router.post("/preview", response_model=dict)
async def quick_preview(
    request: PreviewRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Generate a quick audio preview using the Realtime model.
    Returns a URL to the generated audio file.
    """
    # This would typically use the Realtime model for quick preview
    # For now, return a placeholder response
    return {
        "status": "preview_queued",
        "message": "Preview generation started. Use WebSocket for streaming.",
        "text_length": len(request.text),
        "voice_id": request.voice_id,
    }
