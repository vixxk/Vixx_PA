"""
LangGraph Workflow — Enhanced with generate_report intent support.
The graph runs: Router → Extractor → Clarifier → END
Domain execution (CRUD/PDF) is handled by the ai.py dispatcher AFTER the graph completes.
"""

from langgraph.graph import StateGraph, END
from app.graphs.state import WorkflowState
from app.agents.router_agent import run_router_agent
from app.agents.requirement_agent import run_requirement_extractor_agent
from app.agents.clarification_agent import run_clarification_agent
from app.agents.timeline_agent import run_timeline_agent
from app.agents.todo_agent import run_todo_agent
from app.agents.sprint_agent import run_sprint_agent
from app.agents.risk_agent import run_risk_agent
from app.agents.summary_agent import run_summary_agent

from typing import Dict, Any

# --- Wrapped nodes for Reasoning / Thought Log collection ---
async def wrapped_router_node(state: WorkflowState) -> Dict[str, Any]:
    if state.get("confirmed_deletion"):
        return {}
    res = await run_router_agent(state)
    
    # If the router returns 'clarify' but we have a more specific intent carried over, preserve it
    intent = res.get("intent")
    state_intent = state.get("intent")
    if (intent == "clarify" or not intent) and state_intent and state_intent != "clarify":
        intent = state_intent
        res["intent"] = intent
        
    steps = [f"🧠 Intent Router → classified as '{intent}'"]
    res["reasoning_steps"] = steps
    return res

async def wrapped_extractor_node(state: WorkflowState) -> Dict[str, Any]:
    if state.get("confirmed_deletion"):
        return {}
    res = await run_requirement_extractor_agent(state)
    steps = list(state.get("reasoning_steps") or [])
    intent = state.get("intent")
    extracted_keys = []
    if intent == "create_project" and res.get("project"):
        extracted_keys = [k for k, v in res["project"].items() if v is not None]
    elif intent == "create_task" and res.get("todos"):
        extracted_keys = [k for k, v in res["todos"][-1].items() if v is not None]
    elif intent == "track_payment" and res.get("payment"):
        extracted_keys = [k for k, v in res["payment"].items() if v is not None]
    elif intent == "update_timeline" and res.get("timeline"):
        extracted_keys = [k for k, v in res["timeline"][-1].items() if v is not None]
    elif intent == "set_reminder" and res.get("reminder"):
        extracted_keys = [k for k, v in res["reminder"].items() if v is not None]
    elif intent == "generate_report" and res.get("report"):
        extracted_keys = [k for k, v in res["report"].items() if v is not None]
        
    extracted_str = ", ".join(extracted_keys) if extracted_keys else "none"
    steps.append(f"🔍 Extractor → parsed fields: {extracted_str}")
    res["reasoning_steps"] = steps
    return res

async def wrapped_clarifier_node(state: WorkflowState) -> Dict[str, Any]:
    if state.get("confirmed_deletion"):
        steps = list(state.get("reasoning_steps") or [])
        steps.append("✅ Deletion confirmed → proceeding to execute.")
        return {
            "needs_clarification": False,
            "clarification_message": None,
            "reasoning_steps": steps
        }
    res = await run_clarification_agent(state)
    steps = list(state.get("reasoning_steps") or [])
    needs_clar = res.get("needs_clarification") or False
    if needs_clar:
        missing = ", ".join(res.get("missing_fields") or [])
        if missing:
            steps.append(f"⚠️ Validation → missing: {missing}")
        else:
            steps.append("💬 Conversational response generated.")
    else:
        steps.append("✅ Validation passed → executing.")
    res["reasoning_steps"] = steps
    return res

async def wrapped_timeline_node(state: WorkflowState) -> Dict[str, Any]:
    res = await run_timeline_agent(state)
    steps = list(state.get("reasoning_steps") or [])
    events_count = len(res.get("timeline") or [])
    steps.append(f"📅 Timeline → {events_count} milestones planned.")
    res["reasoning_steps"] = steps
    return res

async def wrapped_todo_node(state: WorkflowState) -> Dict[str, Any]:
    res = await run_todo_agent(state)
    steps = list(state.get("reasoning_steps") or [])
    todos_count = len(res.get("todos") or [])
    steps.append(f"📋 Tasks → {todos_count} tasks generated.")
    res["reasoning_steps"] = steps
    return res

async def wrapped_sprint_node(state: WorkflowState) -> Dict[str, Any]:
    res = await run_sprint_agent(state)
    steps = list(state.get("reasoning_steps") or [])
    steps.append("⚡ Sprint → tasks distributed across phases.")
    res["reasoning_steps"] = steps
    return res

async def wrapped_risk_node(state: WorkflowState) -> Dict[str, Any]:
    res = await run_risk_agent(state)
    steps = list(state.get("reasoning_steps") or [])
    risks_count = len(res.get("risks") or [])
    steps.append(f"🛡️ Risks → {risks_count} risks identified.")
    res["reasoning_steps"] = steps
    return res

async def wrapped_summary_node(state: WorkflowState) -> Dict[str, Any]:
    res = await run_summary_agent(state)
    steps = list(state.get("reasoning_steps") or [])
    steps.append("📝 Summary → kickoff report generated.")
    res["reasoning_steps"] = steps
    return res

def check_clarification(state: WorkflowState) -> str:
    """Route based on clarification need and intent."""
    return "end"

def create_workflow():
    workflow = StateGraph(WorkflowState)
    
    # Add nodes
    workflow.add_node("router", wrapped_router_node)
    workflow.add_node("extractor", wrapped_extractor_node)
    workflow.add_node("clarifier", wrapped_clarifier_node)
    workflow.add_node("timeline", wrapped_timeline_node)
    workflow.add_node("todo", wrapped_todo_node)
    workflow.add_node("sprint", wrapped_sprint_node)
    workflow.add_node("risk", wrapped_risk_node)
    workflow.add_node("summary", wrapped_summary_node)
    
    # Define execution graph flow
    workflow.set_entry_point("router")
    workflow.add_edge("router", "extractor")
    workflow.add_edge("extractor", "clarifier")
    
    # Conditional routing based on clarification need and intent
    workflow.add_conditional_edges(
        "clarifier",
        check_clarification,
        {
            "end": END,
            "timeline": "timeline"
        }
    )
    
    workflow.add_edge("timeline", "todo")
    workflow.add_edge("todo", "sprint")
    workflow.add_edge("sprint", "risk")
    workflow.add_edge("risk", "summary")
    workflow.add_edge("summary", END)
    
    return workflow.compile()

app_workflow = create_workflow()
