from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional
from enum import Enum

class ProjectStatus(str, Enum):
    planning = "planning"
    developing = "developing"
    finished = "finished"

class ProjectBase(BaseModel):
    title: str
    description: Optional[str] = None
    status: Optional[ProjectStatus] = ProjectStatus.planning
    priority: Optional[str] = None
    deadline: Optional[datetime] = None
    total_amount: Optional[float] = 0.0
    notepad: Optional[str] = None

class ProjectCreate(ProjectBase):
    pass

class ProjectUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[ProjectStatus] = None
    priority: Optional[str] = None
    deadline: Optional[datetime] = None
    total_amount: Optional[float] = None
    notepad: Optional[str] = None

class ProjectResponse(ProjectBase):
    id: UUID
    user_id: UUID
    created_at: datetime

    class Config:
        from_attributes = True
