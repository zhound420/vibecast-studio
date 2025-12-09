"""TTS generation Celery task."""

from datetime import datetime
from typing import List, Dict, Any
import asyncio

from celery import shared_task

from app.workers.celery_app import GPUTask
from app.models.database import sync_session_factory
from app.models.generation import GenerationJob, GenerationStatus
from app.config import settings


@shared_task(base=GPUTask, bind=True, name="generate_audio")
def generate_audio_task(
    self,
    job_id: str,
    script_segments: List[Dict[str, Any]],
    voice_mapping: Dict[int, str],
    options: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Main generation task - runs on GPU worker.

    Args:
        job_id: Unique job identifier
        script_segments: List of segment dictionaries
        voice_mapping: speaker_id -> voice_name mapping
        options: Generation options

    Returns:
        Result dictionary with file paths and status
    """
    db = sync_session_factory()

    try:
        # Get the job record
        job = db.query(GenerationJob).filter(GenerationJob.id == job_id).first()
        if not job:
            return {"status": "failed", "error": "Job not found"}

        # Update job status
        job.status = GenerationStatus.LOADING_MODEL
        job.started_at = datetime.utcnow()
        db.commit()

        # Import generation components
        from app.services.vibevoice.chunker import ContentChunker
        from app.services.vibevoice.generator import VibeVoiceGenerator
        from pathlib import Path

        # Chunk the content
        chunker = ContentChunker()
        chunks = chunker.chunk_script(script_segments)

        job.total_chunks = len(chunks)
        job.status = GenerationStatus.GENERATING
        db.commit()

        # Set up progress callback
        def update_progress(progress_data: dict):
            """Update job progress in database."""
            job.progress = progress_data.get("overall_progress", 0)
            job.current_chunk = progress_data.get("current_chunk", 0)
            db.commit()

            # Broadcast via Redis pub/sub (for WebSocket)
            _broadcast_progress(job_id, progress_data)

        # Run generation
        generator = VibeVoiceGenerator(
            model_manager=self.model_manager,
            storage_path=Path(settings.storage_path),
            progress_callback=update_progress,
        )

        # Run the async generation
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            final_path = loop.run_until_complete(
                generator.generate_full(chunks, voice_mapping, job_id)
            )
        finally:
            loop.close()

        # Update job as completed
        job.status = GenerationStatus.COMPLETED
        job.output_path = str(final_path)
        job.progress = 100.0
        job.completed_at = datetime.utcnow()

        # Calculate audio duration (rough estimate from file size)
        if final_path.exists():
            # WAV at 24kHz mono: ~48KB per second
            file_size = final_path.stat().st_size
            job.audio_duration = int(file_size / 48000)

        db.commit()

        return {
            "status": "completed",
            "output_path": str(final_path),
            "chunks_generated": len(chunks),
            "audio_duration": job.audio_duration,
        }

    except Exception as e:
        # Update job as failed
        job = db.query(GenerationJob).filter(GenerationJob.id == job_id).first()
        if job:
            job.status = GenerationStatus.FAILED
            job.error_message = str(e)
            db.commit()

        return {"status": "failed", "error": str(e)}

    finally:
        db.close()


def _broadcast_progress(job_id: str, progress_data: dict):
    """Broadcast progress update via Redis pub/sub."""
    try:
        import redis
        import json

        r = redis.from_url(settings.redis_url)
        r.publish(
            f"progress:{job_id}",
            json.dumps({
                "type": "progress",
                "job_id": job_id,
                "data": progress_data,
            }),
        )
    except Exception:
        # Silently ignore broadcast failures
        pass
