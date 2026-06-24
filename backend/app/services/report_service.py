"""
Report Service — Simplified report/PDF generation across all domains.
Handles notepad, to do list, and payments reports.
"""

import os
import re
import uuid as uuid_mod
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.project import Project
from app.models.todo import Todo
from app.models.payment import Payment

from app.services.entity_resolver import resolve_project_from_context
from app.utils.pdf_generator_templates import (
    NotepadReport,
    ToDoReport,
    PaymentsReport,
)
import logging

logger = logging.getLogger(__name__)


def _sanitize_filename(name: str, default_prefix: str, uid: str) -> str:
    if not name or not name.strip():
        return f"uploads/{default_prefix}_{uid}.pdf"
    
    clean = name.strip()
    if clean.lower().endswith(".pdf"):
        clean = clean[:-4]
        
    # Keep only alphanumeric characters, spaces, hyphens, and underscores
    clean = re.sub(r"[^a-zA-Z0-9_\-\s]", "", clean)
    # Replace spaces with underscores
    clean = re.sub(r"\s+", "_", clean)
    if not clean:
        return f"uploads/{default_prefix}_{uid}.pdf"
    return f"uploads/{clean}.pdf"


async def _format_notepad_with_ai(raw_text: str) -> str:
    """Uses Groq LLM to format notepad content professionally."""
    if not raw_text or not raw_text.strip():
        return ""
    try:
        from app.utils.llm import get_llm
        llm = get_llm()
        prompt = (
            "You are an AI formatting assistant. The user wants to format their project notepad notes "
            "into a clean, professional, and well-structured document for a PDF report.\n\n"
            "Rules:\n"
            "1. Clean up grammar, typographical errors, and spelling mistakes.\n"
            "2. Organize into neat sections with markdown headers (#, ##, or ###) and bullet lists where appropriate.\n"
            "3. RETAIN ALL factual information, numbers, client names, transaction IDs, credentials, links, due dates, and details. Do not lose, summarize out, or invent any facts.\n"
            "4. Return ONLY the clean formatted markdown notes. Do not include any intro, conversational explanation, or outro.\n\n"
            f"Raw Notepad Notes:\n{raw_text}"
        )
        response = await llm.ainvoke(prompt)
        return response.content.strip()
    except Exception as e:
        logger.warning(f"Failed to use AI for notepad formatting: {e}")
        return raw_text  # Fallback to raw text if AI fails


async def generate_report(
    db: AsyncSession,
    user_id: UUID,
    report_data: dict,
    raw_input: str = "",
    session_data: Optional[dict] = None,
) -> str:
    """
    Unified report generation. Determines report type and invokes the
    appropriate template-based PDF generator.
    """
    report_type = (report_data.get("report_type") or "").lower()
    project_title = report_data.get("project_title")
    custom_filename = report_data.get("filename")
    raw_lower = raw_input.lower()

    # Auto-detect report type from raw_input or config
    if not report_type or report_type in ["auto", "general", "all", "everything", "full", "complete"]:
        report_type = _detect_report_type(raw_lower or report_type)

    theme = next((t for t in ["teal", "emerald", "charcoal", "ruby", "dark"] if t in raw_lower), "navy")
    uid = uuid_mod.uuid4().hex[:8]
    os.makedirs("uploads", exist_ok=True)

    # Resolve target project if specified
    target_project = None
    if project_title or "project" in raw_lower or "this" in raw_lower:
        target_project = await resolve_project_from_context(db, user_id, raw_input, extracted_title=project_title, session_data=session_data)

    try:
        if report_type == "notepad":
            return await _generate_notepad_report_flow(db, user_id, target_project, theme, uid, custom_filename)
        elif report_type == "payments":
            return await _generate_payments_report_flow(db, user_id, target_project, theme, uid, custom_filename)
        else:
            # Default to todo list report
            return await _generate_todo_report_flow(db, user_id, target_project, theme, uid, custom_filename)

    except Exception as e:
        logger.exception("Error generating report PDF")
        return f"Failed to generate report PDF: {str(e)}"


