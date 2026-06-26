from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from uuid import UUID

from app.database import get_db
from app.models.user import User
from app.models.reminder import Reminder
from app.utils.auth_helper import get_current_user

router = APIRouter(prefix="/reminders", tags=["Reminders"])


class ReminderCreate(BaseModel):
    title: str
    description: Optional[str] = None
    remind_at: str  # ISO format datetime string
    channel: Optional[str] = "sms"  # 'sms', 'email', 'both'


class ReminderUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    remind_at: Optional[str] = None
    channel: Optional[str] = None
    status: Optional[str] = None


@router.get("/")
async def list_reminders(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Reminder).filter(
        Reminder.user_id == current_user.id
    ).order_by(Reminder.created_at.desc())
    result = await db.execute(stmt)
    reminders = result.scalars().all()
    return [
        {
            "id": str(r.id),
            "title": r.title,
            "description": r.description,
            "remind_at": r.remind_at.isoformat() if r.remind_at else None,
            "channel": r.channel,
            "status": r.status,
            "sent_at": r.sent_at.isoformat() if r.sent_at else None,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in reminders
    ]


@router.post("/")
async def create_reminder(
    data: ReminderCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    import dateutil.parser
    from app.utils.timezone_helper import localize_to_utc
    try:
        parsed_dt = dateutil.parser.parse(data.remind_at)
        remind_at = localize_to_utc(parsed_dt)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid remind_at datetime format.")

    reminder = Reminder(
        user_id=current_user.id,
        title=data.title,
        description=data.description,
        remind_at=remind_at,
        channel=data.channel or "sms",
        status="pending"
    )
    db.add(reminder)
    await db.commit()
    await db.refresh(reminder)
    return {
        "id": str(reminder.id),
        "title": reminder.title,
        "description": reminder.description,
        "remind_at": reminder.remind_at.isoformat(),
        "channel": reminder.channel,
        "status": reminder.status,
        "created_at": reminder.created_at.isoformat() if reminder.created_at else None,
    }


@router.put("/{reminder_id}")
async def update_reminder(
    reminder_id: UUID,
    data: ReminderUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Reminder).filter(Reminder.id == reminder_id, Reminder.user_id == current_user.id)
    result = await db.execute(stmt)
    reminder = result.scalars().first()
    if not reminder:
        raise HTTPException(status_code=404, detail="Reminder not found.")

    if data.title is not None:
        reminder.title = data.title
    if data.description is not None:
        reminder.description = data.description
    if data.remind_at is not None:
        import dateutil.parser
        from app.utils.timezone_helper import localize_to_utc
        try:
            parsed_dt = dateutil.parser.parse(data.remind_at)
            reminder.remind_at = localize_to_utc(parsed_dt)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid remind_at format.")
    if data.channel is not None:
        reminder.channel = data.channel
    if data.status is not None:
        reminder.status = data.status

    await db.commit()
    await db.refresh(reminder)
    return {
        "id": str(reminder.id),
        "title": reminder.title,
        "remind_at": reminder.remind_at.isoformat(),
        "channel": reminder.channel,
        "status": reminder.status,
    }


@router.delete("/{reminder_id}")
async def delete_reminder(
    reminder_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Reminder).filter(Reminder.id == reminder_id, Reminder.user_id == current_user.id)
    result = await db.execute(stmt)
    reminder = result.scalars().first()
    if not reminder:
        raise HTTPException(status_code=404, detail="Reminder not found.")

    await db.delete(reminder)
    await db.commit()
    return {"success": True, "message": f"Reminder '{reminder.title}' deleted."}


@router.delete("/")
async def clear_reminders(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Reminder).filter(Reminder.user_id == current_user.id)
    result = await db.execute(stmt)
    reminders = result.scalars().all()
    count = len(reminders)
    for r in reminders:
        await db.delete(r)
    await db.commit()
    return {"success": True, "message": f"Cleared {count} reminders."}


@router.post("/test-sms")
async def test_sms_delivery(
    current_user: User = Depends(get_current_user),
):
    """Diagnostic endpoint — sends a test SMS via Twilio to verify config."""
    from app.config import settings
    from app.utils.notification_helper import send_sms

    to_number = settings.USER_SMS_NUMBER
    result = await send_sms(
        to_number,
        "🔧 Diagnostic test SMS from Vixx Personal Assistant."
    )
    return {
        "sms_result": result,
        "config": {
            "account_sid": settings.TWILIO_ACCOUNT_SID[:10] + "..." if settings.TWILIO_ACCOUNT_SID else "(empty)",
            "phone_number": settings.TWILIO_PHONE_NUMBER,
            "to": to_number,
        },
    }
