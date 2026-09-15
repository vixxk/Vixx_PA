"""
AI Orchestrator Router — Thin Dispatcher with DB-backed Memory
===============================================================
Receives user input, runs the LangGraph workflow, then dispatches to the
appropriate domain service based on the classified intent.

Phase 3: Now uses memory_service for persistent conversations instead of
volatile in-memory session_store.
"""

from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, Optional
from uuid import UUID

from app.database import get_db
from app.models.user import User
from app.schemas.ai import AIProcessRequest, AIProcessResponse, AIFeedbackRequest
from app.utils.auth_helper import get_current_user
from app.graphs.workflow import app_workflow
from app.config import settings

# Domain services
from app.services import project_service, task_service, payment_service
from app.services import timeline_service, reminder_service, pending_service
from app.services import report_service
from app.services import memory_service

router = APIRouter(prefix="/ai", tags=["AI Orchestrator"])


@router.post("/transcribe")
async def transcribe_audio(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """
    Transcribes audio to text using Groq's Whisper API.
    """
    if not settings.GROQ_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="GROQ_API_KEY is not configured. Please add it to your .env file."
        )

    # Read audio bytes
    audio_bytes = await file.read()
    filename = file.filename or "recording.webm"
    content_type = file.content_type or "audio/webm"

    import httpx
    headers = {
        "Authorization": f"Bearer {settings.GROQ_API_KEY}"
    }

    async with httpx.AsyncClient() as client:
        files = {
            "file": (filename, audio_bytes, content_type)
        }
        data = {
            "model": "whisper-large-v3"
        }
        try:
            response = await client.post(
                "https://api.groq.com/openai/v1/audio/transcriptions",
                headers=headers,
                files=files,
                data=data,
                timeout=30.0
            )
            
            if response.status_code != 200:
                detail_msg = f"Groq Whisper transcription failed: {response.text}"
                try:
                    error_json = response.json()
                    if "error" in error_json and "message" in error_json["error"]:
                        detail_msg = error_json["error"]["message"]
                except Exception:
                    pass
                raise HTTPException(
                    status_code=response.status_code,
                    detail=detail_msg
                )
                
            res_data = response.json()
            return {"text": res_data.get("text", "")}
            
        except httpx.RequestError as e:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Network error communicating with Groq: {str(e)}"
            )


