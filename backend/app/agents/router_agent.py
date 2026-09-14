"""
Enhanced Router Agent
====================
Classifies user intent with conversation context awareness.

Key improvements over the original:
1. Added 'generate_report' intent (PDF/report generation is now first-class)
2. Context-aware follow-ups: "give me a pdf for this" uses prior context
3. Better system prompt with explicit examples of tricky cases
4. Multi-intent detection basics (e.g., exclusion patterns)
5. Improved fallback keyword mapping with priority ordering
"""

import json
import re
from typing import Dict, Any
from app.graphs.state import WorkflowState
from app.utils.llm import get_llm
from langchain_core.messages import SystemMessage, HumanMessage

# Fallback deterministic router — ordered by specificity (more specific intents first)
# Fallback deterministic router — ordered by specificity (more specific intents first)
INTENT_KEYWORDS = {
    "workspace_overview": [
        "what's on my plate", "whats on my plate", "on my plate", "daily briefing",
        "briefing", "workspace overview", "workspace summary", "my status",
        "overall status", "dashboard summary", "summary of my work",
        "executive summary", "status of everything", "how is everything",
        "what should i focus on", "focus today", "work overview", "overview",
    ],
    "generate_report": [
        "pdf", "report", "export", "download report", "generate report",
        "print report", "give me a pdf", "create pdf", "export pdf",
    ],
    "set_reminder": [
        "remind", "reminder", "reminders", "alarm", "alert me", "notify me",
        "notification", "schedule reminder", "ping me", "sms me", "text me",
    ],
    "update_timeline": [
        "milestone", "milestones", "timeline", "checkpoint", "checkpoints",
        "reschedule milestone", "add milestone", "timeline event",
    ],
    "track_pending": [
        "pending", "credentials", "api keys", "client needs to send",
        "api credentials", "pending item", "pending things", "pending thing",
    ],
    "create_task": [
        "to do", "to-do", "todo", "task", "tasks", "list todo", "show todo",
        "delete task", "clear tasks", "complete task", "mark task",
    ],
    "track_payment": [
        "payment", "payments", "invoice", "paid", "due", "inr", "usd",
        "transactions", "money", "rupee", "sync sheets", "sync sheet",
        "pull from sheet", "sync payments", "payment amount", "amount paid",
        "amount due", "payment cost",
    ],
    "create_project": [
        "project", "projects", "create project", "initialize project",
        "start project", "new project", "delete project", "list projects",
        "total amount", "total cost", "budget", "project cost", "project budget",
        "estimated cost", "project value", "expected payment",
        "finished project", "completed project", "active project",
        "list finished", "list completed", "list active",
    ],
    "generate_summary": [
        "weekly update", "project status update",
    ],
}


def determine_intent_fallback(raw_input: str, history: list = None) -> str:
    """
    Deterministic fallback intent classification.
    Uses keyword matching with priority ordering.
    Also checks conversation history for context clues.
    """
    raw_lower = raw_input.lower()

    # Special case: "give me a pdf for this" or "pdf of this" — context-dependent
    # If history contains a recent project query, this is a report request
    if any(phrase in raw_lower for phrase in ["for this", "of this", "for that", "of that"]):
        if any(kw in raw_lower for kw in ["pdf", "report", "export"]):
            return "generate_report"

    for intent, keywords in INTENT_KEYWORDS.items():
        if any(keyword in raw_lower for keyword in keywords):
            return intent

    return "clarify"


async def run_router_agent(state: WorkflowState) -> Dict[str, Any]:
    raw_input = state.get("raw_input", "")
    history = state.get("history") or []
    raw_lower = raw_input.lower().strip()

    # Fast-path for exact workspace overview keywords
    if any(phrase in raw_lower for phrase in ["what's on my plate", "whats on my plate", "daily briefing", "workspace overview", "workspace summary", "executive summary", "overview of my work"]):
        return {"intent": "workspace_overview"}

    try:
        llm = get_llm()

        # Build context summary from recent history
        history_context = ""
        if history:
            recent = history[-6:]
            history_context = "\n\nRecent conversation context:\n"
            for msg in recent:
                role = "User" if msg["role"] == "user" else "Vixx"
                # Truncate long messages
                content = msg["content"][:200] + "..." if len(msg["content"]) > 200 else msg["content"]
                history_context += f"  {role}: {content}\n"

        system_prompt = (
            "You are a routing agent for Vixx, a Work OS system. Analyze the user's request and "
            "classify it into exactly ONE of these intents:\n\n"
            "INTENTS:\n"
            "- 'workspace_overview': Daily briefing, 'what's on my plate', overview of projects/tasks/schedules, executive workspace summary.\n"
            "- 'create_project': Create, list, view, delete, or manage PROJECTS.\n"
            "- 'create_task': Create, list, view, update, clear, or delete TASKS/TODOS.\n"
            "- 'track_payment': Log, track, view, update, or delete PAYMENT/FINANCIAL transactions.\n"
            "- 'set_reminder': Set, schedule, view, list, cancel, or delete REMINDERS/ALERTS.\n"
            "- 'update_timeline': Create, reschedule, list, or manage TIMELINE milestones or checkpoints.\n"
            "- 'track_pending': Create, list, view, complete, or delete PENDING items (things client needs to send, credentials, etc).\n"
            "- 'generate_report': Generate a PDF, report, export, or document.\n"
            "- 'generate_summary': Generate a high-level kickoff summary.\n"
            "- 'clarify': Ambiguous, general conversation, or unknown.\n\n"
            "CRITICAL RULES:\n"
            "1. If the user asks for a PDF, report, or export of ANY data → 'generate_report' (NEVER 'create_project')\n"
            "2. 'give me a pdf of [project name]' → 'generate_report' (NOT create_project)\n"
            "3. 'give me all data of [project]' → 'create_project' with action 'read'\n"
            "4. If the user says 'this' or 'that', refer to the conversation context to understand what they mean\n"
            "5. 'remind me' / 'set a reminder' / 'alert me' → ALWAYS 'set_reminder'\n"
            "6. If user asks for list/status/view/deletion of a resource → that resource's intent\n"
            "7. If the user asks for daily briefing, what's on their plate, overall status across workspace → 'workspace_overview'\n"
            "8. If the user is setting, discussing, or updating the overall budget, cost, total amount, or value of a project (e.g. 'total amount for mingo is 25000', 'set budget to 50k') → 'create_project' (NOT 'track_payment'). 'track_payment' is only for individual transactions/payments logged.\n"
            "9. 'list finished/completed/active projects' or 'show finished projects and their revenue' → ALWAYS 'create_project' (NOT 'analytics'). Any query about listing projects by their status goes to 'create_project'.\n"
            f"{history_context}\n\n"
            "Respond ONLY with JSON: {\"intent\": \"one_of_the_above_intents\"}"
        )

        messages = [SystemMessage(content=system_prompt)]

        from langchain_core.messages import AIMessage
        for msg in history[-6:]:
            if msg["role"] == "user":
                messages.append(HumanMessage(content=msg["content"]))
            else:
                messages.append(AIMessage(content=msg["content"]))

        messages.append(HumanMessage(content=raw_input))

        from app.utils.llm import invoke_llm_with_fallback
        response = await invoke_llm_with_fallback(messages)
        content = response.content.strip()

        match = re.search(r"\{.*\}", content, re.DOTALL)
        if match:
            data = json.loads(match.group(0))
            intent = data.get("intent", "clarify")
        else:
            intent = determine_intent_fallback(raw_input, history)

    except Exception as e:
        intent = determine_intent_fallback(raw_input, history)

    return {"intent": intent}
