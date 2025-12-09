"""Pydantic schemas for Template API."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class TemplateBase(BaseModel):
    """Base schema for template data."""
    name: str = Field(..., min_length=1, max_length=255, description="Template name")
    description: Optional[str] = Field(None, description="Template description")
    category: str = Field("general", description="Template category")


class TemplateCreate(TemplateBase):
    """Schema for creating a new template."""
    voice_mapping: Optional[dict[int, str]] = Field(
        default_factory=dict,
        description="Default speaker to voice mapping"
    )
    speakers: Optional[dict[str, str]] = Field(
        default_factory=dict,
        description="Speaker configuration"
    )
    structure: Optional[dict] = Field(
        None,
        description="Script structure template"
    )
    settings: Optional[dict] = Field(
        default_factory=dict,
        description="Default generation settings"
    )


class TemplateUpdate(BaseModel):
    """Schema for updating a template."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    category: Optional[str] = None
    voice_mapping: Optional[dict[int, str]] = None
    speakers: Optional[dict[str, str]] = None
    structure: Optional[dict] = None
    settings: Optional[dict] = None


class TemplateResponse(TemplateBase):
    """Schema for template response."""
    id: str
    voice_mapping: dict[int, str]
    speakers: dict[str, str]
    structure: Optional[dict]
    settings: dict
    is_system: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