@router.post("/process", response_model=AIProcessResponse)
async def process_ai_command(
    request: AIProcessRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    user_id = current_user.id
    raw_input = request.raw_input

    # Get or create session metadata (lightweight in-memory cache)
    session_data = memory_service.get_or_create_session(user_id, request.session_id)
    session_id = session_data["session_id"]

    # Load conversation history from DB
    history = await memory_service.get_session_history(db, user_id, session_id, limit=20)

    # Auto-summarize if session gets long (every 40 messages)
    msg_count = await memory_service.get_session_count(db, user_id, session_id)
    if msg_count > 0 and msg_count % 40 == 0:
        try:
            await memory_service.summarize_and_archive_session(db, user_id, session_id)
        except Exception:
            pass

    # ── Handle pending deletion confirmation ──
    pending_delete = session_data.get("pending_delete_action")
    if pending_delete:
        confirm_input = raw_input.strip().lower()
        if confirm_input in ["yes", "y", "confirm", "proceed", "sure", "ok", "okay", "do it"]:
            initial_state = pending_delete
            initial_state["confirmed_deletion"] = True
            initial_state["raw_input"] = raw_input
            initial_state["history"] = history
            session_data["pending_delete_action"] = None
        else:
            session_data["pending_delete_action"] = None
            cancel_msg = "Action cancelled."
            await memory_service.save_message(db, user_id, session_id, "user", raw_input)
            await memory_service.save_message(db, user_id, session_id, "assistant", cancel_msg)
            return _make_response({"intent": "clarify"}, summary=cancel_msg, session_id=str(session_id))
    else:
        # ── Handle Google Sheets link requests ──
        lower_input = raw_input.lower()
        if ("link" in lower_input or "url" in lower_input) and (
            ("sheet" in lower_input or "spreadsheet" in lower_input)
            and not any(w in lower_input for w in ["add", "create", "insert", "delete", "remove", "clear", "update", "track", "new", "complete"])
        ):
            msg = "Google Sheets integration has been disabled. All data is stored and managed directly in PostgreSQL."
            await memory_service.save_message(db, user_id, session_id, "user", raw_input)
            await memory_service.save_message(db, user_id, session_id, "assistant", msg)
            return _make_response({"intent": "clarify"}, summary=msg, session_id=str(session_id))

        # ── Deterministic Report Bypass ──
        if lower_input.startswith("generate ") and ("report" in lower_input or "pdf" in lower_input or "notepad" in lower_input):
            import re
            
            report_type = None
            if "notepad" in lower_input or "notes" in lower_input:
                report_type = "notepad"
            elif any(w in lower_input for w in ["payment", "revenue", "earnings", "invoice", "bill"]):
                report_type = "payments"
            elif any(w in lower_input for w in ["todo", "task", "tasks", "backlog"]):
                report_type = "todo"
            else:
                report_type = "todo"
                
            filename = None
            filename_match = re.search(r'named\s+"([^"]+)"', raw_input, re.IGNORECASE)
            if not filename_match:
                filename_match = re.search(r'named\s+([a-zA-Z0-9_\-\s]+)', raw_input, re.IGNORECASE)
            if filename_match:
                filename = filename_match.group(1).strip()
                
            theme = "navy"
            for t in ["teal", "emerald", "charcoal", "ruby", "dark"]:
                if t in lower_input:
                    theme = t
                    break
                    
            # Parse multiple project titles if present
            temp_input = raw_input
            if filename_match:
                temp_input = temp_input.replace(filename_match.group(0), "")
                
            project_titles = re.findall(r'"([^"]+)"', temp_input)
            if not project_titles:
                project_match = re.search(r'projects?\s+([a-zA-Z0-9_\-\s,]+?)(?:\s+in\s+|\s+named\s+|$)', temp_input, re.IGNORECASE)
                if project_match:
                    cleaned_titles = project_match.group(1).replace(" and ", ",")
                    project_titles = [t.strip() for t in cleaned_titles.split(",") if t.strip() and t.strip().lower() not in ["all", "list", "projects"]]
            
            report_data = {
                "report_type": report_type,
                "project_titles": project_titles,
                "theme": theme,
                "filename": filename
            }
            
            summary_msg = await report_service.generate_report(db, user_id, report_data, raw_input, session_data)
            
            await memory_service.save_message(db, user_id, session_id, "user", raw_input, intent="generate_report")
            await memory_service.save_message(db, user_id, session_id, "assistant", summary_msg, intent="generate_report")
            
            session_data["message_count"] = session_data.get("message_count", 0) + 2
            return _make_response({
                "intent": "generate_report",
                "report": report_data,
                "summary": summary_msg,
                "reasoning_steps": ["⚡ Deterministic Engine → bypassed LLM to guarantee report delivery."]
            }, summary=summary_msg, session_id=str(session_id))

        # Pre-fetch all workspace projects to give the agent full context awareness
        workspace_projects = []
        try:
            from app.models.project import Project
            from sqlalchemy import select
            p_res = await db.execute(select(Project).filter(Project.user_id == user_id))
            p_rows = p_res.scalars().all()
            workspace_projects = [
                {
                    "id": str(p.id),
                    "title": p.title,
                    "status": p.status,
                    "total_amount": float(p.total_amount or 0.0),
                    "description": p.description
                }
                for p in p_rows
            ]
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"Could not load workspace_projects: {e}")

        # ── Resolve project context from frontend dropdown if provided ──
        context_project_title = request.project_title
        if request.project_id and not context_project_title and request.project_id != "all":
            try:
                for wp in workspace_projects:
                    if wp["id"] == request.project_id:
                        context_project_title = wp["title"]
                        break
            except Exception:
                pass

        if context_project_title:
            session_data["project_title"] = context_project_title

        # ── Build initial state for LangGraph ──
        prev_state = session_data.get("pending_state")
        if not prev_state:
            prev_state = await memory_service.get_session_state(db, user_id, session_id)
            if prev_state:
                session_data["pending_state"] = prev_state
        initial_state = {
            "user_id": str(user_id),
            "raw_input": raw_input,
            "intent": "clarify",
            "project": None,
            "timeline": [],
            "todos": [],
            "milestones": [],
            "risks": [],
            "payment": None,
            "reminder": None,
            "pending": None,
            "report": None,
            "summary": None,
            "needs_clarification": False,
            "clarification_message": None,
            "missing_fields": [],
            "approved": False,
            "history": history,
            "last_project": session_data.get("last_project"),
            "project_id": request.project_id if request.project_id != "all" else None,
            "project_title": context_project_title,
            "workspace_projects": workspace_projects,
            "google_token": request.google_token,
            "reasoning_steps": [],
            "local_time": request.local_time,
            "timezone_offset": request.timezone_offset,
        }

        if prev_state:
            for key in ["project", "todos", "timeline", "milestones", "risks", "payment", "reminder", "pending", "report", "summary"]:
                if prev_state.get(key) is not None:
                    initial_state[key] = prev_state[key]
            initial_state["intent"] = prev_state.get("intent") or "clarify"

    # ── Run the LangGraph state machine ──
    try:
        final_state = await app_workflow.ainvoke(initial_state)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error running agent graph: {str(e)}",
        )

    # ── If clarification is needed, save state and return ──
    if final_state.get("needs_clarification"):
        session_data["pending_state"] = final_state
        await memory_service.save_session_state(db, user_id, session_id, final_state)
        clar_msg = final_state.get("clarification_message") or "Could you provide more details?"
        # Save to persistent memory
        await memory_service.save_message(db, user_id, session_id, "user", raw_input, intent=final_state.get("intent"))
        await memory_service.save_message(db, user_id, session_id, "assistant", clar_msg)
        return _make_response(final_state, session_id=str(session_id))

    # ── Dispatch to domain service based on intent ──
    intent = final_state.get("intent")
    summary_msg = None

    try:
        if intent == "create_project":
            summary_msg = await _handle_project(db, user_id, final_state, initial_state, session_data, raw_input)
        elif intent == "create_task":
            summary_msg = await _handle_task(db, user_id, final_state, initial_state, session_data, raw_input, request)
        elif intent == "track_payment":
            summary_msg = await _handle_payment(db, user_id, final_state, initial_state, session_data, raw_input)
        elif intent == "update_timeline":
            summary_msg = await _handle_timeline(db, user_id, final_state, initial_state, session_data, raw_input, request)
        elif intent == "set_reminder":
            summary_msg = await _handle_reminder(db, user_id, final_state, session_data, request)
        elif intent == "track_pending":
            summary_msg = await _handle_pending(db, user_id, final_state, session_data, raw_input)
        elif intent == "generate_report":
            summary_msg = await _handle_report(db, user_id, final_state, session_data, raw_input)
        elif intent in ["workspace_overview", "generate_summary", "analytics"]:
            summary_msg = await _handle_workspace_overview(db, user_id, session_data, raw_input)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing {intent}: {str(e)}")

    session_data["pending_state"] = None
    await memory_service.delete_session_state(db, user_id, session_id)
    raw_summary = summary_msg or final_state.get("summary") or "Action processed."
    filtered_summary = await _filter_and_format_response(
        raw_input=raw_input,
        system_response=raw_summary,
        history=history,
        local_time=request.local_time,
        timezone_offset=request.timezone_offset
    )
    final_state["summary"] = filtered_summary

    # Save to persistent memory with entity extraction
    entities = _extract_entities(final_state)
    await memory_service.save_message(db, user_id, session_id, "user", raw_input, intent=intent, entities=entities)
    await memory_service.save_message(db, user_id, session_id, "assistant", final_state["summary"], intent=intent, entities={"reasoningSteps": final_state.get("reasoning_steps", [])})

    # Store entity facts for long-term memory
    await _store_entity_facts(db, user_id, session_id, final_state)

    session_data["message_count"] = session_data.get("message_count", 0) + 2
    return _make_response(final_state, summary=final_state["summary"], session_id=str(session_id))


