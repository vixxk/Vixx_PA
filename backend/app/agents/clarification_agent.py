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
            has_project_title = payment.get("project_title") or (
                "payments" in payment 
                and isinstance(payment["payments"], list) 
                and any(p.get("project_title") for p in payment["payments"] if isinstance(p, dict))
            )
            if not has_project_title:
                missing_fields.append("project_title")
                
            has_amount = payment.get("amount") or (
                "payments" in payment 
                and isinstance(payment["payments"], list) 
                and any(p.get("amount") for p in payment["payments"] if isinstance(p, dict))
            )
            if action != "update" and not has_amount:
                missing_fields.append("amount")
                
            if missing_fields:
                needs_clarification = True
                fields_str = " and ".join(missing_fields)
                clarification_message = f"Please specify the {fields_str} for the payment."
    
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
        try:
            from app.utils.llm import get_llm
            from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
            
            llm = get_llm()
            user_query = state.get("raw_input", "").strip()
            
            # 1. Fast keyword check for greetings and capability questions
            lower_query = user_query.lower()
            greetings = ["hi", "hello", "hey", "hola", "greetings", "good morning", "good afternoon", "good evening"]
            self_questions = ["who are you", "what can you do", "what is vixx", "help me", "help", "who is vixx", "what are your features", "what do you do"]
            
            is_simple_greeting = any(lower_query == g or lower_query.startswith(g + " ") for g in greetings)
            is_self_query = any(sq in lower_query for sq in self_questions)
            
            # 2. LLM classification check for general knowledge/external queries
            is_workspace_or_self = True
            if not is_simple_greeting and not is_self_query:
                classification_prompt = (
                    "Determine if the following user query is related to managing a workspace (projects, tasks, schedules, invoicing/payments, clients, files, reminders) "
                    "or is a conversation/capability query about the assistant itself (Vixx).\n\n"
                    "If the query asks about general knowledge, external entities, science, trivia, math, coding, politics, "
                    "or public figures (e.g., 'why is the sky blue', 'who is the president', 'what is 4+4', 'who is vivek', 'write a function'): respond with NO.\n"
                    "Otherwise, respond with YES.\n\n"
                    f"Query: \"{user_query}\"\n"
                    "Response (YES or NO):"
                )
                class_res = await llm.ainvoke([HumanMessage(content=classification_prompt)])
                class_text = class_res.content.strip().upper()
                if "NO" in class_text:
                    is_workspace_or_self = False
            
            # 3. Direct response or workspace context generation
            if not is_workspace_or_self:
                clarification_message = (
                    "I am a dedicated workspace assistant. I can only assist you with information and actions "
                    "related to your projects, tasks, schedules, invoices, reminders, and files. Please ask me about "
                    "your workspace data or capabilities."
                )
            else:
                last_project = state.get("last_project")
                last_project_context = ""
                if last_project:
                    last_project_context = (
                        f"\nContext - Recently Created/Modified Project:\n"
                        f"- Title: {last_project.get('title')}\n"
                        f"- Description: {last_project.get('description') or 'No description'}\n"
                        f"- Summary: {last_project.get('summary') or 'No summary yet'}\n"
                    )
                
                system_prompt = (
                    "You are Vixx, a premium personal workspace assistant. You only work on information available in the user's database or related to their workspace/capabilities.\n\n"
                    "CRITICAL MANDATE:\n"
                    "1. If the user greets you (e.g. 'hello', 'hi') or asks about your capabilities (e.g. 'who are you', 'what can you do'), briefly and warmly introduce yourself as Vixx, their personal workspace assistant, and explain that you help manage their tasks, projects, schedules, invoices, and reminders.\n"
                    "2. If the user asks ANY question about external topics, general knowledge, trivia, public figures, math, coding, or anything not stored in their database or related to their workspace features (e.g., 'who is the president of India', 'what is 4+4', 'who is vivek', etc.):\n"
                    "   You MUST immediately refuse to answer. You MUST reply exactly with:\n"
                    "   \"I am a dedicated workspace assistant. I can only assist you with information and actions related to your projects, tasks, schedules, invoices, reminders, and files. Please ask me about your workspace data or capabilities.\"\n"
                    "   Do NOT cater to the query, do NOT explain, do NOT suggest checking other sites, and do NOT add any other conversational text."
                )
                
                messages = [SystemMessage(content=system_prompt)]
                
                # Append history to LLM messages
                history = state.get("history") or []
                for msg in history[-6:]:
                    if msg.get("role") == "user":
                        messages.append(HumanMessage(content=msg.get("content")))
                    else:
                        messages.append(AIMessage(content=msg.get("content")))
                
                # Add current raw input
                if not history or history[-1].get("content") != state.get("raw_input"):
                    messages.append(HumanMessage(content=state.get("raw_input", "")))
                
                res = await llm.ainvoke(messages)
                clarification_message = res.content.strip()
        except Exception:
            clarification_message = (
                "I am a dedicated workspace assistant. I can only assist you with information and actions "
                "related to your projects, tasks, schedules, invoices, reminders, and files."
            )
            
    return {
        "needs_clarification": needs_clarification,
        "clarification_message": clarification_message,
        "missing_fields": missing_fields
    }
