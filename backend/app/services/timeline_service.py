"""
Timeline Service — All timeline/milestone CRUD operations.
"""
from typing import Optional, Dict, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
import dateutil.parser
from datetime import datetime

from app.models.project import Project
from app.models.timeline_event import TimelineEvent
from app.services.entity_resolver import resolve_project_from_context
import logging

logger = logging.getLogger(__name__)


async def list_timeline(db, user_id, raw_input="", session_data=None):
    proj_ids_stmt = select(Project.id).filter(Project.user_id == user_id)
    proj_ids = [row[0] for row in (await db.execute(proj_ids_stmt)).all()]
    if not proj_ids: return "No projects found."
    stmt = select(TimelineEvent, Project.title).join(Project).filter(TimelineEvent.project_id.in_(proj_ids)).order_by(TimelineEvent.event_date.asc())
    rows = (await db.execute(stmt)).all()
    if not rows: return "No timeline events or milestones found."
    msg = "### 📅 Timeline Checkpoints & Milestones:\n\n"
    for ev, ptitle in rows:
        date_str = ev.event_date.strftime("%Y-%m-%d") if ev.event_date else "N/A"
        msg += f"- **{ev.event_name}** ({date_str}) [Type: {ev.event_type.upper()}] - *{ev.notes or 'No notes'}*\n"
    return msg


async def create_timeline_event(db, user_id, event_data, raw_input="", session_data=None, google_token=None):
    proj_result = await db.execute(select(Project).filter(Project.user_id == user_id).order_by(Project.created_at.desc()))
    project = proj_result.scalars().first()
    if not project: return "Please create a project first."
    event_dt = None
    if event_data.get("event_date"):
        try: event_dt = dateutil.parser.parse(event_data["event_date"])
        except: pass
    new_event = TimelineEvent(project_id=project.id, event_name=event_data["event_name"],
                              event_type=event_data.get("event_type") or "milestone",
                              event_date=event_dt, notes=event_data.get("notes"), status="pending")
    db.add(new_event)
    await db.commit()
    msg = f"Successfully added timeline event '{new_event.event_name}'."
    if google_token and new_event.event_date:
        try:
            from app.tools.calendar_tool import create_google_calendar_event
            cal_res = await create_google_calendar_event(access_token=google_token, event_title=f"Milestone: {new_event.event_name}", event_description=new_event.notes or "", due_date_str=new_event.event_date.isoformat())
            if cal_res.get("success"): msg += " and synced to Google Calendar"
        except: pass
    return msg


async def delete_timeline(db, user_id, confirmed=False):
    if not confirmed:
        return {"needs_confirmation": True, "message": "⚠️ Are you sure you want to clear the timeline? Please choose Yes or No."}
    proj_ids = [row[0] for row in (await db.execute(select(Project.id).filter(Project.user_id == user_id))).all()]
    events = (await db.execute(select(TimelineEvent).filter(TimelineEvent.project_id.in_(proj_ids)))).scalars().all()
    count = len(events)
    for ev in events: await db.delete(ev)
    await db.commit()
    return {"needs_confirmation": False, "message": f"Successfully cleared all {count} timeline events."}


async def update_timeline_event(db, user_id, event_data, raw_input=""):
    proj_ids_stmt = select(Project.id).filter(Project.user_id == user_id)
    proj_ids = [row[0] for row in (await db.execute(proj_ids_stmt)).all()]
    if not proj_ids: return "No projects found."

    event_name = event_data.get("event_name")
    stmt = select(TimelineEvent).filter(TimelineEvent.project_id.in_(proj_ids))
    if event_name:
        stmt = stmt.filter(TimelineEvent.event_name.ilike(f"%{event_name}%"))
    stmt = stmt.order_by(TimelineEvent.created_at.desc())
    ev_obj = (await db.execute(stmt)).scalars().first()

    if not ev_obj:
        return f"Timeline milestone '{event_name or 'to update'}' not found."

    changes = []
    if event_data.get("new_event_name"):
        old_n = ev_obj.event_name
        ev_obj.event_name = event_data["new_event_name"]
        changes.append(f"name from '{old_n}' to '{ev_obj.event_name}'")

    if event_data.get("event_date"):
        try:
            ev_obj.event_date = dateutil.parser.parse(str(event_data["event_date"]))
            changes.append(f"date to {ev_obj.event_date.strftime('%b %d, %Y')}")
        except Exception:
            pass

    if event_data.get("event_type"):
        ev_obj.event_type = event_data["event_type"]
        changes.append(f"type to '{ev_obj.event_type}'")

    if event_data.get("notes") is not None:
        ev_obj.notes = event_data["notes"]
        changes.append("notes")

    if event_data.get("status"):
        ev_obj.status = event_data["status"]
        changes.append(f"status to '{ev_obj.status}'")

    await db.commit()
    await db.refresh(ev_obj)

    if changes:
        return f"Successfully updated timeline milestone '{ev_obj.event_name}': {', '.join(changes)}."
    return f"Timeline milestone '{ev_obj.event_name}' is already up to date."
