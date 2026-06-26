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
from typing import Dict, Any
from app.graphs.state import WorkflowState
from app.utils.llm import get_llm
from langchain_core.messages import SystemMessage, HumanMessage


async def run_requirement_extractor_agent(state: WorkflowState) -> Dict[str, Any]:
    raw_input = state.get("raw_input", "")
    intent = state.get("intent", "clarify")
    history = state.get("history") or []

    # Initialize containers
    project_data = state.get("project") or {"title": None, "description": None, "total_amount": None, "notepad": None}
    todos = state.get("todos") or []
    timeline = state.get("timeline") or []
    payment = state.get("payment") or {"action": "create", "project_title": None, "amount": None, "currency": "INR", "payment_type": "Advance", "received_date": None, "notes": None, "status": "pending"}
    reminder = state.get("reminder") or {"action": "create", "title": None, "description": None, "remind_at": None, "channel": "email"}
    pending = state.get("pending") or {"action": "create", "title": None, "description": None, "project_title": None, "is_completed": False}
    report = state.get("report") or {"report_type": None, "project_title": None, "theme": None, "title": None}
    client = state.get("client") or {"action": "create", "name": None, "email": None, "phone": None, "company": None, "notes": None, "priority_score": None}
    analytics = state.get("analytics") or {"action": "dashboard", "project_title": None}

    if intent not in ["create_project", "create_task", "track_payment", "set_reminder", "track_pending", "generate_report", "manage_client", "analytics"]:
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

        if intent == "set_reminder":
            system_prompt = (
                "You are a requirements extraction agent. Extract structured details for setting a reminder.\n\n"
                f"Date Calculation Context:\n{date_context}\n"
                "Extract these fields:\n"
                "- action: 'create', 'list', 'delete', 'clear', 'update' (default 'create')\n"
                "- title: what the reminder is about. Strip generic terms like 'reminder'.\n"
                "- description: optional extra detail\n"
                "- remind_at: ISO 8601 datetime. Parse relative times using the Date Context above.\n"
                "- channel: 'email' (default 'email')\n\n"
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
                "Extract these fields:\n"
                "- action: 'dashboard', 'summary', 'health', 'workload' (default 'dashboard')\n"
                "- project_title: specific project title if filtering by a project (null if all projects)\n\n"
                "Respond ONLY with a JSON object."
            )
        else:
            system_prompt = (
                "You are a requirements extraction agent for a Work OS. Extract structured details.\n\n"
                f"Date Calculation Context:\n{date_context}\n"
                f"User Intent: {intent}\n\n"
                "Extract details based on the intent:\n"
                "- For 'create_project': Extract action ('create', 'update', 'delete', 'clear', 'empty', 'read', 'list', 'query'), title, new_title (if renaming a project, e.g., 'rename X to Y' -> title='X', new_title='Y'), description, status (strictly one of the project status enum values: 'planning', 'developing', or 'finished'; map 'completed'/'active'/'done'/'on hold' to these accordingly), total_amount (budget or project value as a float/number), notepad (any notes, details, brief, notepad contents or updates). ALSO, if user mentions any initial or advance payment (e.g. 'advance payment of 5000 received on 14th June'), extract it into a nested 'payment' object with: 'amount' (float), 'currency' (default 'INR'), 'payment_type' (e.g. 'Advance'), 'status' ('received'), 'received_date' (date string), and 'notes'. If updating status or values of MULTIPLE projects at once (e.g. 'mark apniestate as finished and rest as developing'), extract a list/array under the 'updates' key, where each item in the array is an object with: 'title' (project name, or 'rest'/'others' to represent all other projects), and the properties to change (e.g., 'status', 'description', 'total_amount'). Example: 'mark apniestate as finished and rest as developing' -> action='update', updates=[{'title': 'apniestate', 'status': 'finished'}, {'title': 'rest', 'status': 'developing'}].\n"
                "  IMPORTANT: For project titles, extract ONLY the actual name (e.g. 'Alpha project' → 'Alpha').\n"
                "  IMPORTANT: If user wants to DELETE MULTIPLE projects, also extract 'exclude_names' as a list of project names to KEEP.\n"
                "  Example: 'remove every project named acme except acme pdf project' → action='delete', title='acme', exclude_names=['acme pdf project']\n"
                "- For 'create_task': Extract action ('create', 'update', 'delete', 'clear', 'empty', 'read', 'list', 'query', 'complete', 'generate_pdf'), title, description, priority, status, project_title, due_date, estimated_hours.\n"
                "- For 'track_pending': Extract action ('create', 'update', 'delete', 'clear', 'read', 'list', 'query', 'complete'), title, description, project_title, is_completed.\n"
                "- For 'track_payment': Extract action ('create', 'update', 'delete', 'clear', 'empty', 'read', 'list', 'query', 'sync', 'generate_pdf'), project_title, amount, currency (default INR), payment_type, status, received_date, notes.\n"
                "  IMPORTANT: If user says 'add', 'log', or 'record' → action='create'. Only 'edit'/'modify'/'correct'/'change' → 'update'.\n\n"
                "CONTEXT & MEMORY RULES:\n"
                "1. Read the conversation history context to resolve references like 'this', 'that', 'its', 'first one', 'next', 'the project', etc.\n"
                "2. If the user is modifying or correcting previous statements (e.g. 'only the first one is advance, next is first installment'), extract the resolved project_title and amount from the conversation history.\n"
                "3. Set action='update' if the user is correcting or modifying a previously created item.\n\n"
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
        response = await llm.ainvoke(messages)
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
            elif intent == "generate_report":
                for key in ["report_type", "project_title", "theme", "title", "filename"]:
                    if extracted.get(key) is not None:
                        report[key] = extracted[key]
            elif intent == "create_project":
                project_data["action"] = extracted.get("action") or "create"
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
                                "description": t_item.get("description"),
                                "priority": t_item.get("priority") or "medium",
                                "status": t_item.get("status") or "todo",
                                "project_title": t_item.get("project_title") or extracted.get("project_title"),
                                "due_date": t_item.get("due_date"),
                                "estimated_hours": t_item.get("estimated_hours"),
                            })
                else:
                    if todos:
                        last_todo = todos[-1]
                        for key in ["action", "title", "description", "priority", "status", "project_title", "due_date", "estimated_hours"]:
                            if extracted.get(key) is not None:
                                last_todo[key] = extracted[key]
                    else:
                        todos.append({
                            "action": extracted.get("action") or "create",
                            "title": extracted.get("title"),
                            "description": extracted.get("description"),
                            "priority": extracted.get("priority") or "medium",
                            "status": extracted.get("status") or "todo",
                            "project_title": extracted.get("project_title"),
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
                                "event_type": e_item.get("event_type") or "milestone",
                                "event_date": e_item.get("event_date"),
                                "notes": e_item.get("notes"),
                            })
                else:
                    if timeline:
                        last_event = timeline[-1]
                        for key in ["action", "event_name", "event_type", "event_date", "notes"]:
                            if extracted.get(key) is not None:
                                last_event[key] = extracted[key]
                    else:
                        timeline.append({
                            "action": extracted.get("action") or "create",
                            "event_name": extracted.get("event_name"),
                            "event_type": extracted.get("event_type") or "milestone",
                            "event_date": extracted.get("event_date"),
                            "notes": extracted.get("notes"),
                        })
            elif intent == "track_payment":
                for key in ["action", "project_title", "amount", "currency", "payment_type", "status", "received_date", "notes", "payments"]:
                    if extracted.get(key) is not None:
                        payment[key] = extracted[key]
                if "payments" in extracted and isinstance(extracted["payments"], list) and extracted["payments"]:
                    first_p = extracted["payments"][0]
                    for k in ["amount", "currency", "payment_type", "status", "received_date", "notes"]:
                        if payment.get(k) is None and isinstance(first_p, dict):
                            payment[k] = first_p.get(k)
            elif intent == "track_pending":
                for key in ["action", "title", "description", "project_title", "is_completed"]:
                    if extracted.get(key) is not None:
                        pending[key] = extracted[key]
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

    return {
        "project": project_data,
        "todos": todos,
        "timeline": timeline,
        "payment": payment,
        "reminder": reminder,
        "pending": pending,
        "report": report,
        "client": client,
        "analytics": analytics,
    }
