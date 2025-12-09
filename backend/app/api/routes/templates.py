"""Template management API routes."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import get_db
from app.models.template import Template
from app.schemas.template import (
    TemplateCreate,
    TemplateUpdate,
    TemplateResponse,
)

router = APIRouter()


@router.get("", response_model=list[TemplateResponse])
async def list_templates(
    category: Optional[str] = None,
    include_system: bool = True,
    db: AsyncSession = Depends(get_db),
):
    """List all templates."""
    query = select(Template)

    if category:
        query = query.where(Template.category == category)

    if not include_system:
        query = query.where(Template.is_system == False)

    query = query.order_by(Template.is_system.desc(), Template.name)
    result = await db.execute(query)
    templates = result.scalars().all()

    return [TemplateResponse.model_validate(t) for t in templates]


@router.post("", response_model=TemplateResponse, status_code=201)
async def create_template(
    template_data: TemplateCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a new template."""
    template = Template(
        name=template_data.name,
        description=template_data.description,
        category=template_data.category,
        voice_mapping=template_data.voice_mapping or {},
        speakers=template_data.speakers or {},
        structure=template_data.structure,
        settings=template_data.settings or {},
        is_system=False,
    )
    db.add(template)
    await db.commit()
    await db.refresh(template)

    return TemplateResponse.model_validate(template)


@router.get("/{template_id}", response_model=TemplateResponse)
async def get_template(
    template_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get a template by ID."""
    query = select(Template).where(Template.id == template_id)
    result = await db.execute(query)
    template = result.scalar_one_or_none()

    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    return TemplateResponse.model_validate(template)


@router.put("/{template_id}", response_model=TemplateResponse)
async def update_template(
    template_id: str,
    template_data: TemplateUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update a template."""
    query = select(Template).where(Template.id == template_id)
    result = await db.execute(query)
    template = result.scalar_one_or_none()

    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    if template.is_system:
        raise HTTPException(status_code=400, detail="Cannot modify system templates")

    update_data = template_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(template, field, value)

    await db.commit()
    await db.refresh(template)

    return TemplateResponse.model_validate(template)


@router.delete("/{template_id}", status_code=204)
async def delete_template(
    template_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Delete a template."""
    query = select(Template).where(Template.id == template_id)
    result = await db.execute(query)
    template = result.scalar_one_or_none()

    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    if template.is_system:
        raise HTTPException(status_code=400, detail="Cannot delete system templates")

    await db.delete(template)
    await db.commit()

    return None
