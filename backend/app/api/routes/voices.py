"""Voice management API routes."""

from fastapi import APIRouter
from fastapi.responses import FileResponse

from app.schemas.voice import VoiceInfo, VoiceListResponse, EMBEDDED_VOICES

router = APIRouter()


@router.get("", response_model=VoiceListResponse)
async def list_voices():
    """List all available voices."""
    return VoiceListResponse(
        voices=EMBEDDED_VOICES,
        total=len(EMBEDDED_VOICES),
    )


@router.get("/embedded", response_model=list[VoiceInfo])
async def list_embedded_voices():
    """List only embedded voices from VibeVoice."""
    return EMBEDDED_VOICES


@router.get("/{voice_id}", response_model=VoiceInfo)
async def get_voice(voice_id: str):
    """Get information about a specific voice."""
    for voice in EMBEDDED_VOICES:
        if voice.id == voice_id:
            return voice

    from fastapi import HTTPException
    raise HTTPException(status_code=404, detail="Voice not found")


@router.get("/{voice_id}/preview")
async def preview_voice(voice_id: str):
    """
    Get a preview audio sample for a voice.
    Returns a pre-generated sample audio file.
    """
    from pathlib import Path
    from app.config import settings

    # Check if preview file exists
    preview_path = settings.storage_path / "previews" / f"{voice_id}.wav"

    if not preview_path.exists():
        # Return a 404 if no preview is available
        # In production, this would trigger generation of a sample
        from fastapi import HTTPException
        raise HTTPException(
            status_code=404,
            detail="Voice preview not yet generated"
        )

    return FileResponse(
        path=preview_path,
        media_type="audio/wav",
        filename=f"{voice_id}_preview.wav",
    )
