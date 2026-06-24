import json
import re
from datetime import datetime, timedelta
from typing import Dict, Any
from app.graphs.state import WorkflowState
from app.utils.llm import get_llm
from langchain_core.messages import SystemMessage, HumanMessage

async def run_timeline_agent(state: WorkflowState) -> Dict[str, Any]:
    intent = state.get("intent")
    project = state.get("project")
    needs_clarification = state.get("needs_clarification", False)

    if intent != "create_project" or not project or needs_clarification:
        return {}

    title = project.get("title")
    description = project.get("description") or "No description provided."
    deadline = project.get("deadline")
    priority = project.get("priority") or "medium"
    
    # Calculate fallback dates in case LLM is slow or offline
    import dateutil.parser
    now = datetime.utcnow()
    deadline_dt = now + timedelta(days=90)
    if deadline:
        try:
            deadline_dt = dateutil.parser.parse(deadline)
        except Exception:
            try:
                deadline_dt = datetime.fromisoformat(deadline.replace("Z", ""))
            except Exception:
                pass
    total_days = (deadline_dt - now).days
    if total_days < 7:
        total_days = 30
        deadline_dt = now + timedelta(days=30)
    
    milestones = []
    timeline_events = []
    
    try:
        llm = get_llm()
        system_prompt = (
            "You are a Project Timeline Architect agent. Your goal is to break down a project into "
            "logical milestones and timeline events distributed from the current date until the deadline.\n\n"
            f"Current Date: {now.strftime('%Y-%m-%d')}\n"
            f"Project Title: {title}\n"
            f"Project Description: {description}\n"
            f"Project Deadline: {deadline_dt.strftime('%Y-%m-%d')}\n"
            f"Project Priority: {priority}\n\n"
            "Generate 3-4 major project milestones. For each milestone, provide:\n"
            "- title: milestone name\n"
            "- description: what is accomplished\n"
            "- start_date: YYYY-MM-DD\n"
            "- end_date: YYYY-MM-DD\n"
            "- status: 'planned'\n\n"
            "Also generate 4-5 key timeline events. For each event, provide:\n"
            "- event_name: event name\n"
            "- event_type: one of 'milestone', 'payment', 'contract', 'task_deadline', 'meeting'\n"
            "- event_date: YYYY-MM-DD\n"
            "- notes: brief notes\n"
            "- status: 'pending'\n\n"
            "Format the output strictly as a JSON object with two top-level keys: 'milestones' and 'timeline_events'. "
            "Do not include any other text outside the JSON."
        )
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"Create a project plan timeline for '{title}'")
        ]
        
        response = await llm.ainvoke(messages)
        content = response.content.strip()
        
        match = re.search(r"\{.*\}", content, re.DOTALL)
        if match:
            data = json.loads(match.group(0))
            milestones = data.get("milestones", [])
            timeline_events = data.get("timeline_events", [])
            
    except Exception as e:
        # Fallback timeline generation if LLM fails
        m1_end = now + timedelta(days=int(total_days * 0.2))
        m2_end = now + timedelta(days=int(total_days * 0.6))
        m3_end = deadline_dt
        
        milestones = [
            {
                "title": "Kickoff and Design Phase",
                "description": "Establish architecture, designs, and database schemas.",
                "start_date": now.strftime("%Y-%m-%d"),
                "end_date": m1_end.strftime("%Y-%m-%d"),
                "status": "planned"
            },
            {
                "title": "Core Development Phase",
                "description": "Implement essential API endpoints and key frontend modules.",
                "start_date": m1_end.strftime("%Y-%m-%d"),
                "end_date": m2_end.strftime("%Y-%m-%d"),
                "status": "planned"
            },
            {
                "title": "QA, Testing, and Deployment",
                "description": "Perform end-to-end integration tests and release production build.",
                "start_date": m2_end.strftime("%Y-%m-%d"),
                "end_date": m3_end.strftime("%Y-%m-%d"),
                "status": "planned"
            }
        ]
        
        timeline_events = [
            {
                "event_name": "Project Kickoff Meeting",
                "event_type": "meeting",
                "event_date": now.strftime("%Y-%m-%d"),
                "notes": "Define requirements and align expectations.",
                "status": "pending"
            },
            {
                "event_name": "Database Schema Setup",
                "event_type": "milestone",
                "event_date": m1_end.strftime("%Y-%m-%d"),
                "notes": "Finalize database models and migrations.",
                "status": "pending"
            },
            {
                "event_name": "API Completion Checkpoint",
                "event_type": "milestone",
                "event_date": m2_end.strftime("%Y-%m-%d"),
                "notes": "Verify all REST routes work correctly.",
                "status": "pending"
            },
            {
                "event_name": "Product Launch",
                "event_type": "milestone",
                "event_date": m3_end.strftime("%Y-%m-%d"),
                "notes": "Deploy build to production server.",
                "status": "pending"
            }
        ]

    return {
        "milestones": milestones,
        "timeline": timeline_events
    }
