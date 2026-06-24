from typing import TypedDict, List, Dict, Any, Optional

class ProjectState(TypedDict):
    title: Optional[str]
    description: Optional[str]

class WorkflowState(TypedDict):
    user_id: str
    raw_input: str
    intent: str  # create_project, update_timeline, create_task, track_payment, set_reminder, generate_report, generate_summary, clarify
    
    # State accumulated / modified by nodes
    project: Optional[ProjectState]
    timeline: List[Dict[str, Any]]
    todos: List[Dict[str, Any]]
    milestones: List[Dict[str, Any]]
    risks: List[Dict[str, Any]]
    payment: Optional[Dict[str, Any]]
    reminder: Optional[Dict[str, Any]]
    pending: Optional[Dict[str, Any]]
    report: Optional[Dict[str, Any]]  # NEW: for generate_report intent
    client: Optional[Dict[str, Any]]  # NEW: for manage_client intent
    analytics: Optional[Dict[str, Any]]  # NEW: for analytics intent
    summary: Optional[str]
    
    # Interaction / Control flow
    needs_clarification: bool
    clarification_message: Optional[str]
    missing_fields: List[str]
    
    # Validation / Approval status
    approved: bool
    confirmed_deletion: Optional[bool]
    
    # Context Preservation
    history: Optional[List[Dict[str, str]]]
    last_project: Optional[Dict[str, Any]]
    google_token: Optional[str]
    reasoning_steps: List[str]
    local_time: Optional[str]
    timezone_offset: Optional[int]
