"""
Reminder Service — All reminder CRUD operations.
"""
import dateutil.parser
from typing import Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.reminder import Reminder
from app.utils.timezone_helper import localize_to_utc
import logging

logger = logging.getLogger(__name__)


async def list_reminders(db, user_id):
    stmt = select(Reminder).filter(Reminder.user_id == user_id, Reminder.status == "pending").order_by(Reminder.remind_at.asc())
    reminders = (await db.execute(stmt)).scalars().all()
    if not reminders: return "No active reminders found."
    msg = "### ⏰ Active Reminders:\n\n"
    for r in reminders:
        time_str = r.remind_at.strftime("%b %d, %Y at %I:%M %p") if r.remind_at else "N/A"
        ch_emoji = "📱" if r.channel == "whatsapp" else "📧" if r.channel == "email" else "📱📧"
        msg += f"- {ch_emoji} **{r.title}** — {time_str}\n"
        if r.description: msg += f"  _{r.description}_\n"
    return msg


async def create_reminder(db, user_id, reminder_data, timezone_offset=None):
    remind_at = None
    local_remind_at = None
    if reminder_data.get("remind_at"):
        try:
            parsed_dt = dateutil.parser.parse(reminder_data["remind_at"])
            local_remind_at = parsed_dt
            remind_at = localize_to_utc(parsed_dt, timezone_offset)
        except: pass
    if not remind_at:
        return {"needs_clarification": True, "message": "I couldn't parse the time. Please specify when you want to be reminded (e.g., 'tomorrow at 9am', 'June 20 at 3pm')."}
    new_reminder = Reminder(user_id=user_id, title=reminder_data["title"], description=reminder_data.get("description"),
                            remind_at=remind_at, channel=reminder_data.get("channel") or "whatsapp", status="pending")
    db.add(new_reminder)
    await db.commit()
    await db.refresh(new_reminder)
    time_str = local_remind_at.strftime("%b %d, %Y at %I:%M %p")
    ch_label = "WhatsApp" if new_reminder.channel == "whatsapp" else "Email" if new_reminder.channel == "email" else "WhatsApp & Email"
    return {"needs_clarification": False, "message": f"✅ Reminder set: **{new_reminder.title}** on {time_str} via {ch_label}."}


async def cancel_reminder(db, user_id, title):
    if not title: return "Please specify which reminder to cancel."
    stmt = select(Reminder).filter(Reminder.user_id == user_id, Reminder.title.ilike(f"%{title}%"), Reminder.status == "pending")
    r_obj = (await db.execute(stmt)).scalars().first()
    if r_obj:
        r_obj.status = "cancelled"
        await db.commit()
        return f"Cancelled reminder '{r_obj.title}'."
    return f"Reminder '{title}' not found."


async def clear_all_reminders(db, user_id):
    stmt = select(Reminder).filter(Reminder.user_id == user_id, Reminder.status == "pending")
    reminders = (await db.execute(stmt)).scalars().all()
    count = len(reminders)
    for r in reminders: r.status = "cancelled"
    await db.commit()
    return f"Cancelled all {count} active reminders."
