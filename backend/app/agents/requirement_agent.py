"""
Enhanced Requirement Extractor Agent
====================================
Extracts structured data from user's natural language input.

Key improvements:
1. Handles 'generate_report' intent (report_type, project_title, theme, etc.)
2. Extracts exclusion patterns ("except X", "but not X")
3. Better date parsing with user timezone context
4. Extracts multi-entity references
"""

import json
import re
import logging
from typing import Dict, Any
from app.graphs.state import WorkflowState
from app.utils.llm import get_llm
from langchain_core.messages import SystemMessage, HumanMessage

logger = logging.getLogger(__name__)


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


async def run_requirement_extractor_agent(state: WorkflowState) -> Dict[str, Any]:
    raw_input = state.get("raw_input", "")
    intent = state.get("intent", "clarify")
    history = state.get("history") or []

    # Initialize containers
    project_data = state.get("project") or {"title": None, "description": None, "total_amount": None, "notepad": None}
    todos = state.get("todos") or []
    timeline = state.get("timeline") or []
    payment = state.get("payment") or {"action": "create", "project_title": None, "amount": None, "currency": "INR", "payment_type": "Advance", "received_date": None, "notes": None, "status": "pending"}
    reminder = state.get("reminder") or {"action": "create", "title": None, "description": None, "remind_at": None, "channel": "sms"}
    whatsapp = state.get("whatsapp") or {"action": "send", "recipient": None, "recipient_name": None, "message": None, "scheduled_at": None}
    email = state.get("email") or {"action": "send", "recipient": None, "recipient_name": None, "subject": None, "message": None, "scheduled_at": None}
    contact = state.get("contact") or {"action": "create", "name": None, "phone": None, "email": None, "notes": None}
    pending = state.get("pending") or {"action": "create", "title": None, "description": None, "project_title": None, "is_completed": False}
    report = state.get("report") or {"report_type": None, "project_title": None, "theme": None, "title": None}
    client = state.get("client") or {"action": "create", "name": None, "email": None, "phone": None, "company": None, "notes": None, "priority_score": None}
    analytics = state.get("analytics") or {"action": "dashboard", "project_title": None}

    if intent not in ["create_project", "create_task", "track_payment", "set_reminder", "track_pending", "generate_report", "manage_client", "analytics", "update_timeline", "manage_timeline", "send_whatsapp", "send_email", "manage_contact"]:
        return {}

    try:
        import dateutil.parser
        from datetime import datetime, timedelta

        local_time_str = state.get("local_time")
        timezone_offset = state.get("timezone_offset")
        if local_time_str:
            try:
                local_dt = dateutil.parser.parse(local_time_str)
                if local_dt.tzinfo is not None and timezone_offset is not None:
                    from datetime import timezone as dt_timezone
                    user_tz = dt_timezone(timedelta(minutes=-timezone_offset))
                    local_dt = local_dt.astimezone(user_tz)
            except Exception:
                local_dt = datetime.now()
        else:
            local_dt = datetime.now()

        today = local_dt.date()
        tomorrow = today + timedelta(days=1)
        yesterday = today - timedelta(days=1)
        day_name = local_dt.strftime("%A")

        date_context = (
            f"Current User Local Datetime: {local_dt.strftime('%Y-%m-%d %H:%M:%S')} ({day_name})\n"
            f"- Yesterday: {yesterday.strftime('%Y-%m-%d')}\n"
            f"- Today: {today.strftime('%Y-%m-%d')} ({day_name})\n"
            f"- Tomorrow: {tomorrow.strftime('%Y-%m-%d')}\n"
        )

        llm = get_llm()
        from app.utils.llm import invoke_llm_with_fallback
        from app.agents.entity_resolver import resolve_project_from_text, parse_amount_from_text, parse_date_from_text

        workspace_projects = state.get("workspace_projects") or []
        known_project_names = [p["title"] for p in workspace_projects if p.get("title")]
        projects_context = ""
        if known_project_names:
            projects_context = (
                f"\nExisting Workspace Projects (match user mentions to these exact names where appropriate):\n"
                f"- {', '.join(known_project_names)}\n"
            )

        if intent == "set_reminder":
            system_prompt = (
                "You are a requirements extraction agent. Extract structured details for creating, updating, or managing a reminder.\n\n"
                f"Date Calculation Context:\n{date_context}\n"
                "Extract these fields:\n"
                "- action: 'create', 'update', 'list', 'delete', 'clear', 'cancel' (default 'create'; set 'update' if user says 'reschedule', 'change reminder', 'update reminder', 'move reminder')\n"
                "- title: what the reminder is about. (For updates, this is the existing reminder title)\n"
                "- new_title: new title if renaming the reminder\n"
                "- description: optional extra detail\n"
                "- remind_at: ISO 8601 datetime. (For updates, this is the new rescheduled time). Parse relative times using the Date Context above.\n"
                "- channel: 'sms', 'email', or 'both'. Only extract 'both' if explicitly requested.\n\n"
                "Respond ONLY with a JSON object."
            )
        elif intent == "send_whatsapp":
            system_prompt = (
                "You are a requirements extraction agent for WhatsApp messaging via Green API.\n"
                "Extract structured details for sending, scheduling, listing, or cancelling a WhatsApp message.\n\n"
                f"Date & Time Calculation Context:\n{date_context}\n"
                "Extract these fields:\n"
                "- action: 'send' (immediate message), 'schedule' (send later/at specific time), 'list' (view scheduled messages), 'cancel' (cancel a scheduled message)\n"
                "- recipient: phone number or recipient identifier (e.g. '+919876543210', '9876543210'). If user refers to a name (e.g. 'Alex'), put in recipient.\n"
                "- recipient_name: contact name if mentioned (e.g. 'Alex', 'client', 'John').\n"
                "- message: the text content of the message to send.\n"
                "- scheduled_at: ISO 8601 datetime if scheduled for later (e.g. 'tomorrow at 10 AM', 'in 30 mins'). Null if immediate.\n\n"
                "RULES:\n"
                "1. If user mentions a future time or says 'schedule' → action is 'schedule', parse scheduled_at.\n"
                "2. If user asks to list/view scheduled messages → action is 'list'.\n"
                "3. If user asks to cancel/delete a scheduled message → action is 'cancel'.\n"
                "4. Extract message text cleanly without preamble like 'saying' or 'that'.\n\n"
                "Respond ONLY with a JSON object."
            )
        elif intent == "send_email":
            system_prompt = (
                "You are a requirements extraction agent for outbound email messaging.\n"
                "Extract structured details for sending, drafting, scheduling, or listing emails.\n\n"
                f"Date & Time Calculation Context:\n{date_context}\n"
                "Extract these fields:\n"
                "- action: 'send' (immediate email), 'schedule' (send later), 'list' (view scheduled emails), 'cancel' (cancel a scheduled email)\n"
                "- recipient: email address or recipient contact name (e.g. 'alex@example.com', 'Alex', 'client')\n"
                "- recipient_name: friendly contact name (e.g. 'Alex')\n"
                "- subject: email subject line if specified or implied\n"
                "- message: instructions or text body of the email\n"
                "- scheduled_at: ISO 8601 datetime if scheduled for later (e.g. 'tomorrow at 9 AM'). Null if immediate.\n\n"
                "RULES:\n"
                "1. If user mentions a future time or says 'schedule' → action is 'schedule', parse scheduled_at.\n"
                "2. If user asks to list/view scheduled emails → action is 'list'.\n"
                "3. If user asks to cancel/delete a scheduled email → action is 'cancel'.\n"
                "4. Extract message text cleanly without preamble like 'saying' or 'that'.\n\n"
                "Respond ONLY with a JSON object."
            )
        elif intent == "manage_contact":
            system_prompt = (
                "You are a requirements extraction agent for managing address book contacts.\n"
                "Extract structured details for saving, listing, or deleting contacts.\n\n"
                "Extract these fields:\n"
                "- action: 'create' (save or add contact), 'list' (view contacts), 'delete' (remove contact)\n"
                "- name: contact person's name (e.g. 'Alex', 'Sarah', 'John Doe')\n"
                "- phone: phone number (e.g. '+919876543210')\n"
                "- email: optional email address\n"
                "- notes: optional notes\n\n"
                "Respond ONLY with a JSON object."
            )
        elif intent == "generate_report":
            # Build context from conversation history for "this" / "that" resolution
            history = state.get("history") or []
            context_hint = ""
            if history:
                for msg in reversed(history[-6:]):
                    if msg.get("role") == "assistant" and "Project:" in msg.get("content", ""):
                        # Extract project name from prior assistant message
                        pm = re.search(r"Project:\s*(.+?)[\n\r]", msg["content"])
                        if pm:
                            context_hint = f"\nContext: The user was recently viewing data about project '{pm.group(1).strip()}'."
                            break

            system_prompt = (
                "You are a requirements extraction agent. Extract details for generating a PDF report.\n\n"
                f"{projects_context}\n"
                f"{context_hint}\n"
                "Extract these fields:\n"
                "- report_type: 'payments', 'tasks', 'project', 'invoice', 'overview', or 'auto'\n"
                "  * If user says 'pdf of project X' or 'all details' → 'project'\n"
                "  * If user says 'payment report' → 'payments'\n"
                "  * If user says 'task report' or 'todo report' → 'tasks'\n"
                "  * If user says 'invoice' → 'invoice'\n"
                "  * If unclear → 'auto'\n"
                "- project_title: which project to filter by (null if all projects)\n"
                "  * IMPORTANT: If user says 'this' or 'that', check the conversation context above\n"
                "- project_titles: list/array of project titles if user specifies multiple projects (null if not specified or all projects)\n"
                "- theme: 'navy', 'teal', 'emerald', 'charcoal', 'ruby' (null if not specified)\n"
                "- title: custom report title (null if not specified)\n"
                "- filename: custom file name for the generated PDF. Strip any '.pdf' extension (null if not specified)\n\n"
                "IMPORTANT: Extract the project name accurately. 'pdf of acme project' → project_title='acme'.\n"
                "'give me a pdf for this' with context about 'Acme PDF Project' → project_title='Acme PDF Project'.\n\n"
                "Respond ONLY with a JSON object."
            )
        elif intent == "manage_client":
            system_prompt = (
                "You are a requirements extraction agent. Extract structured details for managing a Client.\n\n"
                "Extract these fields:\n"
                "- action: 'create', 'update', 'delete', 'read', 'list', 'query' (default 'create')\n"
                "  * If user says 'list clients' or 'show clients' → action='list'\n"
                "  * If user says 'delete client X' → action='delete'\n"
                "  * If user says 'update client' or 'modify client' → action='update'\n"
                "- name: client's personal name (e.g. 'John Doe')\n"
                "- email: email address\n"
                "- phone: telephone number\n"
                "- company: company name (e.g. 'Acme Inc')\n"
                "- notes: additional notes\n"
                "- priority_score: integer score (null if not specified)\n\n"
                "Respond ONLY with a JSON object."
            )
        elif intent == "analytics":
            system_prompt = (
                "You are a requirements extraction agent. Extract details for viewing analytics.\n\n"
                f"{projects_context}\n"
                "Extract these fields:\n"
                "- action: 'dashboard', 'summary', 'health', 'workload' (default 'dashboard')\n"
                "- project_title: specific project title if filtering by a project (null if all projects)\n\n"
                "Respond ONLY with a JSON object."
            )
        else:
            system_prompt = (
                "You are a requirements extraction agent for a Work OS. Extract structured details.\n\n"
                f"Date Calculation Context:\n{date_context}\n"
                f"{projects_context}\n"
                f"User Intent: {intent}\n\n"
                "Extract details based on the intent:\n"
                "- For 'create_project': Extract action ('create', 'update', 'delete', 'clear', 'empty', 'read', 'list', 'query'), title, new_title (if renaming a project, e.g. 'rename X to Y' -> title='X', new_title='Y'), description, status (strictly one of: 'developing' or 'finished'; map 'completed'/'active'/'done'/'on hold' accordingly), total_amount (budget or project value as a float/number), notepad (notes or notepad contents). ALSO, if user mentions initial/advance payment, extract into nested 'payment'. If updating multiple projects, extract into 'updates' list.\n"
                "  IMPORTANT: If user says 'rename project X to Y', 'change budget of X to Y', 'mark X as finished', action='update'.\n"
                "- For 'create_task': Extract action ('create', 'update', 'delete', 'clear', 'empty', 'read', 'list', 'query', 'complete', 'generate_pdf'), title (existing task name), new_title (if renaming task, e.g. 'rename task X to Y' -> title='X', new_title='Y'), description, priority ('low', 'medium', 'high', 'critical'), status ('todo', 'in_progress', 'done', 'completed'), project_title, new_project_title (if moving task to another project), due_date, estimated_hours (float/number).\n"
                "  IMPORTANT: If user says 'mark task X as done', 'complete task X', 'change priority of X to high', 'rename task X to Y', 'move task X to project Y' → action='update'.\n"
                "- For 'track_pending': Extract action ('create', 'update', 'delete', 'clear', 'read', 'list', 'query', 'complete'), title, new_title (if renaming), description, project_title, is_completed (boolean).\n"
                "  IMPORTANT: If user says 'mark pending X as done' or 'update pending item X' → action='update' (or 'complete').\n"
                "- For 'track_payment': Extract action ('create', 'update', 'delete', 'clear', 'empty', 'read', 'list', 'query', 'sync', 'generate_pdf'), project_title, amount (the new or updated amount), old_amount / target_amount (the previous amount being changed, e.g. 'change 7000 payment to 8500' -> old_amount=7000, amount=8500), payment_type ('Advance', 'Final', 'Partial'), status ('received', 'pending'), received_date, notes, is_latest (boolean, True if user says 'update last payment' or 'change latest payment').\n"
                "  IMPORTANT: If user says 'change payment of X to Y', 'update last payment to Y', 'change payment date to D' → action='update'.\n"
                "- For 'update_timeline': Extract action ('create', 'update', 'delete', 'clear', 'read', 'list'), event_name (milestone name), new_event_name (if renaming), event_type ('milestone', 'checkpoint'), event_date (new date if rescheduling), notes, status ('pending', 'completed').\n"
                "  IMPORTANT: If user says 'reschedule milestone X to date D', 'postpone milestone X', or 'move milestone X' → action='update'.\n\n"
                "CONTEXT & MEMORY RULES:\n"
                "1. Read conversation history to resolve references like 'this', 'that', 'its', 'first one', 'next', 'the project', etc.\n"
                "2. If user is modifying or correcting previous statements, extract resolved project_title and amount from conversation history.\n"
                "3. Set action='update' if user is modifying, editing, renaming, rescheduling, or correcting an existing item.\n\n"
                "Use Date Context to translate relative dates. Format output as JSON. Set null for missing properties."
            )

        from langchain_core.messages import AIMessage
        messages = [SystemMessage(content=system_prompt)]
        
        # Append conversation history for context
        for msg in history[-6:]:
            if msg["role"] == "user":
                messages.append(HumanMessage(content=msg["content"]))
            else:
                messages.append(AIMessage(content=msg["content"]))
                
        messages.append(HumanMessage(content=f"User request: {raw_input}"))
        response = await invoke_llm_with_fallback(messages)
        content = response.content.strip()

        extracted = {}
        # 1. Try to find all content between ```json and ```
        code_blocks = re.findall(r"```json\s*(.*?)\s*```", content, re.DOTALL | re.IGNORECASE)
        if not code_blocks:
            # 2. Try to find all content between ``` and ```
            code_blocks = re.findall(r"```\s*(.*?)\s*```", content, re.DOTALL)
            
        if code_blocks:
            parsed_blocks = []
            for block in code_blocks:
                try:
                    val = json.loads(block.strip())
                    if isinstance(val, list):
                        parsed_blocks.extend(val)
                    else:
                        parsed_blocks.append(val)
                except Exception:
                    pass
            if len(parsed_blocks) > 1:
                extracted = parsed_blocks
            elif len(parsed_blocks) == 1:
                extracted = parsed_blocks[0]
        else:
            # 3. Fallback to brace matching
            first_brace = content.find('{')
            first_bracket = content.find('[')
            start_idx = -1
            if first_brace != -1 and first_bracket != -1:
                if first_bracket < first_brace:
                    start_idx = first_bracket
                    end_idx = content.rfind(']')
                else:
                    start_idx = first_brace
                    end_idx = content.rfind('}')
            elif first_brace != -1:
                start_idx = first_brace
                end_idx = content.rfind('}')
            elif first_bracket != -1:
                start_idx = first_bracket
                end_idx = content.rfind(']')
            
            if start_idx != -1 and end_idx != -1 and end_idx >= start_idx:
                json_str = content[start_idx:end_idx+1]
                try:
                    extracted = json.loads(json_str)
                except Exception:
                    pass

        if extracted:
            if isinstance(extracted, list):
                extracted_list = extracted
                if intent == "create_task":
                    extracted = {"action": "create", "todos": extracted_list}
                elif intent == "update_timeline":
                    extracted = {"action": "create", "timeline": extracted_list}
                elif intent == "track_payment":
                    extracted = {"action": "create", "payments": extracted_list}
                else:
                    extracted = {"action": "create"}
                
                if any(isinstance(item, dict) and item.get("action") == "update" for item in extracted_list):
                    extracted["action"] = "update"
                for item in extracted_list:
                    if isinstance(item, dict) and item.get("project_title"):
                        extracted["project_title"] = item["project_title"]
                        break

            if intent == "set_reminder":
                for key in ["action", "title", "description", "remind_at", "channel"]:
                    if extracted.get(key) is not None:
                        reminder[key] = extracted[key]
            elif intent == "send_whatsapp":
                for key in ["action", "recipient", "recipient_name", "message", "scheduled_at"]:
                    if extracted.get(key) is not None:
                        whatsapp[key] = extracted[key]
            elif intent == "send_email":
                for key in ["action", "recipient", "recipient_name", "subject", "message", "scheduled_at"]:
                    if extracted.get(key) is not None:
                        email[key] = extracted[key]
            elif intent == "manage_contact":
                for key in ["action", "name", "phone", "email", "notes"]:
                    if extracted.get(key) is not None:
                        contact[key] = extracted[key]
            elif intent == "generate_report":
                for key in ["report_type", "project_title", "theme", "title", "filename"]:
                    if extracted.get(key) is not None:
                        report[key] = extracted[key]
            elif intent == "create_project":
                extracted_action = extracted.get("action")
                if not extracted_action and is_list_query(raw_input):
                    project_data["action"] = "read"
                else:
                    project_data["action"] = extracted_action or "create"
                for key in ["title", "new_title", "description", "total_amount", "status", "notepad", "updates"]:
                    if extracted.get(key) is not None:
                        project_data[key] = extracted[key]
                if extracted.get("exclude_names"):
                    project_data["exclude_names"] = extracted["exclude_names"]
                if extracted.get("payment") and isinstance(extracted["payment"], dict):
                    for pkey in ["amount", "currency", "payment_type", "status", "received_date", "notes"]:
                        if extracted["payment"].get(pkey) is not None:
                            payment[pkey] = extracted["payment"][pkey]
            elif intent == "create_task":
                if "todos" in extracted and isinstance(extracted["todos"], list):
                    for t_item in extracted["todos"]:
                        if isinstance(t_item, dict):
                            todos.append({
                                "action": t_item.get("action") or extracted.get("action") or "create",
                                "title": t_item.get("title"),
                                "new_title": t_item.get("new_title"),
                                "description": t_item.get("description"),
                                "priority": t_item.get("priority") or "medium",
                                "status": t_item.get("status") or "todo",
                                "project_title": t_item.get("project_title") or extracted.get("project_title"),
                                "new_project_title": t_item.get("new_project_title"),
                                "due_date": t_item.get("due_date"),
                                "estimated_hours": t_item.get("estimated_hours"),
                            })
                else:
                    if todos:
                        last_todo = todos[-1]
                        for key in ["action", "title", "new_title", "description", "priority", "status", "project_title", "new_project_title", "due_date", "estimated_hours"]:
                            if extracted.get(key) is not None:
                                last_todo[key] = extracted[key]
                    else:
                        todos.append({
                            "action": extracted.get("action") or "create",
                            "title": extracted.get("title"),
                            "new_title": extracted.get("new_title"),
                            "description": extracted.get("description"),
                            "priority": extracted.get("priority") or "medium",
                            "status": extracted.get("status") or "todo",
                            "project_title": extracted.get("project_title"),
                            "new_project_title": extracted.get("new_project_title"),
                            "due_date": extracted.get("due_date"),
                            "estimated_hours": extracted.get("estimated_hours"),
                        })
            elif intent == "update_timeline":
                if "timeline" in extracted and isinstance(extracted["timeline"], list):
                    for e_item in extracted["timeline"]:
                        if isinstance(e_item, dict):
                            timeline.append({
                                "action": e_item.get("action") or extracted.get("action") or "create",
                                "event_name": e_item.get("event_name"),
                                "new_event_name": e_item.get("new_event_name"),
                                "event_type": e_item.get("event_type") or "milestone",
                                "event_date": e_item.get("event_date"),
                                "notes": e_item.get("notes"),
                            })
                else:
                    if timeline:
                        last_event = timeline[-1]
                        for key in ["action", "event_name", "new_event_name", "event_type", "event_date", "notes"]:
                            if extracted.get(key) is not None:
                                last_event[key] = extracted[key]
                    else:
                        timeline.append({
                            "action": extracted.get("action") or "create",
                            "event_name": extracted.get("event_name"),
                            "new_event_name": extracted.get("new_event_name"),
                            "event_type": extracted.get("event_type") or "milestone",
                            "event_date": extracted.get("event_date"),
                            "notes": extracted.get("notes"),
                        })
            elif intent == "track_payment":
                for key in ["action", "project_title", "amount", "old_amount", "target_amount", "is_latest", "currency", "payment_type", "status", "received_date", "notes", "payments"]:
                    if extracted.get(key) is not None:
                        payment[key] = extracted[key]
                if "payments" in extracted and isinstance(extracted["payments"], list) and extracted["payments"]:
                    first_p = extracted["payments"][0]
                    for k in ["amount", "currency", "payment_type", "status", "received_date", "notes"]:
                        if payment.get(k) is None and isinstance(first_p, dict):
                            payment[k] = first_p.get(k)
            elif intent == "track_pending":
                for key in ["action", "title", "new_title", "description", "project_title", "is_completed"]:
                    if extracted.get(key) is not None:
                        pending[key] = extracted[key]
            elif intent in ["update_timeline", "manage_timeline"]:
                tl_item = {"action": extracted.get("action") or "create"}
                for key in ["event_name", "new_event_name", "event_type", "event_date", "notes", "status"]:
                    if extracted.get(key) is not None:
                        tl_item[key] = extracted[key]
                if not tl_item.get("event_name") and extracted.get("title"):
                    tl_item["event_name"] = extracted["title"]
                timeline.append(tl_item)
            elif intent == "manage_client":
                for key in ["action", "name", "email", "phone", "company", "notes", "priority_score"]:
                    if extracted.get(key) is not None:
                        client[key] = extracted[key]
            elif intent == "analytics":
                for key in ["action", "project_title"]:
                    if extracted.get(key) is not None:
                        analytics[key] = extracted[key]
        else:
            # Fallback regex for project title
            if intent == "create_project":
                title_match = re.search(r"(?:project called|project|called)\s+([A-Za-z0-9_\-\s]+)", raw_input, re.IGNORECASE)
                if title_match:
                    project_data["title"] = title_match.group(1).replace(" project", "").strip()

    except Exception as e:
        logger.exception("Exception in run_requirement_extractor_agent:")
        if intent == "create_project":
            title_match = re.search(r"(?:project called|project|called)\s+([A-Za-z0-9_\-\s]+)", raw_input, re.IGNORECASE)
            if title_match:
                project_data["title"] = title_match.group(1).replace(" project", "").strip()

    # ── Intelligent Entity Resolution & Workspace Matching ──
    from app.agents.entity_resolver import resolve_project_from_text, parse_amount_from_text, parse_date_from_text, parse_update_amounts, parse_rename_pattern
    workspace_projects = state.get("workspace_projects") or []
    active_project_title = state.get("project_title")

    matched_project = resolve_project_from_text(raw_input, workspace_projects, active_project_title)
    if matched_project:
        resolved_title = matched_project["title"]
        if intent == "track_payment" and not payment.get("project_title"):
            payment["project_title"] = resolved_title
        elif intent == "create_task":
            if todos and isinstance(todos, list) and not todos[-1].get("project_title"):
                todos[-1]["project_title"] = resolved_title
            elif not todos:
                todos.append({"action": "create", "project_title": resolved_title})
        elif intent == "create_project":
            if project_data.get("action") == "update" or any(w in raw_input.lower() for w in ["budget", "cost", "total amount", "value", "status"]):
                project_data["title"] = resolved_title
                if "rename" not in raw_input.lower():
                    project_data["new_title"] = None
        elif intent == "track_pending" and not pending.get("project_title"):
            pending["project_title"] = resolved_title
        elif intent == "generate_report" and not report.get("project_title"):
            report["project_title"] = resolved_title

    # Smart heuristics for payment updates, amounts & dates
    if intent == "track_payment":
        old_amt, new_amt = parse_update_amounts(raw_input)
        if new_amt is not None:
            if any(w in raw_input.lower() for w in ["change", "update", "edit", "modify", "set"]):
                payment["action"] = "update"
                payment["amount"] = new_amt
                if old_amt is not None:
                    payment["old_amount"] = old_amt
            elif payment.get("amount") is None:
                payment["amount"] = new_amt
        elif payment.get("amount") is None:
            parsed_amt = parse_amount_from_text(raw_input)
            if parsed_amt is not None:
                payment["amount"] = parsed_amt

        if any(w in raw_input.lower() for w in ["last payment", "latest payment", "recent payment"]):
            payment["is_latest"] = True
            payment["action"] = "update"

        if payment.get("received_date") is None:
            parsed_d = parse_date_from_text(raw_input, local_dt if 'local_dt' in locals() else datetime.now())
            if parsed_d:
                payment["received_date"] = parsed_d

    # Smart heuristics for task updates & renames
    if intent == "create_task":
        old_n, new_n = parse_rename_pattern(raw_input)
        if old_n and new_n:
            if todos and isinstance(todos, list):
                todos[-1]["action"] = "update"
                todos[-1]["title"] = old_n
                todos[-1]["new_title"] = new_n
        if any(w in raw_input.lower() for w in ["complete", "mark done", "mark as done", "mark completed"]):
            if todos and isinstance(todos, list):
                todos[-1]["action"] = "update"
                todos[-1]["status"] = "done"

    # Smart heuristics for project renames & budget updates
    if intent == "create_project":
        old_n, new_n = parse_rename_pattern(raw_input)
        if old_n and new_n:
            project_data["action"] = "update"
            project_data["title"] = old_n
            project_data["new_title"] = new_n
        if any(w in raw_input.lower() for w in ["budget", "cost", "total amount", "value"]):
            parsed_amt = parse_amount_from_text(raw_input)
            if parsed_amt is not None:
                project_data["total_amount"] = parsed_amt
                project_data["action"] = "update"
                if "rename" not in raw_input.lower():
                    project_data["new_title"] = None

    # Smart heuristics for pending item updates & renames
    if intent == "track_pending":
        old_n, new_n = parse_rename_pattern(raw_input)
        if old_n and new_n:
            pending["action"] = "update"
            pending["title"] = old_n
            pending["new_title"] = new_n
        if any(w in raw_input.lower() for w in ["mark done", "mark as done", "mark completed", "completed", "finish"]):
            pending["action"] = "update"
            pending["is_completed"] = True

    # Smart heuristics for timeline updates, renames & rescheduling
    if intent in ["manage_timeline", "update_timeline"]:
        old_n, new_n = parse_rename_pattern(raw_input)
        if old_n and new_n:
            if not timeline:
                timeline.append({"action": "update", "event_name": old_n, "new_event_name": new_n})
            else:
                timeline[-1]["action"] = "update"
                timeline[-1]["event_name"] = old_n
                timeline[-1]["new_event_name"] = new_n
        if any(w in raw_input.lower() for w in ["reschedule", "postpone", "move", "change date", "shift"]):
            if not timeline:
                timeline.append({"action": "update"})
            else:
                timeline[-1]["action"] = "update"
            if not timeline[-1].get("event_date"):
                parsed_d = parse_date_from_text(raw_input, local_dt if 'local_dt' in locals() else datetime.now())
                if parsed_d:
                    timeline[-1]["event_date"] = parsed_d

    # Smart heuristics for reminder updates, renames & rescheduling
    if intent == "manage_reminder":
        old_n, new_n = parse_rename_pattern(raw_input)
        if old_n and new_n:
            reminder["action"] = "update"
            reminder["title"] = old_n
            reminder["new_title"] = new_n
        if any(w in raw_input.lower() for w in ["reschedule", "postpone", "change reminder", "move reminder", "delay", "push back"]):
            reminder["action"] = "update"
            if not reminder.get("remind_at"):
                parsed_d = parse_date_from_text(raw_input, local_dt if 'local_dt' in locals() else datetime.now())
                if parsed_d:
                    reminder["remind_at"] = parsed_d

    # Smart heuristics for WhatsApp messaging
    if intent == "send_whatsapp":
        # Extract phone number if missing from LLM response
        if not whatsapp.get("recipient"):
            phone_match = re.search(r"(\+?\d{10,15})", raw_input)
            if phone_match:
                whatsapp["recipient"] = phone_match.group(1)
            else:
                name_match = re.search(r"(?:to|message)\s+([A-Za-z]+)\b", raw_input, re.IGNORECASE)
                if name_match and name_match.group(1).lower() not in ["whatsapp", "green", "api", "him", "her", "them"]:
                    whatsapp["recipient_name"] = name_match.group(1)
                    whatsapp["recipient"] = name_match.group(1)

        # Extract message content if quotes are used
        if not whatsapp.get("message"):
            quote_match = re.search(r"[\"']([^\"']{2,})[\"']", raw_input)
            if quote_match:
                whatsapp["message"] = quote_match.group(1)
            else:
                saying_match = re.search(r"(?:saying|that|message\s*:)\s*(.+)$", raw_input, re.IGNORECASE)
                if saying_match:
                    whatsapp["message"] = saying_match.group(1).strip()

        # Check for scheduling intent and parse relative dates
        low_input = raw_input.lower()
        if any(w in low_input for w in ["schedule", "later", "tomorrow", "tonight", "at ", "pm", "am", "in ", "mins", "hours"]):
            if not whatsapp.get("scheduled_at"):
                parsed_d = parse_date_from_text(raw_input, local_dt if 'local_dt' in locals() else datetime.now())
                if parsed_d:
                    whatsapp["scheduled_at"] = parsed_d
                    whatsapp["action"] = "schedule"
            elif whatsapp.get("scheduled_at"):
                whatsapp["action"] = "schedule"

    # Smart heuristics for Contact management
    if intent == "manage_contact":
        if not contact.get("phone"):
            p_match = re.search(r"(\+?\d{10,15})", raw_input)
            if p_match:
                contact["phone"] = p_match.group(1)
        if not contact.get("name"):
            n_match = re.search(r"(?:contact|add|save)\s+([A-Za-z\s]+?)(?:\s+(?:as|with|phone|number|\+?\d))", raw_input, re.IGNORECASE)
            if n_match:
                contact["name"] = n_match.group(1).strip()

    # Smart heuristics for Email messaging
    if intent == "send_email":
        if not email.get("recipient"):
            email_match = re.search(r"([\w\.-]+@[\w\.-]+\.\w+)", raw_input)
            if email_match:
                email["recipient"] = email_match.group(1)
            else:
                to_match = re.search(r"(?:email|mail|to)\s+([A-Za-z]+)\b", raw_input, re.IGNORECASE)
                if to_match and to_match.group(1).lower() not in ["email", "mail", "him", "her", "them"]:
                    email["recipient_name"] = to_match.group(1)
                    email["recipient"] = to_match.group(1)

        if not email.get("message"):
            quote_match = re.search(r"[\"']([^\"']{2,})[\"']", raw_input)
            if quote_match:
                email["message"] = quote_match.group(1)
            else:
                saying_match = re.search(r"(?:saying|that|message\s*:|body\s*:)\s*(.+)$", raw_input, re.IGNORECASE)
                if saying_match:
                    email["message"] = saying_match.group(1).strip()
                else:
                    email["message"] = raw_input

        low_input = raw_input.lower()
        if any(w in low_input for w in ["schedule", "later", "tomorrow", "tonight", "at ", "pm", "am", "in ", "mins", "hours"]):
            if not email.get("scheduled_at"):
                parsed_d = parse_date_from_text(raw_input, local_dt if 'local_dt' in locals() else datetime.now())
                if parsed_d:
                    email["scheduled_at"] = parsed_d
                    email["action"] = "schedule"
            elif email.get("scheduled_at"):
                email["action"] = "schedule"

    context_project = state.get("project_title")
    if context_project:
        if todos and isinstance(todos, list) and not todos[-1].get("project_title"):
            todos[-1]["project_title"] = context_project
        if payment and isinstance(payment, dict) and not payment.get("project_title"):
            payment["project_title"] = context_project
        if pending and isinstance(pending, dict) and not pending.get("project_title"):
            pending["project_title"] = context_project
        if report and isinstance(report, dict) and not report.get("project_title"):
            report["project_title"] = context_project

    return {
        "project": project_data,
        "todos": todos,
        "timeline": timeline,
        "payment": payment,
        "reminder": reminder,
        "whatsapp": whatsapp,
        "email": email,
        "contact": contact,
        "pending": pending,
        "report": report,
        "client": client,
        "analytics": analytics,
    }