def _detect_report_type(raw_lower: str) -> str:
    """Detect the report type from user's natural language input."""
    if "note" in raw_lower or "notepad" in raw_lower or "brief" in raw_lower:
        return "notepad"
    if "payment" in raw_lower or "bill" in raw_lower or "invoice" in raw_lower or "earnings" in raw_lower or "revenue" in raw_lower or "financial" in raw_lower:
        return "payments"
    return "todo"  # Default fallback is To Do list


# ══════════════════════════════════════════════════════════════
# Report Flow Handlers
# ══════════════════════════════════════════════════════════════

async def _generate_notepad_report_flow(
    db: AsyncSession,
    user_id: UUID,
    project: Optional[Project],
    theme: str,
    uid: str,
    custom_filename: Optional[str] = None
) -> str:
    if not project:
        # Get first project for user
        proj_stmt = select(Project).filter(Project.user_id == user_id).limit(1)
        project = (await db.execute(proj_stmt)).scalars().first()
        if not project:
            return "No projects found. Please create a project first before compiling its notepad."

    raw_notes = project.notepad or ""
    formatted_notes = await _format_notepad_with_ai(raw_notes)

    fname = _sanitize_filename(custom_filename, f"project_notepad_{project.title.lower().replace(' ', '_')}", uid)
    report = NotepadReport(fname, {
        "title": f"Project Notepad: {project.title}",
        "subtitle": f"AI-Formatted Project Documentation | Generated: {datetime.now().day} {datetime.now().strftime('%B %Y')}",
        "theme": theme
    })
    report.generate(formatted_notes)

    base_fname = os.path.basename(fname)
    url = f"http://localhost:8000/uploads/{base_fname}"
    return (
        f"### 📝 Project Notepad PDF Compiled!\n\n"
        f"Project notes for **{project.title}** have been formatted and compiled using AI:\n"
        f"- **File Name**: `{base_fname}`\n"
        f"- **Source Characters**: {len(raw_notes)} chars\n"
        f"- **AI Formatted Sections**: Neat layout built with headers and bullet items\n\n"
        f"📥 **[Download Notepad PDF]({url})**"
    )


async def _generate_todo_report_flow(
    db: AsyncSession,
    user_id: UUID,
    project: Optional[Project],
    theme: str,
    uid: str,
    custom_filename: Optional[str] = None
) -> str:
    if project:
        stmt = select(Todo, Project.title).join(Project).filter(Todo.project_id == project.id).order_by(Todo.status.desc(), Todo.due_date.asc())
    else:
        # Fetch all projects for user
        proj_stmt = select(Project).filter(Project.user_id == user_id)
        proj_ids = [p.id for p in (await db.execute(proj_stmt)).scalars().all()]
        if not proj_ids:
            return "No projects found to compile tasks backlog."
        stmt = select(Todo, Project.title).join(Project).filter(Todo.project_id.in_(proj_ids)).order_by(Todo.status.desc(), Todo.due_date.asc())

    rows = (await db.execute(stmt)).all()
    tasks_list = []
    for t, ptitle in rows:
        tasks_list.append({
            "title": t.title,
            "description": t.description or "",
            "priority": t.priority,
            "status": t.status,
            "due_date": t.due_date,
            "project_title": ptitle,
            "estimated_hours": float(t.estimated_hours or 0),
            "actual_hours": float(t.actual_hours or 0)
        })

    default_prefix = f"todo_list_{project.title.lower().replace(' ', '_')}" if project else "todo_list_all"
    fname = _sanitize_filename(custom_filename, default_prefix, uid)
    report = ToDoReport(fname, {
        "title": f"To Do List & Tasks Backlog" + (f": {project.title}" if project else ""),
        "subtitle": f"Full Task Status Details | Generated: {datetime.now().day} {datetime.now().strftime('%B %Y')}",
        "theme": theme
    })
    report.generate(tasks_list)

    base_fname = os.path.basename(fname)
    url = f"http://localhost:8000/uploads/{base_fname}"
    return (
        f"### 📋 To-Do List PDF Generated!\n\n"
        f"Compiled task backlog in full detail:\n"
        f"- **File Name**: `{base_fname}`\n"
        f"- **Total Tasks**: {len(tasks_list)}\n"
        f"- **Completed**: {sum(1 for t in tasks_list if t['status'] in ['done', 'completed'])}\n"
        f"- **Pending**: {sum(1 for t in tasks_list if t['status'] not in ['done', 'completed'])}\n\n"
        f"📥 **[Download To-Do List PDF]({url})**"
    )


