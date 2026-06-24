"""
Project Service
===============
All project CRUD operations extracted from the ai.py monolith.
"""

import dateutil.parser
from datetime import datetime
from typing import Optional, Dict, Any, List
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.project import Project
from app.models.todo import Todo
from app.models.timeline_event import TimelineEvent
from app.models.milestone import Milestone
from app.models.payment import Payment
from app.models.pending_thing import PendingThing
from app.services.entity_resolver import resolve_project, resolve_projects_multi, resolve_project_from_context
from app.services.analytics_service import invalidate_analytics_cache
import logging

logger = logging.getLogger(__name__)


async def read_project(
    db: AsyncSession,
    user_id: UUID,
    project_title: Optional[str],
    raw_input: str,
    session_data: Optional[dict] = None,
) -> str:
    """
    Fetch and format project details. If a specific project is identified,
    return all its data. Otherwise, list all projects.
    """
    # Fetch all user projects
    proj_stmt = select(Project).filter(Project.user_id == user_id).order_by(Project.created_at.desc())
    proj_result = await db.execute(proj_stmt)
    projects = proj_result.scalars().all()

    target_project = None

    if project_title and project_title.lower() not in ["all", "list", "projects"]:
        target_project = await resolve_project(db, user_id, project_title)

    # Fallback: try to find project name in raw_input
    if not target_project:
        target_project = await resolve_project_from_context(
            db, user_id, raw_input,
            extracted_title=project_title,
            session_data=session_data
        )

    if target_project:
        return await _format_project_details(db, target_project)
    else:
        # Determine which projects to list based on user's query
        lower_input = raw_input.lower()
        wants_finished = any(w in lower_input for w in ["finished", "completed", "done", "closed"])
        wants_all = any(w in lower_input for w in ["all project", "every project", "all my"])

        if wants_finished:
            filtered = [p for p in projects if p.status in ["finished", "completed"]]
            if not filtered:
                return "No finished/completed projects found."
            # Fetch payments for revenue info
            from app.models.payment import Payment
            filtered_ids = [p.id for p in filtered]
            pay_stmt = select(Payment).filter(Payment.project_id.in_(filtered_ids))
            payments = (await db.execute(pay_stmt)).scalars().all()
            msg = "### ✅ Finished Projects:\n\n"
            for p in filtered:
                total = float(p.total_amount or 0)
                received = sum(float(pay.amount) for pay in payments if pay.project_id == p.id and pay.status == "received")
                msg += f"- **{p.title}** — Total Deal: ₹{total:,.0f} | Received: ₹{received:,.0f}\n"
            return msg
        elif wants_all:
            if not projects:
                return "No projects found."
            msg = "### 💼 All Projects:\n\n"
            for p in projects:
                status_emoji = "✅" if p.status in ["finished", "completed"] else "🟡"
                msg += f"- {status_emoji} **{p.title}** — *{p.status}*\n"
            return msg
        else:
            active_projects = [p for p in projects if p.status not in ["finished", "completed"]]
            if not active_projects:
                return "No active projects found."
            msg = "### 💼 Active Projects:\n\n"
            for p in active_projects:
                msg += f"- **{p.title}** - *{p.description or 'No description'}*\n"
            return msg


