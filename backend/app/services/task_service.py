"""
Task Service — All task/todo CRUD operations.
"""
import dateutil.parser
import uuid as uuid_mod
import os
import re
from typing import Optional, Dict, Any, List
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.project import Project
from app.models.todo import Todo
from app.services.entity_resolver import resolve_project_from_context, resolve_task
from app.services.analytics_service import invalidate_analytics_cache
import logging

logger = logging.getLogger(__name__)


async def _get_user_projects_and_ids(db: AsyncSession, user_id: UUID):
    proj_stmt = select(Project).filter(Project.user_id == user_id)
    proj_result = await db.execute(proj_stmt)
    projects = proj_result.scalars().all()
    return projects, [p.id for p in projects]


async def list_tasks(db, user_id, project_title=None, raw_input="", session_data=None, include_completed=False):
    projects, proj_ids = await _get_user_projects_and_ids(db, user_id)
    if not proj_ids:
        return "No projects found. Please create a project first."
    
    target_project = await resolve_project_from_context(db, user_id, raw_input, extracted_title=project_title, session_data=session_data) if (project_title or session_data) else None
    
    if target_project:
        q = select(Todo).filter(Todo.project_id == target_project.id)
    else:
        q = select(Todo).filter(Todo.project_id.in_(proj_ids))

    lower_input = raw_input.lower()
    wants_completed_only = any(w in lower_input for w in ["completed", "finished", "closed", "done"]) and not any(w in lower_input for w in ["not completed", "not done", "pending", "active"])
    wants_all = any(w in lower_input for w in ["all tasks", "all todos", "every task", "everything", "all my tasks"])
    wants_high_prio = any(w in lower_input for w in ["high priority", "urgent", "critical", "highest priority", "p1"])

    if wants_completed_only:
        q = q.filter(Todo.status == "done")
        header_title = "Completed Tasks"
    elif wants_all or include_completed:
        header_title = "All Tasks"
    else:
        q = q.filter(Todo.status != "done")
        header_title = "Pending Tasks"

    if wants_high_prio:
        q = q.filter(Todo.priority.in_(["high", "critical"]))
        header_title = f"High Priority {header_title}"

    # Order by due date asc (nulls last)
    q = q.order_by(Todo.due_date.asc().nullslast(), Todo.created_at.desc())
    todo_objs = (await db.execute(q)).scalars().all()

    scope_str = f" in {target_project.title}" if target_project else ""
    if not todo_objs:
        return f"No {header_title.lower()} found{scope_str}."

    header = f"### 📋 {header_title}{scope_str} ({len(todo_objs)}):\n\n"
    proj_map = {p.id: p.title for p in projects}
    msg = header
    for t in todo_objs:
        due_str = t.due_date.strftime("%Y-%m-%d") if t.due_date else "No deadline"
        status_symbol = "✅" if t.status == "done" else "🔴" if t.priority in ["high", "critical"] else "🟡" if t.priority == "medium" else "🟢" if t.priority == "low" else "⚪"
        prio_label = (t.priority or "NORMAL").upper()
        status_label = "DONE" if t.status == "done" else "PENDING"
        proj_name = proj_map.get(t.project_id, "General")
        msg += f"- {status_symbol} **{t.title}** (Project: {proj_name}, Priority: {prio_label}, Status: {status_label}, Due: {due_str})\n"
        if t.description:
            msg += f"  *{t.description}*\n"
    return msg


async def create_task(db, user_id, todo_data, raw_input="", session_data=None, google_token=None):
    projects, proj_ids = await _get_user_projects_and_ids(db, user_id)
    if not proj_ids:
        return "Please create a project first before managing tasks."
    project = await resolve_project_from_context(db, user_id, raw_input, extracted_title=todo_data.get("project_title"), session_data=session_data)
    if not project:
        project = projects[0]
    due_dt = None
    if todo_data.get("due_date"):
        try: due_dt = dateutil.parser.parse(todo_data["due_date"])
        except: pass
    new_todo = Todo(project_id=project.id, title=todo_data["title"], description=todo_data.get("description"),
                    priority=todo_data.get("priority") or None, status=todo_data.get("status") or "todo",
                    due_date=due_dt, estimated_hours=todo_data.get("estimated_hours"))
    db.add(new_todo)
    await db.commit()
    invalidate_analytics_cache(user_id)
    await db.refresh(new_todo)
    msg = f"Successfully added task '{new_todo.title}' to project '{project.title}'."
    if google_token and new_todo.due_date:
        try:
            from app.tools.calendar_tool import create_google_calendar_event
            cal_res = await create_google_calendar_event(access_token=google_token, event_title=f"Task: {new_todo.title}", event_description=new_todo.description or "", due_date_str=new_todo.due_date.isoformat())
            if cal_res.get("success"): msg += " and added to Google Calendar"
        except: pass
    return msg