# ══════════════════════════════════════════════════════════════
# Helpers
# ══════════════════════════════════════════════════════════════

def _make_response(final_state: dict, summary: str = None, session_id: str = None) -> dict:
    """Build a standardized response from the workflow state."""
    return {
        "intent": final_state.get("intent", "clarify"),
        "needs_clarification": final_state.get("needs_clarification", False),
        "clarification_message": final_state.get("clarification_message"),
        "missing_fields": final_state.get("missing_fields", []),
        "project": final_state.get("project"),
        "timeline": final_state.get("timeline", []),
        "todos": final_state.get("todos", []),
        "milestones": final_state.get("milestones", []),
        "risks": final_state.get("risks", []),
        "reminder": final_state.get("reminder"),
        "payment": final_state.get("payment"),
        "report": final_state.get("report"),
        "summary": summary or final_state.get("summary"),
        "reasoning_steps": final_state.get("reasoning_steps", []),
        "session_id": session_id,
    }


def _extract_entities(final_state: dict) -> Optional[dict]:
    """Extract entity names from the final state for indexing."""
    entities = {}
    project = final_state.get("project")
    if project and isinstance(project, dict) and project.get("title"):
        entities["project"] = project["title"]
    payment = final_state.get("payment")
    if payment and isinstance(payment, dict) and payment.get("project_title"):
        entities["payment_project"] = payment["project_title"]
    report = final_state.get("report")
    if report and isinstance(report, dict) and report.get("project_title"):
        entities["report_project"] = report["project_title"]
    todos = final_state.get("todos")
    if todos and isinstance(todos, list) and todos:
        last = todos[-1]
        if isinstance(last, dict) and last.get("title"):
            entities["task"] = last["title"]
    return entities if entities else None