async def _format_project_details(db: AsyncSession, project: Project) -> str:
    """Format a detailed markdown report for a single project."""
    # Fetch todos
    todo_stmt = select(Todo).filter(Todo.project_id == project.id).order_by(Todo.created_at.asc())
    todo_res = await db.execute(todo_stmt)
    todos_list = todo_res.scalars().all()

    # Fetch timeline events
    timeline_stmt = select(TimelineEvent).filter(TimelineEvent.project_id == project.id).order_by(TimelineEvent.event_date.asc())
    timeline_res = await db.execute(timeline_stmt)
    events_list = timeline_res.scalars().all()

    # Fetch payments
    payment_stmt = select(Payment).filter(Payment.project_id == project.id).order_by(Payment.received_date.desc())
    payment_res = await db.execute(payment_stmt)
    payments_list = payment_res.scalars().all()

    # Fetch pending things
    pending_stmt = select(PendingThing).filter(PendingThing.project_id == project.id).order_by(PendingThing.created_at.desc())
    pending_res = await db.execute(pending_stmt)
    pending_list = pending_res.scalars().all()

    # Format markdown report
    msg = f"### 💼 Project: {project.title}\n"
    msg += f"- **Description**: {project.description or 'No description'}\n"
    if project.total_amount is not None:
        msg += f"- **Total Amount**: {project.total_amount:,.2f} INR\n"
    if project.deadline:
        msg += f"- **Deadline**: {project.deadline.strftime('%Y-%m-%d')}\n"
    if project.summary:
        msg += f"- **Kickoff Summary**: {project.summary}\n"
    if project.risks:
        msg += f"- **Identified Risks**: {project.risks}\n"
    msg += "\n"

    # Add Tasks
    msg += "### 📋 Project Tasks & Todos:\n"
    if not todos_list:
        msg += "*No tasks found.*\n"
    else:
        for t in todos_list:
            status_emoji = "✅" if t.status in ["done", "completed"] else "⏳" if t.status == "in_progress" else "📁"
            due_str = t.due_date.strftime("%Y-%m-%d") if t.due_date else "N/A"
            prio_str = f" [Priority: {t.priority.upper()}]" if t.priority else ""
            msg += f"- {status_emoji} **{t.title}** (Due: {due_str}){prio_str} - *{t.description or 'No description'}*\n"
    msg += "\n"



    # Add Payments
    msg += "### 💳 Logged Payments:\n"
    if not payments_list:
        msg += "*No payments logged.*\n"
        if project.total_amount is not None:
            msg += f"- **Total Amount (Budget)**: {project.total_amount:,.2f} INR\n"
            msg += f"- **Payment Received**: 0.00 INR\n"
            msg += f"- **Remaining Payment**: {project.total_amount:,.2f} INR\n"
    else:
        total_pay = 0
        total_received = 0
        for p in payments_list:
            dt_str = p.received_date.strftime("%Y-%m-%d") if p.received_date else p.due_date.strftime("%Y-%m-%d") if p.due_date else "N/A"
            status_emoji = "✅" if p.status == "received" else "⏳" if p.status == "pending" else "❌"
            msg += f"- {status_emoji} **{p.amount:,.2f} {p.currency}** ({p.payment_type}) on {dt_str} - *{p.notes or 'No notes'}*\n"
            total_pay += p.amount
            if p.status == "received":
                total_received += p.amount
        msg += f"**Total Payments Logged**: {total_pay:,.2f} INR equivalent\n"
        if project.total_amount is not None:
            remaining_payment = project.total_amount - total_received
            msg += f"**Total Amount (Budget)**: {project.total_amount:,.2f} INR\n"
            msg += f"**Payment Received**: {total_received:,.2f} INR\n"
            msg += f"**Remaining Payment**: {remaining_payment:,.2f} INR\n"
    msg += "\n"

    # Add Pending Things
    msg += "### ⏳ Pending Things & Credentials:\n"
    if not pending_list:
        msg += "*No pending items or credentials found.*\n"
    else:
        for pt in pending_list:
            status_emoji = "✅" if pt.is_completed else "⏳"
            file_indicator = f" (📎 File: {pt.filename})" if pt.filename else ""
            msg += f"- {status_emoji} **{pt.title}**{file_indicator} - *{pt.description or 'No description'}*\n"

    return msg


