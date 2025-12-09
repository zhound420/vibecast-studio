"""Script and segment management API routes."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.database import get_db
from app.models.script import Script, Segment
from app.schemas.script import (
    ScriptResponse,
    ScriptUpdate,
    SegmentCreate,
    SegmentUpdate,
    SegmentResponse,
    ParseRequest,
    EnhanceRequest,
)

router = APIRouter()


@router.get("/{project_id}", response_model=ScriptResponse)
async def get_script(
    project_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get the script for a project."""
    query = (
        select(Script)
        .where(Script.project_id == project_id)
        .options(selectinload(Script.segments))
    )
    result = await db.execute(query)
    script = result.scalar_one_or_none()

    if not script:
        raise HTTPException(status_code=404, detail="Script not found for this project")

    return ScriptResponse.model_validate(script)


@router.put("/{project_id}", response_model=ScriptResponse)
async def update_script(
    project_id: str,
    script_data: ScriptUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update the script for a project."""
    query = (
        select(Script)
        .where(Script.project_id == project_id)
        .options(selectinload(Script.segments))
    )
    result = await db.execute(query)
    script = result.scalar_one_or_none()

    if not script:
        raise HTTPException(status_code=404, detail="Script not found for this project")

    update_data = script_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(script, field, value)

    await db.commit()
    await db.refresh(script)

    return ScriptResponse.model_validate(script)


@router.get("/{project_id}/segments", response_model=list[SegmentResponse])
async def get_segments(
    project_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get all segments for a project's script."""
    query = select(Script).where(Script.project_id == project_id)
    result = await db.execute(query)
    script = result.scalar_one_or_none()

    if not script:
        raise HTTPException(status_code=404, detail="Script not found for this project")

    query = (
        select(Segment)
        .where(Segment.script_id == script.id)
        .order_by(Segment.order)
    )
    result = await db.execute(query)
    segments = result.scalars().all()

    return [SegmentResponse.model_validate(s) for s in segments]


@router.post("/{project_id}/segments", response_model=SegmentResponse, status_code=201)
async def create_segment(
    project_id: str,
    segment_data: SegmentCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a new segment in the script."""
    query = select(Script).where(Script.project_id == project_id)
    result = await db.execute(query)
    script = result.scalar_one_or_none()

    if not script:
        raise HTTPException(status_code=404, detail="Script not found for this project")

    # Get the next order value if not specified
    if segment_data.order is None:
        max_order_query = select(Segment.order).where(
            Segment.script_id == script.id
        ).order_by(Segment.order.desc()).limit(1)
        result = await db.execute(max_order_query)
        max_order = result.scalar_one_or_none()
        order = (max_order or 0) + 1
    else:
        order = segment_data.order

    # Estimate duration based on word count (~150 WPM)
    word_count = len(segment_data.text.split())
    estimated_duration = int((word_count / 150) * 60)

    segment = Segment(
        script_id=script.id,
        text=segment_data.text,
        speaker_id=segment_data.speaker_id,
        speaker_name=segment_data.speaker_name,
        voice_id=segment_data.voice_id,
        direction=segment_data.direction,
        order=order,
        estimated_duration=estimated_duration,
    )
    db.add(segment)
    await db.commit()
    await db.refresh(segment)

    return SegmentResponse.model_validate(segment)


@router.put("/{project_id}/segments/{segment_id}", response_model=SegmentResponse)
async def update_segment(
    project_id: str,
    segment_id: str,
    segment_data: SegmentUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update a segment."""
    query = select(Segment).where(Segment.id == segment_id)
    result = await db.execute(query)
    segment = result.scalar_one_or_none()

    if not segment:
        raise HTTPException(status_code=404, detail="Segment not found")

    update_data = segment_data.model_dump(exclude_unset=True)

    # Recalculate duration if text changed
    if "text" in update_data:
        word_count = len(update_data["text"].split())
        update_data["estimated_duration"] = int((word_count / 150) * 60)

    for field, value in update_data.items():
        setattr(segment, field, value)

    await db.commit()
    await db.refresh(segment)

    return SegmentResponse.model_validate(segment)


@router.delete("/{project_id}/segments/{segment_id}", status_code=204)
async def delete_segment(
    project_id: str,
    segment_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Delete a segment."""
    query = select(Segment).where(Segment.id == segment_id)
    result = await db.execute(query)
    segment = result.scalar_one_or_none()

    if not segment:
        raise HTTPException(status_code=404, detail="Segment not found")

    await db.delete(segment)
    await db.commit()

    return None


@router.post("/{project_id}/parse", response_model=list[SegmentResponse])
async def parse_text_to_segments(
    project_id: str,
    parse_request: ParseRequest,
    db: AsyncSession = Depends(get_db),
):
    """Parse text into segments using the script parser."""
    from app.services.content.parser import ScriptParser

    query = select(Script).where(Script.project_id == project_id)
    result = await db.execute(query)
    script = result.scalar_one_or_none()

    if not script:
        raise HTTPException(status_code=404, detail="Script not found for this project")

    # Parse the text
    parser = ScriptParser()
    parsed_segments = parser.parse(parse_request.text, format=parse_request.format)

    # Clear existing segments
    delete_query = select(Segment).where(Segment.script_id == script.id)
    result = await db.execute(delete_query)
    for seg in result.scalars().all():
        await db.delete(seg)

    # Create new segments
    segments = []
    for idx, seg_data in enumerate(parsed_segments):
        word_count = len(seg_data["text"].split())
        estimated_duration = int((word_count / 150) * 60)

        segment = Segment(
            script_id=script.id,
            text=seg_data["text"],
            speaker_id=seg_data["speaker_id"],
            speaker_name=seg_data.get("speaker_name"),
            direction=seg_data.get("direction"),
            order=idx,
            estimated_duration=estimated_duration,
        )
        db.add(segment)
        segments.append(segment)

    # Update script raw content
    script.raw_content = parse_request.text

    await db.commit()

    # Refresh all segments
    for segment in segments:
        await db.refresh(segment)

    return [SegmentResponse.model_validate(s) for s in segments]


@router.post("/{project_id}/enhance", response_model=dict)
async def enhance_with_claude(
    project_id: str,
    enhance_request: EnhanceRequest,
    db: AsyncSession = Depends(get_db),
):
    """Enhance text to dialogue using Claude API."""
    from app.services.claude.dialogue_enhancer import DialogueEnhancer
    from app.config import settings

    if not settings.claude_api_key:
        raise HTTPException(
            status_code=400,
            detail="Claude API key not configured"
        )

    enhancer = DialogueEnhancer(settings.claude_api_key)

    try:
        enhanced_text = await enhancer.enhance_to_dialogue(
            content=enhance_request.text,
            style=enhance_request.style,
            target_speakers=enhance_request.target_speakers,
            speaker_names=enhance_request.speaker_names,
        )
        return {"enhanced_text": enhanced_text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Enhancement failed: {str(e)}")
