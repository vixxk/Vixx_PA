from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from uuid import UUID
from app.database import get_db
from app.models.timeline_event import TimelineEvent
from app.models.project import Project
from app.models.user import User
from app.schemas.timeline import TimelineEventCreate, TimelineEventUpdate, TimelineEventResponse
from app.utils.auth_helper import get_current_user

router = APIRouter(prefix="/timeline", tags=["Timeline"])

@router.get("/", response_model=List[TimelineEventResponse])
async def list_timeline_events(
    project_id: Optional[UUID] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    query = select(TimelineEvent).join(Project).filter(Project.user_id == current_user.id)
    if project_id:
        query = query.filter(TimelineEvent.project_id == project_id)

    result = await db.execute(query.order_by(TimelineEvent.event_date.asc()))
    return result.scalars().all()

@router.post("/", response_model=TimelineEventResponse, status_code=status.HTTP_201_CREATED)
async def create_timeline_event(
    event_data: TimelineEventCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Verify project belongs to user
    project_result = await db.execute(
        select(Project).filter(Project.id == event_data.project_id, Project.user_id == current_user.id)
    )
    project = project_result.scalars().first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found or access denied"
        )

    event = TimelineEvent(
        project_id=event_data.project_id,
        event_name=event_data.event_name,
        event_type=event_data.event_type,
        event_date=event_data.event_date,
        notes=event_data.notes,
        status=event_data.status
    )
    db.add(event)
    await db.commit()
    await db.refresh(event)
    return event

@router.put("/{event_id}", response_model=TimelineEventResponse)
async def update_timeline_event(
    event_id: UUID,
    event_data: TimelineEventUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(TimelineEvent).join(Project).filter(TimelineEvent.id == event_id, Project.user_id == current_user.id)
    )
    event = result.scalars().first()
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Timeline event not found"
        )

    update_dict = event_data.model_dump(exclude_unset=True)
    for key, value in update_dict.items():
        setattr(event, key, value)

    await db.commit()
    await db.refresh(event)
    return event
