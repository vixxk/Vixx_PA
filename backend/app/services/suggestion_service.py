"""
Suggestion Service
==================
Generates proactive alerts, suggestions, and recommendations based on user operations.
Analyzes:
1. Overdue payments
2. Upcoming deadlines
3. Project health risks (high number of outstanding blockers)
4. Heavy project workloads
"""

from typing import List, Dict, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from datetime import datetime, timedelta

from app.models.project import Project
from app.models.todo import Todo
from app.models.payment import Payment
from app.models.pending_thing import PendingThing


async def generate_proactive_suggestions(db: AsyncSession, user_id: UUID) -> List[Dict[str, Any]]:
    """Analyzes the database state and compiles active suggestions."""
    suggestions = []

    # Get user projects
    proj_stmt = select(Project).filter(Project.user_id == user_id, Project.status == "active")
    projects = (await db.execute(proj_stmt)).scalars().all()
    proj_ids = [p.id for p in projects]

    if not proj_ids:
        return []

    # 1. Check for overdue payments
    pay_stmt = select(Payment, Project.title).join(Project).filter(
        Payment.project_id.in_(proj_ids),
        Payment.status == "overdue"
    )
    overdue_payments = (await db.execute(pay_stmt)).all()
    for pay, p_title in overdue_payments:
        suggestions.append({
            "type": "payment_alert",
            "priority": "high",
            "title": f"Overdue Payment Alert for {p_title}",
            "message": f"Payment of {pay.amount:,} {pay.currency} is marked as OVERDUE. Consider reaching out to the client to send a reminder."
        })

    # 2. Check for upcoming task deadlines (within 48 hours)
    todo_stmt = select(Todo, Project.title).join(Project).filter(
        Todo.project_id.in_(proj_ids),
        Todo.status != "done",
        Todo.due_date <= datetime.now() + timedelta(days=2)
    )
    upcoming_todos = (await db.execute(todo_stmt)).all()
    for todo, p_title in upcoming_todos:
        prio = "high" if todo.priority in ["high", "critical"] else "medium"
        suggestions.append({
            "type": "deadline_alert",
            "priority": prio,
            "title": f"Approaching Task Deadline: {todo.title}",
            "message": f"Task is due soon ({todo.due_date.strftime('%Y-%m-%d')}) in project '{p_title}'. Current priority is {todo.priority.upper()}."
        })

    # 3. Check for blocker blockages
    for p in projects:
        block_stmt = select(PendingThing).filter(
            PendingThing.project_id == p.id,
            PendingThing.is_completed == False
        )
        blockers = (await db.execute(block_stmt)).scalars().all()
        if len(blockers) >= 3:
            suggestions.append({
                "type": "blocker_warning",
                "priority": "medium",
                "title": f"Roadblock build-up in '{p.title}'",
                "message": f"There are {len(blockers)} outstanding pending items / blockers from the client. Consider scheduling a weekly sync."
            })

    # 4. Check for high workload warnings
    for p in projects:
        task_count_stmt = select(Todo).filter(Todo.project_id == p.id, Todo.status != "done")
        task_count = len((await db.execute(task_count_stmt)).scalars().all())
        if task_count >= 10:
            suggestions.append({
                "type": "workload_warning",
                "priority": "low",
                "title": f"High Workload: '{p.title}'",
                "message": f"Project '{p.title}' currently has {task_count} active pending tasks. Consider breaking down items or adjusting delivery schedules."
            })

    return suggestions


async def get_suggestions_markdown(db: AsyncSession, user_id: UUID) -> str:
    """Returns a friendly markdown listing of proactive recommendations."""
    suggestions = await generate_proactive_suggestions(db, user_id)
    if not suggestions:
        return "✨ All clear! No critical alerts or suggestions at this time. Keep up the good work!"

    msg = "### 💡 Proactive Alerts & Recommendations:\n\n"
    for s in suggestions:
        prio_emoji = "🔴" if s["priority"] == "high" else "🟡" if s["priority"] == "medium" else "🔵"
        msg += f"- {prio_emoji} **{s['title']}**\n  _{s['message']}_\n"
    return msg
