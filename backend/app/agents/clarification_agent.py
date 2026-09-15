from typing import Dict, Any
from app.graphs.state import WorkflowState

def is_list_query(raw_input: str) -> bool:
    low = raw_input.lower().strip()
    list_keywords = ["list", "show", "find", "name", "display", "get", "what are", "how many", "count", "summary", "status", "classify", "view", "read"]
    resource_keywords = ["project", "task", "todo", "payment", "invoice", "reminder", "file", "client", "pending"]
    
    # Direct list/classification indicators
    if any(k in low for k in ["classify", "categories", "status"]):
        return True
        
    for kw in list_keywords:
        if kw in low:
            for rk in resource_keywords:
                if rk in low:
                    return True
            if "all" in low:
                return True
    return False


async def run_clarification_agent(state: WorkflowState) -> Dict[str, Any]:
    intent = state.get("intent", "clarify")
    project = state.get("project") or {}
    todos = state.get("todos") or []
    timeline = state.get("timeline") or []
    
    needs_clarification = False
    clarification_message = None
    missing_fields = []
    
    raw_query = state.get("raw_input", "")
    
    if intent == "create_project":
        action = project.get("action") or "create"
        if is_list_query(raw_query) or action in ["read", "list", "query", "enquire", "delete", "clear", "empty"]:
            pass
        else:
            title = project.get("title")
            description = project.get("description")
            updates = project.get("updates")
            
            if not updates:
                if not title:
                    missing_fields.append("project_name")
                if action != "update" and not description:
                    missing_fields.append("description")
                    
                if missing_fields:
                    needs_clarification = True
                    fields_str = " and ".join(missing_fields).replace("_", " ")
                    clarification_message = f"Please provide the {fields_str} for your new project."
            
    elif intent == "create_task":
        todo_item = todos[-1] if todos else {}
        action = todo_item.get("action") or "create"
        title = todo_item.get("title")
        is_read_or_clear = is_list_query(raw_query) or action in ["read", "list", "query", "enquire", "generate_pdf"] or (action in ["delete", "clear", "empty"] and (not title or title.lower() in ["all", "list", "todo list", "to-do list", "todos", "tasks", "to do list"]))
        is_update = action in ["update", "complete"]
        
        if not is_read_or_clear and not is_update and (not todos or not todo_item.get("title")):
            needs_clarification = True
            missing_fields.append("task_title")
            clarification_message = "What is the title of the task you want to create?"
            
    elif intent == "update_timeline":
        event_item = timeline[-1] if timeline else {}
        action = event_item.get("action") or "create"
        if action not in ["read", "list", "query", "enquire", "delete", "clear", "empty"]:
            event_name = event_item.get("event_name")
            event_date = event_item.get("event_date")
            if not event_name:
                missing_fields.append("event_name")
            if not event_date:
                missing_fields.append("event_date")
                
            if missing_fields:
                needs_clarification = True
                fields_str = " and ".join(missing_fields)
                clarification_message = f"Please specify the {fields_str} for the milestone/timeline event."
            
    elif intent == "track_payment":
        payment = state.get("payment") or {}
        action = payment.get("action") or "create"
        if is_list_query(raw_query) or action in ["read", "list", "query", "enquire", "delete", "clear", "empty", "generate_pdf", "sync"]:
            pass
        else:
            workspace_projects = state.get("workspace_projects") or []
            known_projects = [p["title"] for p in workspace_projects if p.get("title")]

            has_project_title = bool(payment.get("project_title")) or (
                "payments" in payment 
                and isinstance(payment["payments"], list) 
                and any(p.get("project_title") for p in payment["payments"] if isinstance(p, dict))
            )
            # Auto-infer if user only has 1 project in their workspace
            if not has_project_title and len(workspace_projects) == 1:
                has_project_title = True
                payment["project_title"] = workspace_projects[0]["title"]

            if not has_project_title:
                missing_fields.append("project")
                
            has_amount = bool(payment.get("amount")) or (
                "payments" in payment 
                and isinstance(payment["payments"], list) 
                and any(p.get("amount") for p in payment["payments"] if isinstance(p, dict))
            )
            if action != "update" and not has_amount:
                missing_fields.append("amount")
                
            if missing_fields:
                needs_clarification = True
                if "project" in missing_fields and "amount" in missing_fields:
                    proj_hint = f" (Existing projects: {', '.join(known_projects)})" if known_projects else ""
                    clarification_message = f"Could you please specify the amount and which project this payment is for?{proj_hint}"
                elif "project" in missing_fields:
                    proj_hint = f" (Existing projects: {', '.join(known_projects)})" if known_projects else ""
                    clarification_message = f"Which project should I log this payment for?{proj_hint}"
                else:
                    proj_name = payment.get('project_title') or 'this project'
                    clarification_message = f"Please specify the payment amount for {proj_name}."
    
    elif intent == "set_reminder":
        reminder = state.get("reminder") or {}
        action = reminder.get("action") or "create"
        if is_list_query(raw_query) or action in ["list", "clear"]:
            pass
        else:
            if action == "create" and not reminder.get("title"):
                missing_fields.append("title")
            if action == "create" and not reminder.get("remind_at"):
                missing_fields.append("remind_at (when to remind you)")
                
            if missing_fields:
                needs_clarification = True
                fields_str = " and ".join(missing_fields)
                clarification_message = f"Please specify the {fields_str} for the reminder."
            
    elif intent == "generate_report" or intent == "analytics":
        # Reports and analytics don't need clarification — report_service / analytics_service handle auto-detection
        pass
 
    elif intent == "manage_client":
        client = state.get("client") or {}
        action = client.get("action") or "create"
        if is_list_query(raw_query) or action in ["list", "query", "read"]:
            pass
        else:
            if action == "create" and not client.get("name"):
                missing_fields.append("name")
                
            if missing_fields:
                needs_clarification = True
                fields_str = " and ".join(missing_fields)
                clarification_message = f"Please specify the client's {fields_str}."

    elif intent == "clarify":
        needs_clarification = True
        user_query = state.get("raw_input", "").strip()
        lower_query = user_query.lower()
        greetings = ["hi", "hello", "hey", "hola", "greetings", "good morning", "good afternoon", "good evening"]
        
        # Fast response for simple greetings without waiting on LLM
        if any(lower_query == g or lower_query == g + "!" or lower_query.startswith(g + " ") for g in greetings) and len(user_query.split()) <= 4:
            clarification_message = (
                "Hello! I am Vixx, your personal workspace AI assistant. "
                "I can help you manage projects, prioritize tasks, track invoices and payments, "
                "schedule reminders, and generate executive PDF reports. What would you like to work on?"
            )
        else:
            try:
                from app.utils.llm import get_llm
                from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

                llm = get_llm()

                last_project = state.get("last_project")
                context_proj_title = state.get("project_title")
                last_project_context = ""
                if context_proj_title:
                    last_project_context = f"\nActive Project Context: '{context_proj_title}'\n"
                elif last_project:
                    last_project_context = (
                        f"\nRecent Project Context:\n"
                        f"- Title: {last_project.get('title')}\n"
                        f"- Description: {last_project.get('description') or 'No description'}\n"
                    )

                system_prompt = (
                    "You are Vixx, a premium personal workspace assistant for managing projects, tasks, schedules, invoices/payments, files, and reminders.\n"
                    f"{last_project_context}\n"
                    "CRITICAL RULES:\n"
                    "1. If the user greets you or asks what you can do, warmly introduce yourself as Vixx and summarize key capabilities in clean bullet points.\n"
                    "2. If the user asks about external topics, general knowledge, trivia, public figures, math, coding, politics, or unrelated topics (e.g., 'who is the president', 'what is 4+4', 'write a function'):\n"
                    "   You MUST immediately refuse to answer with:\n"
                    "   \"I am a dedicated workspace assistant. I can only assist you with information and actions related to your projects, tasks, schedules, invoices, reminders, and files. Please ask me about your workspace data or capabilities.\"\n"
                    "3. If the user asks how to perform an action or needs guidance, give crisp, actionable step-by-step instructions.\n"
                    "4. Keep your response concise, polite, and styled in clean Markdown."
                )

                messages = [SystemMessage(content=system_prompt)]

                history = state.get("history") or []
                for msg in history[-6:]:
                    if msg.get("role") == "user":
                        messages.append(HumanMessage(content=msg.get("content")))
                    else:
                        messages.append(AIMessage(content=msg.get("content")))

                if not history or history[-1].get("content") != state.get("raw_input"):
                    messages.append(HumanMessage(content=user_query))

                from app.utils.llm import invoke_llm_with_fallback
                res = await invoke_llm_with_fallback(messages)
                clarification_message = res.content.strip()
            except Exception:
                clarification_message = (
                    "I am a dedicated workspace assistant. I can help you with your projects, tasks, "
                    "schedules, invoices, reminders, and files. How can I assist you today?"
                )
            
    return {
        "needs_clarification": needs_clarification,
        "clarification_message": clarification_message,
        "missing_fields": missing_fields
    }