async def delete_project(
    db: AsyncSession,
    user_id: UUID,
    project_title: Optional[str],
    exclude_names: Optional[List[str]] = None,
    confirmed: bool = False,
    raw_input: str = "",
) -> Dict[str, Any]:
    """
    Delete project(s). Supports:
    - Single project deletion by name
    - Multi-project deletion with exclusion ("delete all acme except acme pdf project")
    
    Returns:
        Dict with keys: action, needs_confirmation, message, project_titles
    """
    # Check for multi-delete with exclusion
    if exclude_names:
        projects_to_delete = await resolve_projects_multi(
            db, user_id, project_title or "", exclude_names=exclude_names
        )

        if not projects_to_delete:
            return {
                "action": "noop",
                "needs_confirmation": False,
                "message": f"No projects matching '{project_title}' found (after applying exclusions).",
                "project_titles": [],
            }

        if not confirmed:
            titles = [p.title for p in projects_to_delete]
            excluded_str = ", ".join(exclude_names)
            return {
                "action": "confirm_multi_delete",
                "needs_confirmation": True,
                "message": (
                    f"⚠️ Found {len(titles)} project(s) to delete: {', '.join(titles)}.\n"
                    f"Excluded: {excluded_str}.\n"
                    f"Reply with 'yes' or 'confirm' to proceed."
                ),
                "project_titles": titles,
            }

        deleted_titles = []
        for project in projects_to_delete:
            deleted_titles.append(project.title)
            await db.delete(project)
        await db.commit()
        invalidate_analytics_cache(user_id)
        return {
            "action": "deleted",
            "needs_confirmation": False,
            "message": f"Successfully deleted {len(deleted_titles)} project(s): {', '.join(deleted_titles)}.",
            "project_titles": deleted_titles,
        }

    # Single project deletion
    if not project_title or project_title.lower() in ["all", "current", "last", "latest"]:
        proj_stmt = select(Project).filter(Project.user_id == user_id).order_by(Project.created_at.desc())
        proj_result = await db.execute(proj_stmt)
        project = proj_result.scalars().first()
    else:
        project = await resolve_project(db, user_id, project_title)

    if not project:
        return {
            "action": "noop",
            "needs_confirmation": False,
            "message": f"Project '{project_title}' not found.",
            "project_titles": [],
        }

    title = project.title
    if not confirmed:
        return {
            "action": "confirm_delete",
            "needs_confirmation": True,
            "message": f"⚠️ Are you sure you want to delete project '{title}' and all associated tasks/timeline events? Reply with 'yes' or 'confirm' to proceed.",
            "project_titles": [title],
        }

    await db.delete(project)
    await db.commit()
    invalidate_analytics_cache(user_id)
    return {
        "action": "deleted",
        "needs_confirmation": False,
        "message": f"Successfully deleted project '{title}' and all its tasks/milestones.",
        "project_titles": [title],
    }


