from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional

class PendingThingBase(BaseModel):
    project_id: UUID
    title: str
    description: Optional[str] = None
    is_completed: bool = False
    filename: Optional[str] = None
    file_url: Optional[str] = None
    file_size: Optional[int] = None
    file_type: Optional[str] = None

class PendingThingCreate(BaseModel):
    project_id: UUID
    title: str
    description: Optional[str] = None
    is_completed: Optional[bool] = False

class PendingThingUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    is_completed: Optional[bool] = None
    filename: Optional[str] = None
    file_url: Optional[str] = None
    file_size: Optional[int] = None
    file_type: Optional[str] = None

class PendingThingResponse(PendingThingBase):
    id: UUID
    created_at: datetime

    class Config:
        from_attributes = True
