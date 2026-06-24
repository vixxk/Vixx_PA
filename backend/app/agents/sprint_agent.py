from typing import Dict, Any
from datetime import datetime
from app.graphs.state import WorkflowState

async def run_sprint_agent(state: WorkflowState) -> Dict[str, Any]:
    intent = state.get("intent")
    todos = state.get("todos") or []
    needs_clarification = state.get("needs_clarification", False)

    if intent != "create_project" or not todos or needs_clarification:
        return {}

    # Sort todos by due date
    def parse_date(date_str):
        try:
            return datetime.strptime(date_str, "%Y-%m-%d")
        except Exception:
            return datetime.max

    sorted_todos = sorted(todos, key=lambda t: parse_date(t.get("due_date", "")))
    
    # Simple rule-based sprint assignment:
    # 2-3 tasks per sprint or based on timeline timeline checkpoints.
    # We will assign sprint numbers: Sprint 1 (first 40% of timeline), Sprint 2 (next 40%), Sprint 3 (rest).
    updated_todos = []
    total_tasks = len(sorted_todos)
    
    for idx, todo in enumerate(sorted_todos):
        # Determine sprint number
        if total_tasks <= 3:
            sprint_num = 1
        else:
            percentile = idx / total_tasks
            if percentile < 0.4:
                sprint_num = 1
            elif percentile < 0.8:
                sprint_num = 2
            else:
                sprint_num = 3
        
        todo_copy = dict(todo)
        todo_copy["description"] = f"[Sprint {sprint_num}] {todo_copy.get('description', '')}"
        updated_todos.append(todo_copy)

    return {
        "todos": updated_todos
    }
