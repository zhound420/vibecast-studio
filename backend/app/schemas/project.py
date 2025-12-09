"""Pydantic schemas for Project API."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class ProjectBase(BaseModel):
    """Base schema for project data."""
    name: str = Field(..., min_length=1, max_length=255, description="Project name")
    description: Optional[str] = Field(None, description="Project description")


class ProjectCreate(ProjectBase):
    """Schema for creating a new project."""
    voice_mapping: Optional[dict[int, str]] = Field(
        default_factory=dict,
        description="Speaker ID to voice ID mapping"
    )
    settings: Optional[dict] = Field(
        default_factory=dict,
        description="Project-specific settings"
    )


class ProjectUpdate(BaseModel):
    """Schema for updating a project."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    voice_mapping: Optional[dict[int, str]] = None
    settings: Optional[dict] = None


class ProjectResponse(ProjectBase):
    """Schema for project response."""
    id: str
    voice_mapping: dict[int, str]
    settings: dict
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ProjectListResponse(BaseModel):
    """Schema for listing projects."""
    items: list[ProjectResponse]
    total: int