async def _store_entity_facts(db, user_id, session_id, final_state):
    """Auto-extract and store entity facts from completed operations."""
    try:
        intent = final_state.get("intent")
        if intent == "create_project":
            project = final_state.get("project") or {}
            if project.get("title"):
                action = project.get("action") or "create"
                await memory_service.store_entity_fact(
                    db, user_id, "project", project["title"],
                    f"Project action: {action}",
                    session_id=session_id,
                )
        elif intent == "track_payment":
            payment = final_state.get("payment") or {}
            if payment.get("project_title") and payment.get("amount"):
                await memory_service.store_entity_fact(
                    db, user_id, "project", payment["project_title"],
                    f"Payment of {payment['amount']} {payment.get('currency', 'INR')} logged",
                    session_id=session_id,
                )
    except Exception:
        pass  # Non-critical — don't break the main flow


# ══════════════════════════════════════════════════════════════
# Intent Handlers — thin wrappers that delegate to services
# ══════════════════════════════════════════════════════════════

async def _handle_project(db, user_id, final_state, initial_state, session_data, raw_input):
    project_data = final_state.get("project") or {}
    action = project_data.get("action") or "create"

    if action in ["read", "list", "query", "enquire"]:
        return await project_service.read_project(db, user_id, project_data.get("title"), raw_input, session_data)

    elif action in ["delete", "clear", "empty"]:
        exclude_names = project_data.get("exclude_names")
        confirmed = initial_state.get("confirmed_deletion", False)
        result = await project_service.delete_project(
            db, user_id, project_data.get("title"),
            exclude_names=exclude_names, confirmed=confirmed, raw_input=raw_input,
        )
        if result["needs_confirmation"]:
            session_data["pending_delete_action"] = final_state
            final_state["needs_clarification"] = True
            final_state["clarification_message"] = result["message"]
            session_data["pending_state"] = final_state
            return result["message"]
        return result["message"]

    elif action == "update":
        # Check if the user is correcting an accidental payment log
        # E.g. "not payment, but..."
        lower_input = raw_input.lower()
        if any(ph in lower_input for ph in ["not payment", "no payment", "cancel payment", "revert payment", "revert the payment"]):
            title = project_data.get("title")
            if title:
                from app.models.payment import Payment
                from app.services.entity_resolver import resolve_project
                from sqlalchemy import select, desc
                proj = await resolve_project(db, user_id, title)
                if proj:
                    pay_stmt = select(Payment).filter(Payment.project_id == proj.id).order_by(desc(Payment.created_at))
                    pay_res = await db.execute(pay_stmt)
                    last_payment = pay_res.scalars().first()
                    if last_payment:
                        await db.delete(last_payment)
                        await db.commit()
                        from app.services.analytics_service import invalidate_analytics_cache
                        invalidate_analytics_cache(user_id)
                        import logging
                        logging.getLogger(__name__).info(f"Reverted accidental payment of {last_payment.amount} for project {proj.title} due to user correction: '{raw_input}'")

        result = await project_service.update_project(db, user_id, project_data, final_state)
        if isinstance(result, dict) and result.get("needs_confirmation"):
            session_data["pending_delete_action"] = final_state
            final_state["needs_clarification"] = True
            final_state["clarification_message"] = result["summary"]
            session_data["pending_state"] = final_state
            return result["summary"]

        p = result.get("project")
        if p:
            session_data["last_project"] = {
                "id": str(p.id), "title": p.title,
                "description": p.description, "summary": p.summary,
            }
        return result["summary"]

    else:  # create
        if not project_data.get("title"):
            return "Please provide a title for the new project."

        # Check if the user is correcting an accidental payment log
        lower_input = raw_input.lower()
        if any(ph in lower_input for ph in ["not payment", "no payment", "cancel payment", "revert payment", "revert the payment"]):
            title = project_data.get("title")
            if title:
                from app.models.payment import Payment
                from app.services.entity_resolver import resolve_project
                from sqlalchemy import select, desc
                proj = await resolve_project(db, user_id, title)
                if proj:
                    pay_stmt = select(Payment).filter(Payment.project_id == proj.id).order_by(desc(Payment.created_at))
                    pay_res = await db.execute(pay_stmt)
                    last_payment = pay_res.scalars().first()
                    if last_payment:
                        await db.delete(last_payment)
                        await db.commit()
                        from app.services.analytics_service import invalidate_analytics_cache
                        invalidate_analytics_cache(user_id)
                        import logging
                        logging.getLogger(__name__).info(f"Reverted accidental payment of {last_payment.amount} for project {proj.title} due to user correction: '{raw_input}'")

        result = await project_service.create_project(db, user_id, project_data, final_state)
        p = result["project"]
        if p:
            session_data["last_project"] = {
                "id": str(p.id), "title": p.title,
                "description": p.description, "summary": p.summary,
            }
        return result["summary"]