async def _generate_payments_report_flow(
    db: AsyncSession,
    user_id: UUID,
    project: Optional[Project],
    theme: str,
    uid: str,
    custom_filename: Optional[str] = None
) -> str:
    if project:
        stmt = select(Payment, Project.title).join(Project).filter(Payment.project_id == project.id).order_by(Payment.due_date.asc())
    else:
        # Fetch all projects for user
        proj_stmt = select(Project).filter(Project.user_id == user_id)
        proj_ids = [p.id for p in (await db.execute(proj_stmt)).scalars().all()]
        if not proj_ids:
            return "No projects found to compile payment history."
        stmt = select(Payment, Project.title).join(Project).filter(Payment.project_id.in_(proj_ids)).order_by(Payment.due_date.asc())

    rows = (await db.execute(stmt)).all()
    payments_list = []
    for p, ptitle in rows:
        payments_list.append({
            "amount": float(p.amount),
            "currency": p.currency,
            "payment_type": p.payment_type,
            "received_date": p.received_date,
            "due_date": p.due_date,
            "status": p.status,
            "notes": p.notes or "",
            "project_title": ptitle
        })

    # Sort payments_list chronologically by the date shown in the table
    def get_payment_date_str(item):
        status = str(item.get("status") or "pending").lower()
        d = item.get("received_date") if status == "received" else item.get("due_date")
        if not d:
            return "9999-12-31"
        if hasattr(d, "strftime"):
            return d.strftime("%Y-%m-%d")
        s = str(d).replace("T", " ").split(" ")[0]
        return s if s else "9999-12-31"

    payments_list.sort(key=get_payment_date_str)

    # Fetch project total amount
    project_total = 0.0
    if project:
        project_total = float(project.total_amount or 0)
    else:
        proj_stmt = select(Project).filter(Project.user_id == user_id)
        all_projects = (await db.execute(proj_stmt)).scalars().all()
        project_total = sum(float(p.total_amount or 0) for p in all_projects)

    default_prefix = f"payments_report_{project.title.lower().replace(' ', '_')}" if project else "payments_report_all"
    fname = _sanitize_filename(custom_filename, default_prefix, uid)
    print(f"DEBUG: PaymentsReport class is {PaymentsReport}, MRO: {PaymentsReport.__mro__}")
    report = PaymentsReport(fname, {
        "title": f"Payments & Billings Ledger" + (f": {project.title}" if project else ""),
        "subtitle": f"Full Financial Records Details | Generated: {datetime.now().day} {datetime.now().strftime('%B %Y')}",
        "theme": theme,
        "project_total_amount": project_total
    })
    report.generate(payments_list)

    base_fname = os.path.basename(fname)
    url = f"http://localhost:8000/uploads/{base_fname}"
    received_total = sum(p['amount'] for p in payments_list if p['status'] == 'received')
    remaining_display = max(0.0, project_total - received_total) if project_total > 0 else sum(p['amount'] for p in payments_list if p['status'] != 'received')
    
    return (
        f"### 💳 Payments & Billings Report Generated!\n\n"
        f"Compiled payment history and financial ledger:\n"
        f"- **File Name**: `{base_fname}`\n"
        f"- **Total Payments**: {len(payments_list)}\n"
        f"- **Received**: {received_total:,.0f} {payments_list[0]['currency'] if payments_list else 'INR'}\n"
        f"- **Remaining Payment**: {remaining_display:,.0f} {payments_list[0]['currency'] if payments_list else 'INR'}\n\n"
        f"📥 **[Download Payments Report PDF]({url})**"
    )
