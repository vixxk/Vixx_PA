from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from uuid import UUID, uuid4
import os
import shutil

from app.database import get_db
from app.models.pending_thing import PendingThing
from app.models.project import Project
from app.models.user import User
from app.schemas.pending_thing import PendingThingResponse, PendingThingUpdate
from app.utils.auth_helper import get_current_user

router = APIRouter(prefix="/pending-things", tags=["Pending Things"])

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.get("/", response_model=List[PendingThingResponse])
async def list_pending_things(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Fetch projects belonging to user
    proj_stmt = select(Project.id).filter(Project.user_id == current_user.id)
    proj_result = await db.execute(proj_stmt)
    proj_ids = proj_result.scalars().all()
    
    if not proj_ids:
        return []
        
    result = await db.execute(
        select(PendingThing).filter(PendingThing.project_id.in_(proj_ids)).order_by(PendingThing.created_at.desc())
    )
    return result.scalars().all()

@router.post("/", response_model=PendingThingResponse, status_code=status.HTTP_201_CREATED)
async def create_pending_thing(
    project_id: UUID = Form(...),
    title: str = Form(...),
    description: Optional[str] = Form(None),
    is_completed: bool = Form(False),
    file: Optional[UploadFile] = File(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Validate project belongs to user
    proj_stmt = select(Project).filter(Project.id == project_id, Project.user_id == current_user.id)
    proj_result = await db.execute(proj_stmt)
    project = proj_result.scalars().first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found or access denied"
        )
        
    filename = None
    file_url = None
    file_size = None
    file_type = None

    if file and file.filename:
        file_ext = os.path.splitext(file.filename)[1]
        unique_filename = f"{uuid4()}{file_ext}"
        file_path = os.path.join(UPLOAD_DIR, unique_filename)
        
        # Save file to disk
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        file_url = f"/uploads/{unique_filename}"
        filename = file.filename
        file_type = file.content_type
        # We can read file size or keep it 0 / null
        file_size = 0
    
    pending_thing = PendingThing(
        project_id=project_id,
        title=title,
        description=description,
        is_completed=is_completed,
        filename=filename,
        file_url=file_url,
        file_size=file_size,
        file_type=file_type
    )
    db.add(pending_thing)
    await db.commit()
    await db.refresh(pending_thing)
    return pending_thing

@router.put("/{pending_thing_id}", response_model=PendingThingResponse)
async def update_pending_thing(
    pending_thing_id: UUID,
    thing_data: PendingThingUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(PendingThing).join(Project).filter(PendingThing.id == pending_thing_id, Project.user_id == current_user.id)
    result = await db.execute(stmt)
    pending_thing = result.scalars().first()
    if not pending_thing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pending thing not found or access denied"
        )
        
    update_dict = thing_data.model_dump(exclude_unset=True)
    for key, value in update_dict.items():
        setattr(pending_thing, key, value)
        
    await db.commit()
    await db.refresh(pending_thing)
    return pending_thing

@router.delete("/{pending_thing_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_pending_thing(
    pending_thing_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(PendingThing).join(Project).filter(PendingThing.id == pending_thing_id, Project.user_id == current_user.id)
    result = await db.execute(stmt)
    pending_thing = result.scalars().first()
    if not pending_thing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pending thing not found"
        )
        
    # Delete local file if exists
    if pending_thing.file_url and pending_thing.file_url.startswith("/uploads/"):
        filename = pending_thing.file_url.replace("/uploads/", "")
        file_path = os.path.join(UPLOAD_DIR, filename)
        if os.path.exists(file_path):
            try: os.remove(file_path)
            except: pass
            
    await db.delete(pending_thing)
    await db.commit()
    return None