async def _handle_task(db, user_id, final_state, initial_state, session_data, raw_input, request):
    if not final_state.get("todos"):
        return "I couldn't determine the task details. Please try again."
    todo_data = final_state["todos"][-1]
    action = todo_data.get("action") or "create"

    if action == "generate_pdf" or "pdf" in raw_input.lower():
        return await task_service.generate_tasks_pdf(db, user_id, raw_input, todo_data.get("project_title"), session_data)

    if action in ["read", "list", "query", "enquire"]:
        return await task_service.list_tasks(db, user_id, todo_data.get("project_title"), raw_input, session_data)

    elif action in ["delete", "clear", "empty"]:
        confirmed = initial_state.get("confirmed_deletion", False)
        result = await task_service.delete_tasks(db, user_id, todo_data.get("title"), confirmed)
        if result["needs_confirmation"]:
            session_data["pending_delete_action"] = final_state
            final_state["needs_clarification"] = True
            final_state["clarification_message"] = result["message"]
            session_data["pending_state"] = final_state
            return result["message"]
        return result["message"]

    elif action in ["update", "complete"]:
        return await task_service.update_task(db, user_id, todo_data, raw_input)

    else:  # create
        google_token = request.google_token or session_data.get("google_token")
        return await task_service.create_task(db, user_id, todo_data, raw_input, session_data, google_token)


async def _handle_payment(db, user_id, final_state, initial_state, session_data, raw_input):
    payment_data = final_state.get("payment") or {}
    action = payment_data.get("action") or "create"

    if action == "generate_pdf" or ("pdf" in raw_input.lower() and "payment" in raw_input.lower()):
        return await payment_service.generate_payments_pdf(db, user_id, raw_input, payment_data.get("project_title"), session_data)

    if action == "sync":
        return "Google Sheets integration has been disabled. All data is managed directly in PostgreSQL."

    if action in ["read", "list", "query", "enquire"]:
        return await payment_service.list_payments(db, user_id, payment_data.get("project_title"), raw_input, session_data)

    elif action == "delete":
        confirmed = initial_state.get("confirmed_deletion", False)
        result = await payment_service.delete_payment(db, user_id, payment_data, raw_input, session_data, confirmed)
        if result["needs_confirmation"]:
            session_data["pending_delete_action"] = final_state
            final_state["needs_clarification"] = True
            final_state["clarification_message"] = result["message"]
            session_data["pending_state"] = final_state
            return result["message"]
        return result["message"]

    elif action == "update":
        return await payment_service.update_payment(db, user_id, payment_data, raw_input, session_data)

    else:  # create
        has_amount = payment_data.get("amount") or (
            "payments" in payment_data 
            and isinstance(payment_data["payments"], list) 
            and any(p.get("amount") for p in payment_data["payments"] if isinstance(p, dict))
        )
        if not has_amount:
            return "Please specify the payment amount."
        return await payment_service.create_payment(db, user_id, payment_data, raw_input, session_data)


async def _handle_timeline(db, user_id, final_state, initial_state, session_data, raw_input, request):
    if not final_state.get("timeline"):
        return "I couldn't determine the timeline event details."
    event_data = final_state["timeline"][-1]
    action = event_data.get("action") or "create"

    if action in ["read", "list", "query", "enquire"]:
        return await timeline_service.list_timeline(db, user_id, raw_input, session_data)

    elif action in ["delete", "clear", "empty"]:
        confirmed = initial_state.get("confirmed_deletion", False)
        result = await timeline_service.delete_timeline(db, user_id, confirmed)
        if result["needs_confirmation"]:
            session_data["pending_delete_action"] = final_state
            final_state["needs_clarification"] = True
            final_state["clarification_message"] = result["message"]
            session_data["pending_state"] = final_state
            return result["message"]
        return result["message"]

    elif action == "update":
        return await timeline_service.update_timeline_event(db, user_id, event_data, raw_input)

    else:  # create
        google_token = request.google_token or session_data.get("google_token")
        return await timeline_service.create_timeline_event(db, user_id, event_data, raw_input, session_data, google_token)


