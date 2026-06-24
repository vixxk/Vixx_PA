"""
Analytics Service
=================
Computes project-wise financial analytics for the work OS.
"""

from typing import Dict, Any, List
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from datetime import datetime, timedelta

from app.models.project import Project
from app.models.payment import Payment


# Global in-memory cache for analytics stats
_ANALYTICS_CACHE = {}

def invalidate_analytics_cache(user_id: UUID):
    """Invalidates the analytics cache for a user when write operations occur."""
    _ANALYTICS_CACHE.pop(user_id, None)

async def get_dashboard_analytics(db: AsyncSession, user_id: UUID) -> Dict[str, Any]:
    """Generates financial analytics payload for the dashboard."""
    # Check cache
    now = datetime.now()
    if user_id in _ANALYTICS_CACHE:
        cached = _ANALYTICS_CACHE[user_id]
        if cached["expires_at"] > now:
            return cached["data"]

    # 1. Projects stats
    proj_stmt = select(Project).filter(Project.user_id == user_id)
    projects = (await db.execute(proj_stmt)).scalars().all()
    total_projects = len(projects)
    active_projects = sum(1 for p in projects if p.status in ["active", "planning", "developing"])
    completed_projects = sum(1 for p in projects if p.status in ["completed", "finished"])

    # Get project IDs
    proj_ids = [p.id for p in projects]

    if not proj_ids:
        empty_res = {
            "projects": {"total": 0, "active": 0, "completed": 0},
            "financials": {"total_earned": 0.0, "total_pending": 0.0, "total_overdue": 0.0, "currency": "INR"},
        }
        _ANALYTICS_CACHE[user_id] = {
            "data": empty_res,
            "expires_at": datetime.now() + timedelta(seconds=30)
        }
        return empty_res

    # 2. Financial metrics
    pay_stmt = select(Payment).filter(Payment.project_id.in_(proj_ids))
    payments = (await db.execute(pay_stmt)).scalars().all()
    
    total_earned = 0.0
    total_pending = 0.0
    total_overdue = 0.0

    for p in payments:
        amt = float(p.amount)
        if p.status == "received":
            total_earned += amt
        elif p.status == "pending":
            total_pending += amt
        elif p.status == "overdue":
            total_overdue += amt

    res = {
        "projects": {
            "total": total_projects,
            "active": active_projects,
            "completed": completed_projects
        },
        "financials": {
            "total_earned": total_earned,
            "total_pending": total_pending,
            "total_overdue": total_overdue,
            "currency": "INR"
        },
    }

    _ANALYTICS_CACHE[user_id] = {
        "data": res,
        "expires_at": datetime.now() + timedelta(seconds=30)
    }
    return res


async def get_analytics_markdown_summary(db: AsyncSession, user_id: UUID) -> str:
    """Generates a project-wise financial summary."""
    data = await get_dashboard_analytics(db, user_id)
    if data["projects"]["total"] == 0:
        return "No projects found. Create some projects and log payments first!"

    # Fetch projects and payments for per-project breakdown
    proj_stmt = select(Project).filter(Project.user_id == user_id)
    projects = (await db.execute(proj_stmt)).scalars().all()

    proj_ids = [p.id for p in projects]
    pay_stmt = select(Payment).filter(Payment.project_id.in_(proj_ids))
    payments = (await db.execute(pay_stmt)).scalars().all()

    msg = "## 📊 Project-wise Financial Stats\n\n"

    grand_total = 0.0
    grand_received = 0.0
    grand_remaining = 0.0

    for p in projects:
        p_payments = [pay for pay in payments if pay.project_id == p.id]
        total_amount = float(p.total_amount or 0)
        received = sum(float(pay.amount) for pay in p_payments if pay.status == "received")
        pending = sum(float(pay.amount) for pay in p_payments if pay.status == "pending")
        overdue = sum(float(pay.amount) for pay in p_payments if pay.status == "overdue")
        remaining = total_amount - received

        grand_total += total_amount
        grand_received += received
        grand_remaining += max(remaining, 0)

        status_emoji = "🟢" if remaining <= 0 and total_amount > 0 else "🟡" if received > 0 else "⚪"
        msg += f"### {status_emoji} {p.title}\n"
        msg += f"- **Total Deal**: ₹{total_amount:,.0f}\n"
        msg += f"- **Received**: ₹{received:,.0f}\n"
        if pending > 0:
            msg += f"- **Pending**: ₹{pending:,.0f}\n"
        if overdue > 0:
            msg += f"- **Overdue**: ₹{overdue:,.0f}\n"
        msg += f"- **Remaining**: ₹{max(remaining, 0):,.0f}\n\n"

    msg += "---\n"
    msg += f"**Overall**: ₹{grand_received:,.0f} received out of ₹{grand_total:,.0f} total | "
    msg += f"**₹{max(grand_remaining, 0):,.0f} remaining**\n"

    return msg

