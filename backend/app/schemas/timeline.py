from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional

class TimelineEventBase(BaseModel):
    event_name: str
    event_type: str # milestone, payment, contract, task_deadline, meeting
    event_date: datetime
    notes: Optional[str] = None
    status: Optional[str] = "pending" # pending, completed, overdue, cancelled
    project_id: UUID

class TimelineEventCreate(TimelineEventBase):
    pass

class TimelineEventUpdate(BaseModel):
    event_name: Optional[str] = None
    event_type: Optional[str] = None
    event_date: Optional[datetime] = None
    notes: Optional[str] = None
    status: Optional[str] = None

class TimelineEventResponse(TimelineEventBase):
    id: UUID
    created_at: datetime

    class Config:
        from_attributes = True
