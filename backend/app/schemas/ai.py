from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class AIProcessRequest(BaseModel):
    raw_input: str
    google_token: Optional[str] = None
    timezone_offset: Optional[int] = None
    local_time: Optional[str] = None
    session_id: Optional[str] = None


class AIFeedbackRequest(BaseModel):
    rating: int  # 1 = thumbs up, -1 = thumbs down
    feedback_text: Optional[str] = None


class ProjectStateSchema(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    total_amount: Optional[float] = None

class AIProcessResponse(BaseModel):
    intent: str
    needs_clarification: bool
    clarification_message: Optional[str] = None
    missing_fields: List[str] = []
    project: Optional[ProjectStateSchema] = None
    timeline: List[Dict[str, Any]] = []
    todos: List[Dict[str, Any]] = []
    milestones: List[Dict[str, Any]] = []
    risks: List[Dict[str, Any]] = []
    reminder: Optional[Dict[str, Any]] = None
    payment: Optional[Dict[str, Any]] = None
    report: Optional[Dict[str, Any]] = None
    summary: Optional[str] = None
    reasoning_steps: List[str] = []