async def update_task(db, user_id, todo_data, raw_input=""):
    projects, proj_ids = await _get_user_projects_and_ids(db, user_id)
    if not proj_ids: return "No projects found."
    task_title = todo_data.get("title")
    if not task_title: return "Please specify which task to update."
    todo_obj = await resolve_task(db, proj_ids, task_title)
    if not todo_obj: return f"Task '{task_title}' not found."

    changes = []
    if todo_data.get("new_title"):
        old_title = todo_obj.title
        todo_obj.title = todo_data["new_title"]
        changes.append(f"title from '{old_title}' to '{todo_obj.title}'")
    if todo_data.get("status"):
        todo_obj.status = todo_data["status"]
        changes.append(f"status to '{todo_obj.status}'")
    if todo_data.get("priority"):
        todo_obj.priority = todo_data["priority"]
        changes.append(f"priority to '{todo_obj.priority}'")
    if todo_data.get("description") is not None:
        todo_obj.description = todo_data["description"]
        changes.append("description")
    if todo_data.get("due_date"):
        try:
            todo_obj.due_date = dateutil.parser.parse(str(todo_data["due_date"]))
            changes.append(f"due date to {todo_obj.due_date.strftime('%b %d, %Y')}")
        except: pass
    if todo_data.get("estimated_hours") is not None:
        todo_obj.estimated_hours = todo_data["estimated_hours"]
        changes.append(f"estimated hours to {todo_obj.estimated_hours}")
    if todo_data.get("new_project_title"):
        new_proj = await resolve_project_from_context(db, user_id, raw_input, extracted_title=todo_data["new_project_title"])
        if new_proj and new_proj.id != todo_obj.project_id:
            todo_obj.project_id = new_proj.id
            changes.append(f"moved to project '{new_proj.title}'")

    await db.commit()
    invalidate_analytics_cache(user_id)
    await db.refresh(todo_obj)

    if changes:
        return f"Successfully updated task '{todo_obj.title}': {', '.join(changes)}."
    return f"Task '{todo_obj.title}' is already up to date."


async def delete_tasks(db, user_id, task_title=None, confirmed=False):
    projects, proj_ids = await _get_user_projects_and_ids(db, user_id)
    if not proj_ids: return {"needs_confirmation": False, "message": "No projects found."}
    is_all = not task_title or task_title.lower() in ["all", "list", "todo list", "to-do list", "todos", "tasks", "to do list"]
    if is_all:
        if not confirmed:
            return {"needs_confirmation": True, "message": "⚠️ Are you sure you want to empty the to-do list? Please choose Yes or No."}
        todo_objs = (await db.execute(select(Todo).filter(Todo.project_id.in_(proj_ids)))).scalars().all()
        count = len(todo_objs)
        for t in todo_objs: await db.delete(t)
        await db.commit()
        invalidate_analytics_cache(user_id)
        return {"needs_confirmation": False, "message": f"Successfully cleared all {count} tasks from your to-do list."}
    if not confirmed:
        return {"needs_confirmation": True, "message": f"⚠️ Are you sure you want to delete the task '{task_title}'? Please choose Yes or No."}
    todo_obj = await resolve_task(db, proj_ids, task_title)
    if not todo_obj: return {"needs_confirmation": False, "message": f"Task '{task_title}' not found."}
    name = todo_obj.title
    await db.delete(todo_obj)
    await db.commit()
    invalidate_analytics_cache(user_id)
    return {"needs_confirmation": False, "message": f"Successfully deleted task '{name}'."}


async def generate_tasks_pdf(db, user_id, raw_input="", project_title=None, session_data=None):
    from app.utils.pdf_generator import generate_todos_report_pdf
    projects, proj_ids = await _get_user_projects_and_ids(db, user_id)
    if not proj_ids: return "No projects found. Please create a project first."
    target_project = await resolve_project_from_context(db, user_id, raw_input, extracted_title=project_title, session_data=session_data)
    q = select(Todo).filter(Todo.project_id == target_project.id) if target_project else select(Todo).filter(Todo.project_id.in_(proj_ids))
    todo_objs = (await db.execute(q)).scalars().all()
    if not todo_objs: return "No tasks/todos found to generate a PDF report."
    raw_lower = raw_input.lower()
    status_filter = "pending" if "only pending" in raw_lower else ("done" if "only done" in raw_lower or "only completed" in raw_lower else None)
    priority_filter = next((p for p in ["high","medium","low","critical"] if f"only {p}" in raw_lower or f"{p} priority" in raw_lower), None)
    data_list = []
    for t in todo_objs:
        is_done = str(t.status or "").lower() in ["done", "completed"]
        if status_filter == "pending" and is_done: continue
        if status_filter == "done" and not is_done: continue
        if priority_filter and str(t.priority or "").lower() != priority_filter: continue
        p_title = next((p.title for p in projects if p.id == t.project_id), "General")
        data_list.append({"title": t.title, "project_title": p_title, "priority": t.priority, "status": t.status, "due_date": t.due_date, "description": t.description})
    if not data_list: return "No tasks matched your filters. Cannot generate PDF."
    theme = next((t for t in ["teal","emerald","charcoal","ruby"] if t in raw_lower or (t=="emerald" and "green" in raw_lower) or (t=="ruby" and "red" in raw_lower)), "navy")
    title_val = "Tasks & Todos Report"
    tm = re.search(r"title\s+['\"](.+?)['\"]", raw_input, re.IGNORECASE)
    if tm: title_val = tm.group(1)
    elif target_project: title_val = f"Task List: {target_project.title}"
    uid = uuid_mod.uuid4().hex[:8]
    fname = f"uploads/tasks_report_{uid}.pdf"
    os.makedirs("uploads", exist_ok=True)
    generate_todos_report_pdf(data_list, fname, {"title": title_val, "subtitle": f"Total tasks: {len(data_list)}", "theme": theme})
    url = f"http://localhost:5000/{fname}"
    tbl = "\n### 📋 Tasks Details:\n\n| Task | Project | Priority | Status | Due |\n| :--- | :--- | :--- | :--- | :--- |\n"
    for i in data_list:
        p = str(i["priority"]).upper()
        s = str(i["status"]).upper()
        d = i["due_date"].strftime("%Y-%m-%d") if i["due_date"] else "-"
        tbl += f"| **{i['title']}** | {i['project_title']} | {p} | {s} | {d} |\n"
    return f"### 📄 PDF Tasks Report Generated!\n\nUsing **{theme.upper()}** theme.\n- **Title**: {title_val}\n- **Tasks**: {len(data_list)}\n\n📥 **[Download PDF]({url})**\n{tbl}"
