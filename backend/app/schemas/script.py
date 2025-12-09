"""Pydantic schemas for Script and Segment API."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class SegmentBase(BaseModel):
    """Base schema for segment data."""
    text: str = Field(..., description="Segment text content")
    speaker_id: int = Field(1, ge=1, le=4, description="Speaker ID (1-4)")
    speaker_name: Optional[str] = Field(None, max_length=100, description="Speaker display name")
    voice_id: Optional[str] = Field(None, description="Override voice for this segment")
    direction: Optional[str] = Field(None, max_length=100, description="Acting direction/emotion")


class SegmentCreate(SegmentBase):
    """Schema for creating a new segment."""
    order: Optional[int] = Field(None, description="Segment order in script")


class SegmentUpdate(BaseModel):
    """Schema for updating a segment."""
    text: Optional[str] = None
    speaker_id: Optional[int] = Field(None, ge=1, le=4)
    speaker_name: Optional[str] = Field(None, max_length=100)
    voice_id: Optional[str] = None
    direction: Optional[str] = Field(None, max_length=100)
    order: Optional[int] = None


class SegmentResponse(SegmentBase):
    """Schema for segment response."""
    id: str
    script_id: str
    order: int
    estimated_duration: Optional[int]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ScriptBase(BaseModel):
    """Base schema for script data."""
    raw_content: Optional[str] = Field(None, description="Raw script content before segmentation")
    speakers: Optional[dict[str, str]] = Field(
        default_factory=dict,
        description="Speaker ID to name mapping"
    )


class ScriptCreate(ScriptBase):
    """Schema for creating a new script."""
    pass


class ScriptUpdate(BaseModel):
    """Schema for updating a script."""
    raw_content: Optional[str] = None
    speakers: Optional[dict[str, str]] = None


class ScriptResponse(ScriptBase):
    """Schema for script response."""
    id: str
    project_id: str
    estimated_duration: Optional[int]
    segments: list[SegmentResponse]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ParseRequest(BaseModel):
    """Schema for parsing text into segments."""
    text: str = Field(..., description="Text to parse into segments")
    format: Optional[str] = Field(
        "auto",
        description="Script format: auto, bracket, colon, numbered"
    )


class EnhanceRequest(BaseModel):
    """Schema for Claude dialogue enhancement."""
    text: str = Field(..., description="Text to enhance")
    style: str = Field("conversational", description="Enhancement style")
    target_speakers: int = Field(2, ge=1, le=4, description="Number of speakers")
    speaker_names: Optional[list[str]] = Field(None, description="Speaker names to use")