async def _handle_reminder(db, user_id, final_state, session_data, request):
    reminder_data = final_state.get("reminder") or {}
    action = reminder_data.get("action") or "create"

    if action in ["list", "read", "query"]:
        return await reminder_service.list_reminders(db, user_id)
    elif action in ["delete", "cancel"]:
        return await reminder_service.cancel_reminder(db, user_id, reminder_data.get("title"))
    elif action == "clear":
        return await reminder_service.clear_all_reminders(db, user_id)
    elif action == "update":
        return await reminder_service.update_reminder(db, user_id, reminder_data, request.timezone_offset)
    else:  # create
        result = await reminder_service.create_reminder(db, user_id, reminder_data, request.timezone_offset)
        if result.get("needs_clarification"):
            final_state["needs_clarification"] = True
            final_state["clarification_message"] = result["message"]
            session_data["pending_state"] = final_state
            return result["message"]
        return result["message"]


async def _handle_pending(db, user_id, final_state, session_data, raw_input):
    pending_data = final_state.get("pending") or {}
    action = pending_data.get("action") or "create"

    if action in ["read", "list", "query"]:
        return await pending_service.list_pending(db, user_id, pending_data.get("project_title"), raw_input, session_data)
    elif action in ["delete", "cancel", "clear"]:
        confirmed = final_state.get("confirmed_deletion", False)
        result = await pending_service.delete_pending(db, user_id, pending_data, confirmed)
        if isinstance(result, dict) and result.get("needs_confirmation"):
            session_data["pending_delete_action"] = final_state
            final_state["needs_clarification"] = True
            final_state["clarification_message"] = result["message"]
            session_data["pending_state"] = final_state
            return result["message"]
        return result["message"] if isinstance(result, dict) else result
    elif action == "complete":
        return await pending_service.complete_pending(db, user_id, pending_data)
    elif action == "update":
        return await pending_service.update_pending(db, user_id, pending_data, raw_input)
    else:  # create
        result = await pending_service.create_pending(db, user_id, pending_data, raw_input, session_data)
        if isinstance(result, dict) and result.get("needs_clarification"):
            final_state["needs_clarification"] = True
            final_state["clarification_message"] = result["message"]
            session_data["pending_state"] = final_state
            return result["message"]
        return result


async def _handle_report(db, user_id, final_state, session_data, raw_input):
    report_data = final_state.get("report") or {}
    return await report_service.generate_report(db, user_id, report_data, raw_input, session_data)


