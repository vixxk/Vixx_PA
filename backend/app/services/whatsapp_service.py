"""
WhatsApp Service — Handles immediate sending, scheduling, listing, and cancellation of WhatsApp messages via Green API.
"""

from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import desc

from app.models.scheduled_message import ScheduledMessage
from app.utils.green_api_helper import send_whatsapp_message, format_whatsapp_chat_id
from app.utils.timezone_helper import localize_to_utc
from app.config import settings
import logging

logger = logging.getLogger(__name__)


def resolve_default_recipient(recipient: Optional[str] = None) -> str:
    """Returns provided recipient or falls back to system configured WhatsApp/SMS number."""
    if recipient and recipient.strip():
        return recipient.strip()
    return (settings.DEFAULT_WHATSAPP_NUMBER or settings.USER_SMS_NUMBER or "").strip()


async def send_immediate(recipient: str, message: str) -> Dict[str, Any]:
    """Sends a WhatsApp message immediately via Green API."""
    target = resolve_default_recipient(recipient)
    if not target:
        return {
            "success": False,
            "error": "No recipient phone number provided or configured in .env."
        }
    return await send_whatsapp_message(target, message)


async def schedule_message(
    db: AsyncSession,
    user_id: UUID,
    recipient: str,
    message: str,
    scheduled_at: datetime,
    recipient_name: Optional[str] = None
) -> ScheduledMessage:
    """Saves a message to the database to be sent at scheduled_at time."""
    target = resolve_default_recipient(recipient)
    new_msg = ScheduledMessage(
        user_id=user_id,
        recipient=target,
        recipient_name=recipient_name,
        message=message,
        scheduled_at=scheduled_at,
        channel="whatsapp",
        status="pending"
    )
    db.add(new_msg)
    await db.commit()
    await db.refresh(new_msg)
    logger.info(f"Scheduled WhatsApp message {new_msg.id} for {target} at {scheduled_at}")
    return new_msg


async def list_scheduled_messages(
    db: AsyncSession,
    user_id: UUID,
    status: Optional[str] = "pending"
) -> List[Dict[str, Any]]:
    """Lists scheduled WhatsApp messages for the current user."""
    stmt = select(ScheduledMessage).filter(ScheduledMessage.user_id == user_id)
    if status:
        stmt = stmt.filter(ScheduledMessage.status == status)
    stmt = stmt.order_by(ScheduledMessage.scheduled_at.asc())

    result = await db.execute(stmt)
    records = result.scalars().all()
    output = []
    for r in records:
        output.append({
            "id": str(r.id),
            "recipient": r.recipient,
            "recipient_name": r.recipient_name,
            "message": r.message,
            "scheduled_at": r.scheduled_at.isoformat() if r.scheduled_at else None,
            "status": r.status,
            "sent_at": r.sent_at.isoformat() if r.sent_at else None,
            "error_message": r.error_message
        })
    return output


async def cancel_scheduled_message(
    db: AsyncSession,
    user_id: UUID,
    identifier: str
) -> Dict[str, Any]:
    """Cancels a scheduled WhatsApp message by its UUID or recipient match."""
    if not identifier:
        return {"success": False, "message": "Please specify which scheduled message to cancel."}

    cleaned = identifier.strip()
    stmt = select(ScheduledMessage).filter(
        ScheduledMessage.user_id == user_id,
        ScheduledMessage.status == "pending"
    )

    # Try UUID match first
    matched = None
    try:
        val_uuid = UUID(cleaned)
        stmt_uuid = stmt.filter(ScheduledMessage.id == val_uuid)
        res = await db.execute(stmt_uuid)
        matched = res.scalars().first()
    except ValueError:
        pass

    # Try recipient or name match
    if not matched:
        stmt_text = stmt.filter(
            (ScheduledMessage.recipient.ilike(f"%{cleaned}%")) |
            (ScheduledMessage.recipient_name.ilike(f"%{cleaned}%")) |
            (ScheduledMessage.message.ilike(f"%{cleaned}%"))
        ).order_by(desc(ScheduledMessage.created_at))
        res = await db.execute(stmt_text)
        matched = res.scalars().first()

    if matched:
        matched.status = "cancelled"
        await db.commit()
        return {
            "success": True,
            "message": f"Cancelled scheduled message to {matched.recipient_name or matched.recipient}: '{matched.message[:40]}...'"
        }

    return {"success": False, "message": f"No active scheduled message found matching '{identifier}'."}
