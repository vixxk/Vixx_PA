import json
import re
from datetime import datetime, timedelta
from typing import Dict, Any
from app.graphs.state import WorkflowState
from app.utils.llm import get_llm
from langchain_core.messages import SystemMessage, HumanMessage

async def run_todo_agent(state: WorkflowState) -> Dict[str, Any]:
    intent = state.get("intent")
    project = state.get("project")
    milestones = state.get("milestones") or []
    needs_clarification = state.get("needs_clarification", False)

    if intent != "create_project" or not project or needs_clarification:
        return {}

    title = project.get("title")
    description = project.get("description") or "No description provided."
    deadline = project.get("deadline")
    
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
    
    todos = []
    
    try:
        llm = get_llm()
        milestones_str = "\n".join([f"- {m.get('title')}: {m.get('description')}" for m in milestones])
        
        system_prompt = (
            "You are a Technical Product Manager / Scrum Master agent. Your job is to break down a project into "
            "detailed engineering tasks (todos) based on the project description and major milestones.\n\n"
            f"Project: {title}\n"
            f"Description: {description}\n"
            f"Milestones:\n{milestones_str}\n\n"
            "Generate 5-7 actionable, granular tasks (todos) necessary to execute this project. For each task, provide:\n"
            "- title: clear name of the task\n"
            "- description: technical explanation of what to do\n"
            "- priority: 'low', 'medium', 'high', or 'critical'\n"
            "- estimated_hours: decimal value (e.g. 4.0, 8.5)\n"
            "- due_date: YYYY-MM-DD (estimate realistic dates preceding the project deadline)\n"
            "- milestone_title: (Optional) title of the milestone this task belongs to\n\n"
            "Format the output strictly as a JSON object containing a 'todos' key with the list of tasks. "
            "Do not include any other text."
        )
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"Create a sprint task breakdown for project '{title}'")
        ]
        
        response = await llm.ainvoke(messages)
        content = response.content.strip()
        
        match = re.search(r"\{.*\}", content, re.DOTALL)
        if match:
            data = json.loads(match.group(0))
            todos = data.get("todos", [])
            
    except Exception as e:
        # Fallback tasks if LLM fails
        todos = [
            {
                "title": "Configure Backend API Shell",
                "description": "Initialize database configurations, routes, and middleware.",
                "priority": "high",
                "estimated_hours": 8.0,
                "due_date": (now + timedelta(days=5)).strftime("%Y-%m-%d"),
                "milestone_title": "Kickoff and Design Phase"
            },
            {
                "title": "Build Frontend UI Components",
                "description": "Develop main navigation bars, dashboard pages, and modals.",
                "priority": None,
                "estimated_hours": 12.0,
                "due_date": (now + timedelta(days=12)).strftime("%Y-%m-%d"),
                "milestone_title": "Kickoff and Design Phase"
            },
            {
                "title": "Implement Database Models and Schemas",
                "description": "Write models for main tables and run Alembic migrations.",
                "priority": "high",
                "estimated_hours": 6.0,
                "due_date": (now + timedelta(days=8)).strftime("%Y-%m-%d"),
                "milestone_title": "Core Development Phase"
            },
            {
                "title": "Integrate AI Agent Workflows",
                "description": "Setup LangGraph state machines and API processor route.",
                "priority": "critical",
                "estimated_hours": 16.0,
                "due_date": (now + timedelta(days=20)).strftime("%Y-%m-%d"),
                "milestone_title": "Core Development Phase"
            },
            {
                "title": "Write End-to-End Integration Tests",
                "description": "Verify authentication, dashboard stats loading, and command routing.",
                "priority": None,
                "estimated_hours": 10.0,
                "due_date": (deadline_dt - timedelta(days=5)).strftime("%Y-%m-%d"),
                "milestone_title": "QA, Testing, and Deployment"
            }
        ]

    return {
        "todos": todos
    }