async def create_project(
    db: AsyncSession,
    user_id: UUID,
    project_data: Dict[str, Any],
    final_state: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Create a new project with optional milestones, timeline events, and todos.
    Returns dict with project info and summary message.
    """
    # Check if a project with the same title already exists
    existing_project = await resolve_project(db, user_id, project_data["title"])
    if existing_project:
        return await update_project(db, user_id, project_data, final_state)

    new_project = Project(
        user_id=user_id,
        title=project_data["title"],
        description=project_data.get("description"),
        status=project_data.get("status") or "planning",
        priority=None,
        deadline=None,
        total_amount=project_data.get("total_amount"),
        summary=final_state.get("summary"),
        risks=final_state.get("risks"),
    )
    db.add(new_project)
    await db.commit()
    await db.refresh(new_project)

    # Save generated milestones
    milestones_data = final_state.get("milestones") or []
    milestone_map = {}
    for m_data in milestones_data:
        start_dt = _safe_parse_date(m_data.get("start_date"))
        end_dt = _safe_parse_date(m_data.get("end_date"))

        m_obj = Milestone(
            project_id=new_project.id,
            title=m_data["title"],
            description=m_data.get("description"),
            start_date=start_dt,
            end_date=end_dt,
            status="planned",
        )
        db.add(m_obj)
        milestone_map[m_data["title"]] = m_obj

    if milestones_data:
        await db.flush()

    # Save generated timeline events
    timeline_data = final_state.get("timeline") or []
    for t_data in timeline_data:
        event_dt = _safe_parse_date(t_data.get("event_date"))
        t_obj = TimelineEvent(
            project_id=new_project.id,
            event_name=t_data["event_name"],
            event_type=t_data.get("event_type") or "milestone",
            event_date=event_dt or datetime.utcnow(),
            notes=t_data.get("notes"),
            status="pending",
        )
        db.add(t_obj)

    # Save generated todos/tasks
    todos_data = final_state.get("todos") or []
    for todo_data in todos_data:
        due_dt = _safe_parse_date(todo_data.get("due_date"))
        m_id = None
        m_title = todo_data.get("milestone_title")
        if m_title and m_title in milestone_map:
            m_id = milestone_map[m_title].id

        new_todo = Todo(
            project_id=new_project.id,
            milestone_id=m_id,
            title=todo_data["title"],
            description=todo_data.get("description"),
            priority=todo_data.get("priority") or None,
            status="todo",
            due_date=due_dt,
            estimated_hours=todo_data.get("estimated_hours"),
        )
        db.add(new_todo)

    await db.commit()

    # Save initial/advance payment if provided in the prompt (e.g. during project creation)
    p_data = final_state.get("payment") or {}
    if p_data and p_data.get("amount") is not None:
        rec_dt = _safe_parse_date(p_data.get("received_date"))
        from app.models.models import Payment
        p_type = p_data.get("payment_type")
        if p_type:
            p_type_lower = str(p_type).lower()
            if "advance" in p_type_lower:
                p_type = "Advance"
            elif "final" in p_type_lower:
                p_type = "Final"
            elif "partial" in p_type_lower or "installment" in p_type_lower or "milestone" in p_type_lower:
                p_type = "Partial"
            else:
                p_type = str(p_type).capitalize()
        else:
            p_type = "Advance"

        init_payment = Payment(
            project_id=new_project.id,
            amount=p_data["amount"],
            currency=p_data.get("currency") or "INR",
            payment_type=p_type,
            status=p_data.get("status") or "received",
            received_date=rec_dt or datetime.utcnow(),
            notes=p_data.get("notes") or "Logged during project creation.",
        )
        db.add(init_payment)
        await db.commit()

    invalidate_analytics_cache(user_id)

    val_str = f"₹{new_project.total_amount:,.2f}" if new_project.total_amount else "Not specified"
    default_summary = (
        f"### Project Created Successfully\n\n"
        f"* **Project Name**: {new_project.title}\n"
        f"* **Description**: {new_project.description or 'No description'}\n"
        f"* **Value**: {val_str}"
    )
    if p_data and p_data.get("amount") is not None:
        p_amount = float(p_data["amount"])
        p_type = p_data.get("payment_type") or "Advance"
        p_date = p_data.get("received_date") or "today"
        default_summary += f"\n* **{p_type} Payment**: ₹{p_amount:,.2f} received on {p_date}"

    return {
        "project": new_project,
        "summary": final_state.get("summary") or default_summary,
    }


async def update_project(
    db: AsyncSession,
    user_id: UUID,
    project_data: Dict[str, Any],
    final_state: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Update an existing project's fields (description, status, priority, deadline, total_amount)
    or a batch of projects if 'updates' list is provided.
    """
    updates = project_data.get("updates")
    if updates and isinstance(updates, list):
        summary_lines = []
        from app.models.project import Project
        stmt = select(Project).filter(Project.user_id == user_id)
        all_projects = (await db.execute(stmt)).scalars().all()
        
        specific_updates = []
        rest_update = None
        for up in updates:
            title_lower = str(up.get("title")).lower()
            if title_lower in ["rest", "others", "other", "all other", "all others", "remaining", "else"]:
                rest_update = up
            else:
                specific_updates.append(up)
                
        updated_ids = set()
        for up in specific_updates:
            title = up.get("title")
            if not title:
                continue
            proj = await resolve_project(db, user_id, title)
            if proj:
                updated_ids.add(proj.id)
                parts = []
                if "description" in up and up["description"] is not None:
                    proj.description = up["description"]
                    parts.append("description updated")
                if "total_amount" in up and up["total_amount"] is not None:
                    proj.total_amount = up["total_amount"]
                    parts.append(f"value set to {proj.total_amount:,.2f} INR")
                if "status" in up and up["status"] is not None:
                    proj.status = up["status"]
                    parts.append(f"status updated to '{proj.status}'")
                if parts:
                    summary_lines.append(f"- **{proj.title}**: {', '.join(parts)}")
                    
        if rest_update:
            for proj in all_projects:
                if proj.id not in updated_ids:
                    proj_parts = []
                    if "description" in rest_update and rest_update["description"] is not None:
                        proj.description = rest_update["description"]
                        proj_parts.append("description updated")
                    if "total_amount" in rest_update and rest_update["total_amount"] is not None:
                        proj.total_amount = rest_update["total_amount"]
                        proj_parts.append(f"value set to {proj.total_amount:,.2f} INR")
                    if "status" in rest_update and rest_update["status"] is not None:
                        proj.status = rest_update["status"]
                        proj_parts.append(f"status updated to '{proj.status}'")
                    if proj_parts:
                        updated_ids.add(proj.id)
                        summary_lines.append(f"- **{proj.title}**: {', '.join(proj_parts)}")
                        
        if updated_ids:
            await db.commit()
            invalidate_analytics_cache(user_id)
            return {
                "project": all_projects[0] if all_projects else None,
                "summary": "### Batch Project Update Successful\n\n" + "\n".join(summary_lines)
            }
        else:
            return {"project": None, "summary": "No matching projects found to update."}

    title = project_data.get("title")
    if not title:
        return {"project": None, "summary": "Project title not provided."}

    project = await resolve_project(db, user_id, title)
    if not project:
        # If project does not exist, fallback to creating it
        # Temporarily clear recursion path by calling the DB creation part directly
        new_project = Project(
            user_id=user_id,
            title=title,
            description=project_data.get("description"),
            status=project_data.get("status") or "planning",
            priority=None,
            deadline=None,
            total_amount=project_data.get("total_amount"),
            summary=final_state.get("summary"),
            risks=final_state.get("risks"),
        )
        db.add(new_project)
        await db.commit()
        await db.refresh(new_project)
        invalidate_analytics_cache(user_id)
        return {
            "project": new_project,
            "summary": f"Successfully created project '{new_project.title}'."
        }

    # Update fields if provided
    summary_parts = []
    if "new_title" in project_data and project_data["new_title"] is not None:
        other_project = await resolve_project(db, user_id, project_data["new_title"])
        if other_project and other_project.id != project.id:
            return {"project": project, "summary": f"A project named '{project_data['new_title']}' already exists."}
        old_title = project.title
        project.title = project_data["new_title"]
        summary_parts.append(f"renamed from '{old_title}' to '{project.title}'")
    if "description" in project_data and project_data["description"] is not None:
        project.description = project_data["description"]
        summary_parts.append("description updated")
    if "total_amount" in project_data and project_data["total_amount"] is not None:
        project.total_amount = project_data["total_amount"]
        summary_parts.append(f"value set to {project.total_amount:,.2f} INR")
    if "status" in project_data and project_data["status"] is not None:
        project.status = project_data["status"]
        summary_parts.append(f"status updated to '{project.status}'")
    if "priority" in project_data and project_data["priority"] is not None:
        project.priority = project_data["priority"]
        summary_parts.append(f"priority set to '{project.priority}'")
    if "deadline" in project_data and project_data["deadline"] is not None:
        project.deadline = _safe_parse_date(project_data["deadline"])
        summary_parts.append("deadline updated")

    await db.commit()
    await db.refresh(project)
    invalidate_analytics_cache(user_id)

    summary_str = f"Successfully updated project '{project.title}': " + ", ".join(summary_parts) if summary_parts else f"Updated project '{project.title}'."

    return {
        "project": project,
        "summary": summary_str
    }


def _safe_parse_date(date_str):
    """Safely parse a date string, returning None on failure."""
    if not date_str:
        return None
    try:
        return dateutil.parser.parse(date_str)
    except Exception:
        return None