async def _handle_workspace_overview(db: AsyncSession, user_id: UUID, session_data: dict = None, raw_input: str = "") -> str:
    """
    Generates a multi-domain Executive Briefing of projects, urgent tasks,
    financial health, pending client deliverables, and upcoming alerts.
    """
    from app.models.project import Project
    from app.models.todo import Todo
    from app.models.payment import Payment
    from app.models.reminder import Reminder
    from app.models.pending_thing import PendingThing
    from sqlalchemy import select, desc

    # 1. Projects
    p_stmt = select(Project).filter(Project.user_id == user_id).order_by(desc(Project.created_at))
    projects = (await db.execute(p_stmt)).scalars().all()

    active_projects = [p for p in projects if p.status not in ["finished", "completed"]]
    finished_projects = [p for p in projects if p.status in ["finished", "completed"]]
    total_budget = sum(float(p.total_amount or 0) for p in projects)

    # 2. Tasks
    proj_ids = [p.id for p in projects]
    if proj_ids:
        t_stmt = select(Todo).filter(Todo.project_id.in_(proj_ids)).order_by(Todo.due_date.asc().nullslast(), desc(Todo.created_at))
        todos = (await db.execute(t_stmt)).scalars().all()
    else:
        todos = []

    pending_todos = [t for t in todos if t.status != "done"]
    high_prio_todos = [t for t in pending_todos if t.priority in ["high", "critical"]]

    # 3. Payments
    if proj_ids:
        pay_stmt = select(Payment).filter(Payment.project_id.in_(proj_ids))
        payments = (await db.execute(pay_stmt)).scalars().all()
    else:
        payments = []

    total_received = sum(float(p.amount) for p in payments if p.status == "received")
    pending_revenue = max(0.0, total_budget - total_received)

    # 4. Reminders
    rem_stmt = select(Reminder).filter(Reminder.user_id == user_id, Reminder.status == "scheduled").order_by(Reminder.remind_at.asc()).limit(3)
    reminders = (await db.execute(rem_stmt)).scalars().all()

    # 5. Pending deliverables
    pend_stmt = select(PendingThing).filter(PendingThing.user_id == user_id, PendingThing.is_completed == False).limit(3)
    pending_things = (await db.execute(pend_stmt)).scalars().all()

    # Build Executive Briefing Markdown
    proj_map = {p.id: p.title for p in projects}

    msg = "### ⚡ Vixx Executive Workspace Briefing\n\n"

    msg += "**💼 Workspace Projects:**\n"
    if projects:
        msg += f"- **Active:** {len(active_projects)} | **Completed:** {len(finished_projects)} | **Pipeline Value:** ₹{total_budget:,.0f}\n"
        active_titles = ", ".join(f"*{p.title}*" for p in active_projects[:4])
        if active_titles:
            msg += f"- **Focus Workspaces:** {active_titles}\n"
    else:
        msg += "- No projects created yet. Say *'Create project [name]'* to start.\n"

    msg += "\n**📋 Priority Action Items:**\n"
    if high_prio_todos:
        for t in high_prio_todos[:4]:
            p_name = proj_map.get(t.project_id, "General")
            due_str = f", Due: {t.due_date.strftime('%b %d')}" if t.due_date else ""
            msg += f"- 🔴 **{t.title}** *(Project: {p_name}{due_str})*\n"
    elif pending_todos:
        for t in pending_todos[:3]:
            p_name = proj_map.get(t.project_id, "General")
            due_str = f", Due: {t.due_date.strftime('%b %d')}" if t.due_date else ""
            msg += f"- 🟡 **{t.title}** *(Project: {p_name}{due_str})*\n"
    else:
        msg += "- 🎉 All sprint tasks are completed!\n"

    msg += "\n**💳 Financial Snapshot:**\n"
    msg += f"- **Total Received:** ₹{total_received:,.0f} | **Remaining Outstanding:** ₹{pending_revenue:,.0f}\n"

    if reminders:
        msg += "\n**⏰ Upcoming Alerts:**\n"
        for r in reminders:
            time_str = r.remind_at.strftime("%b %d, %I:%M %p") if r.remind_at else "Upcoming"
            channel_label = r.channel.upper() if r.channel else "SMS"
            msg += f"- 🔔 **{r.title}** ({time_str} via {channel_label})\n"

    if pending_things:
        msg += "\n**⏳ Client Deliverables Awaiting:**\n"
        for pt in pending_things:
            p_name = proj_map.get(pt.project_id, "General") if pt.project_id else "General"
            msg += f"- 📦 **{pt.title}** *(Project: {p_name})*\n"

    return msg


# ══════════════════════════════════════════════════════════════
# Feedback endpoint
# ══════════════════════════════════════════════════════════════

FEEDBACK_FILE = "feedback_log.json"

@router.post("/feedback")
async def log_feedback(
    req: AIFeedbackRequest,
    current_user: User = Depends(get_current_user),
):
    import json
    import os
    from datetime import datetime

    data = []
    if os.path.exists(FEEDBACK_FILE):
        try:
            with open(FEEDBACK_FILE, "r") as f:
                data = json.load(f)
        except Exception:
            pass

    data.append({
        "user_id": str(current_user.id),
        "user_email": current_user.email,
        "rating": req.rating,
        "feedback_text": req.feedback_text,
        "timestamp": datetime.utcnow().isoformat(),
    })

    with open(FEEDBACK_FILE, "w") as f:
        json.dump(data, f, indent=2)

    return {"success": True, "message": "Feedback submitted successfully."}


@router.get("/sessions")
async def list_user_sessions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    sessions = await memory_service.get_all_sessions(db, current_user.id)
    return sessions


