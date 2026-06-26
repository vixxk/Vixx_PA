from typing import Dict, Any
from app.graphs.state import WorkflowState

async def run_clarification_agent(state: WorkflowState) -> Dict[str, Any]:
    intent = state.get("intent", "clarify")
    project = state.get("project") or {}
    todos = state.get("todos") or []
    timeline = state.get("timeline") or []
    
    needs_clarification = False
    clarification_message = None
    missing_fields = []
    
    if intent == "create_project":
        action = project.get("action") or "create"
        if action not in ["read", "list", "query", "enquire", "delete", "clear", "empty"]:
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
        is_read_or_clear = action in ["read", "list", "query", "enquire", "generate_pdf"] or (action in ["delete", "clear", "empty"] and (not title or title.lower() in ["all", "list", "todo list", "to-do list", "todos", "tasks", "to do list"]))
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
        if action not in ["read", "list", "query", "enquire", "delete", "clear", "empty", "generate_pdf", "sync"]:
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
        if action not in ["list", "clear"]:
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
        if action not in ["list", "query", "read"]:
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
                "You are Vixx, a premium, intelligent personal AI assistant.\n"
                "You can help the user with:\n"
                "- Creating/managing projects, tasks, payments, timeline milestones\n"
                "- Setting reminders that get sent via SMS or email\n"
                "- Viewing and listing data\n"
                "- Syncing with Google Sheets and Calendar\n"
                f"{last_project_context}\n"
                "If the user's query is conversational or a general question, respond helpfully.\n"
                "If they seem to want to do something specific, guide them.\n"
                "Respond in a warm, professional tone. Keep responses brief and action-oriented.\n"
                "IMPORTANT: All monetary amounts are ALWAYS in Indian Rupees (INR / ₹). Never use dollars ($), USD, or any other currency. Never convert amounts. If the user says '10000', it means ₹10,000."
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
            clarification_message = "I'm not sure how to help with that. You can ask me to create a project, manage tasks, set reminders, or track payments."
            
    return {
        "needs_clarification": needs_clarification,
        "clarification_message": clarification_message,
        "missing_fields": missing_fields
    }
