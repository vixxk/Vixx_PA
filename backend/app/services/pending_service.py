"""
Pending Things Service — All pending items CRUD operations.
"""
from typing import Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.project import Project
from app.models.pending_thing import PendingThing
from app.services.entity_resolver import resolve_project_from_context, resolve_pending_item
from app.services.analytics_service import invalidate_analytics_cache
import logging

logger = logging.getLogger(__name__)


async def _get_user_projects_and_ids(db, user_id):
    projects = (await db.execute(select(Project).filter(Project.user_id == user_id))).scalars().all()
    return projects, [p.id for p in projects]


async def list_pending(db, user_id, project_title=None, raw_input="", session_data=None):
    projects, proj_ids = await _get_user_projects_and_ids(db, user_id)
    if not proj_ids: return "No projects found."
    target_project = await resolve_project_from_context(db, user_id, raw_input, extracted_title=project_title, session_data=session_data) if project_title else None
    if target_project:
        stmt = select(PendingThing, Project.title).join(Project).filter(PendingThing.project_id == target_project.id).order_by(PendingThing.created_at.desc())
    else:
        stmt = select(PendingThing, Project.title).join(Project).filter(PendingThing.project_id.in_(proj_ids)).order_by(PendingThing.created_at.desc())
    rows = (await db.execute(stmt)).all()
    if not rows:
        return f"No pending items found{' for project ' + repr(target_project.title) if target_project else ''}."
    header = f"### ⏳ Pending Items in {target_project.title}:\n\n" if target_project else "### ⏳ Pending Items & Credentials:\n\n"
    msg = header
    for pt, ptitle in rows:
        status_str = "✅ Done" if pt.is_completed else "⏳ Pending"
        file_indicator = f" (📎 File: {pt.filename})" if pt.filename else ""
        msg += f"- **{pt.title}** ({ptitle}) — {status_str}{file_indicator}\n"
        if pt.description: msg += f"  _{pt.description}_\n"
    return msg


async def create_pending(db, user_id, pending_data, raw_input="", session_data=None):
    projects, proj_ids = await _get_user_projects_and_ids(db, user_id)
    if not proj_ids: return "Please create a project first."
    pt_title = pending_data.get("title")
    if not pt_title:
        return {"needs_clarification": True, "message": "What is the pending thing you want to add? (e.g. 'client needs to send API keys')"}
    project = await resolve_project_from_context(db, user_id, raw_input, extracted_title=pending_data.get("project_title"), session_data=session_data)
    if not project: project = projects[0]
    new_pt = PendingThing(project_id=project.id, title=pt_title, description=pending_data.get("description"), is_completed=pending_data.get("is_completed") or False)
    db.add(new_pt)
    await db.commit()
    invalidate_analytics_cache(user_id)
    await db.refresh(new_pt)
    return f"Successfully added pending item '{new_pt.title}' to project '{project.title}'."


async def complete_pending(db, user_id, pending_data):
    projects, proj_ids = await _get_user_projects_and_ids(db, user_id)
    pt_title = pending_data.get("title")
    if not pt_title: return "Please specify which pending item to update/complete."
    pt_obj = await resolve_pending_item(db, proj_ids, pt_title)
    if not pt_obj: return f"Pending item '{pt_title}' not found."
    pt_obj.is_completed = True
    if pending_data.get("description"): pt_obj.description = pending_data["description"]
    await db.commit()
    invalidate_analytics_cache(user_id)
    await db.refresh(pt_obj)
    return f"Successfully marked pending item '{pt_obj.title}' as completed."


async def delete_pending(db, user_id, pending_data, confirmed=False):
    projects, proj_ids = await _get_user_projects_and_ids(db, user_id)
    pt_title = pending_data.get("title")
    is_all = not pt_title or pt_title.lower() in ["all", "list", "pending things", "pending items"]
    if is_all:
        if not confirmed:
            return {"needs_confirmation": True, "message": "⚠️ Are you sure you want to clear all pending items? Please choose Yes or No."}
        pts = (await db.execute(select(PendingThing).filter(PendingThing.project_id.in_(proj_ids)))).scalars().all()
        count = len(pts)
        for pt in pts: await db.delete(pt)
        await db.commit()
        invalidate_analytics_cache(user_id)
        return {"needs_confirmation": False, "message": f"Successfully cleared all {count} pending items."}
    pt_obj = await resolve_pending_item(db, proj_ids, pt_title)
    if not pt_obj: return {"needs_confirmation": False, "message": f"Pending item '{pt_title}' not found."}
    if not confirmed:
        return {"needs_confirmation": True, "message": f"⚠️ Are you sure you want to delete the pending item '{pt_obj.title}'? Please choose Yes or No."}
    name = pt_obj.title
    await db.delete(pt_obj)
    await db.commit()
    invalidate_analytics_cache(user_id)
    return {"needs_confirmation": False, "message": f"Successfully deleted pending item '{name}'."}