@router.put("/sessions/{session_id}/rename")
async def rename_user_session(
    session_id: str,
    title: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        s_uuid = UUID(session_id)
    except (ValueError, TypeError):
        import uuid as uuid_mod
        s_uuid = uuid_mod.uuid5(current_user.id, session_id)
        
    await memory_service.rename_session(db, current_user.id, s_uuid, title)
    return {"success": True}


@router.delete("/sessions/{session_id}")
async def delete_user_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        s_uuid = UUID(session_id)
    except (ValueError, TypeError):
        import uuid as uuid_mod
        s_uuid = uuid_mod.uuid5(current_user.id, session_id)
        
    await memory_service.delete_session(db, current_user.id, s_uuid)
    return {"success": True}


async def _filter_and_format_response(
    raw_input: str,
    system_response: str,
    history: list = None,
    local_time: str = None,
    timezone_offset: int = None
) -> str:
    """
    Feedback and filtering layer: passes the raw database/domain output through the LLM 
    to filter and format it according to the user's instructions and constraints.
    """
    if not system_response:
        return "Action processed."

    # Fast bypass: if domain response is already structured markdown and no strict formatting was asked
    raw_lower = raw_input.lower().strip()
    explicit_formatting_cues = ["only", "just the", "one word", "in json", "short form", "format as", "in table", "summarize in", "briefly", "single word", "bullet points only"]
    has_explicit_formatting = any(cue in raw_lower for cue in explicit_formatting_cues)

    if not has_explicit_formatting and (
        system_response.startswith("###") or
        system_response.startswith("#") or
        system_response.startswith("⚡") or
        system_response.startswith("Successfully") or
        system_response.startswith("Action cancelled") or
        system_response.startswith("No projects found") or
        system_response.startswith("No pending tasks found") or
        system_response.startswith("No payment records found") or
        "### 📋" in system_response or
        "### 💳" in system_response
    ):
        return system_response

    try:
        from app.utils.llm import get_llm
        from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
        import dateutil.parser
        from datetime import datetime, timezone as dt_timezone, timedelta
        
        llm = get_llm()
        
        local_dt = None
        if local_time:
            try:
                local_dt = dateutil.parser.parse(local_time)
                if local_dt.tzinfo is not None and timezone_offset is not None:
                    user_tz = dt_timezone(timedelta(minutes=-timezone_offset))
                    local_dt = local_dt.astimezone(user_tz)
            except Exception:
                pass
        if not local_dt:
            local_dt = datetime.now()
            
        date_context = f"Current User Local Datetime: {local_dt.strftime('%Y-%m-%d %I:%M:%S %p')} ({local_dt.strftime('%A')})"
        
        # Format history context
        history_msgs = []
        if history:
            # Add up to 4 recent messages for context
            for msg in history[-4:]:
                if msg["role"] == "user":
                    history_msgs.append(HumanMessage(content=msg["content"]))
                else:
                    history_msgs.append(AIMessage(content=msg["content"]))
                    
        system_prompt = (
            "You are Vixx, the Personal Assistant. "
            "Your task is to review the user's query and the raw system/database data, "
            "and generate the final response to the user.\n\n"
            f"Date Context:\n- {date_context}\n\n"
            "CRITICAL INSTRUCTIONS:\n"
            "1. You MUST satisfy all the formatting constraints requested by the user in their query "
            "(e.g., if they ask 'just tell me all project names nothing else', list ONLY the names and NO description/tasks/payments/etc.).\n"
            "2. Never override or modify the dates/times, status, or IDs returned in the raw system/database response. Keep them completely intact as the source of truth.\n"
            "3. Never hallucinate or add any projects, tasks, or transactions that are NOT in the raw system data.\n"
            "4. If the raw data is empty, or states no data is found, mention that politely.\n"
            "5. Keep the response clean, readable, and professional using Markdown.\n"
            "6. Keep any links, file paths, numbers, and critical action results (like status or success/failure messages) completely intact.\n"
            "7. All monetary amounts are ALWAYS in Indian Rupees (INR / ₹). Never use dollars ($), USD, or any other currency. Never convert amounts between currencies. If the user says '10000', it means ₹10,000 — not dollars.\n"
            "8. When listing tasks/todos, you MUST always include the project name in parentheses/brackets next to the task title (e.g., '(Project: Hyrego)') for every task listed, ensuring no task is left without its project name.\n"
            "9. If the user's query is about external topics, general knowledge, trivia, public figures, math, coding, or anything not related to their workspace database or Vixx's capabilities (e.g., 'who is the president of India', 'what is 4+4', 'who is vivek', etc.):\n"
            "   You MUST immediately refuse to answer. You MUST reply exactly with:\n"
            "   \"I am a dedicated workspace assistant. I can only assist you with information and actions related to your projects, tasks, schedules, invoices, reminders, and files. Please ask me about your workspace data or capabilities.\"\n"
            "   Do NOT cater to the query, do NOT explain, do NOT suggest checking other sites, and do NOT add any other conversational text."
        )
        
        prompt_content = (
            f"User's request: {raw_input}\n\n"
            f"Raw system/database response:\n{system_response}"
        )
        
        messages = [
            SystemMessage(content=system_prompt),
            *history_msgs,
            HumanMessage(content=prompt_content)
        ]
        
        response = await llm.ainvoke(messages)
        return response.content.strip()
        
    except Exception as e:
        # Fallback to the original system response if LLM call fails
        return system_response
